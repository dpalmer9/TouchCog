# Import

import configparser
import datetime
import os
import pandas as pd
import pathlib
import sys
import time
import threading
import random
from collections import Counter

from kivy.app import App
from kivy.clock import Clock
from kivy.loader import Loader
from kivy.uix.button import ButtonBehavior, Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image, AsyncImage
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
		
		self.event_columns = [
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
		
		self.event_dataframe = pd.DataFrame(columns=self.event_columns)
		self.event_dataframe.Time = self.event_dataframe.Time.astype('float64')
		self.app.session_event_data = self.event_dataframe
		self.event_index = 0
		self.save_path = ''
		self.elapsed_time = 0
		self.touch_time = 0
		self.start_time = 0
	
	
	
	def filter_children(self, string):
		
		return
	
	
	
	def on_touch_down(self, touch):
		
		self.touch_pos = touch.pos
		self.touch_time = time.time() - self.start_time
		
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
			).start()
	
	
	
	def on_touch_move(self, touch):
		
		self.touch_pos = touch.pos
		self.touch_time = time.time() - self.start_time
		
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
					
					threading.Thread(
						target=self.add_event
						, args=([
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
							, 
							)
						).start()
				
				return True
		
		self.held_name = ''
		
		if (abs(self.touch_pos[0] - self.last_recorded_pos[0]) >= self.width_min) \
			or (abs(self.touch_pos[1] - self.last_recorded_pos[1]) >= self.height_min):
			
			self.last_recorded_pos = self.touch_pos
			
			threading.Thread(
				target=self.add_event
				, args=([
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
					, 
					)
				).start()

	
	
	def on_touch_up(self, touch):
		
		self.touch_pos = touch.pos
		self.touch_time = time.time() - self.start_time
		
		if self.disabled:
			return
		
		for child in self.children:
			
			if child.dispatch('on_touch_up', touch):
				
				if isinstance(child, ImageButton):
					self.held_name = child.name
				
				else:
					self.held_name = ''
				
				threading.Thread(
					target=self.add_event
					, args=([
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
						, 
						)
					).start()
				
				return True
		
		self.held_name = ''
		
		threading.Thread(
			target=self.add_event
			, args=([
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
				, 
				)
			).start()
		
		if self.held_name != '':
			self.held_name = ''
	
	
	
	def add_event(self, row):
		
		row_df = pd.DataFrame(columns=self.event_columns)
		new_row = {}
		
		for iCol in range(len(self.event_columns)):

			if iCol >= len(row):
				new_row[self.event_columns[iCol]] = ''
			
			else:
				if self.event_columns[iCol] == 'Time':
					new_row[self.event_columns[iCol]] = float(row[iCol])
				
				else:
					new_row[self.event_columns[iCol]] = str(row[iCol])

		row_df.loc[0] = new_row
		
		self.app.session_event_data = pd.concat([self.app.session_event_data,row_df])

	def add_stage_event(self, stage_name):
		self.add_event([
			(time.time() - self.start_time)
			, 'Stage Change'
			, stage_name
			])
		return
	
	def add_button_event(self, event_type, button_name):
		self.add_event([
			(time.time() - self.start_time)
			, 'Button ' + event_type
			, button_name
			])
		return
	
	def add_text_event(self, event_type, text_name):
		self.add_event([
			(time.time() - self.start_time)
			, 'Text ' + event_type
			, text_name
			])
		return
	
	def add_variable_event(self, variable_class, variable_name, variable_value, variable_type=None, variable_units=None):
		if variable_type is None and variable_units is None:
			self.add_event([
				(time.time() - self.start_time),
			 	'Variable Change',
				variable_class,
				variable_name,
				variable_value])
			
		elif variable_type is not None and variable_units is None:
			self.add_event([
				(time.time() - self.start_time),
			 	'Variable Change',
				variable_class,
				variable_name,
				'Type',
				variable_type])
		
		else:
			self.add_event([
				(time.time() - self.start_time),
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
			(time.time() - self.start_time),
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
		
		self.app.session_event_data = self.app.session_event_data.sort_values(by=['Time'])
		self.app.session_event_data.to_csv(self.app.session_event_path, index=False)
	
	
	
	def update_path(self, path):
		
		self.save_path = pathlib.Path(path)
		self.app.session_event_path = self.save_path




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
			# print('Width > Height')
		
		elif width < height:
			self.height_adjust = width / height
		
		
		
		# Define App
		
		self.app = App.get_running_app()
		
		
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
		
		self.current_block = 1
		self.current_trial = 1
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
		
		self.image_folder = pathlib.Path('Protocol', self.protocol_name, 'Image')
		return


	def constrained_shuffle(self, seq, max_run=3, attempts=1000, rng=None):
		"""
		Instance helper: constrained shuffle that returns a pseudorandom ordering
		of seq where no value repeats more than max_run times consecutively.
		"""
		if rng is None:
			rng = random
		if not seq:
			return []
		n = len(seq)
		counts = Counter(seq)
		for _ in range(attempts):
			result = []
			remaining = dict(counts)
			while len(result) < n:
				candidates = [k for k, v in remaining.items() if v > 0 and not (
					len(result) >= max_run and all(x == k for x in result[-max_run:])
				)]
				if not candidates:
					break
				weights = [remaining[k] for k in candidates]
				choice = rng.choices(candidates, weights=weights, k=1)[0]
				result.append(choice)
				remaining[choice] -= 1
			if len(result) == n:
				return result
		# fallback: try plain shuffle
		for _ in range(attempts):
			tmp = list(seq)
			rng.shuffle(tmp)
			ok = True
			for i in range(len(tmp) - max_run):
				if all(tmp[i + j] == tmp[i] for j in range(max_run + 1)):
					ok = False
					break
			if ok:
				return tmp
		tmp = list(seq)
		rng.shuffle(tmp)
		return tmp
	
	
	
	def load_images(self, image_list):
		
		# Load Images - Async
		
		self.image_dict = {}
		
		for image_file in image_list:
			
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
		
		lang_folder_path = pathlib.Path('Protocol', self.protocol_name, 'Language', self.language)
		
		start_path = lang_folder_path / 'Start.txt'
		start_open = open(start_path, 'r', encoding='utf-8')
		start_label_str = start_open.read()
		start_open.close()
		self.instruction_label.text = start_label_str
		
		break_path = lang_folder_path / 'Break.txt'
		break_open = open(break_path, 'r', encoding='utf-8')
		break_label_str = break_open.read()
		break_open.close()
		self.block_label.text = break_label_str
		
		end_path = lang_folder_path / 'End.txt'
		end_open = open(end_path, 'r', encoding='utf-8')
		end_label_str = end_open.read()
		end_open.close()
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
		
		folder_path = pathlib.Path('Data', self.participant_id)
		
		if not folder_path.is_dir():
			folder_path.mkdir()
		
		self.file_index = 1
		temp_filename = '_'.join([self.participant_id, self.protocol_name, str(datetime.date.today()), str(self.file_index)])
		self.file_path = pathlib.Path(folder_path, temp_filename + '_Summary_Data.csv')
		
		while self.file_path.exists():
			self.file_index += 1
			temp_filename = '_'.join([self.participant_id, self.protocol_name, str(datetime.date.today()), str(self.file_index)])
			self.file_path = pathlib.Path(folder_path, temp_filename + '_Summary_Data.csv')
		
		self.session_data = pd.DataFrame(columns=self.data_cols)
		self.session_data.to_csv(path_or_buf=self.file_path, sep=',', index=False)
		
		event_path = pathlib.Path(folder_path, temp_filename + '_Event_Data.csv')
		
		self.protocol_floatlayout.update_path(event_path)
		self.app.summary_event_path = self.file_path
		self.app.summary_event_data = self.session_data
		return
	
	
	
	def metadata_output_generation(self):
		
		folder_path = pathlib.Path('Data', self.participant_id)
		
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
			
			self.block_start = time.time()
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
		
		self.block_start = time.time()
		self.trial_end_time = time.time()
		self.hold_button.bind(on_press=self.iti_start)
		self.protocol_floatlayout.add_widget(self.hold_button)

		self.protocol_floatlayout.add_button_event('Displayed', 'Hold Button')

		return
	
	
	
	# End Staging #
	
	def protocol_end(self, *args):

		# reset any pending hold_remind stage
		self.hold_remind_stage = 0
		
		self.protocol_floatlayout.clear_widgets()
		self.protocol_floatlayout.add_widget(self.end_label)
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Text Displayed'
			, 'End Instruction'
			])
		
		self.protocol_floatlayout.add_widget(self.return_button)

		self.protocol_floatlayout.add_button_event('Displayed', 'Return Button')

		self.app.summary_event_data.to_csv(self.app.summary_event_path, index=False)
		self.protocol_floatlayout.write_data()

		return
	
	
	
	def return_to_main(self, *args):
		
		self.manager.current = 'mainmenu'

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
		
		self.hold_button.bind(on_press=self.start_iti)

		return
	


	def hold_remind(self, *args):
		if self.feedback_on_screen:
			if self.feedback_label.text in [self.feedback_dict['return'], self.feedback_dict['abort'], self.feedback_dict['wait']]:
					# leave feedback as-is
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

			self.feedback_start_time = time.time()
			self.feedback_on_screen = True

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback', self.feedback_label.text)
		return
		# No further scheduling needed; one-shot behavior keeps polling minimal
	
	
	
	def iti_start(self, *args):	
		if not self.iti_active:
			# ensure no pending reminder stage remains and swap bindings
			self.hold_button_pressed = True
			self.hold_button.unbind(on_press=self.iti_start)
			# bind release to hold_remind instead of premature_response to drive reminder logic

			self.start_iti = time.time()
			self.iti_active = True

			self.protocol_floatlayout.add_stage_event('ITI Start')

			Clock.schedule_once(self.iti_end, self.iti_length)
			if (time.time() - self.start_iti) > (time.time() - self.feedback_start_time) and self.feedback_on_screen:
				Clock.schedule_once(self.remove_feedback, self.feedback_length - (time.time() - self.feedback_start_time))
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
			self.hold_button.bind(on_release=self.hold_lift_trial)
			self.hold_active = True
			self.stimulus_presentation()
				
			return
		else:
			return
	
	def hold_lift_trial(self, *args):
		self.hold_button.unbind(on_release=self.hold_lift_trial)
		self.hold_button_pressed = False

	def remove_feedback(self, *args):
		if self.feedback_on_screen:
			self.protocol_floatlayout.remove_widget(self.feedback_label)

			self.protocol_floatlayout.add_text_event('Removed', 'Feedback')

			self.feedback_on_screen = False  
				
			return
		else:
			return
	
	def write_summary_file(self, data_row):
		
		data_row = pd.Series(data_row, index=self.data_cols)
		self.app.summary_event_data = pd.concat([
			self.app.summary_event_data
			, data_row.to_frame().T
			]
			, axis=0
			, ignore_index=True
			)
		self.app.summary_event_data
		
		return
	
	
	
	def start_clock(self, *args):
		
		self.start_time = time.time()
		self.session_event()
		self.protocol_floatlayout.set_start_time(self.start_time)
		
		return
	
	
	
	def clock_monitor(self, *args):
		
		self.session_event.cancel()
		self.protocol_end()
		
		return