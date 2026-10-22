"""Base classes and widgets shared by all protocol task screens."""
# Import

import configparser
import datetime
import pandas as pd
import pathlib
import time
import threading
import queue
import random
import gc
import math
from collections import Counter
from ffpyplayer.player import MediaPlayer

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.loader import Loader
from kivy.uix.button import ButtonBehavior, Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.config import Config
from kivy.logger import Logger

from Classes.DataFiles import DATA_FOLDER, next_free_path, sanitize_participant_id






class ImageButton(ButtonBehavior, Image):
	"""Image widget that behaves as a button with move-out release tracking.

	on_release is dispatched once per pressed interval: when the grabbed touch
	slides off the widget, or when it lifts inside, whichever comes first. Sliding
	back in starts a new press (on_press, then another on_release).

	Attributes
	----------
	coord : object or None
		Arbitrary coordinate value attached to the button (default None).
	fit_mode : str
		Image fit mode. Defaults to ``'fill'``.
	touch_pos : tuple of (int, int)
		Most recent touch position passed to the button.
	name : str
		Stimulus name used when the button is touched or held.
	_grabbed_touch : kivy.input.MotionEvent or None
		The touch that initiated the press on this widget.
	_touch_inside : bool
		Whether the grabbed touch is currently inside the widget.
	"""

	def __init__(self, **kwargs):
		"""Initialise the button and its touch-tracking state.

		Parameters
		----------
		**kwargs : dict
			Additional keyword arguments passed to
			:class:`kivy.uix.button.ButtonBehavior` and :class:`kivy.uix.image.Image`.
		"""

		super(ImageButton, self).__init__(**kwargs)
		self.coord = None
		self.fit_mode = 'fill'
		self.touch_pos = (0, 0)
		self.name = ''

		# Internal touch tracking for move-out release behaviour
		# _grabbed_touch: the current touch instance that began a press on this widget
		# _touch_inside: whether that touch is currently inside the widget
		self._grabbed_touch = None
		self._touch_inside = False


	def on_touch_down(self, touch):
		"""Track a press on this widget and let the base button handle it.

		When the widget is disabled the event is ignored. Touches outside the
		widget propagate normally; a handled touch that begins inside is stored as
		the grabbed touch for move/release tracking.

		Parameters
		----------
		touch : kivy.input.MotionEvent
			The touch event to handle.

		Returns
		-------
		bool
			True if the touch was consumed, False otherwise.
		"""
		# Only start tracking if the touch is within this widget and the widget is enabled
		if self.disabled:
			return False

		if not self.collide_point(*touch.pos):
			# Let normal propagation occur
			return super(ImageButton, self).on_touch_down(touch)

		# Let ButtonBehavior handle press/state changes
		handled = super(ImageButton, self).on_touch_down(touch)
		if handled:
			self._grabbed_touch = touch
			self._touch_inside = True
		return handled


	def on_touch_move(self, touch):
		"""Release or re-press the button as the grabbed touch crosses the boundary.

		If the grabbed touch moves outside while the button is down, an on_release
		is dispatched and the grab is dropped. If it moves back inside while up,
		the button is grabbed and pressed again. Moves for other touches pass
		through to the base widget.

		Parameters
		----------
		touch : kivy.input.MotionEvent
			The touch event to handle.

		Returns
		-------
		bool
			True when the move was consumed, otherwise the base class result.
		"""
		# If this move is not for the touch that initiated the press, pass through
		if touch is not self._grabbed_touch:
			return super(ImageButton, self).on_touch_move(touch)

		inside = self.collide_point(*touch.pos)

		# If the touch moved outside while the button was pressed, release it
		if not inside and self._touch_inside:
			# Only trigger a release if the button was down
			if getattr(self, 'state', None) == 'down':
				# Dispatch on_release so listeners are notified
				try:
					self.dispatch('on_release')
				except Exception:
					Logger.exception('TouchCog: ImageButton on_release failed')
				# ensure visual/state is normal
				self.state = 'normal'
			# drop the grab so ButtonBehavior cannot dispatch a second on_release at lift
			touch.ungrab(self)
			self._touch_inside = False
			# consume the move event
			return True

		# If moved back inside, press it again
		if inside and not self._touch_inside:
			if getattr(self, 'state', None) != 'down':
				# re-grab so ButtonBehavior dispatches the single on_release at lift
				touch.grab(self)
				self._do_press()
				try:
					self.dispatch('on_press')
				except Exception:
					Logger.exception('TouchCog: ImageButton on_press failed')
			self._touch_inside = True
			# consume the move event
			return True

		# Otherwise, nothing special to do
		return True


	def on_touch_up(self, touch):
		"""Release the grabbed touch and clear the tracking state.

		If the touch is still inside and the button is down, the base class handles
		the release. Otherwise a release is dispatched directly if the button is
		still down (e.g. after a move-out release), and the tracking state is
		reset.

		Parameters
		----------
		touch : kivy.input.MotionEvent
			The touch event to handle.

		Returns
		-------
		bool
			True when the event was consumed, otherwise the base class result.
		"""
		# If this up event is not the one we tracked, pass through
		if touch is not self._grabbed_touch:
			return super(ImageButton, self).on_touch_up(touch)

		# If the touch is still inside and the button is down, let ButtonBehavior handle release
		if self._touch_inside and getattr(self, 'state', None) == 'down':
			res = super(ImageButton, self).on_touch_up(touch)
		else:
			# If we already released due to move-out, ensure state is normal and do not dispatch again
			if getattr(self, 'state', None) == 'down':
				try:
					self.dispatch('on_release')
				except Exception:
					Logger.exception('TouchCog: ImageButton on_release failed')
				self.state = 'normal'
			res = True

		# Clear tracked touch
		self._grabbed_touch = None
		self._touch_inside = False
		return res




class FloatLayoutLog(FloatLayout):
	"""Float layout that logs touch and stimulus events for protocol task screens.

	Events are queued as rows of ``app.event_columns`` and drained by a background
	writer thread; each row is also queued to the session event CSV. Tracks active
	touches to detect multi-touch, during which child touches are blocked.

	Attributes
	----------
	app : kivy.app.App
		The running TouchCog app.
	width : int
		Screen width in pixels (from ``screen_resolution``).
	height : int
		Screen height in pixels (from ``screen_resolution``).
	width_min : float
		Minimum X movement for a move to be logged (``width / 100``).
	height_min : float
		Minimum Y movement for a move to be logged (``height / 100``).
	event_columns : list of str
		Column names of the event data (Time, Event_Type, Event_Name, Arg1-3 pairs).
	session_event_data : pandas.DataFrame
		DataFrame of the logged events.
	save_path : pathlib.Path or str
		Path of the session event CSV file.
	touch_time : float
		Seconds since ``start_time`` at the last touch (``time.perf_counter``).
	start_time : float
		Reference timestamp set by :meth:`set_start_time`.
	active_touches : set
		Uids of the currently active touches.
	multi_touch_active : bool
		Whether more than one touch is currently active.
	block_on_move_touch_down : bool
		Whether touch-downs triggered during moves are suppressed.
	"""
	
	def __init__(self, screen_resolution, **kwargs):
		"""Initialise the layout, its event queue and its writer thread.

		Sets up the event columns and DataFrame, stops and joins any previous
		event-writer thread held on the app, then starts a fresh daemon writer
		thread for this layout's queue.

		Parameters
		----------
		screen_resolution : tuple of (int, int)
			Screen width and height in pixels.
		**kwargs : dict
			Additional keyword arguments passed to :class:`kivy.uix.floatlayout.FloatLayout`.
		"""

		super(FloatLayoutLog, self).__init__(**kwargs)
		self.register_event_type('on_multi_touch')
		
		self.app = App.get_running_app()
		self.block_on_move_touch_down = False
		self.touch_pos = [0, 0]
		self.last_recorded_pos = [0, 0]
		self.width = screen_resolution[0]
		self.height = screen_resolution[1]
		self.width_min = self.width / 100
		self.height_min = self.height / 100
		self.held_name = ''
		
		self.app.event_columns = [
			'Time'
			, 'Event_Type'
			, 'Event_Name'
			, 'Arg1_Name'
			, 'Arg1_Value'
			, 'Arg2_Name'
			, 'Arg2_Value'
			, 'Arg3_Name'
			, 'Arg3_Value'
			]
		
		self.app.session_event_data = pd.DataFrame(columns=self.app.event_columns)
		self.save_path = ''
		self.touch_time = 0
		self.start_time = 0
		self.active_touches = set()
		self.multi_touch_active = False

		# Stop any previous writer and give this layout its own queue, so events
		# logged after a prior task ended cannot leak into this task's data.
		previous_thread = getattr(self.app, 'event_writer_thread', None)
		if previous_thread is not None and previous_thread.is_alive():
			self.app.event_queue.put(None)
			previous_thread.join(timeout=1.0)
		# Reset only after the previous writer has stopped, so its queued events cannot land here.
		self.app.event_list = list()
		self.event_queue = queue.Queue()
		self.app.event_queue = self.event_queue

		self._event_writer_thread = threading.Thread(target=self.event_writer, daemon=True)
		self._event_writer_thread.start()
		self.app.event_writer_thread = self._event_writer_thread
	
	def event_writer(self):
		"""Drain the event queue until the ``None`` sentinel is received.

		Each queued row is appended to ``self.app.event_list`` and passed to
		:meth:`_append_event_row`. A ``None`` sentinel stops the thread.
		"""
		while True:
			try:
				event_row = self.event_queue.get()
				if event_row is None: # Sentinel to stop the thread
					break
				self.app.event_list.append(event_row)
				self._append_event_row(event_row)
			except queue.Empty:
				continue # Should not happen with blocking get()

	def _append_event_row(self, event_row):
		"""Queue one event row to the session event CSV, if a path is set.

		Builds a row of cell values from ``self.app.event_columns`` and queues it
		for writing via ``self.app.queue_csv_row`` to ``self.app.session_event_path``.
		Does nothing when no session event path is set.

		Parameters
		----------
		event_row : dict
			The event values keyed by event column name.
		"""
		if not getattr(self.app, 'session_event_path', ''):
			return

		row = [event_row.get(column, '') for column in self.app.event_columns]
		self.app.queue_csv_row(self.app.session_event_path, row)
	
	def on_multi_touch(self, touch, touch_count):
		"""Handle the custom multi-touch event (default handler; does nothing).

		Parameters
		----------
		touch : kivy.input.MotionEvent
			The touch that caused the second simultaneous touch.
		touch_count : int
			Number of active touches.
		"""
		return

	def _track_touch_down(self, touch):
		"""Record a touch-down and raise the multi-touch event on a second touch.

		Adds the touch uid to ``active_touches``. When a second touch begins, sets
		``multi_touch_active``, releases any child currently in the down state, and
		dispatches the ``on_multi_touch`` event.

		Parameters
		----------
		touch : kivy.input.MotionEvent
			The touch that went down.
		"""
		touch_uid = getattr(touch, 'uid', None)
		if touch_uid is None:
			return

		self.active_touches.add(touch_uid)
		if len(self.active_touches) > 1 and not self.multi_touch_active:
			self.multi_touch_active = True

			for child in self.children:
				if getattr(child, 'state', None) == 'down':
					child.state = 'normal'
					if hasattr(child, '_touch_inside'):
						child._touch_inside = False

			self.dispatch('on_multi_touch', touch, len(self.active_touches))

	def _track_touch_up(self, touch):
		"""Remove a touch uid and clear multi-touch when one touch remains.

		Parameters
		----------
		touch : kivy.input.MotionEvent
			The touch that went up.
		"""
		touch_uid = getattr(touch, 'uid', None)
		if touch_uid is not None:
			self.active_touches.discard(touch_uid)

		if len(self.active_touches) <= 1:
			self.multi_touch_active = False
	
	
	
	def on_touch_down(self, touch):
		"""Log a touch press, blocking it during multi-touch.

		Tracks the touch, records its position and a ``time.perf_counter`` timestamp
		relative to ``start_time``, and forwards the event to children. During
		multi-touch the press is logged as blocked and consumed; a handled child
		press is logged using the child's name for an ``ImageButton``.

		Parameters
		----------
		touch : kivy.input.MotionEvent
			The touch event to handle.

		Returns
		-------
		bool or None
			True when the event was consumed; None when no child handled it (and the
			layout is not disabled).
		"""

		self._track_touch_down(touch)
		self.touch_pos = touch.pos
		self.touch_time = time.perf_counter() - self.start_time
		
		if self.disabled and self.collide_point(*touch.pos):
			return True
		
		if self.multi_touch_active:
			self.held_name = ''
			self._log_touch('Touch Press (Blocked)', 'Multi-Touch')
			return True
		
		for child in self.children[:]:
			
			if child.dispatch('on_touch_down', touch):
				
				if isinstance(child, ImageButton):
					self.held_name = child.name
				
				else:
					self.held_name = ''
				
				self._log_touch('Touch Press', self.held_name)
				
				return True
		
		self.held_name = ''

		self._log_touch('Touch Press', self.held_name)
	
	
	
	def on_touch_move(self, touch):
		"""Log touch moves, re-dispatching down events when sliding into children.

		Records position and relative timestamp, and forwards the move to children,
		optionally logging a press when a move first enters a child (unless
		``block_on_move_touch_down``). A ``Touch Move`` event is logged whenever the
		position has moved at least ``width_min``/``height_min`` since the last
		recorded position.

		Parameters
		----------
		touch : kivy.input.MotionEvent
			The touch event to handle.

		Returns
		-------
		bool or None
			True when the event was consumed; None when disabled or no child handled it.
		"""

		self.touch_pos = touch.pos
		self.touch_time = time.perf_counter() - self.start_time
		
		if self.disabled:
			return
		
		if self.multi_touch_active:
			return True
		
		for child in self.children[:]:
			
			if not self.block_on_move_touch_down:
				if child.collide_point(*touch.pos):
					if child.dispatch('on_touch_down', touch):
						# a press that started by sliding in
						self._log_touch('Touch Press', child.name if isinstance(child, ImageButton) else '')

			if child.dispatch('on_touch_move', touch):
				
				if isinstance(child, ImageButton):
					self.held_name = child.name
				
				else:
					self.held_name = ''
				
				
				if (abs(self.touch_pos[0] - self.last_recorded_pos[0]) >= self.width_min) \
					or (abs(self.touch_pos[1] - self.last_recorded_pos[1]) >= self.height_min):
					
					self.last_recorded_pos = self.touch_pos

					self._log_touch('Touch Move', self.held_name)
				
				return True
		
		self.held_name = ''
		
		if (abs(self.touch_pos[0] - self.last_recorded_pos[0]) >= self.width_min) \
			or (abs(self.touch_pos[1] - self.last_recorded_pos[1]) >= self.height_min):
			
			self.last_recorded_pos = self.touch_pos

			self._log_touch('Touch Move', self.held_name)

	
	
	def on_touch_up(self, touch):
		"""Log a touch release.

		Tracks the touch up, records its position and relative timestamp, and
		forwards the event to children. During multi-touch the release is logged as
		blocked; a handled child release is logged using the child's name for an
		``ImageButton``.

		Parameters
		----------
		touch : kivy.input.MotionEvent
			The touch event to handle.

		Returns
		-------
		bool or None
			True when the event was consumed; None when disabled or no child handled it.
		"""

		was_multi_touch = self.multi_touch_active
		
		self._track_touch_up(touch)
		self.touch_pos = touch.pos
		self.touch_time = time.perf_counter() - self.start_time
		
		if self.disabled:
			return
		
		if was_multi_touch:
			self.held_name = ''
			self._log_touch('Touch Release (Blocked)', 'Multi-Touch')
			return True
		
		for child in self.children[:]:
			
			if child.dispatch('on_touch_up', touch):
				
				if isinstance(child, ImageButton):
					self.held_name = child.name
				
				else:
					self.held_name = ''

				self._log_touch('Touch Release', self.held_name)

				return True
		
		self.held_name = ''

		self._log_touch('Touch Release', self.held_name)
		
		if self.held_name != '':
			self.held_name = ''
	
	
	
	def _log_touch(self, event_name, stimulus_name):
		"""Queue a screen touch event row with position and stimulus name.

		Parameters
		----------
		event_name : str
			The event name, e.g. ``'Touch Press'``.
		stimulus_name : str
			Name of the stimulus or button touched.

		Notes
		-----
		Event row: Time is the current ``touch_time`` (seconds since ``start_time``),
		Event_Type ``'Screen'``, Event_Name the given event name, then the pairs
		``'X Position'``/x, ``'Y Position'``/y and ``'Stimulus Name'``/name in the
		Arg1-Arg3 columns.
		"""
		self.add_event([self.touch_time, 'Screen', event_name, 'X Position', self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', stimulus_name])

	def add_event(self, row):
		"""Queue an event row mapped onto the event columns.

		Builds a dict keyed by ``self.app.event_columns`` from the positional row,
		casting the Time column to float and all others to str and padding missing
		columns with empty strings, then puts it on ``self.event_queue`` for the
		writer thread.

		Parameters
		----------
		row : list
			Positional values aligned with the event columns (Time first).
		"""
		new_row = {}
		
		for iCol in range(len(self.app.event_columns)):

			if iCol >= len(row):
				new_row[self.app.event_columns[iCol]] = ''
			
			else:
				if self.app.event_columns[iCol] == 'Time':
					new_row[self.app.event_columns[iCol]] = float(row[iCol])
				
				else:
					new_row[self.app.event_columns[iCol]] = str(row[iCol])

		self.event_queue.put(new_row)

	def add_stage_event(self, stage_name):
		"""Queue a stage-change event with the relative time in seconds.

		Parameters
		----------
		stage_name : str
			Name of the stage that began.
		"""
		self.add_event([
			(time.perf_counter() - self.start_time)
			, 'Stage Change'
			, stage_name
			])
		return
	
	def add_button_event(self, event_type, button_name):
		"""Queue a button event with the relative time in seconds.

		Parameters
		----------
		event_type : str
			Action performed, e.g. ``'Displayed'`` or ``'Removed'``.
		button_name : str
			Label of the button.
		"""
		self.add_event([
			(time.perf_counter() - self.start_time)
			, 'Button ' + event_type
			, button_name
			])
		return
	
	def add_text_event(self, event_type, text_name):
		"""Queue a text event with the relative time in seconds.

		Parameters
		----------
		event_type : str
			Action performed, e.g. ``'Displayed'`` or ``'Removed'``.
		text_name : str
			Label of the text element.
		"""
		self.add_event([
			(time.perf_counter() - self.start_time)
			, 'Text ' + event_type
			, text_name
			])
		return
	
	def add_variable_event(self, variable_class, variable_name, variable_value, variable_type=None, variable_units=None):
		"""Queue a variable-change event with optional type and units.

		Parameters
		----------
		variable_class : str
			Class or category of the variable.
		variable_name : str
			Name of the variable.
		variable_value : object
			Value of the variable.
		variable_type : str, optional
			Data type of the variable. Defaults to None.
		variable_units : str, optional
			Units of the variable. Defaults to None.

		Notes
		-----
		Event row: Time (seconds since ``start_time``), Event_Type
		``'Variable Change'``, Event_Name ``variable_class``, Arg1_Name
		``variable_name``, Arg1_Value ``variable_value``. When a type or units is
		given, Arg2 is ``'Type'`` / the type; when units are given, Arg3 is
		``'Units'`` / the units.
		"""
		row = [(time.perf_counter() - self.start_time), 'Variable Change', variable_class, variable_name, variable_value]
		if variable_type is not None or variable_units is not None:
			row.extend(['Type', variable_type])
		if variable_units is not None:
			row.extend(['Units', variable_units])
		self.add_event(row)

	def add_object_event(self, event_type, object_type, object_name, object_detail, image_name=None):
		"""Queue an object event, optionally appending an image name.

		Parameters
		----------
		event_type : str
			Action applied to the object, e.g. ``'Display'``.
		object_type : str
			Type of the object, e.g. ``'Video'`` or ``'Button'``.
		object_name : str
			Name of the object.
		object_detail : str
			Detail describing the object.
		image_name : str, optional
			Image file name appended as an extra pair. Defaults to None.

		Notes
		-----
		Event row: Time (seconds since ``start_time``), Event_Type
		``'Object <event_type>'``, Event_Name ``object_type``, Arg1_Name
		``object_name``, Arg1_Value ``object_detail``; ``'Image Name'`` and the
		name follow in Arg2 only when ``image_name`` is given.
		"""
		# Generic object event builder. This will log the standard fields and
		# append an 'Image Name' pair only when an image_name is provided.
		row = [
			(time.perf_counter() - self.start_time),
			'Object ' + event_type,
			object_type,
			object_name,
			object_detail,
		]
		if image_name is not None:
			row.extend(['Image Name', image_name])
		self.add_event(row)
	
	def set_start_time(self, start_time):
		"""Set the reference time used for event timestamps.

		Parameters
		----------
		start_time : float
			Seconds from :func:`time.perf_counter` used as time zero.
		"""
		self.start_time = start_time
		return
	
	def write_data(self):
		"""Finalise the event queue and sort the session event data.

		Notes
		-----
		Finalises the app's event queue, builds a DataFrame from the logged event
		list, casts Time to float64 and sorts rows by Time, then assigns it to the
		app and queues a DataFrame write to the session event path when set.
		"""
		self.app._finalize_event_queue()
		self.session_event_data = pd.DataFrame(self.app.event_list, columns=self.app.event_columns)
		if not self.session_event_data.empty:
			self.session_event_data.Time = self.session_event_data.Time.astype('float64')
			self.session_event_data = self.session_event_data.sort_values(by=['Time'])
		self.app.session_event_data = self.session_event_data
		if self.app.session_event_path:
			self.app.queue_dataframe_write(self.app.session_event_path, self.app.session_event_data, index=False)
	
	
	
	def update_path(self, path):
		"""Set the session event path and queue a CSV header write.

		Parameters
		----------
		path : pathlib.Path or str
			Path of the event CSV file.

		Notes
		-----
		Stores the path as ``save_path`` and ``app.session_event_path``, then queues
		a header row of ``app.event_columns`` to it.
		"""

		self.save_path = pathlib.Path(path)
		self.app.session_event_path = self.save_path
		self.app.queue_csv_header(self.save_path, self.app.event_columns)

	# Add new bind option to FloatLayoutLog for when multi-touch is detected (i.e., a second touch occurs while one is already active)
	

class PreloadedVideo(Image):
	"""Image widget that plays a video file with ffpyplayer on a background thread.

	The player is created paused. Frames are blitted into the widget texture; the
	``state`` property starts and stops playback.

	Attributes
	----------
	player : ffpyplayer.player.MediaPlayer or None
		The media player (None after :meth:`unload`).
	loop : bool
		Whether playback restarts at end of file.
	duration : float or None
		Video duration in seconds from the player metadata.
	video_fps : float
		Frame rate from the metadata (30.0 when unavailable).
	"""
	def __init__(self, source_path, player=None, loop=False, **kwargs):
		"""Initialise the video widget and its ffpyplayer MediaPlayer.

		Creates a fresh :class:`ffpyplayer.player.MediaPlayer` from ``source_path``
		(ignoring any ``player`` argument), pauses it immediately, reads its
		metadata (``duration`` and ``video_fps``) and loads an initial thumbnail
		frame.

		Parameters
		----------
		source_path : str
			Path of the video file to play.
		player : object, optional
			Ignored; accepted only for call compatibility. Defaults to None.
		loop : bool, optional
			Whether the video should loop at end of file. Defaults to False.
		**kwargs : dict
			Additional keyword arguments passed to :class:`kivy.uix.image.Image`.
		"""
		# We accept 'player' arg just to keep compatibility with your Protocol.py calls,
		# BUT we ignore it. We create a fresh one based on source_path.
		super().__init__(**kwargs)
		self._source_path = source_path
		self.loop = loop
		self._state = 'stop'
		self._stop_event = threading.Event()
		self._playback_thread = None
		self.texture = None
		
		# --- FRESH PLAYER INSTANTIATION ---
		# ff_opts={'out_fmt': 'rgb24'} ensures we get raw RGB bytes for Kivy texture
		self.player = MediaPlayer(
			self._source_path
		)
		
		# Force pause immediately upon creation so it doesn't auto-start
		self.player.set_pause(True)
		
		# --- Metadata Logic ---
		# Wait briefly for the stream to open: seek()/get_frame() on a player that has not
		# opened yet crashes ffpyplayer (access violation). Duration may still be None after.
		timeout = 0
		while self.player.get_metadata()['duration'] is None and timeout < 5:
			time.sleep(0.01)
			timeout += 1

		metadata = self.player.get_metadata()
		fr = metadata.get('frame_rate', (30, 1))
		self.duration = metadata.get('duration', 0)
		if isinstance(fr, (tuple, list)) and len(fr) == 2 and fr[1] != 0:
			self.video_fps = float(fr[0]) / float(fr[1])
		else:
			self.video_fps = 30.0
			
		# Initial Frame Load (Thumbnail) - only once the stream is open (see above)
		if self.duration is None:
			return
		try:
			# We explicitly seek to 0 to ensure we are at start
			self.player.seek(0)
			frame, val = self.player.get_frame()
			if frame:
				self._update_texture(frame[0])
		except Exception:
			pass # thumbnail is best-effort

	@mainthread
	def _update_texture(self, img):
		"""Blit the given video frame into the Kivy texture.

		Creates a new RGB texture when none exists or its size differs, flips it
		vertically, blits the frame buffer and requests a canvas update.

		Parameters
		----------
		img : object
			The decoded frame image to draw onto the texture.
		"""
		if not self.texture or self.texture.size != img.get_size():
			self.texture = Texture.create(size=img.get_size(), colorfmt='rgb')
			self.texture.flip_vertical()
		self.texture.blit_buffer(img.to_memoryview()[0], colorfmt='rgb', bufferfmt='ubyte')
		self.canvas.ask_update()

	@property
	def state(self):
		"""Return the current video playback state (``'stop'``, ``'play'`` or ``'pause'``)."""
		return self._state

	@state.setter
	def state(self, value):
		"""Update the playback state, starting or stopping the player.

		When set to ``'play'`` the player is unpaused and the playback thread is
		started. Any other value pauses and stops the thread; setting ``'stop'``
		additionally resets the video.

		Parameters
		----------
		value : str
			The new state: ``'play'``, ``'pause'`` or ``'stop'``.
		"""
		if value == self._state:
			return
		
		self._state = value
		
		if value == 'play':
			self.player.set_pause(False)
			self._start_thread()
		else:
			self.player.set_pause(True)
			self._stop_thread()
			if value == 'stop':
				self.reset()

	def _start_thread(self):
		"""Start the background playback thread if one is not already running."""
		if self._playback_thread and self._playback_thread.is_alive():
			return
		self._stop_event.clear()
		self._playback_thread = threading.Thread(target=self._video_loop, daemon=True)
		self._playback_thread.start()

	def _stop_thread(self):
		"""Signal the playback thread to stop and join it briefly."""
		self._stop_event.set()
		if self._playback_thread and self._playback_thread.is_alive():
			self._playback_thread.join(timeout=0.5)

	def _video_loop(self):
		"""Drain frames from the player until the stop event is set.

		On end-of-file the video is either restarted (when looping) or the state is
		switched to ``'stop'`` on the Kivy thread. Paused playback and frame timing
		are handled with ``time.sleep``.
		"""
		while not self._stop_event.is_set():
			try:
				frame, val = self.player.get_frame()
			except Exception:
				break
			
			if val == 'eof':
				if self.loop:
					self.player.seek(0)
					time.sleep(0.01)
					continue
				else:
					Clock.schedule_once(lambda dt: setattr(self, 'state', 'stop')) # Schedule on Kivy thread
					break
			
			if val == 'paused':
				time.sleep(0.05)
				continue
			
			if frame:
				self._update_texture(frame[0])
			
			if val is not None:
				if val > 0:
					time.sleep(val)
			else:
				time.sleep(1.0 / 30.0)

	def unload(self):
		"""Completely destroy the media player.

		Stops playback and the playback thread, then closes the player and releases
		it. Any failure is ignored.
		"""
		self.state = 'stop'
		self._stop_thread()
		
		if self.player:
			try:
				self.player.close_player()
			except Exception:
				pass # Best-effort: ignore failures
			self.player = None
			
	def reload(self):
		"""Create a fresh paused MediaPlayer for the stored source path.

		Replaces ``self.player`` with a new player created from
		``self._source_path`` and pauses it. A failure is logged.
		"""
		try:
			self.player = MediaPlayer(
				self._source_path
			)
			# Ensure newly created player is paused by default
			self.player.set_pause(True)
		except Exception:
			Logger.exception('TouchCog: video reload failed')

	def reset(self):
		"""Stop playback, reset the state and seek back to the start frame.

		Stops the playback thread, sets the state to ``'stop'``, pauses and seeks
		the player to zero, and schedules a thumbnail update on the Kivy Clock.
		"""
		# Stop the playback thread and ensure state is stopped
		try:
			self._stop_thread()
		except Exception:
			pass # thread may be stopped already

		self._state = 'stop'
		try:
			if self.player:
				self.player.set_pause(True)
				self.player.seek(0)
				def _update_thumb(dt):
					"""Update the thumbnail texture from the current frame, if the player is still valid."""
					try:
						# Check if self.player is still valid before trying to get frame
						if not self.player:
							return
						f, v = self.player.get_frame()
						if f:
							self._update_texture(f[0])
					except Exception:
						pass # player may be closed

				Clock.schedule_once(_update_thumb, 0.1)
		except Exception:
			# Best-effort: ignore failures
			pass
class ProtocolBase(Screen):
	"""Base screen for protocol task states, holding shared widgets and flow state.

	Builds the logging layout, data folders and configuration-derived defaults, and
	creates the shared widgets (hold button, feedback, labels, buttons and
	tutorial-video controls) used by concrete protocol screens.

	Attributes
	----------
	name : str
		Screen name ``'protocolscreen'``.
	protocol_floatlayout : Classes.Protocol.FloatLayoutLog
		The logging layout that owns this screen's widgets and event queue.
	app : kivy.app.App
		The running TouchCog app.
	language : str
		Current language folder name.
	data_folder : pathlib.Path
		Root output folder for participant data.
	protocol_name : str
		Name of the active protocol.
	image_folder : str
		Path of the protocol's image folder (set by :meth:`update_task`).
	participant_id : str
		Participant identifier used in output file names.
	session_data : pandas.DataFrame
		DataFrame of trial summary rows.
	data_cols : list of str
		Column names of the summary data file.
	metadata_cols : list of str
		Column names of the metadata output file.
	block_max_length : int
		Maximum block duration. Defaults to 600.
	block_max_count : int
		Maximum trials per block. Defaults to 120.
	block_min_rest_duration : int
		Minimum rest between blocks. Defaults to 1.
	session_length_max : int
		Maximum session length. Defaults to 3600.
	session_trial_max : int
		Maximum trials per session. Defaults to 1200.
	iti_length : float
		Inter-trial interval in seconds. Defaults to 2.00.
	feedback_length : float
		Feedback display duration in seconds. Defaults to 1.00.
	hold_remind_delay : float
		Delay before the hold reminder. Defaults to 2.0.
	hold_image : str
		Image shown for the hold stage.
	mask_image : str
		Image used as the hold mask.
	image_dict : dict
		Maps image names to loaded Kivy images.
	file_index : int
		Index appended to generated file names.
	stimulus_on_screen : bool
		Whether a stimulus is currently displayed.
	video_on_screen : bool
		Whether a video is currently displayed.
	iti_active : bool
		Whether the inter-trial interval is active.
	block_started : bool
		Whether the current block rest is running.
	feedback_on_screen : bool
		Whether feedback is currently displayed.
	hold_active : bool
		Whether holding is currently required.
	hold_button_pressed : bool
		Whether the hold button is currently pressed.
	premature_override : bool
		Whether premature-response handling is overridden.
	skip_tutorial_video : bool
		Whether the tutorial video is skipped.
	display_video : bool
		Whether videos are shown.
	protocol_ended : bool
		Whether the protocol has ended.
	output_generated : bool
		Whether summary output files have been generated.
	metadata_generated : bool
		Whether the metadata file has been generated.
	current_block : int
		Number of the current block.
	current_trial : int
		Number of the current trial.
	stage_index : int
		Index of the current stage.
	start_iti : float
		``time.perf_counter`` value when the ITI began.
	start_time : float
		Reference ``time.perf_counter`` value for event timestamps.
	block_start : float
		``time.perf_counter`` value when the current block began.
	feedback_start_time : float
		``time.perf_counter`` value when feedback was shown.
	trial_end_time : float
		``time.perf_counter`` value when the trial ended.
	multi_touch_warning_duration : float
		Seconds to show the multi-touch warning. Defaults to 2.0.
	hold_remind_event : kivy.clock.ClockEvent or None
		Pending hold-reminder Clock event.
	session_clock : kivy.clock.Clock
		Kivy Clock used to schedule the session monitor.
	session_event : kivy.clock.ClockEvent
		Trigger that ends the session after ``session_length_max``.
	parameters_dict : dict
		Protocol parameters parsed from configuration.
	feedback_dict : dict
		Maps feedback keys to markup-wrapped feedback text.
	hold_button : Classes.Protocol.ImageButton
		Image button used for holding.
	feedback_image : kivy.uix.image.Image
		Image widget shown for image feedback.
	tutorial_video : Classes.Protocol.PreloadedVideo or None
		The current tutorial video widget.
	instruction_label : kivy.uix.label.Label
		Label showing the task instructions.
	block_label : kivy.uix.label.Label
		Label showing the block break text.
	end_label : kivy.uix.label.Label
		Label showing the end-of-session text.
	feedback_label : kivy.uix.label.Label
		Label showing feedback text.
	multi_touch_label : kivy.uix.label.Label
		Label showing the multi-touch warning.
	start_button, continue_button, return_button : kivy.uix.button.Button
		Task, block and return navigation buttons.
	tutorial_continue_button, tutorial_start_button, tutorial_restart_button, tutorial_video_button : kivy.uix.button.Button
		Tutorial-video control buttons.
	"""
	
	def __init__(self, screen_resolution, **kwargs):
		"""Initialise the base protocol screen and its shared state.

		Builds the logging ``FloatLayoutLog``, reads screen dimensions and maxfps
		from the Kivy graphics config, creates the data-folder structure, initialises
		long-running state (counters, flags, timing values, dictionaries) and creates
		all shared widgets and the session Clock trigger.

		Parameters
		----------
		screen_resolution : tuple of (int, int)
			Screen width and height in pixels.
		**kwargs : dict
			Additional keyword arguments passed to :class:`kivy.uix.screenmanager.Screen`.
		"""
		
		super(ProtocolBase, self).__init__(**kwargs)
		
		self.name = 'protocolscreen'

		self.protocol_floatlayout = FloatLayoutLog(screen_resolution)
		self.protocol_floatlayout.bind(on_multi_touch=self.multi_touch_warning)
		self.protocol_floatlayout.size = screen_resolution
		self.add_widget(self.protocol_floatlayout)
			
		width = int(Config.get('graphics', 'width'))
		height = int(Config.get('graphics', 'height'))
		self.maxfps = int(Config.get('graphics', 'maxfps'))
		
		if self.maxfps == 0:
			self.maxfps = 60

		self.screen_resolution = (width, height)
		self.protocol_floatlayout.size = self.screen_resolution

		self.width_adjust = 1
		self.height_adjust = 1
		
		if width > height:
			self.width_adjust = height / width
		
		elif width < height:
			self.height_adjust = width / height
		
		
		
		# Define App
		
		self.app = App.get_running_app()
		self.language = self.app.language

		# Folder

		self.data_folder = DATA_FOLDER
		# Create the directory structure if it doesn't exist
		self.data_folder.mkdir(parents=True, exist_ok=True)

		
		
		# Define Folders
		
		self.protocol_name = ''
		self.image_folder = ''
		
		self.config_path = ''
		self.file_path = ''
		
		
		# Define Datafile
		
		self.session_data = pd.DataFrame()
		self.data_cols = []
		self.metadata_cols = []
		
		
		# Define General Parameters
		
		self.participant_id = 'Default'
		self.block_max_length = 600
		self.block_max_count = 120
		self.block_min_rest_duration = 1
		self.session_length_max = 3600
		self.session_trial_max = 1200
		self.iti_length = 2.00
		self.feedback_length = 1.00
		self.hold_remind_delay = 2.0
		self.hold_image = ''
		self.mask_image = ''
		self.image_dict = {}
		self.file_index = 1
		
		
		# Define Language
		
		self.language = 'English'
		
		
		# Define Variables - Boolean
		
		self.stimulus_on_screen = False
		self.video_on_screen = False
		self.iti_active = False
		self.block_started = False
		self.feedback_on_screen = False
		self.hold_active = True
		self.hold_button_pressed = False
		self.premature_override = False
		self.skip_tutorial_video = False
		self.display_video = True
		self.protocol_ended = False
		self.output_generated = False
		self.metadata_generated = False
		
		
		# Define Variables - Counter
		
		self.current_block = 0
		self.current_trial = 0
		self.stage_index = 0
		
		
		# Define Variables - Time
		
		self.start_iti = 0
		self.start_time = 0
		self.block_start = 0
		self.feedback_start_time = 0
		self.trial_end_time = 0
		self.multi_touch_warning_duration = 2.0
		
		
		# Define Class - Clock

		self.hold_remind_event = None

		self.session_clock = Clock
		self.session_event = self.session_clock.create_trigger(self.clock_monitor, self.session_length_max, interval=False)
		
		
		# Define Dictionaries
		
		self.parameters_dict = {}
		self.feedback_dict = {}
		
		
		# Define Widgets - Images
		
		self.hold_button = ImageButton()
		self.hold_button.pos_hint = {'center_x': 0.5, 'center_y': 0.1}
		self.hold_button.name = 'Hold Button'
		self.hold_button.size_hint = ((0.2 * self.width_adjust), (0.2 * self.height_adjust))
		self.hold_button.bind(on_release=self.hold_remind)
		self.hold_button.bind(on_release=self.hold_lift_trial)
		self.hold_button.bind(on_press=self.hold_lift_returned)
		self.hold_button.always_release = True

		self.feedback_image = Image()
		self.feedback_image.size_hint = (0.4, 0.4)
		self.feedback_image.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

		# Define widgets - Video (hold)
		self.tutorial_video = None
		
		
		# Define Widgets - Text
		
		self.instruction_label = Label(font_size='35sp')
		self.instruction_label.size_hint = (0.6, 0.4)
		self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}
		
		self.block_label = Label(font_size='50sp')
		self.block_label.size_hint = (0.5, 0.3)
		self.block_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}
		
		self.end_label = Label(font_size='50sp')
		self.end_label.size_hint = (0.6, 0.4)
		self.end_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}
		
		self.feedback_label = Label(text='', font_size='50sp', markup=True)
		self.feedback_label.size_hint = (0.7, 0.4)
		self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

		self.multi_touch_label = Label(text='', font_size='50sp', markup=True)
		self.multi_touch_label.size_hint = (0.7, 0.4)
		self.multi_touch_label.pos_hint = {'center_x': 0.5, 'center_y': 0.9}

		# Define Widgets - Hold for Feedback
		self.feedback = self.feedback_label
		
		
		# Define Widgets - Buttons
		
		self.start_button = Button()
		self.start_button.size_hint = (0.1, 0.1)
		self.start_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
		self.start_button.bind(on_press=self.start_protocol)
		
		self.continue_button = Button()
		self.continue_button.size_hint = (0.1, 0.1)
		self.continue_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
		self.continue_button.bind(on_press=self.block_end)
		
		self.return_button = Button()
		self.return_button.size_hint = (0.1, 0.1)
		self.return_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
		self.return_button.bind(on_press=self.return_to_main)

		self.tutorial_continue_button = Button(text='Continue', font_size='48sp')
		self.tutorial_continue_button.size_hint = [0.4, 0.15]
		self.tutorial_start_button = Button(text='Start Task', font_size='48sp')
		self.tutorial_start_button.size_hint = [0.4, 0.15]
		self.tutorial_start_button.pos_hint = {'center_x': 0.5, 'center_y': 0.3}
		self.tutorial_restart_button = Button(text='Restart Video', font_size='48sp')
		self.tutorial_restart_button.size_hint = [0.4, 0.15]
		self.tutorial_restart_button.pos_hint = {"center_x": 0.25, "y": 0.01}
		self.tutorial_restart_button.bind(on_press=self.tutorial_restart)
		self.tutorial_video_button = Button(text='Tap the screen\nto start video', font_size='48sp', halign='center', valign='center')
		self.tutorial_video_button.background_color = 'black'
		self.tutorial_video_button.bind(on_press=self.start_tutorial_video)

	def _safe_get_bool(self, key, fallback):
		"""Return the boolean value for a configuration key, coercing strings.

		Parameters
		----------
		key : str
			Key into ``self.parameters_dict``.
		fallback : object
			Value returned when ``key`` is absent.

		Returns
		-------
		bool
			``True`` when the value is the string ``'true'`` (case-insensitive),
			otherwise the truthiness of the value as a bool.
		"""
		val = self.parameters_dict.get(key, fallback)
		if isinstance(val, str):
			return val.lower() == 'true'
		return bool(val)
		
	
	def update_task(self):
		"""Set the image folder path for the active protocol."""
		
		self.image_folder = self.app.app_root / 'Protocol' / self.protocol_name / 'Image'
		return	

	def constrained_shuffle(self,seq, max_run=3, attempts=100, rng=None):
		"""Return a pseudorandom ordering of ``seq`` with no value repeating more than ``max_run`` times consecutively.

		Attempts to build the shuffle by repeatedly picking weighted-random
		candidates from the remaining items, forbidding the last item once it has
		formed a disqualifying run and forcing critical items (those whose count
		exceeds about 80% of the other items' capacity) to be chosen first.

		Parameters
		----------
		seq : list
			The sequence to shuffle.
		max_run : int, optional
			The maximum number of consecutive identical items allowed. Defaults to 3.
		attempts : int, optional
			The number of times to attempt the shuffle before failing. Defaults to 100.
		rng : random.Random, optional
			Random number generator instance. Defaults to the ``random`` module.

		Returns
		-------
		list
			A new list with the shuffled sequence, or an empty list when ``seq`` is empty.

		Raises
		------
		ValueError
			If a valid shuffle cannot be found within the given ``attempts``.
		"""
		if rng is None:
			rng = random
		if not seq:
			return []
		
		# Check if Sequence is Possible
		counts = Counter(seq)
		common_items, max_count = counts.most_common(1)[0]
		total_items = len(seq) - max_count

		max_possible_capacity = (total_items + 1) * max_run

		if max_count > max_possible_capacity:
			min_required_run = math.ceil(max_count / (total_items + 1))
			raise ValueError(
				f"Impossible constraints: You have {max_count} '{common_items}'s "
            f"but only {total_items} other items to separate them. "
            f"With max_run={max_run}, you can only fit {max_possible_capacity}. "
            f"Minimum max_run required is {min_required_run}."
			)

		n = len(seq)
		
		for _ in range(attempts):
			remaining = Counter(seq)
			result = []
			
			while len(result) < n:
				# Determine the last item to check for a run
				last_item = result[-1] if result else None
				
				# Efficiently check if the last item has formed a disqualifying run
				is_run = False
				if len(result) >= max_run:
					# Check if the last `max_run` items are all the same as `last_item`
					if all(result[i] == last_item for i in range(-1, -max_run - 1, -1)):
						is_run = True

				# Get candidates whose counts are greater than 0
				candidates = [item for item, count in remaining.items() if count > 0]
				
				# If the last item formed a run, it's forbidden in this step
				if is_run and last_item in candidates:
					candidates.remove(last_item)

				if not candidates:
					# This attempt is stuck (e.g., only 'A's are left but the run of 'A's is maxed out)
					# Break the inner while loop to start a new attempt.
					break 

				# Check if item is already near critical
				critical_items = []
				for cand in candidates:
					others = sum(c for k, c in remaining.items() if k != cand)

					if remaining[cand] > others * max_run * 0.8:
						critical_items.append(cand)
				
				if critical_items:
					candidates = critical_items
	

				# Weighted random choice from the valid candidates
				weights = [remaining[k] for k in candidates]
				choice = rng.choices(candidates, weights=weights, k=1)[0]
				
				result.append(choice)
				remaining[choice] -= 1
			
			if len(result) == n:
				# Successfully built a valid shuffle
				return result
				
		# If all attempts failed, raise an error
		raise ValueError(f"Failed to find a valid constrained shuffle after {attempts} attempts.")
	
	
	def load_images(self, image_list):
		"""Load the given image files asynchronously into ``self.image_dict``.

		Parameters
		----------
		image_list : list of str or pathlib.Path
			Image names or paths to load.

		Notes
		-----
		``self.image_dict`` is reset first. Each name is looked up in
		``self.image_folder``, then with ``.png`` appended there, then as a direct
		path. Keys are the file stem, except for the ``.png``-appended match, which
		is keyed by the name as given.
		"""
		
		# Load Images - Async
		
		self.image_dict = {}
		
		for image_file in image_list:
			try:
				image_file = pathlib.Path(image_file)
			except Exception:
				pass # keep non-path value as-is
			if pathlib.Path(self.image_folder / image_file).exists():
				load_image = Loader.image(str(self.image_folder / image_file))
				image_name = str(image_file.stem)
			
			elif pathlib.Path(self.image_folder, str(image_file) + '.png').exists():
				load_image = Loader.image(str(self.image_folder / (str(image_file) + '.png')))
				image_name = str(image_file)

			else:
				image_file = pathlib.Path(image_file)
				load_image = Loader.image(str(image_file))
				image_name = str(image_file.stem)

			self.image_dict[image_name] = load_image
		
		return
	
	
	
	def set_language(self, language):
		"""Load the given language's text and build the feedback dictionary.

		Reads ``Start.txt``, ``Break.txt``, ``End.txt`` and ``End_Continue.txt`` and
		assigns them to the instruction, block and end labels; reads ``Button.ini``
		for the button texts; and reads ``Feedback.ini`` to populate
		``self.feedback_dict`` with the keys ``correct``, ``incorrect``, ``wait``,
		``return``, ``multi_touch``, ``too_slow``, ``miss`` and ``abort``.

		Parameters
		----------
		language : str
			Language folder name to load.
		"""
		
		self.language = language
		
		self.lang_folder_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language
		
		start_path = self.lang_folder_path / 'Start.txt'
		with open(start_path, 'r', encoding='utf-8') as file:
			start_label_str = file.read()
		self.instruction_label.text = start_label_str
		
		break_path = self.lang_folder_path / 'Break.txt'
		with open(break_path , 'r', encoding='utf-8') as file:
			break_label_str = file.read()
		self.block_label.text = break_label_str
		
		end_path = self.lang_folder_path / 'End.txt'
		with open(end_path, 'r', encoding='utf-8') as file:
			end_label_str = file.read()

		end_cont_path = self.lang_folder_path / 'End_Continue.txt'
		with open(end_cont_path, 'r', encoding='utf-8') as file:
			end_cont_label_str = file.read()
		
		if self.app.battery_index < (len(self.app.battery_protocols) - 1) and self.app.battery_active:
			self.end_label.text = end_cont_label_str
		elif self.app.battery_index == (len(self.app.battery_protocols) - 1) and self.app.battery_active:
			self.end_label.text = end_label_str
		else:
			self.end_label.text = end_label_str
		
		button_lang_path = self.lang_folder_path / 'Button.ini'
		button_lang_config = configparser.ConfigParser()
		button_lang_config.read(button_lang_path, encoding='utf-8')
		
		start_button_label_str = button_lang_config.get('Button', 'start', fallback='Start')
		self.start_button.text = start_button_label_str
		
		continue_button_label_str = button_lang_config.get('Button', 'continue', fallback='Continue')
		self.continue_button.text = continue_button_label_str
		
		return_button_label_str = button_lang_config.get('Button', 'return', fallback='Return')
		self.return_button.text = return_button_label_str
		
		tutorial_continue_button_label_str = button_lang_config.get('Button', 'tutorial_continue', fallback='Continue')
		self.tutorial_continue_button.text = tutorial_continue_button_label_str

		tutorial_start_button_label_str = button_lang_config.get('Button', 'tutorial_start', fallback='Start Task')
		self.tutorial_start_button.text = tutorial_start_button_label_str

		tutorial_restart_button_label_str = button_lang_config.get('Button', 'tutorial_restart', fallback='Restart Video')
		self.tutorial_restart_button.text = tutorial_restart_button_label_str

		tutorial_button_label_str = button_lang_config.get('Button', 'tutorial', fallback='Tap the screen\nto start video').replace('\\n', '\n')
		self.tutorial_video_button.text = tutorial_button_label_str
		
		feedback_lang_path = self.lang_folder_path / 'Feedback.ini'
		feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
		feedback_lang_config.read(feedback_lang_path, encoding='utf-8')
		
		self.feedback_dict = {}
		
		def _markup(text, colour):
			"""Wrap the feedback text in colour markup, unless it names a PNG image."""
			# PNG filenames are image feedback and must not be wrapped in colour markup
			return text if text.endswith('.png') or not colour else '[color=%s]%s[/color]' % (colour, text)

		stim = feedback_lang_config['Stimulus']
		hold = feedback_lang_config['Hold']
		self.feedback_dict['correct'] = _markup(stim['correct'], stim['correct_colour'])
		self.feedback_dict['incorrect'] = _markup(stim['incorrect'], stim['incorrect_colour'])
		self.feedback_dict['wait'] = _markup(hold['wait'], hold['wait_colour'])
		self.feedback_dict['return'] = _markup(hold['return'], hold['return_colour'])
		self.feedback_dict['multi_touch'] = _markup(
			feedback_lang_config.get('Hold', 'multi_touch', fallback='PLEASE REMOVE EXTRA FINGER AND RETURN TO WHITE SQUARE')
			, feedback_lang_config.get('Hold', 'multi_touch_colour', fallback=hold['return_colour']))
		self.feedback_dict['too_slow'] = _markup(stim['too_slow'], stim['too_slow_colour'])
		self.feedback_dict['miss'] = _markup(stim['miss'], stim['miss_colour'])
		self.feedback_dict['abort'] = _markup(stim['abort'], stim['abort_colour'])
		
		return
	
	
	
	def generate_output_files(self):
		"""Determine the output file paths and queue the summary CSV header once.

		Early-returns if ``self.output_generated`` is already set. Sanitises the
		participant id, creates the participant folder, chooses the first free
		``<id>_<protocol>_<date>_<n>_Summary_Data.csv`` path, queues its header row
		from ``self.data_cols``, sets the matching ``_Event_Data.csv`` path and the
		app-level summary fields, then marks ``self.output_generated`` True.

		Notes
		-----
		Files affected: the summary CSV (header row) at ``self.file_path`` and the
		event-data CSV path passed to the logging layout.
		"""
		if self.output_generated:
			return

		self.participant_id = sanitize_participant_id(self.participant_id)

		folder_path = pathlib.Path(self.data_folder, self.participant_id)
		self.protocol_ended = False

		if not folder_path.is_dir():
			folder_path.mkdir()
		
		stem = lambda i: '_'.join([self.participant_id, self.protocol_name, str(datetime.date.today()), str(i)])
		self.file_index, self.file_path = next_free_path(lambda i: folder_path / (stem(i) + '_Summary_Data.csv'))
		temp_filename = stem(self.file_index)
		
		self.app.queue_csv_header(self.file_path, self.data_cols)
		
		event_path = pathlib.Path(folder_path, temp_filename + '_Event_Data.csv')
		
		self.protocol_floatlayout.update_path(event_path)
		self.app.trial_summary_cols = self.data_cols
		self.app.summary_event_path = self.file_path
		self.app.summary_event_data = self.session_data
		self.app.data_written = False
		self.output_generated = True
		return
	
	
	
	def metadata_output_generation(self):
		"""Queue the metadata CSV file for writing once.

		Early-returns if ``self.metadata_generated`` is already set. Builds a
		``Parameter``/``Value`` DataFrame from ``self.metadata_cols`` and the
		corresponding ``self.parameters_dict`` entries (falling back to the attribute
		of the same name, then ``''``, when a key is absent), picks the first free
		path ``<id>_<protocol>_<date>_<file_index>_Metadata.csv`` (later candidates get
		``_2``, ``_3`` ... before ``_Metadata``), queues it for writing and marks ``self.metadata_generated`` True.
		"""

		if self.metadata_generated:
			return
		
		folder_path = pathlib.Path(self.data_folder, self.participant_id)
		
		meta_list = list()
		
		for meta_row in self.metadata_cols:
			row_list = list()
			row_list.append(meta_row)
			# Fall back to the resolved attribute for keys the menu/config did not supply (task defaults)
			row_list.append(str(self.parameters_dict.get(meta_row, getattr(self, meta_row, ''))))
			meta_list.append(row_list)
		
		meta_stem = '_'.join([self.participant_id, self.protocol_name, str(datetime.date.today()), str(self.file_index)])
		# First file has no suffix; later ones get _2, _3, ...
		_, meta_output_path = next_free_path(lambda i: folder_path / (meta_stem + ('' if i == 1 else '_' + str(i)) + '_Metadata.csv'))
		
		meta_data = pd.DataFrame(meta_list, columns=['Parameter', 'Value'])
		self.app.queue_dataframe_write(meta_output_path, meta_data, index=False)
		self.metadata_generated = True
		return

	def trigger_tutorial_screen(self, *args):
		"""Clear the layout and schedule presentation of the tutorial video.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""

		# Clear the widgets from the float layout
		self.protocol_floatlayout.clear_widgets()

		# Block on_move events in float_layout to prevent accidental interactions during video presentation
		self.protocol_floatlayout.block_on_move_touch_down = True

		# Use Clock.schedule_once to ensure the UI updates before starting the video
		Clock.schedule_once(self.present_tutorial_video, 0.1)
	
	def present_tutorial_video(self, *args):
		"""Display the tutorial video, resolving its duration first.

		Uses a duration of ``0.0`` when skipping is enabled; otherwise reads the
		duration from the player metadata, re-polling via the Kivy Clock (up to
		~5 s) while it is still unknown. Records the ``Object Display`` stage event
		and shows the video and its start button.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch (dt).
		"""

		self.tutorial_continue_button.pos_hint = {"center_x": 0.75, "y": 0.01}
		self.tutorial_restart_button.size_hint = [0.4, 0.15]
		self.tutorial_restart_button.pos_hint = {"center_x": 0.25, "y": 0.01}
		self.tutorial_video_button.size_hint = (1, 1)
		self.tutorial_video_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

		self.tutorial_video.state = 'stop'
		if self.skip_tutorial_video:
			self.tutorial_video_duration = 0.0
		else:
			# Re-read metadata; duration is only set once in PreloadedVideo.__init__
			if self.tutorial_video.duration is None:
				if self.tutorial_video.player is not None:
					self.tutorial_video.duration = self.tutorial_video.player.get_metadata().get('duration')
			# Wait briefly (max ~5 s) for the video to load, then proceed with duration 0.0
			if self.tutorial_video.duration is None and getattr(self, '_tutorial_duration_polls', 0) < 50:
				self._tutorial_duration_polls = getattr(self, '_tutorial_duration_polls', 0) + 1
				Clock.schedule_once(self.present_tutorial_video, 0.1)
				return
			self._tutorial_duration_polls = 0
			self.tutorial_video_duration = self.tutorial_video.duration or 0.0

		self.protocol_floatlayout.add_stage_event('Object Display')
		self.protocol_floatlayout.add_widget(self.tutorial_video)
		self.protocol_floatlayout.add_widget(self.tutorial_video_button)

		self.tutorial_video_first_play = True
		self.video_on_screen = True

		return
	

	def start_tutorial_video(self, *args):
		"""Play the tutorial video and, on its first play, schedule the start button.

		Unblocks on-move touches, and when this is the first play removes the
		start button, schedules ``present_tutorial_video_start_button`` after the
		video duration and records the video-display event.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""

		self.tutorial_video.state = 'play'

		# Reset protocol_floatlayout block on_move flag to allow interactions during video
		self.protocol_floatlayout.block_on_move_touch_down = False

		if self.tutorial_video_first_play:
			self.tutorial_video_first_play = False
			self.protocol_floatlayout.remove_widget(self.tutorial_video_button)
			Clock.schedule_once(self.present_tutorial_video_start_button, self.tutorial_video_duration)
			self.protocol_floatlayout.add_object_event('Display', 'Video', 'Section', 'Instructions')

		return


	def present_tutorial_video_start_button(self, *args):
		"""Show the tutorial continue and restart buttons and record their display events.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch (dt).
		"""

		self.protocol_floatlayout.add_widget(self.tutorial_continue_button)
		self.tutorial_continue_button.disabled = False
		self.protocol_floatlayout.add_widget(self.tutorial_restart_button)
		self.tutorial_restart_button.disabled = False
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Instructions', 'Section Start')
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Instructions', 'Video Restart')
		return

	def tutorial_restart(self, *args):
		"""Restart the tutorial video by stopping, unloading, reloading and playing it.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		self.tutorial_video.state = 'stop'
		self.tutorial_video.unload()
		self.tutorial_video.reload()
		self.tutorial_video.state = 'play'
		# self.start_tutorial_video()
	
	def present_instructions(self):
		"""Present the task instructions and start button to the participant.

		Generates the output files and metadata, shows the instruction label and
		start button, and records the instruction-presentation stage, text and
		button-display events.
		"""
		
		self.generate_output_files()
		self.metadata_output_generation()
		self.protocol_floatlayout.add_widget(self.instruction_label)

		self.protocol_floatlayout.add_stage_event('Instruction Presentation')

		self.protocol_floatlayout.add_text_event('Displayed', 'Task Instruction')
		
		self.protocol_floatlayout.add_widget(self.start_button)

		self.protocol_floatlayout.add_button_event('Displayed', 'Task Start Button')
		return
	
	
	# Block Staging #
	
	def block_screen(self, *args):
		"""Show the block instruction once, if the block has not yet started.

		Records the block start using ``time.perf_counter`` and schedules
		``block_rest_end`` after ``self.block_min_rest_duration`` seconds. Does
		nothing when the block has already started.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		
		if not self.block_started:

			self.protocol_floatlayout.add_widget(self.block_label)
			
			self.protocol_floatlayout.add_text_event('Displayed', 'Block Instruction')

			self.block_start = time.perf_counter()
			self.block_started = True
		
			Clock.schedule_once(self.block_rest_end, self.block_min_rest_duration)
			return
		else:
			return
		

	def block_rest_end(self, *args):
		"""Show the Continue button at the end of the block rest period.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (dt).
		"""
		self.protocol_floatlayout.add_widget(self.continue_button)

		self.protocol_floatlayout.add_button_event('Displayed', 'Continue Button')
		return
	
	
	def block_end(self, *args):
		"""End the current block and return to the hold phase.

		Resets the block state, clears the block and Continue widgets, records
		the block start and trial end using ``time.perf_counter``, and displays
		the hold button bound to ``iti_start``.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		
		self.block_started = False
		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_text_event('Removed', 'Block Instruction')

		self.protocol_floatlayout.add_button_event('Removed', 'Continue Button')
		
		self.block_start = time.perf_counter()
		self.trial_end_time = time.perf_counter()
		self.hold_button.bind(on_press=self.iti_start)
		self.protocol_floatlayout.add_widget(self.hold_button)

		self.protocol_floatlayout.add_button_event('Displayed', 'Hold Button')

		return

	def cancel_hold_remind(self):
		"""Cancel any pending hold reminder event and unschedule the reminder."""
		if self.hold_remind_event is not None:
			try:
				self.hold_remind_event.cancel()
			except Exception:
				pass # event may be unscheduled
			self.hold_remind_event = None
		Clock.unschedule(self.hold_remind)
		return

	def schedule_hold_remind(self, delay=None):
		"""Schedule the hold reminder, replacing any pending one.

		Parameters
		----------
		delay : float, optional
			Seconds to wait before reminding. Defaults to ``self.hold_remind_delay``.

		Returns
		-------
		kivy.clock.ClockEvent
			The scheduled reminder event.
		"""
		self.cancel_hold_remind()
		if delay is None:
			delay = self.hold_remind_delay
		self.hold_remind_event = Clock.schedule_once(self.hold_remind, delay)
		return self.hold_remind_event
	
	
	
	# End Staging #

	def clear_video_cache(self):
		"""Stop and unload the tutorial video and run garbage collection.

		Does nothing when ``self.tutorial_video`` is absent or falsy.
		"""
		if not hasattr(self, 'tutorial_video') or not self.tutorial_video:
			return
		
		self.tutorial_video.state = 'stop'
		self.tutorial_video.unload()
		self.tutorial_video = None
		gc.collect()

		return
	
	def protocol_end(self, *args):
		"""Finish the protocol, writing the event and summary output files.

		Runs once: unloads any tutorial video, cancels scheduled events, shows the
		end label and return button, then finalises the event queue, writes the
		summary CSV from ``self.app.trial_summary_data`` columns to
		``self.app.summary_event_path``, rewrites the sorted event file and resets
		the app's per-session state.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		if self.protocol_ended:
			return

		self.protocol_ended = True
		# Check Video Removal
		self.clear_video_cache()
		# Check if self.tutorial_video still exists and unload if so
		if hasattr(self, 'tutorial_video') and self.tutorial_video:
			try:
				self.tutorial_video.unload()
				self.tutorial_video = None
			except Exception:
				pass # video teardown is best-effort

			gc.collect()
		# Check if the self.session_event is scheduled and unschedule if so
		if self.session_event.is_triggered:
			self.session_event.cancel()
		
		self.protocol_floatlayout.clear_widgets()
		self.cancel_hold_remind()
		Clock.unschedule(self.iti_end)
		self.protocol_floatlayout.add_widget(self.end_label)
		
		self.protocol_floatlayout.add_event([
			(time.perf_counter() - self.start_time)
			, 'Text Displayed'
			, 'End Instruction'
			])
		
		self.protocol_floatlayout.add_widget(self.return_button)

		self.protocol_floatlayout.add_button_event('Displayed', 'Return Button')

		self.app._finalize_event_queue()

		if self.app.summary_event_path:
			self.app.summary_event_data = pd.DataFrame(self.app.trial_summary_data, columns=self.app.trial_summary_cols)
			self.app.queue_dataframe_write(self.app.summary_event_path, self.app.summary_event_data, index=False)
		# write_data() rewrites the sorted event file once
		self.protocol_floatlayout.write_data()
		self.app.trial_summary_data = list()
		self.app.data_written = True
		self.app.event_list = list()
		self.app.session_event_path = ''
		self.app.summary_event_path = ''

		return
	
	
	
	def return_to_main(self, *args):
		"""Return to the main menu, advancing the battery run if active.

		Removes the return button, then notifies the app of task completion via
		``self.app.handle_task_completion``, falling back to the main menu screen
		if that fails.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		# Safe guard remove the return button immediately to prevent multiple presses
		self.protocol_floatlayout.remove_widget(self.return_button)

		# If a battery run is active, notify the app so it can advance to next task
		try:
			self.app.handle_task_completion(self.name)
		except Exception:
			Logger.exception('ProtocolBase: return_to_main failed')
			try:
				self.manager.current = 'mainmenu'
			except Exception:
				Logger.exception('ProtocolBase: fallback to mainmenu failed')

		return
	
	
	
	def start_protocol(self, *args):
		"""Start the task, replacing the instruction screen with the hold button.

		Removes the instruction label and start button, starts the session clock,
		and displays the hold button bound to ``iti_start``.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""

		self.protocol_floatlayout.add_stage_event('Instruction Presentation')

		self.protocol_floatlayout.remove_widget(self.instruction_label)

		self.protocol_floatlayout.add_text_event('Removed', 'Task Instruction')
		
		self.protocol_floatlayout.remove_widget(self.start_button)

		self.protocol_floatlayout.add_button_event('Removed', 'Task Start Button')

		self.start_clock()

		self.protocol_floatlayout.add_widget(self.hold_button)
		
		self.protocol_floatlayout.add_button_event('Displayed', 'Hold Button')
		
		self.hold_button.bind(on_press=self.iti_start)

		return
	
	def multi_touch_warning(self, *args):
		"""Display the multi-touch warning and schedule its removal.

		Shows ``self.multi_touch_label`` with the ``multi_touch`` feedback text and
		schedules ``remove_multi_touch_warning`` after
		``self.multi_touch_warning_duration`` seconds. Does nothing if the warning
		is already on screen.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		# Check if multi-touch warning is already on screen to prevent duplicates
		if self.multi_touch_label in self.protocol_floatlayout.children:
			return
		self.protocol_floatlayout.add_text_event('Multi-touch Detected', 'Screen')
		
		# Assign multi-touch feedback to the multi_touch_label and display it
		self.multi_touch_label.text = self.feedback_dict['multi_touch']
		self.protocol_floatlayout.add_widget(self.multi_touch_label)

		# Schedule removal of multi-touch feedback after a delay
		Clock.schedule_once(self.remove_multi_touch_warning, self.multi_touch_warning_duration)
		
		return
	
	def remove_multi_touch_warning(self, *args):
		"""Remove the multi-touch warning from screen.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch (dt).
		"""
		self.protocol_floatlayout.remove_widget(self.multi_touch_label)
		self.protocol_floatlayout.add_text_event('Removed', 'Multi-touch Warning')
		return

	def hold_remind(self, *args):
		"""Prompt the participant to return to the hold button.

		Does nothing while a stage screen, stimulus, video, block or an
		unchanged ``return``/``abort``/``wait`` feedback is active; otherwise
		removes any other feedback and assigns the ``return`` feedback.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch (dt).
		"""
		self.hold_remind_event = None
		# If a stage-specific screen is active or stimulus is on screen, do nothing
		if hasattr(self, 'stage_screen_started') and getattr(self, 'stage_screen_started'):
			return None
		if hasattr(self, 'stimulus_on_screen') and getattr(self, 'stimulus_on_screen'):
			return None
		if self.video_on_screen:
			return None
		if self.block_started:
			return None
		if self.feedback_on_screen:
			if self.feedback_label.text in [self.feedback_dict['return'], self.feedback_dict['abort'], self.feedback_dict['wait']]:
					# leave feedback as-is
				Clock.unschedule(self.remove_feedback)
				return
			else:
					# remove any other feedback text
				Clock.unschedule(self.remove_feedback)
				self.protocol_floatlayout.remove_widget(self.feedback)
				self.protocol_floatlayout.add_text_event('Removed', 'Feedback')
				self.feedback_on_screen = False

		if not self.feedback_on_screen:
			if self.block_started:
				return
			self.assign_feedback('return')

		return
	
	
	
	def iti_start(self, *args):	
		"""Begin the inter-trial interval once, when not already active.

		Cancels the hold reminder, swaps the hold button binding, records the ITI
		start with ``time.perf_counter`` and schedules ``iti_end`` after
		``self.iti_length`` seconds and ``remove_feedback`` after
		``self.feedback_length`` seconds (adjusted for feedback already shown).

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if not self.iti_active:
			self.cancel_hold_remind()
			# ensure no pending reminder stage remains and swap bindings
			self.hold_button_pressed = True
			self.hold_button.unbind(on_press=self.iti_start)
			if not self.premature_override:
				self.hold_button.bind(on_release=self.hold_remind)
			# bind release to hold_remind instead of premature_response to drive reminder logic

			self.start_iti = time.perf_counter()
			self.iti_active = True

			self.protocol_floatlayout.add_stage_event('ITI Start')

			Clock.schedule_once(self.iti_end, self.iti_length)
			if self.feedback_on_screen:
				# Remove feedback once it has been shown for feedback_length in total
				feedback_elapsed = time.perf_counter() - self.feedback_start_time
				Clock.schedule_once(self.remove_feedback, max(0, self.feedback_length - feedback_elapsed))
			else:
				Clock.schedule_once(self.remove_feedback, self.feedback_length)			
			return
		else:
			return
	
	def iti_end(self, *args):
		"""End the inter-trial interval and present the next stimulus.

		Clears the ITI state, unbinds the hold reminder and calls
		``self.stimulus_presentation``. Does nothing when no ITI is active.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch (dt).
		"""
		if self.iti_active:
				
			self.iti_active = False

			self.protocol_floatlayout.add_stage_event('ITI End')

			self.hold_button.unbind(on_release=self.hold_remind)
			self.hold_active = True
			self.stimulus_presentation()
				
			return
		else:
			return
	
	def hold_lift_trial(self, *args):
		"""Set ``hold_button_pressed`` to False (bound to the hold button on_release).

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		#self.hold_button.unbind(on_release=self.hold_lift_trial)
		self.hold_button_pressed = False
	def hold_lift_returned(self, *args):
		"""Set ``hold_button_pressed`` to True (bound to the hold button on_press).

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		self.hold_button_pressed = True

	def assign_feedback(self, feedback_key=None, override_text=None):
		"""Display the given feedback, as an image or text label.

		Uses ``override_text`` when provided, otherwise the ``feedback_dict`` value
		for ``feedback_key``. A feedback string containing ``.png`` is shown as an
		image from ``self.image_folder``, otherwise as ``self.feedback_label`` text.
		Logs a warning and returns without assigning anything when neither argument
		is valid.

		Parameters
		----------
		feedback_key : str, optional
			Key into ``self.feedback_dict`` identifying the feedback. Defaults to None.
		override_text : str, optional
			Literal text to display instead of a dictionary lookup. Defaults to None.
		"""
		old_feedback = self.feedback
		if feedback_key not in self.feedback_dict and not (isinstance(override_text, str) and override_text != ''):
			Logger.warning(f"TouchCog: Invalid feedback_key '{feedback_key}' and no valid override_text provided. No feedback will be assigned.")
			return
		# Check if override contains value, use as feedback
		if override_text is not None and type(override_text) == str and override_text != '':
			feedback_str = override_text
		# Else use feedback_dict value for feedback_key
		elif feedback_key in self.feedback_dict:
			# Extract string value from feedback_dict, which may contain markup. Default to empty string if key is missing or value is None.
			feedback_str = self.feedback_dict.get(feedback_key, '') or ''
		# Handle error case where neither argument is valid
		else:
			Logger.warning(f"TouchCog: Invalid feedback_key '{feedback_key}' and no valid override_text provided. No feedback will be assigned.")
			return
		
		# Check if feedback_str contains a png file extension. If so, set feedback_image source to that file and display the image instead of text.
		if '.png' in feedback_str:
			self.feedback_image.source = str(self.image_folder / feedback_str)
			# Assign feedback_image to feedback
			self.feedback = self.feedback_image
		# Else if text entry
		else:
			self.feedback_label.text = feedback_str
			# Assign feedback_label to feedback
			self.feedback = self.feedback_label
		# Replace on-screen feedback if the widget changed (it is otherwise left in place)
		if self.feedback_on_screen and (old_feedback is not self.feedback or feedback_key != getattr(self, '_feedback_key', None)):
			self.protocol_floatlayout.remove_widget(old_feedback)
			self.feedback_on_screen = False
		# Add feedback to screen if not already present
		if not self.feedback_on_screen:
			self.protocol_floatlayout.add_widget(self.feedback)

			self.protocol_floatlayout.add_object_event('Display', 'Feedback', 'Trial Feedback', feedback_key)

			self.feedback_start_time = time.perf_counter()
			self.feedback_on_screen = True
			self._feedback_key = feedback_key
		return

	def remove_feedback(self, *args):
		"""Remove the on-screen feedback widget if one is displayed.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch (dt).
		"""
		if self.feedback_on_screen:
			self.protocol_floatlayout.remove_widget(self.feedback)

			self.protocol_floatlayout.add_text_event('Removed', 'Feedback')

			self.feedback_on_screen = False  
				
			return
		else:
			return
	
	def write_summary_file(self, data_row):
		"""Append a trial summary row to the session summary data.

		Also queues the row for writing to the summary CSV at
		``self.app.summary_event_path`` when that path is set.

		Parameters
		----------
		data_row : list of object
			The summary row, matching ``self.app.trial_summary_cols``.
		"""
		self.app.trial_summary_data.append(data_row)
		if self.app.summary_event_path:
			self.app.queue_csv_row(self.app.summary_event_path, data_row)
		return
	
	
	
	def start_clock(self, *args):
		"""Start the session clock.

		Records the start time with ``time.perf_counter``, triggers
		``self.session_event`` (which fires ``clock_monitor`` after
		``self.session_length_max`` seconds), and records the start time in the
		event writer.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		
		self.start_time = time.perf_counter()
		self.session_event()
		self.protocol_floatlayout.set_start_time(self.start_time)
		
		return
	
	
	
	def clock_monitor(self, *args):
		"""End the protocol when the session clock trigger fires.

		Cancels the session event and calls ``protocol_end``.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch (dt).
		"""
		
		self.session_event.cancel()
		self.protocol_end()
		
		return