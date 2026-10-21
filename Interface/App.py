"""TouchCog Kivy launcher application: menus, videos, tasks and batteries."""
# Part of the TouchCog Kivy launcher interface (split out of KivyMenuInterface.py).

# Interface.Startup must be imported first: it configures Kivy before kivy.core.window loads.
import Interface.Startup

import csv
import atexit
import pathlib
import queue
import pandas as pd
import signal
import threading
import time
from Classes.Menu import load_protocol_module
from Classes.Protocol import ProtocolBase
from kivy.app import App
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.popup import Popup
from Interface.Startup import app_root
from Interface.Startup import config_file
from Interface.Menus import LanguageMenu
from Interface.Video import VideoScreen

class MenuApp(App):
	"""Kivy application root that drives the launcher interface.

	Manages language selection, general videos, protocol task screens, the
	file-IO worker queue for CSV/DataFrame output, and battery runs.

	Attributes
	----------
	app_root : pathlib.Path
		Root directory of the TouchCog installation.
	config : ConfigParser-like
		Application configuration (``Interface.Startup.config_file``).
	language : str
		Configured language name used to locate tutorial videos.
	s_manager : kivy.uix.screenmanager.ScreenManager
		The screen manager governing navigation.
	active_screen : str
		Name of the currently active screen.
	language_menu : Interface.Menus.LanguageMenu
		The language selection menu screen.
	general_video_screen : Interface.Video.VideoScreen or None
		The general video playback screen.
	battery_active : bool
		Whether a battery run is currently active.
	battery_protocols : list of str
		Protocol names queued for the battery run.
	battery_index : int
		Index of the current battery task.
	battery_configs : dict
		Maps protocol name to its configuration parameter dictionary.
	battery_required_fields : dict
		Maps protocol name to its list of required fields.
	first_tutorial_played : bool
		Whether the tutorial has been shown at least once.
	event_queue : queue.Queue
		Queue of pending event rows for the event-writer thread.
	file_io_queue : queue.Queue
		Queue of jobs for the file-IO worker thread.
	event_list : list
		Accumulated session event rows.
	event_columns : list of str
		Column names for the session event DataFrame.
	trial_summary_data : list
		Accumulated trial summary rows.
	trial_summary_cols : list of str
		Column names for the trial summary DataFrame.
	survey_data_list : list
		Accumulated survey response rows.
	session_event_path : str
		Output path for the session event DataFrame.
	summary_event_path : str
		Output path for the trial summary DataFrame.
	survey_data_path : str
		Output path for the survey DataFrame.
	data_written : bool
		Whether CSV output has already been written.
	file_io_thread : threading.Thread
		Daemon thread running ``_file_io_worker``.
	"""
	
	def build(self):
		"""Build and return the application's screen manager.

		Initialises session, trial-summary and survey data containers, starts the
		file-IO worker thread, creates the language menu and general video
		screens, and registers shutdown handlers.

		Returns
		-------
		kivy.uix.screenmanager.ScreenManager
			The fully assembled screen manager.
		"""
		self.app_root = app_root

		self.session_event_data = pd.DataFrame()
		self.session_event_path = ''
		self.summary_event_data = pd.DataFrame()
		self.summary_event_path = ''
		self.trial_summary_data = list()
		self.trial_summary_cols = list()
		self.survey_data = pd.DataFrame()
		self.survey_data_path = ''
		self.survey_data_list = list()
		self.event_queue = queue.Queue()
		self.file_io_queue = queue.Queue()
		self.event_list = list()
		self.event_columns = list()
		self.data_written = False
		self.file_io_thread = threading.Thread(target=self._file_io_worker, daemon=True)
		self.file_io_thread.start()

		self.battery_active = False
		self._pending_completions = set()
		self.battery_protocols = list()
		self.battery_index = 0
		self.battery_configs = {}
		self.battery_required_fields = {}  # Maps protocol name to list of required fields

		self.first_tutorial_played = False

		self.s_manager = ScreenManager()
		self.active_screen = ''
		self.config = config_file
		self.language = self.config.get('language', 'language', fallback='English')
		self.language_menu = LanguageMenu()
		self.replace_screen(self.language_menu)
		self.general_video_screen = VideoScreen()
		self.replace_screen(self.general_video_screen)
		self.active_screen = self.language_menu.name
		self._register_shutdown_handlers()
		
		return self.s_manager

	def _register_shutdown_handlers(self):
		"""Register atexit and signal handlers that flush pending output data.

		Registers ``_write_pending_output_data`` with atexit and installs it as the
		handler for ``SIGINT`` and ``SIGTERM``. Registration runs once; later calls
		return immediately.
		"""
		if getattr(self, '_shutdown_handlers_registered', False):
			return

		atexit.register(self._write_pending_output_data)
		for signal_name in ('SIGINT', 'SIGTERM'):
			try:
				signal.signal(getattr(signal, signal_name), self._handle_shutdown_signal)
			except (AttributeError, ValueError):
				pass
		self._shutdown_handlers_registered = True

	def _handle_shutdown_signal(self, signum, frame):
		"""Flush pending output data and stop the app on a shutdown signal.

		Calls ``_write_pending_output_data`` then ``self.stop()``; any exception
		during shutdown is ignored (best effort).

		Parameters
		----------
		signum : int
			The received signal number.
		frame : frame or None
			The current stack frame supplied by the signal handler.
		"""
		self._write_pending_output_data()
		try:
			self.stop()
		except Exception:
			# shutdown, best effort
			pass

	def _run_file_job(self, job, path):
		"""Run a single file job against the given output path.

		Parameters
		----------
		job : dict
			Job description containing the action and its payload.
		path : str
			Path of the output file.

		Raises
		------
		OSError
			If the output file cannot be opened or written.

		Notes
		-----
		Dispatch is by the job's ``'action'`` key: ``'write_header'`` writes a CSV
		header row of ``job['columns']``; ``'append_row'`` appends a CSV row of
		``job['row']``; ``'write_dataframe'`` writes ``job['dataframe']`` via
		``to_csv`` with ``job.get('index', False)``. The header write opens the file
		in ``'w'`` mode (creating or truncating it), the row append in ``'a'`` mode;
		both use UTF-8 with ``newline=''``. ``to_csv`` overwrites the file.
		"""
		action = job.get('action')
		if action == 'write_header':
			with open(path, 'w', newline='', encoding='utf-8') as output_file:
				writer = csv.writer(output_file)
				writer.writerow(job['columns'])
		elif action == 'append_row':
			with open(path, 'a', newline='', encoding='utf-8') as output_file:
				writer = csv.writer(output_file)
				writer.writerow(job['row'])
		elif action == 'write_dataframe':
			job['dataframe'].to_csv(path, index=job.get('index', False))

	def _file_io_worker(self):
		"""Consume and execute jobs from the file-IO queue on this thread.

		Runs until a ``None`` sentinel is received. Each job is attempted up to
		three times with a 0.5 second pause between failures; if it still fails it
		is retried against a sibling ``_unsaved`` file, and errors are logged via
		Kivy's logger.
		"""
		while True:
			job = self.file_io_queue.get()
			try:
				if job is None:
					return

				# Retry briefly (e.g. file locked by Excel/OneDrive), then fall back to a
				# sibling '_unsaved' file so trial data is never silently dropped.
				last_error = None
				for attempt in range(3):
					try:
						self._run_file_job(job, job['path'])
						last_error = None
						break
					except OSError as e:
						last_error = e
						time.sleep(0.5)

				if last_error is not None:
					original_path = pathlib.Path(job['path'])
					fallback_path = original_path.with_name(original_path.stem + '_unsaved' + original_path.suffix)
					Logger.warning(f'TouchCog: could not write {original_path} ({last_error}); writing to {fallback_path}')
					try:
						self._run_file_job(job, fallback_path)
					except OSError as e:
						Logger.error(f'TouchCog: could not write fallback file {fallback_path}: {e}')
			except Exception:
				Logger.exception('TouchCog: file write job failed')
			finally:
				self.file_io_queue.task_done()

	def queue_csv_header(self, path, columns):
		"""Queue a CSV header write for the given path.

		Parameters
		----------
		path : str
			Path of the CSV file to write.
		columns : iterable of str
			Column names for the header row.

		Notes
		-----
		Adds a ``'write_header'`` job to ``file_io_queue`` wrapping the columns as
		a list; returns without queuing when ``path`` is empty.
		"""
		if not path:
			return
		self.file_io_queue.put({
			'action': 'write_header',
			'path': str(path),
			'columns': list(columns),
		})

	def queue_csv_row(self, path, row):
		"""Queue a CSV row append for the given path.

		Parameters
		----------
		path : str
			Path of the CSV file to write.
		row : iterable
			Values of the row to append.

		Notes
		-----
		Adds an ``'append_row'`` job to ``file_io_queue`` wrapping the row as a
		list; returns without queuing when ``path`` is empty.
		"""
		if not path:
			return
		self.file_io_queue.put({
			'action': 'append_row',
			'path': str(path),
			'row': list(row),
		})

	def queue_dataframe_write(self, path, dataframe, index=False):
		"""Queue a DataFrame write for the given path.

		Parameters
		----------
		path : str
			Path of the output file.
		dataframe : pandas.DataFrame
			Data to write to the file.
		index : bool, optional
			Whether to write the row index. Defaults to False.

		Notes
		-----
		Adds a ``'write_dataframe'`` job to ``file_io_queue``; returns without
		queuing when ``path`` is empty.
		"""
		if not path:
			return
		self.file_io_queue.put({
			'action': 'write_dataframe',
			'path': str(path),
			'dataframe': dataframe,
			'index': index,
		})

	def _drain_file_io_queue(self):
		"""Block until all queued file-IO jobs have completed.

		Calls ``join()`` on ``file_io_queue`` when it exists so the current thread
		waits for outstanding file writes.
		"""
		if hasattr(self, 'file_io_queue'):
			self.file_io_queue.join()

	def _finalize_event_queue(self):
		"""Stop the event-writer thread and drain any remaining event rows.

		If an ``event_writer_thread`` is alive a ``None`` sentinel is queued and the
		thread is joined with a 2.0 second timeout, then any leftover event rows on
		``event_queue`` are appended to ``event_list``.
		"""
		event_thread = getattr(self, 'event_writer_thread', None)
		if event_thread is not None and event_thread.is_alive():
			self.event_queue.put(None)
			event_thread.join(timeout=2.0)

		while True:
			try:
				event_row = self.event_queue.get_nowait()
			except queue.Empty:
				break

			if event_row is not None:
				self.event_list.append(event_row)

	def _write_pending_output_data(self):
		"""Write all pending session, trial-summary and survey data to CSV.

		Finalizes the event queue, then, when data has not yet been written, builds
		and queues DataFrames: session events sorted by ``'Time'``, trial summaries
		and surveys (columns ``'question'`` and ``'response'``). Each is written
		only when its output path is set and its data list is non-empty. Finally the
		file-IO queue is drained.
		"""
		if not hasattr(self, 'event_queue'):
			return

		self._finalize_event_queue()

		if (not self.data_written) and self.session_event_path and len(self.event_list) > 0:
			self.session_event_data = pd.DataFrame(self.event_list, columns=self.event_columns)
			if not self.session_event_data.empty:
				self.session_event_data = self.session_event_data.sort_values(by=['Time'])
			self.queue_dataframe_write(self.session_event_path, self.session_event_data, index=False)

		if (not self.data_written) and self.summary_event_path and len(self.trial_summary_data) > 0:
			self.summary_event_data = pd.DataFrame(self.trial_summary_data, columns=self.trial_summary_cols)
			self.queue_dataframe_write(self.summary_event_path, self.summary_event_data, index=False)

		if (not self.data_written) and self.survey_data_path and len(self.survey_data_list) > 0:
			self.survey_data = pd.DataFrame(self.survey_data_list, columns=['question', 'response'])
			self.queue_dataframe_write(self.survey_data_path, self.survey_data, index=False)

		self._drain_file_io_queue()

	def _set_current_screen(self, screen_name, *args):
		"""Switch the active screen to the named screen if it exists.

		Parameters
		----------
		screen_name : str
			Name of the screen to activate.
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. dt).
		"""
		if self.s_manager.has_screen(screen_name):
			self.active_screen = screen_name
			self.s_manager.current = screen_name

	def open_main_menu(self, *args):
		"""Navigate to the main menu screen.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		self._set_current_screen('mainmenu')

	def show_general_video(self, video_key, on_complete=None, destination_screen=None):
		"""Show the general (tutorial, next-task, end-session) video screen.

		Creates the video screen if needed, sizes it to the window and prepares the
		requested video. If preparation succeeds the video screen is shown;
		otherwise the next action is scheduled on the Kivy Clock: the completion
		callback, the destination screen, or the main menu.

		Parameters
		----------
		video_key : str
			Key identifying which video to play (``'tutorial'``, ``'next_task'`` or
			``'end_session'``).
		on_complete : callable, optional
			Callback invoked when the video completes. Defaults to None.
		destination_screen : str, optional
			Screen to switch to on completion when no callback is set. Defaults to None.
		"""
		if not hasattr(self, 'general_video_screen') or self.general_video_screen is None:
			self.general_video_screen = VideoScreen()
			self.replace_screen(self.general_video_screen)

		self.general_video_screen.size = Window.size
		prepared = self.general_video_screen.prepare_video(
			video_key,
			on_complete=on_complete,
			destination_screen=destination_screen
		)

		if prepared:
			self._set_current_screen(self.general_video_screen.name)
		elif callable(on_complete):
			Clock.schedule_once(lambda dt: on_complete(), 0)
		elif destination_screen:
			Clock.schedule_once(lambda dt: self._set_current_screen(destination_screen), 0)
		else:
			Clock.schedule_once(self.open_main_menu, 0)

	def present_task_screen(self, screen_name):
		"""Show the tutorial before a task on its first run, else show the task.

		On the first call the tutorial video is shown and completes by switching to
		``screen_name``; on subsequent calls the task screen is shown directly.

		Parameters
		----------
		screen_name : str
			Name of the task screen to present.
		"""
		if not self.first_tutorial_played:
			self.first_tutorial_played = True
			self.show_general_video('tutorial', on_complete=lambda: self._set_current_screen(screen_name))
		else:
			self._set_current_screen(screen_name)

	def replace_screen(self, screen):
		"""Add a screen to the manager, removing any same-named older screen.

		ScreenManager resolves names to the first match, so any existing screens
		with the same name (other than the one given) are cleared of video caches
		and removed before the new screen is added.

		Parameters
		----------
		screen : kivy.uix.screenmanager.Screen
			The screen to install.
		"""
		# ScreenManager resolves names to the FIRST match, so never keep two screens with one name
		for old in [x for x in self.s_manager.screens if x.name == screen.name and x is not screen]:
			if hasattr(old, 'clear_video_cache'):
				try:
					old.clear_video_cache()
				except Exception:
					Logger.warning('TouchCog: clear_video_cache failed')
			self.s_manager.remove_widget(old)
		self.s_manager.add_widget(screen)

	def cleanup_task_screen(self, screen_name):
		"""Clear the video cache of a task screen and remove it from the manager.

		Parameters
		----------
		screen_name : str
			Name of the task screen to remove.
		"""
		if not screen_name or not self.s_manager.has_screen(screen_name):
			return

		screen = self.s_manager.get_screen(screen_name)
		if hasattr(screen, 'clear_video_cache'):
			try:
				screen.clear_video_cache()
			except Exception:
				Logger.warning('TouchCog: clear_video_cache failed')

		self.s_manager.remove_widget(screen)

	def handle_task_completion(self, completed_screen_name=None):
		"""Handle a task's completion during a normal or battery run.

		Ignores duplicate completion calls (double tap) for an already-removed or
		pending screen. In a battery run control passes to
		``battery_task_finished``; otherwise the task screen is cleaned up and the
		end-session video is shown before returning to the main menu.

		Parameters
		----------
		completed_screen_name : str or None
			Name of the completing task screen, if any.
		"""
		# Ignore repeat calls (double tap): the screen is already gone or its transition is pending
		if completed_screen_name and (not self.s_manager.has_screen(completed_screen_name)
				or completed_screen_name in self._pending_completions):
			return
		if getattr(self, 'battery_active', False):
			self.battery_task_finished(completed_screen_name)
			return

		self.cleanup_task_screen(completed_screen_name)
		self.show_general_video('end_session', on_complete=self.open_main_menu)
	
	def start_next_battery_config(self):
		"""Show the configure screen for the next battery protocol, or start tasks.

		Advances through ``battery_protocols``. Surveys and preloaded protocols with
		an empty required-fields list skip their configure screen. Otherwise the
		protocol's configure screen is built, updated for battery mode, applied with
		external parameters from ``battery_configs``, and installed as the current
		screen. When the end of the list is reached, ``battery_index`` resets and
		``start_battery_tasks`` begins the run.
		"""
		if self.battery_index < len(self.battery_protocols):
			protocol_name = self.battery_protocols[self.battery_index]
			# Skip surveys - they don't have configuration screens in battery mode
			task_type = self.battery_task_types.get(protocol_name, 'task')
			if task_type == 'survey':
				# For surveys, skip configuration and move to next
				self.battery_index += 1
				self.start_next_battery_config()
				return
			
			# Check if this protocol has required fields
			required_fields = self.battery_required_fields.get(protocol_name)
			
			# Show configure screen if:
			# 1. required_fields is None (manual battery - always show menu)
			# 2. required_fields is a non-empty list (preloaded battery with filtering)
			# Skip configure screen if required_fields is an empty list (preloaded battery with all fields pre-configured)
			if required_fields is not None and len(required_fields) == 0:
				# No required fields in preloaded battery: use pre-loaded config and skip configure screen
				self.battery_index += 1
				self.start_next_battery_config()
				return
			
			# Show configure screen (either manual battery or preloaded with required fields)
			protocol_module = load_protocol_module(app_root, protocol_name, 'Menu')
			config_screen = protocol_module.ConfigureScreen()
			config_screen.update_battery_mode(True, required_fields)
			config_screen.size = Window.size
			# Update the config_screen parameters based on self.battery_configs[protocol_name] if available
			if protocol_name in self.battery_configs:
				config_screen.update_parameters_external(self.battery_configs[protocol_name])
			self.replace_screen(config_screen)
			self.s_manager.current = config_screen.name
		else:
			self.battery_index = 0
			self.start_battery_tasks()
	
	def start_battery_tasks(self):
		"""Start the battery task at the current battery index, or end the run.

		With no protocols the main menu is opened and ``battery_active`` is cleared.
		Otherwise the task or survey screen for the current protocol is built and
		presented; task-type screens receive their parameters. A half-initialised
		task aborts the battery, popping up an error and returning to the main menu.
		When the end of the list is reached ``battery_active`` is cleared and the
		end-session video leads back to the main menu.
		"""
		# Start the task at the current battery_index (do not reset here)
		if not self.battery_protocols:
			self.open_main_menu()
			self.battery_active = False
			return

		if self.battery_index < len(self.battery_protocols):
			protocol_name = self.battery_protocols[self.battery_index]
			parameter_dict = self.battery_configs[protocol_name] if protocol_name in self.battery_configs else {}
			if (app_root / 'Protocol' / protocol_name / 'Task' / 'Menu.py').is_file():
				task_module = load_protocol_module(app_root, protocol_name, 'Protocol')
				protocol_task_screen = task_module.ProtocolScreen(screen_resolution=Window.size)
			else:
				task_module = load_protocol_module(app_root, protocol_name, 'Protocol')
				protocol_task_screen = task_module.SurveyProtocol()
			self.replace_screen(protocol_task_screen)
			# Provide parameters to the task only for 'task' types (not surveys)
			try:
				task_type = self.battery_task_types.get(protocol_name, 'task') if hasattr(self, 'battery_task_types') else 'task'
				if task_type == 'task' and hasattr(protocol_task_screen, 'load_parameters'):
					protocol_task_screen.load_parameters(parameter_dict)
			except Exception as e:
				# A half-initialised task would silently produce bad data: abort the battery
				Logger.exception(f"Battery: failed to load parameters for {protocol_name}")
				self.cleanup_task_screen(protocol_task_screen.name)
				self.battery_active = False
				Popup(title='Task failed to load', content=Label(text=f"{protocol_name}: {e}"), size_hint=(0.6, 0.4)).open()
				self.open_main_menu()
				return
			self.present_task_screen(protocol_task_screen.name)
		else:
			# No more tasks in battery
			self.battery_active = False
			self.show_general_video('end_session', on_complete=self.open_main_menu)

	def battery_task_finished(self, completed_screen_name=None):
		"""Record a completed battery task and schedule the next transition.

		Adds the completed screen to ``_pending_completions`` and schedules
		``_perform_battery_transition`` on the Kivy Clock after 0.2 seconds. Does
		nothing unless a battery run is active.

		Parameters
		----------
		completed_screen_name : str or None
			Name of the completing task screen, if any.
		"""
		# Only advance if a battery run is active
		if not getattr(self, 'battery_active', False):
			return
		
		self._pending_completions.add(completed_screen_name)
		Clock.schedule_once(lambda dt: self._perform_battery_transition(completed_screen_name), 0.2)

	def _perform_battery_transition(self, completed_screen_name, *args):
		"""Advance the battery to the next task after one completes.

		Removes the completed screen from ``_pending_completions``, cleans it up and
		increments ``battery_index``. If more tasks remain the next-task video leads
		into ``start_battery_tasks``; otherwise the battery ends with the end-session
		video.

		Parameters
		----------
		completed_screen_name : str or None
			Name of the just-completed task screen, if any.
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch (dt).
		"""
		self._pending_completions.discard(completed_screen_name)
		self.cleanup_task_screen(completed_screen_name)
		self.battery_index = int(self.battery_index) + 1
		if self.battery_index < len(self.battery_protocols):
			self.show_general_video('next_task', on_complete=self.start_battery_tasks)
		else:
			# Finished all battery tasks
			self.battery_active = False
			self.show_general_video('end_session', on_complete=self.open_main_menu)
	
	def on_stop(self):
		"""Flush pending data and clear the current protocol screen's video cache.

		Writes pending output data, then, as a best-effort step, calls
		``clear_video_cache`` on the current screen when it is a protocol screen
		(an instance of ``ProtocolBase`` or named ``'ProtocolScreen'``); failures
		are ignored during shutdown.
		"""
		self._write_pending_output_data()
		try:
				# Only call clear_video_cache() if current_screen is a protocol-related
				# screen. ProtocolScreen subclasses ProtocolBase in protocol modules,
				# but some protocol task screens may not directly import ProtocolBase
				# here; checking for the base class and the class name covers both
				# cases.
			current = getattr(self.s_manager, 'current_screen', None)
			if current is None:
				raise AttributeError('no current screen')

			is_protocol = isinstance(current, ProtocolBase) or current.__class__.__name__ == 'ProtocolScreen'
			if is_protocol and hasattr(current, 'clear_video_cache'):
				current.clear_video_cache()

		except Exception:
			# Best-effort: ignore failures during shutdown
			pass
