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
		self.update_task()
		

		# Set screen size
		
		width = int(Config.get('graphics', 'width'))
		height = int(Config.get('graphics', 'height'))
		self.maxfps = int(Config.get('graphics', 'maxfps'))
		
		if self.maxfps == 0:
			self.maxfps = 120

		self.screen_resolution = (width, height)
		self.protocol_floatlayout.size = self.screen_resolution

		self.width_adjust = 1
		self.height_adjust = 1
		
		if width > height:
			self.width_adjust = height / width
		
		elif width < height:
			self.height_adjust = width / height
		

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
		
		config_path = str(pathlib.Path('Protocol', self.protocol_name, 'Configuration.ini'))
		config_file = configparser.ConfigParser()
		config_file.read(config_path)

		self.debug_mode = False

		if ('DebugParameters' in config_file) \
			and (int(config_file['DebugParameters']['debug_mode']) == 1):

			self.parameters_dict = config_file['DebugParameters']
			self.debug_mode = True

		else:
			self.parameters_dict = config_file['TaskParameters']
			self.debug_mode = False

		self.skip_tutorial_video = int(self.parameters_dict['skip_tutorial_video'])
		self.tutorial_video_duration = int(self.parameters_dict['tutorial_video_duration'])

		self.block_change_on_duration = int(self.parameters_dict['block_change_on_duration_only'])
		
		self.iti_fixed_or_range = self.parameters_dict['iti_fixed_or_range']
		
		iti_import = self.parameters_dict['iti_length']
		iti_import = iti_import.split(',')
		
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

		self.hold_image = config_file['Hold']['hold_image']
		self.mask_image = config_file['Mask']['mask_image']


		# Define Variables - List

		self.stage_list = list()

		if self.parameters_dict['training_task'] == 1:
			self.stage_list.append('Training')

		self.stage_list.append('Test')


		# Define Language

		self.language = 'English'
		self.set_language(self.language)


		# Define Paths

		self.language_dir_path = pathlib.Path('Protocol', self.protocol_name, 'Language', self.language)
		self.image_dir_path = pathlib.Path('Protocol', self.protocol_name, 'Image')


		# Define Clock
		
		self.block_check_clock = Clock
		self.block_check_clock.interupt_next_only = False
		self.block_check_event = self.block_check_clock.create_trigger(self.block_contingency, 0, interval=True)

		self.task_clock = Clock
		self.task_clock.interupt_next_only = False

		# Define Variables - Time

		self.start_stimulus = 0.0
		self.response_latency = 0.0
		self.trial_end_time = 0.0


		# Define Variables - Count

		self.current_hits = 0
		self.current_reversal = 0
		self.point_counter = 0

		self.target_image_index = 0
		self.nontarget_image_index = 1

		self.stage_index = 0


		# Define Boolean

		self.target_rewarded = True
		self.nontarget_rewarded = False
		self.choice_rewarded = True


		# Define Variables - String

		self.target_image = self.training_target_image
		self.nontarget_image = self.training_nontarget_image
		self.current_stage = self.stage_list[self.stage_index]
		self.side_chosen = ''


		# Define Widgets - Images

		self.stimulus_path_list = list(self.image_dir_path.glob(str(pathlib.Path('Targets', self.image_set, '*.png'))))
		stimulus_image_list = list()

		for filename in self.stimulus_path_list:
			stimulus_image_list.append(filename.stem)
		
		self.total_image_list = self.stimulus_path_list

		self.hold_image_path = str(self.image_dir_path / (self.hold_image + '.png'))
		self.mask_image_path = str(self.image_dir_path / (self.mask_image + '.png'))

		self.hold_button.unbind(on_release=self.hold_remind)
		self.hold_button.bind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.iti)

		self.stimulus_size = (0.4 * self.width_adjust, 0.4 * self.height_adjust)
		self.stimulus_pos_l = {'center_x': 0.25, 'center_y': 0.55}
		self.stimulus_pos_r = {'center_x': 0.75, 'center_y': 0.55}

		self.left_stimulus = ImageButton(source=self.mask_image_path)
		self.left_stimulus.size_hint = self.stimulus_size
		self.left_stimulus.pos_hint = self.stimulus_pos_l

		self.right_stimulus = ImageButton(source=self.mask_image_path)
		self.right_stimulus.size_hint = self.stimulus_size
		self.right_stimulus.pos_hint = self.stimulus_pos_r


		# Define Widgets - Text

		self.score_string = 'Your Points:\n%s' % (0)
		self.score_label = Label(text=self.score_string, font_size='50sp', markup=True, halign='center')
		self.score_label.size_hint = (0.8, 0.2)
		self.score_label.pos_hint = {'center_x': 0.5, 'center_y': 0.9}


		# Define Widgets - Instructions
		
		self.instruction_path = str(self.language_dir_path / 'Instructions.ini')
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Main'] = {}
		
		self.instruction_dict['Main']['train'] = self.instruction_config['Main']['train']
		self.instruction_dict['Main']['task'] = self.instruction_config['Main']['task']



	# Initialization Functions #
		
	def load_parameters(self,parameter_dict):

		self.parameters_dict = parameter_dict
		
		config_path = str(pathlib.Path('Protocol', self.protocol_name, 'Configuration.ini'))
		config_file = configparser.ConfigParser()
		config_file.read(config_path)

		self.language = self.parameters_dict['language']

		self.skip_tutorial_video = int(self.parameters_dict['skip_tutorial_video'])
		self.tutorial_video_duration = int(self.parameters_dict['tutorial_video_duration'])

		self.block_change_on_duration = int(self.parameters_dict['block_change_on_duration_only'])
		
		self.iti_fixed_or_range = self.parameters_dict['iti_fixed_or_range']
		
		iti_import = self.parameters_dict['iti_length']
		iti_import = iti_import.split(',')
		
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

		self.hold_image = config_file['Hold']['hold_image']
		self.mask_image = config_file['Mask']['mask_image']


		# Define Variables - List

		self.stage_list = list()

		if self.parameters_dict['training_task'] == 1:
			self.stage_list.append('Training')

		self.stage_list.append('Test')


		# Define Language

		self.language = 'English'
		self.set_language(self.language)


		# Define Paths

		self.language_dir_path = pathlib.Path('Protocol', self.protocol_name, 'Language', self.language)
		self.image_dir_path = pathlib.Path('Protocol', self.protocol_name, 'Image')


		# Define Variables - Time

		self.start_stimulus = 0.0
		self.response_latency = 0.0
		self.trial_end_time = 0.0
		
		self.iti_range = [float(iNum) for iNum in iti_import]
		self.iti_length = self.iti_range[0]


		# Define Variables - Count

		self.current_hits = 0
		self.current_reversal = 0
		self.point_counter = 0

		self.current_block = 0
		self.current_block_trial = 0

		self.stage_index = 0

		image_index_choice = [0, 1]
		random.shuffle(image_index_choice)

		self.target_image_index = image_index_choice[0]
		self.nontarget_image_index = image_index_choice[1]


		# Define Boolean

		self.target_rewarded = True
		self.nontarget_rewarded = False

		self.choice_rewarded = True


		# Nontarget Prob

		self.nontarget_reward_probability = round(1 - self.target_reward_probability, 2)

		self.trial_reward_list = list()
		self.trial_reward_list_index = -1

		for iTrial in range(int(self.target_reward_probability * 5)):
			self.trial_reward_list.append('Target')
		

		for iTrial in range(int(self.nontarget_reward_probability * 5)):
			self.trial_reward_list.append('Nonarget')
		
		random.shuffle(self.trial_reward_list)


		# Define Variables - String

		self.target_image = self.training_target_image
		self.nontarget_image = self.training_nontarget_image

		self.current_stage = self.stage_list[self.stage_index]
		self.side_chosen = ''

		self.target_loc_list = ['Left', 'Right']
		random.shuffle(self.target_loc_list)

		self.target_loc_index = 0
		self.nontarget_loc_index = 1

		self.target_loc = self.target_loc_list[self.target_loc_index]
		self.nontarget_loc = self.target_loc_list[self.nontarget_loc_index]


		# Define Widgets - Images

		self.stimulus_path_list = list(self.image_dir_path.glob(str(pathlib.Path('Targets', self.image_set, '*.png'))))
		self.target_image_list = list()

		for filename in self.stimulus_path_list:
			self.target_image_list.append(filename.stem)
		
		self.total_image_list = self.stimulus_path_list

		self.hold_image_path = str(self.image_dir_path / (self.hold_image + '.png'))
		self.mask_image_path = str(self.image_dir_path / (self.mask_image + '.png'))

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
		

		# Tutorial Import

		lang_folder_path = pathlib.Path('Protocol', self.protocol_name, 'Language', self.language)

		if (lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_path = str(list((lang_folder_path / 'Tutorial_Video').glob('*.mp4'))[0])

			# print(self.tutorial_video_path)

			self.tutorial_video = Video(
				source = self.tutorial_video_path
				, allow_stretch = True
				, options = {'eos': 'stop'}
				, state = 'stop'
				)

			self.tutorial_video.pos_hint = {'center_x': 0.5, 'center_y': 0.6}
			self.tutorial_video.size_hint = (1, 1)


		# Define Widgets - Instructions
		
		self.instruction_path = str(self.language_dir_path / 'Instructions.ini')
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Main'] = {}
		
		self.instruction_dict['Main']['train'] = self.instruction_config['Main']['train']
		self.instruction_dict['Main']['task'] = self.instruction_config['Main']['task']
		
		
		# Begin Task

		if (lang_folder_path / 'Tutorial_Video').is_dir() \
			and (self.skip_tutorial_video == 0):

			self.protocol_floatlayout.clear_widgets()
			self.present_tutorial_video()
		
		else:
			self.present_instructions()
			self.start_button.unbind(on_press=self.start_protocol)
			self.start_button.bind(on_press=self.start_protocol_from_tutorial)



	def present_tutorial_video(self, *args):

		self.protocol_floatlayout.clear_widgets()

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
			
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Object Display'
			])

		self.protocol_floatlayout.add_widget(self.tutorial_video)
		self.protocol_floatlayout.add_widget(self.tutorial_video_button)

		self.tutorial_video.state = 'stop'
	


	def start_tutorial_video(self, *args):

		self.tutorial_video.state = 'play'
		self.protocol_floatlayout.remove_widget(self.tutorial_video_button)
		
		self.tutorial_video_end_event = self.task_clock.schedule_once(self.present_tutorial_video_start_button, self.tutorial_video_duration)
			
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Display'
			, 'Video'
			, 'Section'
			, 'Instructions'
			])



	def present_tutorial_video_start_button(self, *args):

		self.tutorial_video_end_event.cancel()

		self.protocol_floatlayout.add_widget(self.tutorial_start_button)
		self.protocol_floatlayout.add_widget(self.tutorial_restart)
				
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Display'
			, 'Button'
			, 'Section'
			, 'Instructions'
			, 'Type'
			, 'Section Start'
			])
				
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Display'
			, 'Button'
			, 'Section'
			, 'Instructions'
			, 'Type'
			, 'Video Restart'
			])
	
	
	
	def start_protocol_from_tutorial(self, *args):

		self.tutorial_video_end_event.cancel()
		self.tutorial_video.state = 'stop'

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Remove'
			, 'Video'
			, 'Section'
			, 'Instructions'
			])

		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Section Start'
			])

		self.generate_output_files()
		self.metadata_output_generation()

		self.start_clock()
		self.block_check_event()



	def stimulus_presentation(self, *args): # Stimulus presentation
		
		# print('Stimulus presentation')

		self.iti_event.cancel()

		self.hold_button.unbind(on_release=self.premature_response)

		self.protocol_floatlayout.remove_widget(self.hold_button)
		self.protocol_floatlayout.add_widget(self.left_stimulus)
		self.protocol_floatlayout.add_widget(self.right_stimulus)
		
		self.stimulus_start_time = time.time()
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_start_time - self.start_time)
			, 'State Change'
			, 'Object Display'
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_start_time - self.start_time)
			, 'Object Display'
			, 'Stimulus'
			, 'Target'
			, self.target_loc
			, 'Image Name'
			, self.target_image
			, 'Rewarded'
			, self.target_rewarded
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_start_time - self.start_time)
			, 'Object Display'
			, 'Stimulus'
			, 'Nontarget'
			, self.nontarget_loc
			, 'Image Name'
			, self.nontarget_image
			, 'Rewarded'
			, self.nontarget_rewarded
			])



	# Hold released too early
	
	def premature_response(self, *args):
		
		# print('Premature response')
		
		if self.stimulus_on_screen is True:
			return
		
		self.iti_event.cancel()
		
		self.protocol_floatlayout.clear_widgets()
		
		self.response_latency = np.nan
		
		self.protocol_floatlayout.add_event([
			time.time() - self.start_time
			, 'State Change'
			, 'Premature Response'
			])
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Response Latency'
			, self.response_latency
			])
		
		self.iti_active = False
		self.feedback_label.text = self.feedback_dict['wait']

		if self.feedback_on_screen is False:	
			self.protocol_floatlayout.add_widget(self.feedback_label)
			self.feedback_on_screen = True
			self.feedback_start_time = time.time()

			self.protocol_floatlayout.add_event([
				(self.feedback_start_time - self.start_time)
				, 'Object Display'
				, 'Text'
				, 'Feedback'
				, self.feedback_label.text
				])
		
		self.hold_button.unbind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.iti)
	
		self.protocol_floatlayout.add_widget(self.hold_button)
	
	
	
	# Left Stimulus Pressed
	
	def left_pressed(self, *args):

		self.stimulus_press_time = time.time()
		self.side_chosen = 'Left'

		self.protocol_floatlayout.add_event([
			time.time() - self.start_time
			, 'State Change'
			, 'Left Stimulus Pressed'
			])
		
		self.trial_outcomes()
	
	
	
	# Right Stimulus Pressed
	
	def right_pressed(self, *args):

		self.stimulus_press_time = time.time()
		self.side_chosen = 'Right'

		self.protocol_floatlayout.add_event([
			time.time() - self.start_time
			, 'State Change'
			, 'Right Stimulus Pressed'
			])
		
		self.trial_outcomes()



	def trial_outcomes(self, *args):

		if self.side_chosen == self.target_loc:
			self.last_response = 1
			self.current_hits += 1
			
			self.protocol_floatlayout.add_event([
				self.stimulus_press_time - self.start_time
				, 'State Change'
				, 'Target Pressed'
				])
			
			if self.target_rewarded:
				self.choice_rewarded = True
			
			else:
				self.choice_rewarded = False

		elif self.side_chosen == self.nontarget_loc:
			self.last_response = 0
			self.current_hits = 0
			
			self.protocol_floatlayout.add_event([
				self.stimulus_press_time - self.start_time
				, 'State Change'
				, 'Nontarget Pressed'
				])

			if not self.target_rewarded:
				self.choice_rewarded = True
			
			else:
				self.choice_rewarded = False
		

		if self.choice_rewarded:

			self.protocol_floatlayout.add_event([
				self.stimulus_press_time - self.start_time
				, 'State Change'
				, 'Choice Rewarded'
				])

			if self.current_stage == 'Training':
				self.feedback_label.text = '[color=00C000]CORRECT[/color]'

			else:
				self.feedback_label.text = self.feedback_dict['correct']
				self.point_counter += 10

				self.protocol_floatlayout.add_event([
					self.stimulus_press_time - self.start_time
					, 'State Change'
					, 'Points Collected'
					])

				self.protocol_floatlayout.add_event([
					self.stimulus_press_time - self.start_time
					, 'Variable Change'
					, 'Outcome'
					, 'Points'
					, self.response_latency
					])
		
		else:

			self.protocol_floatlayout.add_event([
				self.stimulus_press_time - self.start_time
				, 'State Change'
				, 'Choice Not Rewarded'
				])

		self.protocol_floatlayout.add_event([
			self.stimulus_press_time - self.start_time
			, 'Variable Change'
			, 'Outcome'
			, 'Side Chosen'
			, self.side_chosen
			])
		
		self.protocol_floatlayout.add_event([
			self.stimulus_press_time - self.start_time
			, 'Variable Change'
			, 'Outcome'
			, 'Last Response'
			, self.last_response
			])
	
		self.protocol_floatlayout.add_event([
			self.stimulus_press_time - self.start_time
			, 'Variable Change'
			, 'Outcome'
			, 'Current Hits'
			, self.current_hits
			])
		
		self.protocol_floatlayout.add_event([
			self.stimulus_press_time - self.start_time
			, 'Variable Change'
			, 'Outcome'
			, 'Response Latency'
			, self.response_latency
			])

		self.protocol_floatlayout.remove_widget(self.left_stimulus)
		self.protocol_floatlayout.remove_widget(self.right_stimulus)

		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Image Removed'
			, 'Target'
			, 'Location'
			, self.target_loc
			])

		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Image Removed'
			, 'Nontarget'
			, 'Location'
			, self.nontarget_loc
			])

		self.hold_button.bind(on_press=self.iti)
		self.hold_button.bind(on_release=self.premature_response)

		if self.feedback_label.text != '' \
			and not self.feedback_on_screen:
			print(self.feedback_label.text, time.time() - self.start_time)
			
			self.protocol_floatlayout.add_widget(self.feedback_label)

			self.feedback_start_time = time.time()
			self.feedback_on_screen = True

			self.protocol_floatlayout.add_event([
				(self.feedback_start_time - self.start_time)
				, 'Object Display'
				, 'Text'
				, 'Feedback'
				, self.feedback_label.text
				])
		
		self.protocol_floatlayout.add_widget(self.hold_button)
		
		self.write_trial()
		
		self.trial_contingency()
	
	
	
	# Data Saving Function
	
	def write_trial(self):
		
		'''
		# self.data_cols = [
		# 	'TrialNo'
		# 	, 'Stage'
		# 	, 'ReversalNo'
		# 	, 'TargetImage'
		# 	, 'TargetLoc'
		# 	, 'NontargetImage'
		# 	, 'NontargetLoc'
		# 	, 'TargetReward'
		# 	, 'NontargetReward'
		# 	, 'ImageChosen'
		# 	, 'Correct'
		# 	, 'Rewarded'
		# 	, 'ResponseLat'
		# 	]
		'''

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

			# self.iti_event.cancel()

			# if self.feedback_on_screen:
				
			# 	if (time.time() - self.feedback_start_time) >= self.feedback_length:
			# 		self.trial_contingency_event.cancel()
			# 		self.protocol_floatlayout.remove_widget(self.feedback_label)
			# 		self.feedback_label.text = ''
			# 		self.feedback_on_screen = False

			# 	else:
			# 		return
				
			# else:
			# 	self.trial_contingency_event.cancel()

			if self.current_block_trial != 0:
				
				# print('\n\n\n')
				# print('Trial contingency start')
				# print('')
				# print('Current trial: ', self.current_trial)
				# print('Current stage: ', self.current_stage)
				# print('Current task time: ', (time.time() - self.start_time))
				# print('Current block time: ', (time.time() - self.block_start))
				# print('')
				# print('ITI: ', self.iti_length)
				# print('Start target time: ', (self.stimulus_start_time - self.start_time))
				# print('Response latency: ', self.response_latency)
				# print('')
				# print('Last response: ', self.last_response)
				# print('')
				# print('Target image: ', self.target_image)
				# print('Target loc: ', self.target_loc)
				# print('')
				# print('Nontarget image: ', self.nontarget_image)
				# print('Nontarget loc: ', self.nontarget_loc)
				# print('')
				# print('Target rewarded: ', str(self.target_rewarded))
				# print('Nontarget rewarded: ', str(self.nontarget_rewarded))
				# print('\n\n')

				self.response_tracking.append(self.last_response)

				# Check if block ended

				if (time.time() - self.block_start >= self.block_duration) \
					or (self.current_block_trial >= self.block_trial_max):
					
					self.block_check_event()

				elif (self.current_stage == 'Training') \
					and (sum(self.response_tracking) >= self.training_block_max_correct):
					
					self.block_check_event()

			# Set next trial parameters
			
			# self.feedback_label.text = ''
			# print('label changed blank', time.time() - self.start_time)
			self.side_chosen = ''
			self.choice_rewarded = False
			self.last_response = 0

			self.current_trial += 1
			self.current_block_trial += 1
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Current Trial'
				, str(self.current_trial)
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Current Block Trial'
				, str(self.current_block_trial)
				])
			
			# Set ITI

			if len(self.iti_range) > 1:
				
				if self.iti_fixed_or_range == 'fixed':
					self.iti_length = random.choice(self.iti_range)
				
				else:
					self.iti_length = round(random.uniform(min(self.iti_range), max(self.iti_range)), 2)
				
				self.protocol_floatlayout.add_event([
					time.time() - self.start_time
					, 'Variable Change'
					, 'Parameter'
					, 'Current ITI'
					, self.iti_length
					])


			if self.current_hits >= self.reversal_threshold:
				self.current_hits = 0
				self.current_reversal += 1

				if self.current_reversal > self.max_reversals:
					self.block_check_event()
				
				else:
					self.target_loc_index += 1
					self.nontarget_loc_index += 1

					if self.target_loc_index >= len(self.target_loc_list):
						self.target_loc_index = 0

					elif self.nontarget_loc_index >= len(self.target_loc_list):
						self.nontarget_loc_index = 0

					self.target_loc = self.target_loc_list[self.target_loc_index]
					self.nontarget_loc = self.target_loc_list[self.nontarget_loc_index]

			self.protocol_floatlayout.add_event([
				time.time() - self.start_time
				, 'Variable Change'
				, 'Parameter'
				, 'Current Reversal'
				, self.current_reversal
				])

			self.protocol_floatlayout.add_event([
				time.time() - self.start_time
				, 'Variable Change'
				, 'Parameter'
				, 'Current Hits'
				, self.current_hits
				])

			self.protocol_floatlayout.add_event([
				time.time() - self.start_time
				, 'Variable Change'
				, 'Parameter'
				, 'Target Location'
				, self.target_loc
				])

			self.protocol_floatlayout.add_event([
				time.time() - self.start_time
				, 'Variable Change'
				, 'Parameter'
				, 'Nontarget Location'
				, self.nontarget_loc
				])

			if self.current_stage == 'Training':
				self.target_rewarded = True
				self.nontarget_rewarded = False
			
			else:
				self.trial_reward_list_index += 1

				if (self.trial_reward_list_index >= len(self.trial_reward_list)):
					random.shuffle(self.trial_reward_list)
					self.trial_reward_list_index = 0

				self.protocol_floatlayout.add_event([
					time.time() - self.start_time
					, 'Variable Change'
					, 'Parameter'
					, 'Rewarded Side'
					, self.trial_reward_list[self.trial_reward_list_index]
					])

				if self.trial_reward_list[self.trial_reward_list_index] == 'Target':
					self.target_rewarded = True
					self.nontarget_rewarded = False
				
				else:
					self.target_rewarded = False
					self.nontarget_rewarded = True

			self.trial_end_time = time.time()
		
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()
	
	
	
	def section_start(self, *args):

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Section Start'
			])
				
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Display'
			, 'Text'
			, 'Section'
			, 'Instructions'
			, 'Type'
			, 'Section Start'
			])
				
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Display'
			, 'Button'
			, 'Section'
			, 'Instructions'
			, 'Type'
			, 'Continue'
			])
		
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
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Display'
			, 'Text'
			, 'Stage'
			, 'Results'
			])
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Display'
			, 'Button'
			, 'Stage'
			, 'End Protocol'
			])

		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Task End'
			])


	
	# Block Contingency Function
	
	def block_contingency(self, *args):
		
		try:
			
			self.hold_button.unbind(on_press=self.iti)
			self.hold_button.unbind(on_release=self.premature_response)

			self.iti_event.cancel()

			self.block_started = True

			if self.feedback_on_screen:
				
				if (time.time() - self.feedback_start_time) >= self.feedback_length:
					# print('Feedback over')
					self.block_check_event.cancel()
					self.protocol_floatlayout.clear_widgets()
					self.feedback_label.text = ''
					self.feedback_on_screen = False

				else:
					return
			else:
				# print('Block check event cancel')
				self.block_check_event.cancel()
			
			
			# print('Block contingency')

			self.protocol_floatlayout.clear_widgets()

			# print('Clear widgets')

			self.current_block += 1

			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'State Change'
				, 'Block Change'
				, 'Current Block'
				, self.current_block
				])
			
			# print('Current block: ', self.current_block)
			
			if (self.current_block > self.block_multiplier) \
				or (self.current_block == -1):

				self.stage_index += 1
				self.current_block = 1
				
				# print('Stage index: ', self.stage_index)
			
	
			if self.stage_index >= len(self.stage_list): # Check if all stages complete
				# print('All stages complete')
				self.session_event.cancel()
				self.final_results_screen()
				return
			
			else:
				self.current_stage = self.stage_list[self.stage_index]
				# print('Current stage: ', self.current_stage)
		
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'State Change'
					, 'Stage Change'
					, 'Current Stage'
					, self.current_stage
					])

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

				random.shuffle(self.trial_reward_list)
				self.trial_reward_list_index = 0
				
				if self.trial_reward_list[self.trial_reward_list_index] == 'Target':
					self.target_rewarded = True
					self.nontarget_rewarded = False
				
				else:
					self.target_rewarded = False
					self.nontarget_rewarded = True
			
			self.protocol_floatlayout.add_event([
				time.time() - self.start_time
				, 'Variable Change'
				, 'Parameter'
				, 'Current Reversal'
				, self.current_reversal
				])

			self.protocol_floatlayout.add_event([
				time.time() - self.start_time
				, 'Variable Change'
				, 'Parameter'
				, 'Current Hits'
				, self.current_hits
				])

			self.protocol_floatlayout.add_event([
				time.time() - self.start_time
				, 'Variable Change'
				, 'Parameter'
				, 'Target Location'
				, self.target_loc
				])

			self.protocol_floatlayout.add_event([
				time.time() - self.start_time
				, 'Variable Change'
				, 'Parameter'
				, 'Nontarget Location'
				, self.nontarget_loc
				])

			if self.current_block == 1:
				# print('Section Task Instructions')
				self.block_max_length = 360
				
				if self.current_stage == 'Training':
					self.block_max_length = self.training_block_max_correct
					self.instruction_label.text = self.instruction_dict['Main']['train']

				else:
					self.instruction_label.text = self.instruction_dict['Main']['task']

				self.instruction_button.text = 'Begin Section'

				self.protocol_floatlayout.add_widget(self.instruction_label)
				self.protocol_floatlayout.add_widget(self.instruction_button)
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Object Display'
					, 'Text'
					, 'Block'
					, 'Instructions'
					, 'Type'
					, 'Task'
					])
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Object Display'
					, 'Button'
					, 'Block'
					, 'Instructions'
					, 'Type'
					, 'Continue'
					])
			
			else:
				# print('Else: Block Screen')
				self.block_started = False
				self.block_screen()

			# print('Block contingency end')

			#self.trial_contingency_event()
			self.trial_contingency()
		
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()