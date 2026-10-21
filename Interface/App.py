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
	
	def build(self):
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
		self._write_pending_output_data()
		try:
			self.stop()
		except Exception:
			# shutdown, best effort
			pass

	def _run_file_job(self, job, path):
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
		if not path:
			return
		self.file_io_queue.put({
			'action': 'write_header',
			'path': str(path),
			'columns': list(columns),
		})

	def queue_csv_row(self, path, row):
		if not path:
			return
		self.file_io_queue.put({
			'action': 'append_row',
			'path': str(path),
			'row': list(row),
		})

	def queue_dataframe_write(self, path, dataframe, index=False):
		if not path:
			return
		self.file_io_queue.put({
			'action': 'write_dataframe',
			'path': str(path),
			'dataframe': dataframe,
			'index': index,
		})

	def _drain_file_io_queue(self):
		if hasattr(self, 'file_io_queue'):
			self.file_io_queue.join()

	def _finalize_event_queue(self):
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
		if self.s_manager.has_screen(screen_name):
			self.active_screen = screen_name
			self.s_manager.current = screen_name

	def open_main_menu(self, *args):
		self._set_current_screen('mainmenu')

	def show_general_video(self, video_key, on_complete=None, destination_screen=None):
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
		if not self.first_tutorial_played:
			self.first_tutorial_played = True
			self.show_general_video('tutorial', on_complete=lambda: self._set_current_screen(screen_name))
		else:
			self._set_current_screen(screen_name)

	def replace_screen(self, screen):
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
		"""Called by a protocol when it returns to the main menu during a battery run.
		This advances the battery index and starts the next task if available.
		"""
		# Only advance if a battery run is active
		if not getattr(self, 'battery_active', False):
			return
		
		self._pending_completions.add(completed_screen_name)
		Clock.schedule_once(lambda dt: self._perform_battery_transition(completed_screen_name), 0.2)

	def _perform_battery_transition(self, completed_screen_name, *args):
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
