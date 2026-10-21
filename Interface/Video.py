"""Video playback screen for the TouchCog launcher interface."""
# Part of the TouchCog Kivy launcher interface (split out of KivyMenuInterface.py).

# Interface.Startup must be imported first: it configures Kivy before kivy.core.window loads.
import Interface.Startup

from Classes.Protocol import PreloadedVideo
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen
from Interface.Startup import app_root
from Interface.Startup import skip_video

class VideoScreen(Screen):
	"""Kivy screen that plays tutorial, next-task and end-session videos.

	The screen swaps between a tap-to-start button, the video player and the
	Continue/Restart controls, and can skip straight to the controls when
	video skipping is enabled in configuration.

	Attributes
	----------
	name : str
		Screen name ``'generalvideoscreen'``.
	app : kivy.app.App
		The running TouchCog app.
	language : str
		Language folder name (e.g. ``'English'``) used to locate tutorial videos.
	destination_screen : str or None
		Screen to navigate to on completion when no callback is set.
	finish_callback : callable or None
		Callback invoked when the video is completed.
	current_video : Classes.Protocol.PreloadedVideo or None
		The currently loaded video widget.
	current_video_duration : float
		Length of the current video in seconds.
	video_finish_event : kivy.clock.ClockEvent or None
		Pending scheduled event that triggers the video-end handler.
	skip_video_enabled : bool
		Whether video skipping is active.
	video_prefixes : dict
		Maps video keys to the file-name prefix used to locate each video.
	"""

	def __init__(self, **kwargs):
		"""Initialise the video screen and build its control widgets.

		Parameters
		----------
		**kwargs : dict
			Additional keyword arguments passed to :class:`kivy.uix.screenmanager.Screen`.
		"""

		super(VideoScreen, self).__init__(**kwargs)
		
		self.video_Layout = FloatLayout()
		self.name = 'generalvideoscreen'
		self.app = App.get_running_app()
		self.app.active_screen = self.name
		self.language = self.app.language
		self.destination_screen = None
		self.finish_callback = None
		self.current_video = None
		self.current_video_duration = 0.0
		self.video_finish_event = None
		self.skip_video_enabled = bool(skip_video)
		self.video_prefixes = {
			'tutorial': 'General-Tutorial_Video',
			'next_task': 'General-Next_Task',
			'end_session': 'General-End_Session'
		}
		
		self.add_widget(self.video_Layout)
		self.tutorial_continue_button = Button(text='Continue', font_size='48sp')
		self.tutorial_continue_button.size_hint = [0.4, 0.15]
		self.tutorial_continue_button.pos_hint = {"center_x": 0.75, "y": 0.01}
		self.tutorial_continue_button.bind(on_press=self.complete_video)
		self.tutorial_restart_button = Button(text='Restart Video', font_size='48sp')
		self.tutorial_restart_button.size_hint = [0.4, 0.15]
		self.tutorial_restart_button.pos_hint = {"center_x": 0.25, "y": 0.01}
		self.tutorial_restart_button.bind(on_press=self.restart_video)
		self.tutorial_video_button = Button(text='Tap the screen\nto start video', font_size='48sp', halign='center', valign='center')
		self.tutorial_video_button.background_color = 'black'
		self.tutorial_video_button.bind(on_press=self.start_video)
		self.tutorial_video_button.size_hint = (1, 1)
		self.tutorial_video_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

	def _cancel_video_finish_event(self):
		"""Cancel the pending video-finish Clock event, if any."""
		if self.video_finish_event is not None:
			try:
				self.video_finish_event.cancel()
			except Exception:
				# already stopped
				pass
			self.video_finish_event = None

	def _clear_video_player(self):
		"""Stop and unload the current video and clear its state."""
		self._cancel_video_finish_event()
		if self.current_video is not None:
			try:
				self.current_video.state = 'stop'
			except Exception:
				# stale video, harmless
				pass
			try:
				self.current_video.unload()
			except Exception:
				# already stopped
				pass
		self.current_video = None
		self.current_video_duration = 0.0

	def _resolve_video_path(self, video_key):
		"""Resolve the filesystem path of the video for the given key.

		Parameters
		----------
		video_key : str
			One of ``'tutorial'``, ``'next_task'`` or ``'end_session'``.

		Returns
		-------
		pathlib.Path or None
			The path of the first matching video file, or None if the key is unknown
			or no file is found.
		"""
		prefix = self.video_prefixes.get(video_key)
		if prefix is None:
			return None

		search_roots = [
			app_root / 'Language' / self.language / 'Tutorial_Video',
			app_root / 'Language' / 'English' / 'Tutorial_Video'
		]

		for folder in search_roots:
			if not folder.exists():
				continue
			exact_path = folder / f'{prefix}.mp4'
			if exact_path.exists():
				return exact_path
			matches = sorted(folder.glob(f'{prefix}*.mp4'))
			if matches:
				return matches[0]

		return None

	def prepare_video(self, video_key, on_complete=None, destination_screen=None):
		"""Load and prepare the requested video for display or skipping.

		Parameters
		----------
		video_key : str
			Key identifying which video to play (``'tutorial'``, ``'next_task'`` or
			``'end_session'``).
		on_complete : callable, optional
			Callback invoked when the video is completed. Defaults to None.
		destination_screen : str, optional
			Screen to switch to on completion when no callback is set. Defaults to None.

		Returns
		-------
		bool
			True if the video was found and prepared; False if no path could be resolved.
		"""
		self.language = getattr(self.app, 'language', 'English')
		self.skip_video_enabled = bool(skip_video)
		self.finish_callback = on_complete
		self.destination_screen = destination_screen
		self.video_Layout.clear_widgets()
		self._clear_video_player()

		video_path = self._resolve_video_path(video_key)
		if video_path is None:
			return False

		# Video should occupy the space above the buttons (buttons are at y=0.01 with height=0.15)
		# We set size_hint=(1, 0.8) and center_y=0.55 to leave room for the buttons at the bottom
		self.current_video = PreloadedVideo(
			source_path=str(video_path),
			pos_hint={'center_x': 0.5, 'center_y': 0.55},
			size_hint=(0.95, 0.75),
			fit_mode='contain',
			loop=False
		)
		self.current_video.state = 'stop'
		self.current_video_duration = float(getattr(self.current_video, 'duration', 0) or 0.0)
		if self.skip_video_enabled:
			self.show_video_controls()
			Clock.schedule_once(self._start_video_bypass, 0)
		else:
			self.display_video_widgets()
		return True

	def display_video_widgets(self):
		"""Show the tap-to-start video button in the video layout."""
		self.video_Layout.clear_widgets()
		self.video_Layout.add_widget(self.tutorial_video_button)

	def show_video_controls(self):
		"""Show the video player (if any) and the Continue/Restart buttons."""
		self.video_Layout.clear_widgets()
		if self.current_video is not None:
			self.video_Layout.add_widget(self.current_video)
		self.video_Layout.add_widget(self.tutorial_continue_button)
		self.video_Layout.add_widget(self.tutorial_restart_button)

	def _start_video_bypass(self, *args):
		"""Start the video immediately when skipping is enabled.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch.
		"""
		if self.skip_video_enabled and self.current_video is not None:
			self.start_video()

	def start_video(self, *args):
		"""Begin playing the current video.

		If no video is loaded, the screen is completed instead. When skipping is
		enabled the Continue/Restart controls are shown alongside the video;
		otherwise a Kivy Clock event finishes the video after its duration.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if self.current_video is None:
			self.complete_video()
			return

		self._cancel_video_finish_event()
		self.video_Layout.clear_widgets()
		self.video_Layout.add_widget(self.current_video)
		self.current_video.state = 'play'
		if self.skip_video_enabled:
			self.video_Layout.add_widget(self.tutorial_continue_button)
			self.video_Layout.add_widget(self.tutorial_restart_button)
		else:
			self.video_finish_event = Clock.schedule_once(self.tutorial_video_end, self.current_video_duration)

	def tutorial_video_end(self, *args):
		"""Show the video controls once the tutorial video has finished.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy Clock event dispatch (dt).
		"""
		self.show_video_controls()

	def restart_video(self, *args):
		"""Restart the current video from the beginning.

		If no video is loaded, the screen is completed instead. The video is
		stopped, unloaded, reloaded and played again; the end event is
		rescheduled, or the controls are shown when skipping is enabled.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if self.current_video is None:
			self.complete_video()
			return

		self._cancel_video_finish_event()
		self.video_Layout.clear_widgets()
		self.video_Layout.add_widget(self.current_video)
		try:
			self.current_video.state = 'stop'
		except Exception:
			# stale video, harmless
			pass
		try:
			self.current_video.unload()
			self.current_video.reload()
		except Exception:
			# already stopped
			pass
		self.current_video.state = 'play'
		if self.skip_video_enabled:
			self.video_Layout.add_widget(self.tutorial_continue_button)
			self.video_Layout.add_widget(self.tutorial_restart_button)
		else:
			self.video_finish_event = Clock.schedule_once(self.tutorial_video_end, self.current_video_duration)

	def complete_video(self, *args):
		"""Complete the video and hand control to the finish callback or destination.

		Clears the layout and player, then schedules the next action on the Kivy
		Clock: the finish callback if callable, otherwise navigation to the
		requested destination screen, or ``'mainmenu'`` when no destination was
		set.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		callback = self.finish_callback
		destination_screen = self.destination_screen
		self.finish_callback = None
		self.destination_screen = None
		self.video_Layout.clear_widgets()
		self._clear_video_player()

		if callable(callback):
			Clock.schedule_once(lambda dt: callback(), 0)
		elif destination_screen and self.manager is not None:
			Clock.schedule_once(lambda dt: self._go_to_destination(destination_screen), 0)
		else:
			Clock.schedule_once(lambda dt: self._go_to_destination('mainmenu'), 0)

	def _go_to_destination(self, destination_screen):
		"""Switch the screen manager to the given destination screen.

		Parameters
		----------
		destination_screen : str
			Name of the screen to navigate to.
		"""
		if self.manager is not None and self.manager.has_screen(destination_screen):
			self.manager.current = destination_screen


# Class App Builder #
