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

	def __init__(self, **kwargs):

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
		if self.video_finish_event is not None:
			try:
				self.video_finish_event.cancel()
			except Exception:
				# already stopped
				pass
			self.video_finish_event = None

	def _clear_video_player(self):
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
		self.video_Layout.clear_widgets()
		self.video_Layout.add_widget(self.tutorial_video_button)

	def show_video_controls(self):
		self.video_Layout.clear_widgets()
		if self.current_video is not None:
			self.video_Layout.add_widget(self.current_video)
		self.video_Layout.add_widget(self.tutorial_continue_button)
		self.video_Layout.add_widget(self.tutorial_restart_button)

	def _start_video_bypass(self, *args):
		if self.skip_video_enabled and self.current_video is not None:
			self.start_video()

	def start_video(self, *args):
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
		self.show_video_controls()

	def restart_video(self, *args):
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
		if self.manager is not None and self.manager.has_screen(destination_screen):
			self.manager.current = destination_screen


# Class App Builder #
