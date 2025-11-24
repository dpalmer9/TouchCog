# Import

import configparser
import datetime
import os
import pandas as pd
import pathlib
import sys
import time
import threading
import queue
import random
import gc
from collections import Counter
from ffpyplayer.player import MediaPlayer

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.loader import Loader
from kivy.uix.button import ButtonBehavior, Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image, AsyncImage
from kivy.graphics.texture import Texture
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.config import Config






class ImageButton(ButtonBehavior, Image):

	def __init__(self, **kwargs):

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
					# best-effort: continue even if dispatch fails
					pass
				# ensure visual/state is normal
				self.state = 'normal'
			self._touch_inside = False
			# consume the move event
			return True

		# If moved back inside, do not re-press automatically; simply update flag
		if inside and not self._touch_inside:
			self._touch_inside = True
			# consume the move event
			return True

		# Otherwise, nothing special to do
		return True


	def on_touch_up(self, touch):
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
					pass
				self.state = 'normal'
			res = True

		# Clear tracked touch
		self._grabbed_touch = None
		self._touch_inside = False
		return res




class FloatLayoutLog(FloatLayout):
	
	def __init__(self, screen_resolution, **kwargs):
		
		super(FloatLayoutLog, self).__init__(**kwargs)
		
		self.app = App.get_running_app()
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
		
		self.event_dataframe = pd.DataFrame(columns=self.app.event_columns)
		self.event_dataframe.Time = self.event_dataframe.Time.astype('float64')
		self.app.session_event_data = self.event_dataframe
		self.app.event_list = list()
		self.event_index = 0
		self.save_path = ''
		self.elapsed_time = 0
		self.touch_time = 0
		self.start_time = 0

		threading.Thread(target=self.event_writer, daemon=True).start()
	
	def event_writer(self):
		while True:
			try:
				event_row = self.app.event_queue.get()
				if event_row is None: # Sentinel to stop the thread
					break
				self.app.event_list.append(event_row)
			except queue.Empty:
				continue # Should not happen with blocking get()
	
	def filter_children(self, string):
		
		return
	
	
	
	def on_touch_down(self, touch):
		
		self.touch_pos = touch.pos
		self.touch_time = time.perf_counter() - self.start_time
		
		if self.disabled and self.collide_point(*touch.pos):
			return True
		
		for child in self.children:
			
			if child.dispatch('on_touch_down', touch):
				
				if isinstance(child, ImageButton):
					self.held_name = child.name
				
				else:
					self.held_name = ''
				
				threading.Thread(
					target=self.add_event
					, args=([
						self.touch_time
						, 'Screen'
						, 'Touch Press'
						, 'X Position'
						, self.touch_pos[0]
						, 'Y Position'
						, self.touch_pos[1]
						, 'Stimulus Name'
						, self.held_name
						]
						, 
						)
					, daemon=False
					).start()
				
				return True
		
		self.held_name = ''

		self.add_event([
			self.touch_time
			, 'Screen'
			, 'Touch Press'
			, 'X Position'
			, self.touch_pos[0]
			, 'Y Position'
			, self.touch_pos[1]
			, 'Stimulus Name'
			, self.held_name
			]
			)
	
	
	
	def on_touch_move(self, touch):
		
		self.touch_pos = touch.pos
		self.touch_time = time.perf_counter() - self.start_time
		
		if self.disabled:
			return
		
		for child in self.children:
			
			if child.dispatch('on_touch_move', touch):
				
				if isinstance(child, ImageButton):
					self.held_name = child.name
				
				else:
					self.held_name = ''
				
				
				if (abs(self.touch_pos[0] - self.last_recorded_pos[0]) >= self.width_min) \
					or (abs(self.touch_pos[1] - self.last_recorded_pos[1]) >= self.height_min):
					
					self.last_recorded_pos = self.touch_pos

					self.add_event([
						self.touch_time
						, 'Screen'
						, 'Touch Move'
						, 'X Position'
						, self.touch_pos[0]
						, 'Y Position'
						, self.touch_pos[1]
						, 'Stimulus Name'
						, self.held_name
						]
						)
				
				return True
		
		self.held_name = ''
		
		if (abs(self.touch_pos[0] - self.last_recorded_pos[0]) >= self.width_min) \
			or (abs(self.touch_pos[1] - self.last_recorded_pos[1]) >= self.height_min):
			
			self.last_recorded_pos = self.touch_pos

			self.add_event([
				self.touch_time,
				'Screen',
				'Touch Move',
				'X Position',
				self.touch_pos[0],
				'Y Position',
				self.touch_pos[1],
				'Stimulus Name',
				self.held_name])

	
	
	def on_touch_up(self, touch):
		
		self.touch_pos = touch.pos
		self.touch_time = time.perf_counter() - self.start_time
		
		if self.disabled:
			return
		
		for child in self.children:
			
			if child.dispatch('on_touch_up', touch):
				
				if isinstance(child, ImageButton):
					self.held_name = child.name
				
				else:
					self.held_name = ''

				self.add_event([
					self.touch_time
					, 'Screen'
					, 'Touch Release'
					, 'X Position'
					, self.touch_pos[0]
					, 'Y Position'
					, self.touch_pos[1]
					, 'Stimulus Name'
					, self.held_name
					]
					)

				return True
		
		self.held_name = ''

		self.add_event([
			self.touch_time
			, 'Screen'
			, 'Touch Release'
			, 'X Position'
			, self.touch_pos[0]
			, 'Y Position'
			, self.touch_pos[1]
			, 'Stimulus Name'
			, self.held_name
			])
		
		if self.held_name != '':
			self.held_name = ''
	
	
	
	def add_event(self, row):
		new_row = {}
		
		for iCol in range(len(self.app.event_columns)):

			if iCol >= len(row):
				new_row[self.app.event_columns[iCol]] = ''
			
			else:
				if self.app.event_columns[iCol] == 'Time':
					new_row[self.app.event_columns[iCol]] = float(row[iCol])
				
				else:
					new_row[self.app.event_columns[iCol]] = str(row[iCol])

		self.app.event_queue.put(new_row)

	def add_stage_event(self, stage_name):
		self.add_event([
			(time.perf_counter() - self.start_time)
			, 'Stage Change'
			, stage_name
			])
		return
	
	def add_button_event(self, event_type, button_name):
		self.add_event([
			(time.perf_counter() - self.start_time)
			, 'Button ' + event_type
			, button_name
			])
		return
	
	def add_text_event(self, event_type, text_name):
		self.add_event([
			(time.perf_counter() - self.start_time)
			, 'Text ' + event_type
			, text_name
			])
		return
	
	def add_variable_event(self, variable_class, variable_name, variable_value, variable_type=None, variable_units=None):
		if variable_type is None and variable_units is None:
			self.add_event([
				(time.perf_counter() - self.start_time),
			 	'Variable Change',
				variable_class,
				variable_name,
				variable_value])
			
		elif variable_type is not None and variable_units is None:
			self.add_event([
				(time.perf_counter() - self.start_time),
			 	'Variable Change',
				variable_class,
				variable_name,
				'Type',
				variable_type])
		
		else:
			self.add_event([
				(time.perf_counter() - self.start_time),
			 	'Variable Change',
				variable_class,
				variable_name,
				'Type',
				variable_type,
				'Units',
				variable_units])
			
	def add_object_event(self, event_type, object_type, object_name, object_detail, image_name=None):
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
		self.start_time = start_time
		return
	
	def write_data(self):
		self.session_event_data = pd.DataFrame(self.app.event_list, columns=self.app.event_columns)
		self.session_event_data.Time = self.session_event_data.Time.astype('float64')
		self.app.session_event_data = self.app.session_event_data.sort_values(by=['Time'])
		self.app.session_event_data.to_csv(self.app.session_event_path, index=False)
	
	
	
	def update_path(self, path):
		
		self.save_path = pathlib.Path(path)
		self.app.session_event_path = self.save_path

class PreloadedVideo(Image):
    def __init__(self, source_path, player=None, loop=False, **kwargs):
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
        # We wait briefly for metadata to be available (sometimes takes a ms)
        timeout = 0
        while self.player.get_metadata()['duration'] is None and timeout < 5:
            time.sleep(0.01)
            timeout += 1

        metadata = self.player.get_metadata()
        fr = metadata.get('frame_rate', (30, 1))
        if isinstance(fr, (tuple, list)) and len(fr) == 2 and fr[1] != 0:
            self.video_fps = float(fr[0]) / float(fr[1])
        else:
            self.video_fps = 30.0
            
        # Initial Frame Load (Thumbnail)
        try:
            # We explicitly seek to 0 to ensure we are at start
            self.player.seek(0)
            frame, val = self.player.get_frame()
            if frame:
                self._update_texture(frame[0])
        except Exception:
            pass

    @mainthread
    def _update_texture(self, img):
        if not self.texture or self.texture.size != img.get_size():
            self.texture = Texture.create(size=img.get_size(), colorfmt='rgb')
            self.texture.flip_vertical()
        self.texture.blit_buffer(img.to_bytearray()[0], colorfmt='rgb', bufferfmt='ubyte')
        self.canvas.ask_update()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
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
        if self._playback_thread and self._playback_thread.is_alive():
            return
        self._stop_event.clear()
        self._playback_thread = threading.Thread(target=self._video_loop, daemon=True)
        self._playback_thread.start()

    def _stop_thread(self):
        self._stop_event.set()

    def _video_loop(self):
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
        """
        The Nuclear Option: Completely destroy the player.
        """
        self.state = 'stop'
        self._stop_thread()
        
        if self.player:
            try:
                self.player.toggle_pause() # Ensure player is not running
                self.player.close_player()
            except Exception:
                pass # Best-effort: ignore failures
            self.player = None
			
    def reload(self):
        try:
            self.player = MediaPlayer(
				self._source_path
			)
			# Ensure newly created player is paused by default
            self.player.set_pause(True)
        except Exception:
			# Best-effort: ignore failures
            pass

    def reset(self):
		# Stop the playback thread and ensure state is stopped
        try:
            self._stop_thread()
        except Exception:
            pass

        self._state = 'stop'
        try:
            if self.player:
                self.player.set_pause(True)
                self.player.seek(0)
                def _update_thumb(dt):
                    try:
                        f, v = self.player.get_frame()
                        if f:
                            self._update_texture(f[0])
                    except Exception:
                        pass

                Clock.schedule_once(_update_thumb, 0.1)
        except Exception:
                # Best-effort: ignore failures
            pass

class ProtocolBase(Screen):
	
	def __init__(self, screen_resolution, **kwargs):
		
		super(ProtocolBase, self).__init__(**kwargs)
		
		self.name = 'protocolscreen'

		self.protocol_floatlayout = FloatLayoutLog(screen_resolution)
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

		documents_path = pathlib.Path.home() / 'Documents'
			
		# Define a dedicated folder for your app's data within Documents
		self.data_folder = documents_path / 'TouchCog' / 'Data'
			
		# Create the directory structure if it doesn't exist
		self.data_folder.mkdir(parents=True, exist_ok=True)

		# Trial Store
		self.app.trial_summary_list = list()
		
		
		# Define Folders
		
		self.protocol_name = ''
		self.image_folder = ''
		
		self.config_path = ''
		self.file_path = ''
		
		
		# Define Datafile
		
		self.meta_data = pd.DataFrame()
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
		self.start_label_str = ''
		self.break_label_str = ''
		self.end_label_str = ''
		self.start_button_label_str = ''
		self.continue_button_label_str = ''
		self.return_button_label_str = ''
		self.stim_feedback_correct_str = ''
		self.stim_feedback_incorrect_str = ''
		self.hold_feedback_wait_str = ''
		self.hold_feedback_return_str = ''
		
		
		# Define Variables - Boolean
		
		self.stimulus_on_screen = False
		self.iti_active = False
		self.block_started = False
		self.feedback_on_screen = False
		self.hold_active = True
		self.hold_button_pressed = False
		
		
		# Define Variables - Counter
		
		self.current_block = 0
		self.current_trial = 0
		self.stage_index = 0
		
		
		# Define Variables - Time
		
		self.start_iti = 0
		self.start_time = 0
		self.block_start = 0
		self.elapsed_time = 0
		self.feedback_start_time = 0
		self.trial_end_time = 0
		
		
		# Define Class - Clock

		# hold_remind is managed manually with Clock.schedule_once; use a stage flag
		# stage: 0 = initial (will schedule delayed), 1 = delayed (perform check)
		self.hold_remind_stage = 0

		self.session_clock = Clock
		self.session_clock.interupt_next_only = False
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
	
	def update_task(self):
		
		self.image_folder = self.app.app_root / 'Protocol' / self.protocol_name / 'Image'
		return	

	def constrained_shuffle(self,seq, max_run=3, attempts=100, rng=None):
		"""
		Returns a pseudorandom ordering of a sequence where no value
		repeats more than `max_run` times consecutively.

		Args:
			seq (list): The sequence to shuffle.
			max_run (int): The maximum number of consecutive identical items.
			attempts (int): The number of times to attempt the shuffle before failing.
			rng (random.Random, optional): An instance of a random number generator.

		Returns:
			list: A new list with the shuffled sequence.

		Raises:
			ValueError: If a valid shuffle cannot be found within the given attempts.
		"""
		if rng is None:
			rng = random
		if not seq:
			return []

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
		
		# Load Images - Async
		
		self.image_dict = {}
		
		for image_file in image_list:
			try:
				image_file = pathlib.Path(image_file)
			except Exception:
				pass
			if pathlib.Path(self.image_folder / image_file).exists():
				load_image = Loader.image(str(self.image_folder / image_file))
				image_name = str(image_file.stem)
			
			elif pathlib.Path(self.image_folder, str(image_file) + '.png').exists():
				load_image = Loader.image((str(self.image_folder) + str(image_file) + '.png'))
				image_name = str(image_file)

			else:
				image_file = pathlib.Path(image_file)
				load_image = Loader.image(str(image_file))
				image_name = str(image_file.stem)

			self.image_dict[image_name] = load_image
		
		return
	
	
	
	def set_language(self, language):
		
		self.language = language
		
		lang_folder_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language
		
		start_path = lang_folder_path / 'Start.txt'
		with open(start_path, 'r', encoding='utf-8') as file:
			start_label_str = file.read()
		self.instruction_label.text = start_label_str
		
		break_path = lang_folder_path / 'Break.txt'
		with open(break_path , 'r', encoding='utf-8') as file:
			break_label_str = file.read()
		self.block_label.text = break_label_str
		
		end_path = lang_folder_path / 'End.txt'
		with open(end_path, 'r', encoding='utf-8') as file:
			end_label_str = file.read()
		self.end_label.text = end_label_str
		
		button_lang_path = lang_folder_path / 'Button.ini'
		button_lang_config = configparser.ConfigParser()
		button_lang_config.read(button_lang_path, encoding='utf-8')
		
		start_button_label_str = button_lang_config['Button']['start']
		self.start_button.text = start_button_label_str
		
		continue_button_label_str = button_lang_config['Button']['continue']
		self.continue_button.text = continue_button_label_str
		
		return_button_label_str = button_lang_config['Button']['return']
		self.return_button.text = return_button_label_str
		
		feedback_lang_path = lang_folder_path / 'Feedback.ini'
		feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
		feedback_lang_config.read(feedback_lang_path, encoding='utf-8')
		
		self.feedback_dict = {}
		
		stim_feedback_correct_str = feedback_lang_config['Stimulus']['correct']
		stim_feedback_correct_color = feedback_lang_config['Stimulus']['correct_colour']
		
		if stim_feedback_correct_color != '':
			color_text = '[color=%s]' % stim_feedback_correct_color
			stim_feedback_correct_str = color_text + stim_feedback_correct_str + '[/color]'
		
		self.feedback_dict['correct'] = stim_feedback_correct_str
		
		stim_feedback_incorrect_str = feedback_lang_config['Stimulus']['incorrect']
		stim_feedback_incorrect_color = feedback_lang_config['Stimulus']['incorrect_colour']
		
		if stim_feedback_incorrect_color != '':
			color_text = '[color=%s]' % stim_feedback_incorrect_color
			stim_feedback_incorrect_str = color_text + stim_feedback_incorrect_str + '[/color]'
		
		self.feedback_dict['incorrect'] = stim_feedback_incorrect_str
		
		hold_feedback_wait_str = feedback_lang_config['Hold']['wait']
		hold_feedback_wait_color = feedback_lang_config['Hold']['wait_colour']
		
		if hold_feedback_wait_color != '':
			color_text = '[color=%s]' % hold_feedback_wait_color
			hold_feedback_wait_str = color_text + hold_feedback_wait_str + '[/color]'
		
		self.feedback_dict['wait'] = hold_feedback_wait_str
		
		hold_feedback_return_str = feedback_lang_config['Hold']['return']
		hold_feedback_return_color = feedback_lang_config['Hold']['return_colour']
		
		if hold_feedback_return_color != '':
			color_text = '[color=%s]' % hold_feedback_return_color
			hold_feedback_return_str = color_text + hold_feedback_return_str + '[/color]'
		
		self.feedback_dict['return'] = hold_feedback_return_str


		stim_feedback_too_slow_str = feedback_lang_config['Stimulus']['too_slow']
		stim_feedback_too_slow_color = feedback_lang_config['Stimulus']['too_slow_colour']
		
		if stim_feedback_too_slow_color != '':
			color_text = '[color=%s]' % stim_feedback_too_slow_color
			stim_feedback_too_slow_str = color_text + stim_feedback_too_slow_str + '[/color]'
		
		self.feedback_dict['too_slow'] = stim_feedback_too_slow_str

		
		stim_feedback_miss_str = feedback_lang_config['Stimulus']['miss']
		stim_feedback_miss_color = feedback_lang_config['Stimulus']['miss_colour']
		
		if stim_feedback_miss_color != '':
			color_text = '[color=%s]' % stim_feedback_miss_color
			stim_feedback_miss_str = color_text + stim_feedback_miss_str + '[/color]'
		
		self.feedback_dict['miss'] = stim_feedback_miss_str

		
		stim_feedback_abort_str = feedback_lang_config['Stimulus']['abort']
		stim_feedback_abort_color = feedback_lang_config['Stimulus']['abort_colour']
		
		if stim_feedback_abort_color != '':
			color_text = '[color=%s]' % stim_feedback_abort_color
			stim_feedback_abort_str = color_text + stim_feedback_abort_str + '[/color]'
		
		self.feedback_dict['abort'] = stim_feedback_abort_str
		
		return
	
	
	
	def generate_output_files(self):

		folder_path = pathlib.Path(self.data_folder, self.participant_id)

		if not folder_path.is_dir():
			folder_path.mkdir()
		
		self.file_index = 1
		temp_filename = '_'.join([self.participant_id, self.protocol_name, str(datetime.date.today()), str(self.file_index)])
		self.file_path = pathlib.Path(folder_path, temp_filename + '_Summary_Data.csv')
		
		while self.file_path.exists():
			self.file_index += 1
			temp_filename = '_'.join([self.participant_id, self.protocol_name, str(datetime.date.today()), str(self.file_index)])
			self.file_path = pathlib.Path(folder_path, temp_filename + '_Summary_Data.csv')
		
		# self.session_data = pd.DataFrame(columns=self.data_cols)
		# self.session_data.to_csv(path_or_buf=self.file_path, sep=',', index=False)
		
		event_path = pathlib.Path(folder_path, temp_filename + '_Event_Data.csv')
		
		self.protocol_floatlayout.update_path(event_path)
		self.app.trial_summary_cols = self.data_cols
		self.app.summary_event_path = self.file_path
		self.app.summary_event_data = self.session_data
		return
	
	
	
	def metadata_output_generation(self):
		
		folder_path = pathlib.Path(self.data_folder, self.participant_id)
		
		meta_list = list()
		
		for meta_row in self.metadata_cols:
			row_list = list()
			row_list.append(meta_row)
			row_list.append(str(self.parameters_dict[meta_row]))
			meta_list.append(row_list)
		
		alt_index = 1
		meta_output_filename = '_'.join([self.participant_id, self.protocol_name, str(datetime.date.today()), str(self.file_index)])
		meta_output_path = pathlib.Path(folder_path, meta_output_filename + '_Metadata.csv')
		
		while meta_output_path.exists():
			alt_index += 1
			meta_output_filename = '_'.join([self.participant_id, self.protocol_name, str(datetime.date.today()), str(self.file_index), str(alt_index)])
			meta_output_path = pathlib.Path(folder_path, meta_output_filename + '_Metadata.csv')
		
		self.meta_data = pd.DataFrame(meta_list, columns=['Parameter', 'Value'])
		self.meta_data.to_csv(path_or_buf=meta_output_path, sep=',', index=False)
		return
	
	
	
	def present_instructions(self):
		
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
		
		if not self.block_started:

			self.protocol_floatlayout.add_widget(self.block_label)
			
			self.protocol_floatlayout.add_text_event('Displayed', 'Block Instruction')

			# reset any pending hold_remind stage
			self.hold_remind_stage = 0
			
			self.block_start = time.perf_counter()
			self.block_started = True
		
			Clock.schedule_once(self.block_rest_end, self.block_min_rest_duration)
			return
		else:
			return
		

	def block_rest_end(self, *args):
		self.protocol_floatlayout.add_widget(self.continue_button)

		self.protocol_floatlayout.add_button_event('Displayed', 'Continue Button')
		return
	
	
	def block_end(self, *args):
		
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
	
	
	
	# End Staging #

	def _clear_video_cache(self):
		video_file_names = ['delay_video','tutorial_video']

		for video_name in video_file_names:
			if not hasattr(self, video_name):
				continue
			video_attr = getattr(self, video_name, None)
			if not video_attr:
				continue

			try:
				video_attr.state = 'stop'
			except Exception:
				pass

			try:
				if video_attr._video:
					video_attr._video.stop()
					video_attr._video.unload()
			except Exception:	
				pass

			try:
				if hasattr(self,'_check_delay_video_loaded'):
					video_attr.unbind(loaded=self._check_delay_video_loaded)
			except Exception:
				pass

			try:
				video_attr.source = ''
			except Exception:
				pass

			try:
				delattr(self, video_name)
			except Exception:
				try:
					setattr(self, video_name, None)
				except Exception:
					pass
			
		gc.collect()
	
	def protocol_end(self, *args):
		# Check Video Removal
		self._clear_video_cache()
		# reset any pending hold_remind stage
		self.hold_remind_stage = 0
		
		self.protocol_floatlayout.clear_widgets()
		Clock.unschedule(self.hold_remind)
		Clock.unschedule(self.iti_end)
		self.protocol_floatlayout.add_widget(self.end_label)
		
		self.protocol_floatlayout.add_event([
			(time.perf_counter() - self.start_time)
			, 'Text Displayed'
			, 'End Instruction'
			])
		
		self.protocol_floatlayout.add_widget(self.return_button)

		self.protocol_floatlayout.add_button_event('Displayed', 'Return Button')

		self.app.summary_event_data = pd.DataFrame(self.app.trial_summary_data, columns=self.app.trial_summary_cols)
		self.app.summary_event_data.to_csv(self.app.summary_event_path, index=False)
		self.protocol_floatlayout.write_data()

		return
	
	
	
	def return_to_main(self, *args):
		
		self.manager.current = 'mainmenu'
		self.current_widget = self.manager.get_screen(self.name)
		self.manager.remove_widget(self.current_widget)

		# If a battery run is active, notify the app so it can advance to next task
		try:
			if getattr(self.app, 'battery_active', False):
				# delegate to MenuApp to advance and start next battery task
				if hasattr(self.app, 'battery_task_finished'):
					self.app.battery_task_finished()
		except Exception:
			# best-effort: ignore failures here
			pass

		return
	
	
	
	def start_protocol(self, *args):

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
	


	def hold_remind(self, *args):
		if self.feedback_on_screen:
			if self.feedback_label.text in [self.feedback_dict['return'], self.feedback_dict['abort'], self.feedback_dict['wait']]:
					# leave feedback as-is
				Clock.unschedule(self.remove_feedback)
				return
			elif self.block_started:
				return
			else:
					# remove any other feedback text
				Clock.unschedule(self.remove_feedback)
				self.protocol_floatlayout.remove_widget(self.feedback_label)
				self.protocol_floatlayout.add_text_event('Removed', 'Feedback')
				self.feedback_on_screen = False

		if not self.feedback_on_screen:
			self.feedback_label.text = self.feedback_dict['return']
			self.protocol_floatlayout.add_widget(self.feedback_label)

			self.feedback_start_time = time.perf_counter()
			self.feedback_on_screen = True

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback', self.feedback_label.text)
		return
		# No further scheduling needed; one-shot behavior keeps polling minimal
	
	
	
	def iti_start(self, *args):	
		if not self.iti_active:
			Clock.unschedule(self.hold_remind)
			# ensure no pending reminder stage remains and swap bindings
			self.hold_button_pressed = True
			self.hold_button.unbind(on_press=self.iti_start)
			self.hold_button.bind(on_release=self.hold_remind)
			# bind release to hold_remind instead of premature_response to drive reminder logic

			self.start_iti = time.perf_counter()
			self.iti_active = True

			self.protocol_floatlayout.add_stage_event('ITI Start')

			Clock.schedule_once(self.iti_end, self.iti_length)
			if (time.perf_counter() - self.start_iti) > (time.perf_counter() - self.feedback_start_time) and self.feedback_on_screen:
				Clock.schedule_once(self.remove_feedback, self.feedback_length - (time.perf_counter() - self.feedback_start_time))
			else:
				Clock.schedule_once(self.remove_feedback, self.feedback_length)			
			return
		else:
			return
	
	def iti_end(self, *args):
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
		#self.hold_button.unbind(on_release=self.hold_lift_trial)
		self.hold_button_pressed = False
	def hold_lift_returned(self, *args):
		self.hold_button_pressed = True

	def remove_feedback(self, *args):
		if self.feedback_on_screen:
			self.protocol_floatlayout.remove_widget(self.feedback_label)

			self.protocol_floatlayout.add_text_event('Removed', 'Feedback')

			self.feedback_on_screen = False  
				
			return
		else:
			return
	
	def write_summary_file(self, data_row):
		self.app.trial_summary_data.append(data_row)
		return
	
	
	
	def start_clock(self, *args):
		
		self.start_time = time.perf_counter()
		self.session_event()
		self.protocol_floatlayout.set_start_time(self.start_time)
		
		return
	
	
	
	def clock_monitor(self, *args):
		
		self.session_event.cancel()
		self.protocol_end()
		
		return