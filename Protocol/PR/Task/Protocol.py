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
			, 'response_level_start'
			, 'response_level_end'
			, 'grid_squares_x'
			, 'grid_squares_y'
			, 'min_separation'
			, 'use_confirmation'
			]
		
		
		# Define Variables - Config Import
		
		self.config_path = str(pathlib.Path('Protocol', self.protocol_name, 'Configuration.ini'))
		self.config_file = configparser.ConfigParser()
		self.config_file.read(self.config_path)

		self.debug_mode = False

		if ('DebugParameters' in self.config_file) \
			and (int(self.config_file['DebugParameters']['debug_mode']) == 1):

			self.parameters_dict = self.config_file['DebugParameters']
			self.debug_mode = True

		else:
			self.parameters_dict = self.config_file['TaskParameters']
			self.debug_mode = False



	def _load_config_parameters(self, parameters_dict):
		self.parameters_dict = parameters_dict
		self.participant_id = self.parameters_dict['participant_id']
		self.language = self.parameters_dict['language']
		self.skip_tutorial_video = int(self.parameters_dict['skip_tutorial_video'])
		self.tutorial_video_duration = float(self.parameters_dict['tutorial_video_duration'])

		self.block_change_on_duration = int(self.parameters_dict['block_change_on_duration_only'])
		
		self.iti_fixed_or_range = self.parameters_dict['iti_fixed_or_range']
		
		self.iti_import = self.parameters_dict['iti_length']
		self.iti_import = self.iti_import.split(',')

		self.feedback_length = float(self.parameters_dict['feedback_length'])
		self.timeout_duration = int(self.parameters_dict['timeout_duration'])
		self.hold_button_delay = float(self.parameters_dict['hold_button_delay'])
		self.block_duration = int(self.parameters_dict['block_duration'])
		self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
		self.session_duration = float(self.parameters_dict['session_duration'])
		
		self.block_multiplier = int(self.parameters_dict['block_multiplier'])

		self.background_grid_image = self.parameters_dict['background_grid_image']
		self.stimulus_image = self.parameters_dict['stimulus_image']
		self.stimulus_pressed_image = self.parameters_dict['stimulus_pressed_image']
		
		self.response_level = int(self.parameters_dict['response_level_start'])
		self.response_level_end = int(self.parameters_dict['response_level_end'])

		self.grid_squares_x = int(self.parameters_dict['grid_squares_x'])
		self.grid_squares_y = int(self.parameters_dict['grid_squares_y'])
		
		self.min_separation = int(self.parameters_dict['min_separation'])
		
		self.use_confirmation = int(self.parameters_dict['use_confirmation'])

		self.hold_image = self.config_file['Hold']['hold_image']
		self.mask_image = self.config_file['Mask']['mask_image']

	def _load_task_variables(self):
		# Define Variables - Count

		self.hit_target = 2 ** self.response_level
		self.total_hit_count = 0
		self.response_count_list = list()


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

	def _setup_session_stages(self):
		self.target_x_pos = random.randint(0, self.grid_squares_x - 1)
		self.target_y_pos = random.randint(1, self.grid_squares_y - 1)

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

		self.image_folder = pathlib.Path('Protocol', self.protocol_name, 'Image')

		self.background_grid_image_path = str(self.image_folder / str(self.background_grid_image + '.png'))
		self.stimulus_image_path = str(self.image_folder / str(self.stimulus_image + '.png'))
		self.stimulus_pressed_image_path = str(self.image_folder / str(self.stimulus_pressed_image + '.png'))
		self.hold_image_path = str(self.image_folder / str(self.hold_image + '.png'))
		self.mask_image_path = str(self.image_folder / str(self.mask_image + '.png'))
		self.checkmark_image_path = str(self.image_folder / 'checkmark.png')

		self.hold_button.unbind(on_release=self.hold_remind)
		self.hold_button.bind(on_release=self.premature_response)

		self.target_x_pos = 0
		self.target_y_pos = 1

		self.cell_proportion = 0.07
		self.cell_size = ((self.cell_proportion * self.width_adjust), (self.cell_proportion * self.height_adjust))

		min_y_pos = float(self.hold_button.pos_hint['center_y'] + (self.hold_button.size_hint[1]/2) + (self.cell_size[1]/2) + 0.005)

		self.x_boundaries = [(0.005 + (self.cell_size[0]/2)), (0.995 - (self.cell_size[0]/2))]
		self.y_boundaries = [min_y_pos, (0.995 - (self.cell_size[1]/2))]

		self.x_dim_hint = np.linspace(self.x_boundaries[0], self.x_boundaries[1], self.grid_squares_x).tolist()
		self.y_dim_hint = np.linspace(self.y_boundaries[0], self.y_boundaries[1], self.grid_squares_y).tolist()
		self.background_grid_list = [ImageButton() for square in range((self.grid_squares_x * self.grid_squares_y))]

		x_pos = 0
		y_pos = 0

		for cell in self.background_grid_list:
			cell.fit_mode = 'fill'
			cell.size_hint = (self.cell_proportion * self.width_adjust, self.cell_proportion * self.height_adjust)

			if x_pos >= self.grid_squares_x:
				x_pos = 0
				y_pos = y_pos + 1

			cell.pos_hint = {"center_x": self.x_dim_hint[x_pos], "center_y": self.y_dim_hint[y_pos]}
			cell.source = self.background_grid_image_path
			x_pos = x_pos + 1

		self.stimulus_button = ImageButton(source=self.stimulus_image_path)

		self.stimulus_button.pos_hint = {
			"center_x": self.x_dim_hint[self.target_x_pos]
			, "center_y": self.y_dim_hint[self.target_y_pos]
			}
		
		self.stimulus_button.size_hint = (self.cell_proportion * self.width_adjust, self.cell_proportion * self.height_adjust)
		self.stimulus_button.bind(on_press=self.target_pressed)

		self.stimulus_pressed_button = ImageButton(source=self.stimulus_pressed_image_path)

		self.stimulus_pressed_button.pos_hint = {
			"center_x": self.x_dim_hint[self.target_x_pos]
			, "center_y": self.y_dim_hint[self.target_y_pos]
			}
		
		self.stimulus_pressed_button.size_hint = (self.cell_proportion * self.width_adjust, self.cell_proportion * self.height_adjust)

		self.reward_image = Image(source=self.checkmark_image_path)
		self.reward_image.pos_hint = {"center_x": 0.5, "center_y": 0.8}
		self.reward_image.size_hint = (1 * self.width_adjust, 1 * self.height_adjust)

		total_image_list = [
			self.stimulus_image_path
			, self.stimulus_pressed_image_path
			, self.background_grid_image_path
			, self.hold_image_path
			, self.mask_image_path
			, self.checkmark_image_path
			]
		
		self.hold_button.source = self.hold_image_path

		self.x_dim_hint = np.linspace(self.x_boundaries[0], self.x_boundaries[1], self.grid_squares_x).tolist()
		self.y_dim_hint = np.linspace(self.y_boundaries[0], self.y_boundaries[1], self.grid_squares_y).tolist()
	
	def _setup_language_localization(self):
		self.set_language(self.language)
		self.feedback_dict = {}

		self.feedback_label = Label(font_size='32sp')
		self.feedback_label.size_hint = (0.8, 0.4)
		self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.55}
		self.feedback_label.text = ''


	def _load_video_and_instruction_components(self):
		self.lang_folder_path = pathlib.Path('Protocol', self.protocol_name, 'Language', self.language)

		if (self.lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_path = str(list((self.lang_folder_path / 'Tutorial_Video').glob('*.mp4'))[0])
			self.tutorial_video = Video(source = self.tutorial_video_path)
			self.tutorial_video.pos_hint = {'center_x': 0.5, 'center_y': 0.6}
			self.tutorial_video.size_hint = (1, 1)

		self.tutorial_restart = Button(text='RESTART VIDEO', font_size='48sp')
		self.tutorial_restart.size_hint = self.text_button_size
		self.tutorial_restart.pos_hint = self.text_button_pos_LL
		self.tutorial_restart.bind(on_press=self.start_tutorial_video)

		self.tutorial_start_button = Button(text='START TASK', font_size='48sp')
		self.tutorial_start_button.size_hint = self.text_button_size
		self.tutorial_start_button.pos_hint = self.text_button_pos_LR
		self.tutorial_start_button.bind(on_press=self.start_protocol_from_tutorial)
		
		self.tutorial_video_button = Button(text='TAP THE SCREEN\nTO START VIDEO', font_size='48sp', halign='center', valign='center')
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
			and (self.skip_tutorial_video == 0):

			self.protocol_floatlayout.clear_widgets()
			self.present_tutorial_video()
		
		else:
			self.present_instructions()



	def present_tutorial_video(self, *args):

		self.protocol_floatlayout.clear_widgets()
			
		self.protocol_floatlayout.add_stage_event('State Change')
		self.protocol_floatlayout.add_object_event('Display', 'Object', 'Tutorial Video', 'Start')
		self.protocol_floatlayout.add_widget(self.tutorial_video)
		self.protocol_floatlayout.add_widget(self.tutorial_video_button)

		self.tutorial_video.state = 'stop'
	


	def start_tutorial_video(self, *args):

		self.tutorial_video.state = 'play'
		self.protocol_floatlayout.remove_widget(self.tutorial_video_button)
		
		Clock.schedule_once(self.present_tutorial_video_start_button, self.tutorial_video_duration)

		self.protocol_floatlayout.add_object_event('Display', 'Video', 'Section', 'Instructions')


	def present_tutorial_video_start_button(self, *args):
		self.protocol_floatlayout.add_widget(self.tutorial_start_button)
		self.protocol_floatlayout.add_widget(self.tutorial_restart)
				
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Section', 'Instructions', image_name='Section Start')
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Section', 'Instructions', image_name='Video Restart')
	
	
	
	def start_protocol_from_tutorial(self, *args):
		self.tutorial_video.state = 'stop'

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_object_event('Remove', 'Video', 'Section', 'Instructions')

		self.protocol_floatlayout.add_stage_event('Section Start')
		self.generate_output_files()
		self.metadata_output_generation()

		self.start_clock()

		self.block_contingency()


	def results_screen(self, *args):
			self.protocol_floatlayout.clear_widgets()
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
			and self.use_confirmation == 1:

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
			and self.use_confirmation == 1:

			self.hold_button.unbind(on_press=self.target_pressed)
			self.protocol_floatlayout.remove_widget(self.hold_button)
			self.protocol_floatlayout.remove_widget(self.stimulus_pressed_button)

			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Target', 'Hold Button')
		else:
			self.protocol_floatlayout.remove_widget(self.stimulus_button)
			self.protocol_floatlayout.add_widget(self.stimulus_pressed_button)

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
			, self.target_x_pos
			, self.target_y_pos
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
					and self.use_confirmation == 1:

					# Confirmation button trial
					pass


				else:
					new_x_pos = random.randint(0, self.grid_squares_x - 1)
					new_y_pos = random.randint(1, self.grid_squares_y - 1)

					while (
						abs(new_x_pos - self.target_x_pos) \
						+ abs(new_y_pos - self.target_y_pos)
						) <= self.min_separation:

						new_x_pos = random.randint(0, self.grid_squares_x - 1)
						new_y_pos = random.randint(1, self.grid_squares_y - 1)

					self.target_x_pos = new_x_pos
					self.target_y_pos = new_y_pos
					
					self.stimulus_button.pos_hint = {
						'center_x': self.x_dim_hint[self.target_x_pos]
						, 'center_y': self.y_dim_hint[self.target_y_pos]
						}
					
					self.stimulus_pressed_button.pos_hint = {
						'center_x': self.x_dim_hint[self.target_x_pos]
						, 'center_y': self.y_dim_hint[self.target_y_pos]
						}

					self.protocol_floatlayout.add_variable_event('Parameter', 'Target Location', self.stimulus_button.pos_hint)
				self.stimulus_presentation()
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()
	


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

		for grid_square in self.background_grid_list:
			self.protocol_floatlayout.add_widget(grid_square)

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
					
					self.protocol_floatlayout.add_widget(self.hold_button)
				
				else:
					self.feedback_label.text = 'Block complete!\n\nPress and hold the white button to start the next \ntrial, or press "End Task" to end the task.'

					self.hold_button.bind(on_press=self.start_block)
					
					self.protocol_floatlayout.add_widget(self.reward_image)
					self.protocol_floatlayout.add_widget(self.feedback_label)
					self.protocol_floatlayout.add_widget(self.quit_button)

					self.protocol_floatlayout.add_object_event('Display', 'Text', 'Stage', 'Start')
					
					self.protocol_floatlayout.add_widget(self.hold_button)
			
			# Set ITI

			if len(self.iti_range) > 1:
				
				if self.iti_fixed_or_range == 'fixed':
					self.iti_length = random.choice(self.iti_range)
				
				else:
					self.iti_length = round(random.uniform(min(self.iti_range), max(self.iti_range)), 2)
				
				self.protocol_floatlayout.add_variable_event('Parameter', 'Current ITI', self.iti_length)

			self.target_x_pos = random.randint(0, self.grid_squares_x - 1)
			self.target_y_pos = random.randint(1, self.grid_squares_y - 1)

			self.stimulus_button.pos_hint = {
				'center_x': self.x_dim_hint[self.target_x_pos]
				, 'center_y': self.y_dim_hint[self.target_y_pos]
				}
					
			self.stimulus_pressed_button.pos_hint = {
				'center_x': self.x_dim_hint[self.target_x_pos]
				, 'center_y': self.y_dim_hint[self.target_y_pos]
				}

			self.protocol_floatlayout.add_variable_event('Parameter', 'Target Location', self.stimulus_button.pos_hint)

			self.current_block_trial = 1		

		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()