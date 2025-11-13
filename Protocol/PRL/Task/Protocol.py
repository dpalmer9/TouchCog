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
from kivy.uix.label import Label
from kivy.uix.video import Video


class ProtocolScreen(ProtocolBase):

	def __init__(self, **kwargs):

		super(ProtocolScreen, self).__init__(**kwargs)
		self.protocol_name = 'PRL'
		self.name = self.protocol_name + '_protocolscreen'
		self.update_task()
		# Define Data Columns
		
		self.data_cols = [
			'TrialNo'
			, 'Stage'
			, 'ReversalNo'
			, 'TargetImage'
			, 'TargetLoc'
			, 'NontargetImage'
			, 'NontargetLoc'
			, 'TargetReward'
			, 'NontargetReward'
			, 'SideChosen'
			, 'Correct'
			, 'Rewarded'
			, 'ResponseLat'
			]

		self.metadata_cols = [
			'participant_id'
			, 'skip_tutorial_video'
			, 'tutorial_video_duration'
			, 'block_change_on_duration_only'
			, 'training_task'
			, 'iti_fixed_or_range'
			, 'iti_length'
			, 'feedback_length'
			, 'block_duration'
			, 'block_min_rest_duration'
			, 'session_duration'
			, 'block_multiplier'
			, 'block_trial_max'
			, 'target_reward_probability'
			, 'reversal_threshold'
			, 'max_reversals'
			, 'image_set'
			, 'training_target_image'
			, 'training_nontarget_image'
			, 'training_block_max_correct'
			]
		
		
		# Define Variables - Config Import
		
		self.config_path = str(pathlib.Path('Protocol', self.protocol_name, 'Configuration.ini'))
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

		self.participant_id = self.parameters_dict['participant_id']

		self.skip_tutorial_video = self.parameters_dict['skip_tutorial_video']
		self.tutorial_video_duration = float(self.parameters_dict['tutorial_video_duration'])

		self.block_change_on_duration = self.parameters_dict['block_change_on_duration_only']

		self.iti_fixed_or_range = self.parameters_dict['iti_fixed_or_range']
		
		self.iti_import = self.parameters_dict['iti_length']
		self.iti_import = self.iti_import.split(',')
		
		self.feedback_length = float(self.parameters_dict['feedback_length'])
		self.block_duration = int(self.parameters_dict['block_duration'])
		self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
		self.session_duration = float(self.parameters_dict['session_duration'])
		
		self.block_multiplier = int(self.parameters_dict['block_multiplier'])
		self.block_trial_max = int(self.parameters_dict['block_trial_max'])
		
		self.target_reward_probability = float(self.parameters_dict['target_reward_probability'])
		self.reversal_threshold = int(self.parameters_dict['reversal_threshold'])
		self.max_reversals = int(self.parameters_dict['max_reversals'])

		self.image_set = self.parameters_dict['image_set']

		self.training_target_image = self.parameters_dict['training_target_image']
		self.training_nontarget_image = self.parameters_dict['training_nontarget_image']
		
		self.training_block_max_correct = int(self.parameters_dict['training_block_max_correct'])

		self.hold_image = self.config_file['Hold']['hold_image']
		self.mask_image = self.config_file['Mask']['mask_image']

		# Define Variables - List

		self.stage_list = list()

		if self.parameters_dict['training_task']:
			self.stage_list.append('Training')

		self.stage_list.append('Test')

	def _load_task_variables(self):
		# Define Paths

		self.language_dir_path = pathlib.Path('Protocol', self.protocol_name, 'Language', self.language)
		self.image_dir_path = pathlib.Path('Protocol', self.protocol_name, 'Image')

		# Define Variables - Time

		self.start_stimulus = 0.0
		self.response_latency = 0.0
		self.trial_end_time = 0.0

		self.iti_range = [float(iNum) for iNum in self.iti_import]
		self.iti_length = self.iti_range[0]


		# Define Variables - Count

		self.current_hits = 0
		self.current_reversal = 0
		self.point_counter = 0

		self.current_block = -1
		self.current_block_trial = 0

		self.stage_index = -1

		image_index_choice = [0, 1]
		self.image_index_choice = self.constrained_shuffle(image_index_choice)

		self.target_image_index = image_index_choice[0]
		self.nontarget_image_index = image_index_choice[1]


		# Define Boolean

		self.target_rewarded = True
		self.nontarget_rewarded = False
		self.choice_rewarded = True


		# Define Variables - String

		self.target_image = self.training_target_image
		self.nontarget_image = self.training_nontarget_image
		self.current_stage = self.stage_list[self.stage_index]
		self.side_chosen = ''

		# Define Variables - String

		self.target_loc_list = ['Left', 'Right']
		self.target_loc_list = self.constrained_shuffle(self.target_loc_list)

		self.target_loc_index = 0
		self.nontarget_loc_index = 1

		self.target_loc = self.target_loc_list[self.target_loc_index]
		self.nontarget_loc = self.target_loc_list[self.nontarget_loc_index]

	def _setup_session_stages(self):
		self.nontarget_reward_probability = round(1 - self.target_reward_probability, 2)

		self.trial_reward_list = list()
		self.trial_reward_list_index = -1

		for iTrial in range(int(self.target_reward_probability * 50)):
			self.trial_reward_list.append('Target')
		

		for iTrial in range(int(self.nontarget_reward_probability * 50)):
			self.trial_reward_list.append('Nonarget')
		
		self.trial_reward_list = self.constrained_shuffle(self.trial_reward_list)

	def _setup_image_widgets(self):
		# Define Widgets - Images

		self.stimulus_path_list = list(self.image_dir_path.glob(str(pathlib.Path('Targets', self.image_set, '*.png'))))
		self.target_image_list = list()

		for filename in self.stimulus_path_list:
			self.target_image_list.append(filename.stem)
		
		self.total_image_list = self.stimulus_path_list

		self.hold_image_path = str(self.image_dir_path / (self.hold_image + '.png'))
		self.mask_image_path = str(self.image_dir_path / (self.mask_image + '.png'))

		self.hold_button.unbind(on_release=self.hold_remind)
		self.hold_button.bind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.iti_start)

		self.training_target_image_path = str(self.image_dir_path / (self.training_target_image + '.png'))
		self.training_nontarget_image_path = str(self.image_dir_path / (self.training_nontarget_image + '.png'))

		self.total_image_list += [self.hold_image_path, self.mask_image_path, self.training_target_image_path, self.training_nontarget_image_path]

		# print('\n\nTotal image list: ', self.total_image_list, '\n\n')

		self.load_images(self.total_image_list)

		if len(self.target_image_list) == 1:
			self.stimulus_image_source = str(self.stimulus_path_list[0])
		
		else:
			self.stimulus_image_source = self.mask_image_path		

		self.hold_button.source = self.hold_image_path

		self.text_button_size = [0.4, 0.15]
		self.text_button_pos_LL = {"center_x": 0.25, "center_y": 0.08}
		self.text_button_pos_LR = {"center_x": 0.75, "center_y": 0.08}

		self.stimulus_size = (0.4 * self.width_adjust, 0.4 * self.height_adjust)
		self.stimulus_pos_l = {'center_x': 0.25, 'center_y': 0.55}
		self.stimulus_pos_r = {'center_x': 0.75, 'center_y': 0.55}

		self.left_stimulus = ImageButton(source=self.stimulus_image_source)
		self.left_stimulus.size_hint = self.stimulus_size
		self.left_stimulus.pos_hint = self.stimulus_pos_l
		self.left_stimulus.bind(on_press=self.left_pressed)

		self.right_stimulus = ImageButton(source=self.stimulus_image_source)
		self.right_stimulus.size_hint = self.stimulus_size
		self.right_stimulus.pos_hint = self.stimulus_pos_r
		self.right_stimulus.bind(on_press=self.right_pressed)

		self.instruction_button = Button(font_size='60sp')
		self.instruction_button.size_hint = self.text_button_size
		self.instruction_button.pos_hint =  {"center_x": 0.5, "center_y": 0.9}
		self.instruction_button.bind(on_press=self.section_start)

	def _setup_language_localization(self):
		self.set_language(self.language)

	def _load_video_and_instruction_components(self):
		# Tutorial Import

		self.lang_folder_path = pathlib.Path('Protocol', self.protocol_name, 'Language', self.language)

		feedback_lang_path = self.lang_folder_path / 'Feedback.ini'
		feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
		feedback_lang_config.read(feedback_lang_path, encoding='utf-8')

		points_awarded_feedback_string = '[color=%s]' \
			% feedback_lang_config['Stimulus']['points_awarded_colour'] \
			+ feedback_lang_config['Stimulus']['points_awarded'] \
			+ '[/color]'
		
		self.feedback_dict['points_awarded'] = points_awarded_feedback_string

		if (self.lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_path = str(list((self.lang_folder_path / 'Tutorial_Video').glob('*.mp4'))[0])
			self.tutorial_video = Video(
				source = self.tutorial_video_path
				, pos_hint = {'center_x': 0.5, 'center_y': 0.5 + self.text_button_size[1]}
				, fit_mode = 'contain'
				)


		# Define Widgets - Instructions
		
		self.instruction_path = str(self.language_dir_path / 'Instructions.ini')
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Main'] = {}
		
		self.instruction_dict['Main']['train'] = self.instruction_config['Main']['train']
		self.instruction_dict['Main']['task'] = self.instruction_config['Main']['task']

		self.score_string = 'Your Points:\n%s' % (0)
		self.score_label = Label(text=self.score_string, font_size='50sp', markup=True, halign='center')
		self.score_label.size_hint = (0.8, 0.2)
		self.score_label.pos_hint = {'center_x': 0.5, 'center_y': 0.9}

	def load_parameters(self,parameter_dict):
		self._load_config_parameters(parameter_dict)
		self._load_task_variables()
		self._setup_session_stages()
		self._setup_image_widgets()
		self._setup_language_localization()
		self._load_video_and_instruction_components()
		
		
		# Begin Task
		self.start_clock()
		if (self.lang_folder_path / 'Tutorial_Video').is_dir() \
			and not self.skip_tutorial_video:

			self.protocol_floatlayout.clear_widgets()
			self.present_tutorial_video()
		
		else:
			self.present_instructions()
			self.start_button.unbind(on_press=self.start_protocol)
			self.start_button.bind(on_press=self.start_protocol_from_tutorial)



	def present_tutorial_video(self, *args):

		self.protocol_floatlayout.clear_widgets()

		self.tutorial_restart_button = Button(text='Restart Video', font_size='48sp')
		self.tutorial_restart_button.size_hint = self.text_button_size
		self.tutorial_restart_button.pos_hint = self.text_button_pos_LL
		self.tutorial_restart_button.bind(on_press=self.tutorial_restart)
		
		self.tutorial_start_button = Button(text='Start Task', font_size='48sp')
		self.tutorial_start_button.size_hint = self.text_button_size
		self.tutorial_start_button.pos_hint = self.text_button_pos_LR
		self.tutorial_start_button.bind(on_press=self.stop_tutorial_video)
		
		self.tutorial_video_button = Button(text='Tap the screen\nto start video', font_size='48sp', halign='center', valign='center')
		self.tutorial_video_button.background_color = 'black'
		self.tutorial_video_button.size_hint = (1, 1)
		self.tutorial_video_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
		self.tutorial_video_button.bind(on_press=self.start_tutorial_video)
		
		self.protocol_floatlayout.add_stage_event('Object Display')

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
		self.protocol_floatlayout.add_widget(self.tutorial_restart_button)
				
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Section', 'Instructions', 'Section Start')
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Section', 'Instructions', 'Video Restart')
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

		self.protocol_floatlayout.add_object_event('Remove', 'Video', 'Section', 'Instructions')

		self.protocol_floatlayout.add_stage_event('Section Start')

		self.generate_output_files()
		self.metadata_output_generation()
		self.block_contingency()


	def section_start(self, *args):

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_stage_event('Section Start')
		self.protocol_floatlayout.add_object_event('Display', 'Text', 'Section', 'Instructions', 'Section Start')
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Section', 'Instructions', 'Continue')
		
		self.block_end()
	


	def final_results_screen(self, *args):

		self.end_protocol_button = Button(font_size='60sp')
		self.end_protocol_button.size_hint = [0.4, 0.15]
		self.end_protocol_button.pos_hint =  {"center_x": 0.50, "center_y": 0.1}
		self.end_protocol_button.text = 'End Task'
		self.end_protocol_button.bind(on_press=self.protocol_end)

		self.result_label_str = 'Great job! You have earned ' + str(self.point_counter) + ' points!'
		self.result_label = Label(text=self.result_label_str, font_size='50sp', markup=True, halign='center')
		self.result_label.size_hint = (0.8, 0.3)
		self.result_label.pos_hint = {'center_x': 0.5, 'center_y': 0.6}

		self.protocol_floatlayout.add_widget(self.result_label)
		self.protocol_floatlayout.add_widget(self.end_protocol_button)
		
		self.protocol_floatlayout.add_object_event('Display', 'Text', 'Stage', 'Results')
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Stage', 'End Protocol')
		self.protocol_floatlayout.add_stage_event('Task End')



	def stimulus_presentation(self, *args): # Stimulus presentation
		self.hold_button.unbind(on_release=self.premature_response)

		self.protocol_floatlayout.remove_widget(self.hold_button)
		self.protocol_floatlayout.add_widget(self.left_stimulus)
		self.protocol_floatlayout.add_widget(self.right_stimulus)
		
		self.stimulus_start_time = time.perf_counter()
		
		self.protocol_floatlayout.add_stage_event('Object Display')
		
		self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Target', self.target_loc, self.target_image)
		self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Nontarget', self.nontarget_loc, self.nontarget_image)
		


	# Hold released too early
	
	def premature_response(self, *args):
		
		if self.stimulus_on_screen is True:
			pass
		
		Clock.unschedule(self.iti_end)
		Clock.unschedule(self.remove_feedback)
		self.remove_feedback()
		
		self.protocol_floatlayout.clear_widgets()
		
		self.response_latency = np.nan
		
		self.protocol_floatlayout.add_stage_event('Premature Response')
		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)
		
		self.iti_active = False
		self.feedback_label.text = self.feedback_dict['wait']

		if self.feedback_on_screen is False:	
			self.protocol_floatlayout.add_widget(self.feedback_label)
			self.feedback_on_screen = True
			self.feedback_start_time = time.perf_counter()

			self.protocol_floatlayout.add_event([
				(self.feedback_start_time - self.start_time)
				, 'Object Display'
				, 'Text'
				, 'Feedback'
				, self.feedback_label.text
				])
		
		self.hold_button.unbind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.iti_start)
	
		self.protocol_floatlayout.add_widget(self.hold_button)
	
	
	
	# Left Stimulus Pressed
	
	def left_pressed(self, *args):

		self.stimulus_press_time = time.perf_counter()
		self.side_chosen = 'Left'
		self.protocol_floatlayout.add_stage_event('Left Stimulus Pressed')
		self.trial_outcomes()
	
	
	
	# Right Stimulus Pressed
	
	def right_pressed(self, *args):

		self.stimulus_press_time = time.perf_counter()
		self.side_chosen = 'Right'
		self.protocol_floatlayout.add_stage_event('Right Stimulus Pressed')
		self.trial_outcomes()



	def trial_outcomes(self, *args):

		if self.side_chosen == self.target_loc:
			self.last_response = 1
			self.current_hits += 1
			self.protocol_floatlayout.add_stage_event('Target Pressed')
			
			if self.target_rewarded:
				self.choice_rewarded = True
			
			else:
				self.choice_rewarded = False

		elif self.side_chosen == self.nontarget_loc:
			self.last_response = 0
			self.current_hits = 0
			self.protocol_floatlayout.add_stage_event('Nontarget Pressed')
			
			if not self.target_rewarded:
				self.choice_rewarded = True
			
			else:
				self.choice_rewarded = False
		

		if self.choice_rewarded:

			self.protocol_floatlayout.add_stage_event('Choice Rewarded')

			if self.current_stage == 'Training':
				self.feedback_label.text = self.feedback_dict['correct']

			else:
				self.feedback_label.text = self.feedback_dict['points_awarded']
				self.point_counter += 10

				self.protocol_floatlayout.add_stage_event('Points Collected')
				self.protocol_floatlayout.add_variable_event('Outcome', 'Points', self.response_latency)
		
		else:
			self.feedback_label.text = ''
			self.protocol_floatlayout.add_stage_event('Choice Not Rewarded')

		self.protocol_floatlayout.add_variable_event('Outcome', 'Side Chosen', self.side_chosen)
		self.protocol_floatlayout.add_variable_event('Outcome', 'Last Response', self.last_response)
		self.protocol_floatlayout.add_variable_event('Outcome', 'Current Hits', self.current_hits)
		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)

		self.protocol_floatlayout.remove_widget(self.left_stimulus)
		self.protocol_floatlayout.remove_widget(self.right_stimulus)

		self.protocol_floatlayout.add_object_event('Remove', 'Image', 'Target', 'Location', self.target_loc)
		self.protocol_floatlayout.add_object_event('Remove', 'Image', 'Nontarget', 'Location', self.nontarget_loc)

		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.bind(on_release=self.premature_response)

		if self.feedback_label.text != '' \
			and not self.feedback_on_screen:
			self.protocol_floatlayout.add_widget(self.feedback_label)
			self.feedback_on_screen = True
			Clock.schedule_once(self.remove_feedback, self.feedback_length)
			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback', self.feedback_label.text)
		
		self.protocol_floatlayout.add_widget(self.hold_button)
		
		self.write_trial()
		
		self.trial_contingency()
	
	
	
	# Data Saving Function
	
	def write_trial(self):
		trial_data = [
			self.current_trial
			, self.current_stage
			, self.current_reversal
			, self.target_image
			, self.target_loc
			, self.nontarget_image
			, self.nontarget_loc
			, self.target_rewarded
			, self.nontarget_rewarded
			, self.side_chosen
			, self.last_response
			, self.choice_rewarded
			, self.response_latency
			]
		
		self.write_summary_file(trial_data)
	
	
	
	# Trial Contingency Functions
	
	def trial_contingency(self, *args):
		
		try:
			if self.current_block_trial != 0:
				self.response_tracking.append(self.last_response)

				# Check if block ended

				if (time.perf_counter() - self.block_start >= self.block_duration) \
					or (self.current_block_trial >= self.block_trial_max):
					
					self.block_contingency()

				elif (self.current_stage == 'Training') \
					and (sum(self.response_tracking) >= self.training_block_max_correct):
					
					self.block_contingency()

			# Set next trial parameters
			
			self.side_chosen = ''
			self.choice_rewarded = False
			self.last_response = 0

			self.current_trial += 1
			self.current_block_trial += 1
			
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Trial', str(self.current_trial))
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Block Trial', str(self.current_block_trial))
			
			# Set ITI

			if len(self.iti_range) > 1:
				
				if self.iti_fixed_or_range == 'fixed':
					self.iti_length = random.choice(self.iti_range)
				
				else:
					self.iti_length = round(random.uniform(min(self.iti_range), max(self.iti_range)), 2)
				
				self.protocol_floatlayout.add_variable_event('Parameter', 'Current ITI', self.iti_length)


			if self.current_hits >= self.reversal_threshold:
				self.current_hits = 0
				self.current_reversal += 1

				if self.current_reversal > self.max_reversals:
					self.block_contingency()

				else:
					self.target_loc_index += 1
					self.nontarget_loc_index += 1

					if self.target_loc_index >= len(self.target_loc_list):
						self.target_loc_index = 0

					elif self.nontarget_loc_index >= len(self.target_loc_list):
						self.nontarget_loc_index = 0

					self.target_loc = self.target_loc_list[self.target_loc_index]
					self.nontarget_loc = self.target_loc_list[self.nontarget_loc_index]

			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Reversal', self.current_reversal)
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Hits', self.current_hits)
			self.protocol_floatlayout.add_variable_event('Parameter', 'Target Location', self.target_loc)
			self.protocol_floatlayout.add_variable_event('Parameter', 'Nontarget Location', self.nontarget_loc)

			if self.current_stage == 'Training':
				self.target_rewarded = True
				self.nontarget_rewarded = False
			
			else:
				self.trial_reward_list_index += 1

				if (self.trial_reward_list_index >= len(self.trial_reward_list)):
					self.trial_reward_list = self.constrained_shuffle(self.trial_reward_list)
					self.trial_reward_list_index = 0

				self.protocol_floatlayout.add_variable_event('Parameter', 'Rewarded Side', self.trial_reward_list[self.trial_reward_list_index])

				if self.trial_reward_list[self.trial_reward_list_index] == 'Target':
					self.target_rewarded = True
					self.nontarget_rewarded = False
				
				else:
					self.target_rewarded = False
					self.nontarget_rewarded = True

			self.trial_end_time = time.perf_counter()
		
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()

	
	# Block Contingency Function
	
	def block_contingency(self, *args):
		
		try:

			Clock.unschedule(self.iti_end)
			self.hold_button.unbind(on_press=self.iti_start)
			self.hold_button.unbind(on_release=self.premature_response)

			self.block_started = True

			Clock.unschedule(self.remove_feedback)
			self.remove_feedback()

			self.protocol_floatlayout.clear_widgets()

			self.current_block += 1

			self.protocol_floatlayout.add_stage_event('Block Change')
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Block', self.current_block)
			
			if (self.current_block > self.block_multiplier) \
				or (self.current_block == 0):

				self.stage_index += 1
				self.current_block = 1
			
	
			if self.stage_index >= len(self.stage_list): # Check if all stages complete
				self.session_event.cancel()
				self.final_results_screen()
				return
			
			else:
				self.current_stage = self.stage_list[self.stage_index]
		
				self.protocol_floatlayout.add_stage_event('Stage Change')
				self.protocol_floatlayout.add_variable_event('Parameter', 'Current Stage', self.current_stage)

			# Set next block parameters

			self.response_tracking = list()
			self.last_response = 0
			self.contingency = 0
			self.trial_outcome = 0
			self.current_block_trial = 0

			if self.current_stage == 'Training':
				self.target_image = self.training_target_image
				self.nontarget_image = self.training_nontarget_image
			
			elif len(self.target_image_list) == 1:
				self.target_image = self.target_image_list[0]
				self.nontarget_image = self.target_image

				self.target_loc_index += 1
				self.nontarget_loc_index += 1

				if self.target_loc_index >= len(self.target_loc_list):
					self.target_loc_index = 0

				elif self.nontarget_loc_index >= len(self.target_loc_list):
					self.nontarget_loc_index = 0

				self.target_loc = self.target_loc_list[self.target_loc_index]
				self.nontarget_loc = self.target_loc_list[self.nontarget_loc_index]

			else:
				self.target_image_index += 1
				self.nontarget_image_index += 1

				if self.target_image_index >= len(self.target_image_list):
					self.target_image_index = 0

				elif self.nontarget_image_index >= len(self.target_image_list):
					self.nontarget_image_index = 0

				self.target_image = self.target_image_list[self.target_image_index]
				self.nontarget_image = self.target_image_list[self.nontarget_image_index]

				self.trial_reward_list = self.constrained_shuffle(self.trial_reward_list)
				self.trial_reward_list_index = 0
				
				if self.trial_reward_list[self.trial_reward_list_index] == 'Target':
					self.target_rewarded = True
					self.nontarget_rewarded = False
				
				else:
					self.target_rewarded = False
					self.nontarget_rewarded = True
			
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Reversal', self.current_reversal)
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Hits', self.current_hits)
			self.protocol_floatlayout.add_variable_event('Parameter', 'Target Location', self.target_loc)
			self.protocol_floatlayout.add_variable_event('Parameter', 'Nontarget Location', self.nontarget_loc)

			if self.current_block == 1:
				self.block_max_length = 360
				
				if self.current_stage == 'Training':
					self.block_max_length = self.training_block_max_correct
					self.instruction_label.text = self.instruction_dict['Main']['train']

				else:
					self.instruction_label.text = self.instruction_dict['Main']['task']

				self.instruction_button.text = 'Begin Section'

				self.protocol_floatlayout.add_widget(self.instruction_label)
				self.protocol_floatlayout.add_widget(self.instruction_button)
				
				self.protocol_floatlayout.add_object_event('Display', 'Text', 'Block', 'Instructions', 'Task')
				self.protocol_floatlayout.add_object_event('Display', 'Button', 'Block', 'Instructions', 'Continue')
			
			else:
				self.block_started = False
				self.block_screen()

			self.trial_contingency()
		
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()