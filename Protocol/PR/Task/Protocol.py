# Imports #

import configparser
import numpy as np
import pathlib
import random
import statistics
import time

from Classes.Protocol import ImageButton, ProtocolBase

from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.video import Video




class ProtocolScreen(ProtocolBase):

	def __init__(self, **kwargs):

		super(ProtocolScreen, self).__init__(**kwargs)
		self.protocol_name = 'PR'
		self.name = self.protocol_name + '_protocolscreen'
		self.update_task()
		
		# Define Data Columns

		self.data_cols = [
			'TrialNo'
			, 'CurrentBlock'
			, 'BlockTrial'
			, 'TotalHitCount'
			, 'ResponseLevel'
			, 'TargetXPos'
			, 'TargetYPos'
			, 'Latency'
			]

		self.metadata_cols = [
			'participant_id'
			, 'skip_tutorial_video'
			, 'block_change_on_duration_only'
			, 'iti_fixed_or_range'
			, 'iti_length'
			, 'feedback_length'
			, 'block_duration'
			, 'block_min_rest_duration'
			, 'session_duration'
			, 'stimulus_image'
			, 'stimulus_pressed_image'
			, 'stimulus_size'
			, 'stimulus_distance'
			, 'response_level_start'
			, 'response_level_end'
			, 'use_confirmation'
			]
		
		
		# Define Variables - Config Import
		
		self.config_path = str(self.app.app_root / 'Protocol' / self.protocol_name / 'Configuration.ini')
		self.config_file = configparser.ConfigParser()
		self.config_file.read(self.config_path)

		self.debug_mode = False

		if ('DebugParameters' in self.config_file) \
			and self.config_file.getboolean('DebugParameters', 'debug_mode'):

			self.parameters_dict = self.config_file['DebugParameters']
			self.debug_mode = True

		else:
			self.parameters_dict = self.config_file['TaskParameters']
			self.debug_mode = False



	def _load_config_parameters(self, parameters_dict):
		self.parameters_dict = parameters_dict
		self.participant_id = self.parameters_dict.get('participant_id', '')
		self.skip_tutorial_video = self.parameters_dict.get('skip_tutorial_video', 'False')
		self.tutorial_video_duration = float(self.parameters_dict.get('tutorial_video_duration', '51.5'))

		self.block_change_on_duration = self.parameters_dict.get('block_change_on_duration_only', 'True')

		self.iti_fixed_or_range = self.parameters_dict.get('iti_fixed_or_range', 'range')
		
		self.iti_import = self.parameters_dict.get('iti_length', '0.75,1.25')
		self.iti_import = self.iti_import.split(',')

		self.feedback_length = float(self.parameters_dict.get('feedback_length', '0.75'))
		self.timeout_duration = int(self.parameters_dict.get('timeout_duration', '15'))
		self.hold_button_delay = float(self.parameters_dict.get('hold_button_delay', '1'))
		self.block_duration = int(self.parameters_dict.get('block_duration', '1200'))
		self.block_min_rest_duration = float(self.parameters_dict.get('block_min_rest_duration', '1'))
		self.session_duration = float(self.parameters_dict.get('session_duration', '3600'))
		
		self.block_multiplier = int(self.parameters_dict.get('block_multiplier', '1'))

		self.stimulus_image = self.parameters_dict.get('stimulus_image', 'whitecircle')
		self.stimulus_pressed_image = self.parameters_dict.get('stimulus_pressed_image', 'greycircle')
		self.stimulus_size = float(self.parameters_dict.get('stimulus_size', '0.08'))
		self.stimulus_distance = float(self.parameters_dict.get('stimulus_distance', '0.6'))
		
		self.response_level = int(self.parameters_dict.get('response_level_start', '1'))
		self.response_level_end = int(self.parameters_dict.get('response_level_end', '10'))

		self.use_confirmation = self.parameters_dict.get('use_confirmation', 'True')

		self.hold_image = self.config_file['Hold']['hold_image']
		self.mask_image = self.config_file['Mask']['mask_image']

	def _load_task_variables(self):
		# Define Variables - Count

		self.hit_target = 2 ** self.response_level
		self.total_hit_count = 0
		self.response_count_list = list()

		self.current_block = -1


		# Define Variables - Time
		
		self.iti_range = [float(iNum) for iNum in self.iti_import]
		self.iti_length = self.iti_range[0]

		self.block_start_time = 0.0
		self.block_end_time = 0.0
		self.stimulus_start_time = 0.0
		self.response_latency = 0.0

		# Define Variables - Boolean

		self.feedback_on_screen = False
		self.stimulus_on_screen = False
		self.participant_stopped = False

	def _setup_session_stages(self):
		self.task_clock = Clock
		self.no_response_event = self.task_clock.schedule_once(self.protocol_end, self.timeout_duration)
		self.no_response_event.cancel()

	def _setup_image_widgets(self):
		# Define Widgets - Buttons

		self.text_button_size = [0.4, 0.15]
		self.text_button_pos_LL = {"center_x": 0.25, "center_y": 0.08}
		self.text_button_pos_LR = {"center_x": 0.75, "center_y": 0.08}

		self.quit_button = Button(text='STOP', font_size='24sp')
		self.quit_button.size_hint = (0.2, 0.1)
		self.quit_button.pos_hint = {'center_x': 0.25, 'y': 0.01}
		self.quit_button.bind(on_press=self.results_screen)

		self.confirm_button = Button(text='Confirm', font_size='24sp')
		self.confirm_button.size_hint = (0.2, 0.1)
		self.confirm_button.pos_hint = {'center_x': 0.75, 'center_y': 0.07}
		self.confirm_button.color = 'grey'

		self.block_start_button = Button(text='Start Task', font_size='24sp')
		self.block_start_button.size_hint = self.text_button_size
		self.block_start_button.pos_hint = {'center_x': 0.5, 'center_y': 0.9}
		self.block_start_button.bind(on_press=self.start_block)


		# Define Widgets - Images

		self.image_folder = self.app.app_root / 'Protocol' / self.protocol_name / 'Image'

		self.stimulus_image_path = str(self.image_folder / str(self.stimulus_image + '.png'))
		self.stimulus_pressed_image_path = str(self.image_folder / str(self.stimulus_pressed_image + '.png'))
		self.hold_image_path = str(self.image_folder / str(self.hold_image + '.png'))
		self.mask_image_path = str(self.image_folder / str(self.mask_image + '.png'))
		self.checkmark_image_path = str(self.image_folder / 'checkmark.png')

		self.hold_button.unbind(on_release=self.hold_remind)
		self.hold_button.bind(on_release=self.premature_response)

		# self.target_x_pos = 0
		# self.target_y_pos = 1

		# Stimulus distance variable gives stimulus location as proportion of vertical screen size
		# Stimulus location based on distance from center of hold button
		# main_move gives maximum vertical screen proportion distance between center of hold button and center of stimulus
		# Horizontal distance between stimulus and hold button adjusted by width_adjust to maintain consistent physical distance
		# x and y boundaries provide horizontal/vertical min/max values for possible stimulus locations relative to hold button center

		# First, verify that max vertical distance does not put stimulus outside screen boundaries
		if (self.stimulus_distance + ((self.stimulus_size * self.height_adjust) / 2) + 0.005) > 1:
			self.stimulus_distance = 1 - ((self.stimulus_size * self.height_adjust) / 2) - 0.005

		# Next, identify distance relative to hold button center
		self.main_move = self.stimulus_distance - self.hold_button.pos_hint['center_y']

		# Set Y boundaries based on hold button position and max distance
		self.y_boundaries = [
			round((self.hold_button.pos_hint['center_y'] \
				+ (self.hold_button.size_hint[1] / 2) \
				+ ((self.stimulus_size * self.height_adjust) / 2) \
				+ 0.005), 3)
			, self.stimulus_distance
			]

		# Set X boundaries based on move distance from center of hold button
		self.x_boundaries = [
			round((self.hold_button.pos_hint['center_x'] \
				- (self.main_move * self.width_adjust)), 3)
			, round((self.hold_button.pos_hint['center_x'] \
				+ (self.main_move * self.width_adjust)), 3)
			]

		# Ensure possible x locations don't put stimulus outside edge of screen
		if ((min(self.x_boundaries) - ((self.stimulus_size * self.width_adjust) / 2) - 0.005) < 0) \
			or ((max(self.x_boundaries) + ((self.stimulus_size * self.width_adjust) / 2) + 0.005) > 1):

			# If X boundaries put any portion of stimulus outside screen area, change X boundaries to keep stimulus completely within screen
			self.x_boundaries = [
				round((((self.stimulus_size * self.width_adjust) / 2) + 0.005), 3)
				, round((1 - ((self.stimulus_size * self.width_adjust) / 2) - 0.005), 3)
				]

		self.stimulus_pos = {'center_x': self.hold_button.pos_hint['center_x'], 'center_y': self.stimulus_distance}

		self.stimulus_button = ImageButton(source=str(self.stimulus_image_path))
		self.stimulus_button.pos_hint = self.stimulus_pos
		self.stimulus_button.size_hint = (self.stimulus_size * self.width_adjust, self.stimulus_size * self.height_adjust)
		self.stimulus_button.bind(on_press=self.target_pressed)

		self.stimulus_button_pressed = ImageButton(source=str(self.stimulus_pressed_image_path))
		self.stimulus_button_pressed.pos_hint = self.stimulus_button.pos_hint
		self.stimulus_button_pressed.size_hint = self.stimulus_button.size_hint

		self.reward_image = Image(source=str(self.checkmark_image_path))
		self.reward_image.pos_hint = {"center_x": 0.5, "center_y": 0.8}
		self.reward_image.size_hint = (1 * self.width_adjust, 1 * self.height_adjust)

		total_image_list = [
			self.stimulus_image_path
			, self.stimulus_pressed_image_path
			, self.hold_image_path
			, self.mask_image_path
			, self.checkmark_image_path
			]
		
		self.hold_button.source = str(self.hold_image_path)

	def _setup_language_localization(self):
		self.set_language(self.language)
		self.feedback_label = Label(font_size='32sp')
		self.feedback_label.size_hint = (0.8, 0.4)
		self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.55}
		self.feedback_label.text = ''


	def _load_video_and_instruction_components(self):
		self.lang_folder_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language

		if (self.lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_path = str(list((self.lang_folder_path / 'Tutorial_Video').glob('*.mp4'))[0])
			self.tutorial_video = Video(
				source = self.tutorial_video_path
				, pos_hint = {'center_x': 0.5, 'center_y': 0.5 + self.text_button_size[1]}
				, fit_mode = 'contain'
				)

		self.tutorial_restart_button_button = Button(text='Restart Video', font_size='48sp')
		self.tutorial_restart_button_button.size_hint = self.text_button_size
		self.tutorial_restart_button_button.pos_hint = self.text_button_pos_LL
		self.tutorial_restart_button_button.bind(on_press=self.tutorial_restart)

		self.tutorial_start_button = Button(text='Start Task', font_size='48sp')
		self.tutorial_start_button.size_hint = self.text_button_size
		self.tutorial_start_button.pos_hint = self.text_button_pos_LR
		self.tutorial_start_button.bind(on_press=self.stop_tutorial_video)
		
		self.tutorial_video_button = Button(text='Tap the screen\nto start video', font_size='48sp', halign='center', valign='center')
		self.tutorial_video_button.background_color = 'black'
		self.tutorial_video_button.size_hint = (1, 1)
		self.tutorial_video_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
		self.tutorial_video_button.bind(on_press=self.start_tutorial_video)

		
		# Define Instruction Components

		self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.55}

	# Initialization Functions #
		
	def load_parameters(self,parameter_dict):
		self._load_config_parameters(parameter_dict)
		self._load_task_variables()
		self._setup_session_stages()
		self._setup_image_widgets()
		self._setup_language_localization()
		self._load_video_and_instruction_components()
		
		# Begin Task

		if (self.lang_folder_path / 'Tutorial_Video').is_dir() \
			and not self.skip_tutorial_video:

			self.protocol_floatlayout.clear_widgets()
			self.present_tutorial_video()
		
		else:
			self.present_instructions()



	def generate_stimulus_pos(
		self
		, *args
		):

		# This function requires task-level x and y boundary and main_move variables (can be adjusted to take all of these as arguments instead)
		# Stimulus Y position is always positive relative to hold button
		# Select X position from x boundaries, then derive Y postion from there
		# Every X position has only one Y location associated with it to equal Euclidean distance

		x_pos = random.uniform(min(self.x_boundaries), max(self.x_boundaries))

		# If difference between existing and new x position is less than 10% of screen width, select new location
		while abs(x_pos - self.stimulus_pos['center_x']) < 0.1:
			x_pos = random.uniform(min(self.x_boundaries), max(self.x_boundaries))

		x_move = (self.hold_button.pos_hint['center_x'] - x_pos) / self.width_adjust

		y_move = float(np.sqrt(self.main_move**2 - x_move**2))
		y_pos = self.hold_button.pos_hint['center_y'] + y_move

		while (y_pos < min(self.y_boundaries)) \
			or (y_pos > max(self.y_boundaries)):

			x_pos = random.uniform(min(self.x_boundaries), max(self.x_boundaries))

			# If difference between existing and new x position is less than 10% of screen width, select new location
			while abs(x_pos - self.stimulus_pos['center_x']) < 0.1:
				x_pos = random.uniform(min(self.x_boundaries), max(self.x_boundaries))

			x_move = (self.hold_button.pos_hint['center_x'] - x_pos) / self.width_adjust

			y_move = float(np.sqrt(self.main_move**2 - x_move**2))
			y_pos = self.hold_button.pos_hint['center_y'] + y_move
		
		stimulus_pos = {'center_x': x_pos, 'center_y': y_pos}

		return stimulus_pos



	def present_tutorial_video(self, *args):

		self.protocol_floatlayout.clear_widgets()
			
		self.protocol_floatlayout.add_stage_event('State Change')
		self.protocol_floatlayout.add_object_event('Display', 'Object', 'Tutorial Video', 'Start')
		self.protocol_floatlayout.add_widget(self.tutorial_video)
		self.protocol_floatlayout.add_widget(self.tutorial_video_button)

		self.tutorial_video.state = 'stop'

		self.tutorial_video_first_play = True

		return
	


	def start_tutorial_video(self, *args):

		self.tutorial_video.state = 'play'

		if self.tutorial_video_first_play:
			self.tutorial_video_first_play = False
			self.protocol_floatlayout.remove_widget(self.tutorial_video_button)
			Clock.schedule_once(self.present_tutorial_video_start_button, self.tutorial_video_duration)
			self.protocol_floatlayout.add_object_event('Display', 'Video', 'Section', 'Instructions')

		return


	def present_tutorial_video_start_button(self, *args):
		self.protocol_floatlayout.add_widget(self.tutorial_start_button)
		self.protocol_floatlayout.add_widget(self.tutorial_restart_button_button)
				
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Section', 'Instructions', image_name='Section Start')
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Section', 'Instructions', image_name='Video Restart')
		return
	
	
	def stop_tutorial_video(self, *args):
		self.tutorial_video.state = 'stop'
		self.protocol_floatlayout.add_object_event('Remove', 'Video', 'Section', 'Instructions')
		self.start_protocol_from_tutorial()

	def tutorial_restart(self, *args):
		self.tutorial_video.state = 'stop'
		self.start_tutorial_video()
	
	
	
	def start_protocol_from_tutorial(self, *args):
		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_stage_event('Section Start')
		self.generate_output_files()
		self.metadata_output_generation()

		self.start_clock()

		self.block_contingency()


	def results_screen(self, *args):
			self.protocol_floatlayout.clear_widgets()
			self.participant_stopped = True
			self.feedback_on_screen = False

			self.outcome_string = 'Great job!\n\nYou completed ' \
				+ str(self.total_hit_count//2) \
				+ ' trials and ' \
				+ str(self.current_block - 1) \
				+ ' blocks!\n\n' \
				+ 'Please inform the researcher that you have finished this task.'

			self.feedback_label.text = self.outcome_string
			
			self.quit_button.unbind(on_press=self.results_screen)
			self.quit_button.bind(on_press=self.protocol_end)
			self.quit_button.pos_hint = {'center_x': 0.5, 'center_y': 0.07}

			self.protocol_floatlayout.add_widget(self.feedback_label)
			self.protocol_floatlayout.add_widget(self.quit_button)
			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Stage', 'Results')


	def stimulus_presentation(self, *args): # Stimulus presentation
		self.hold_button.unbind(on_press=self.iti_start)
		self.hold_button.unbind(on_release=self.premature_response)

		self.protocol_floatlayout.remove_widget(self.hold_button)

		self.stimulus_start_time = time.time()
		self.protocol_floatlayout.add_stage_event('State Change')
		if (self.current_block_trial % 2) != 1 \
			and self.use_confirmation:

			self.hold_button.bind(on_press=self.target_pressed)
			self.protocol_floatlayout.add_widget(self.hold_button)
		
			self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Target', 'Hold Button')
		else:
			self.protocol_floatlayout.add_widget(self.stimulus_button)
			self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Target', str(self.stimulus_button.pos_hint))

		self.stimulus_on_screen = True

		Clock.schedule_once(self.no_response_event, self.timeout_duration)
	
				
	
	def premature_response(self, *args): # Trial Outcomes: 0-Premature,1-Hit,2-Miss,3-False Alarm,4-Correct Rejection,5-Hit, no center touch,6-False Alarm, no center touch
		self.hold_button_pressed = False
		if self.stimulus_on_screen:
			return
		
		Clock.unschedule(self.iti_end)
		
		self.protocol_floatlayout.clear_widgets()
		
		self.response_latency = np.nan

		self.protocol_floatlayout.add_stage_event('Premature Response')

		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)
		
		self.iti_active = False
		self.feedback_label.text = self.feedback_dict['wait']

		if self.feedback_on_screen is False:	
			self.protocol_floatlayout.add_widget(self.feedback_label)
			self.feedback_on_screen = True
			self.feedback_start_time = time.time()

			self.protocol_floatlayout.add_text_event('Display', self.feedback_label.text)
		
		self.hold_button.unbind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.start_block)

		self.protocol_floatlayout.add_widget(self.hold_button)
		self.protocol_floatlayout.add_widget(self.quit_button)
		self.hold_button.bind(on_press=self.iti_start)
	
	
	
	# Target Pressed
	
	def target_pressed(self, *args):
		
		# print('Target pressed')

		Clock.unschedule(self.no_response_event)

		self.stimulus_press_time = time.time()
		self.response_latency = self.stimulus_press_time - self.stimulus_start_time

		self.protocol_floatlayout.add_stage_event('Target Pressed')
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)

		if (self.current_block_trial % 2) != 1 \
			and self.use_confirmation:

			self.hold_button.unbind(on_press=self.target_pressed)
			self.protocol_floatlayout.remove_widget(self.hold_button)
			self.protocol_floatlayout.remove_widget(self.stimulus_button_pressed)

			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Target', 'Hold Button')
		else:
			self.protocol_floatlayout.remove_widget(self.stimulus_button)
			self.protocol_floatlayout.add_widget(self.stimulus_button_pressed)

			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Target', str(self.stimulus_button.pos_hint))
		
		self.total_hit_count += 1
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Block Hit Count', str(self.current_block_trial))
		self.protocol_floatlayout.add_variable_event('Outcome', 'Total Hit Count', str(self.total_hit_count))

		self.stimulus_on_screen = False

		self.write_trial()
		self.trial_contingency()

		return
	
	
	
	# Data Saving Function
	
	def write_trial(self):
		
		# print('Write trial')

		trial_data = [
			self.current_trial
			, self.current_block
			, self.current_block_trial
			, self.total_hit_count
			, self.response_level
			, self.stimulus_button.pos_hint['center_x']
			, self.stimulus_button.pos_hint['center_y']
			, self.response_latency
			]
		
		self.write_summary_file(trial_data)
	
	
	
	# Trial Contingency Functions
	
	def trial_contingency(self):
		
		try:
			if self.current_block_trial >= self.hit_target:
				Clock.unschedule(self.iti_end)

				self.current_block += 1
				self.response_level += 1

				self.hit_target = 2 ** self.response_level

				self.block_end_time = time.time()

				self.protocol_floatlayout.add_stage_event('Block End')

				self.protocol_floatlayout.add_variable_event('Parameter', 'Response Level', self.response_level)
				self.protocol_floatlayout.add_variable_event('Parameter', 'Hit Target', self.hit_target)
				
				self.block_contingency()
				return
			

			else:
				self.current_trial += 1
				self.current_block_trial += 1
				
				self.protocol_floatlayout.add_variable_event('Parameter', 'Current Trial', str(self.current_trial))
				self.protocol_floatlayout.add_variable_event('Parameter', 'Current Block Trial', str(self.current_block_trial))
					
				# Set next trial parameters

				if (self.current_block_trial % 2) != 1 \
					and self.use_confirmation:

					# Confirmation button trial
					pass


				else:
					self.stimulus_pos = self.generate_stimulus_pos()

					self.stimulus_button.pos_hint = self.stimulus_pos
					self.stimulus_button_pressed.pos_hint = self.stimulus_button.pos_hint

					self.protocol_floatlayout.add_variable_event('Parameter', 'Target Location', self.stimulus_button.pos_hint)

				self.stimulus_presentation()
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()
	


	def block_screen_display_hold_button(self, *args):
		if not self.participant_stopped:
			self.protocol_floatlayout.add_widget(self.hold_button)
		else:
			return


	# Block start function (add widgets and set block start time)

	def start_block(self, *args):
		self.hold_button_pressed = True
		self.protocol_floatlayout.remove_widget(self.feedback_label)
		self.feedback_label.text = ''
		
		self.protocol_floatlayout.add_object_event('Remove', 'Text', 'Stage', 'Results')

		if self.current_block != 1:
			self.protocol_floatlayout.remove_widget(self.reward_image)

		self.block_start_time = time.time()

		self.hold_button.unbind(on_press=self.start_block)
		self.hold_button.bind(on_press=self.iti_start)

		self.hold_button.bind(on_release=self.premature_response)

		if self.hold_button_pressed:
			self.iti_start()


	# Block Contingency Function
	
	def block_contingency(self, *args):
		
		try:			
			self.hold_button.unbind(on_press=self.iti_start)
			self.hold_button.unbind(on_release=self.premature_response)
			Clock.unschedule(self.iti_end)
			Clock.unschedule(self.remove_feedback)
			self.remove_feedback()

			self.protocol_floatlayout.clear_widgets()

			if self.current_block == -1:
				self.current_block = 1
			
			if self.response_level > self.response_level_end:
				self.session_event.cancel()
				self.results_screen()

				return
			
			else:

				if self.current_block == 1:
					self.feedback_label.text = 'Press and hold the white button to start the first \ntrial, or press "End Task" to end the task.'

					self.hold_button.bind(on_press=self.start_block)
					
					self.protocol_floatlayout.add_widget(self.quit_button)
					self.protocol_floatlayout.add_widget(self.feedback_label)

					self.protocol_floatlayout.add_object_event('Display', 'Text', 'Stage', 'Start')
					
				else:
					self.feedback_label.text = 'Block complete!\n\nPress and hold the white button to start the next \ntrial, or press "End Task" to end the task.'

					self.hold_button.bind(on_press=self.start_block)
					
					self.protocol_floatlayout.add_widget(self.reward_image)
					self.protocol_floatlayout.add_widget(self.feedback_label)
					self.protocol_floatlayout.add_widget(self.quit_button)

					self.protocol_floatlayout.add_object_event('Display', 'Text', 'Stage', 'Start')
					
			# Set ITI

			if len(self.iti_range) > 1:
				
				if self.iti_fixed_or_range == 'fixed':
					self.iti_length = random.choice(self.iti_range)
				
				else:
					self.iti_length = round(random.uniform(min(self.iti_range), max(self.iti_range)), 2)
				
				self.protocol_floatlayout.add_variable_event('Parameter', 'Current ITI', self.iti_length)

			self.stimulus_pos = self.generate_stimulus_pos()

			self.stimulus_button.pos_hint = self.stimulus_pos
			self.stimulus_button_pressed.pos_hint = self.stimulus_button.pos_hint
					
			self.protocol_floatlayout.add_variable_event('Parameter', 'Target Location', self.stimulus_button.pos_hint)

			self.current_block_trial = 1		

			Clock.schedule_once(self.block_screen_display_hold_button, self.block_min_rest_duration)

		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()