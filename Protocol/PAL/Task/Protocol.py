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
from kivy.loader import Loader
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.video import Video




class ProtocolScreen(ProtocolBase):

	def __init__(self,**kwargs):

		super(ProtocolScreen,self).__init__(**kwargs)
		self.protocol_name = 'PAL'
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
			# # print('Width > Height')
		
		elif width < height:
			self.height_adjust = width / height
			# # print('Width < Height')
		
		# # print('Width adjust: ', self.width_adjust)
		# # print('height adjust: ', self.height_adjust)


		# Define Data Columns

		self.data_cols = [
			'TrialNo'
			, 'CurrentStage'
			, 'CurrentBlock'
			, 'BlockTrial'
			, 'TargetImage'
			, 'TargetLoc'
			, 'NontargetImage'
			, 'NontargetLoc'
			, 'Correct'
			, 'ResponseLat'
			]

		self.metadata_cols = [
			'participant_id'
			, 'skip_tutorial_video'
			, 'tutorial_video_duration_pal'
			, 'tutorial_video_duration_pa'
			, 'block_change_on_duration_only'
			, 'training_task'
			, 'dpal_probe'
			, 'spal_probe'
			, 'recall_probe'
			, 'iti_fixed_or_range'
			, 'iti_length'
			, 'feedback_length'
			, 'block_duration'
			, 'block_min_rest_duration'
			, 'session_duration'
			, 'block_multiplier'
			, 'dpal_trial_max'
			, 'spal_trial_max'
			, 'recall_trial_max'
			, 'training_block_max_correct'
			, 'num_stimuli_pal'
			, 'num_stimuli_pa'
			, 'num_rows'
			, 'training_image'
			]


		# Define Variables - Config

		self.protocol_path = pathlib.Path('Protocol', self.protocol_name)

		config_path = str(self.protocol_path / 'Configuration.ini')
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
		self.tutorial_video_duration_PAL = float(self.parameters_dict['tutorial_video_duration_pal'])
		self.tutorial_video_duration_PA = float(self.parameters_dict['tutorial_video_duration_pa'])

		self.block_change_on_duration = int(self.parameters_dict['block_change_on_duration_only'])
		
		self.iti_fixed_or_range = self.parameters_dict['iti_fixed_or_range']
		
		iti_import = self.parameters_dict['iti_length']
		iti_import = iti_import.split(',')
		
		self.feedback_length = float(self.parameters_dict['feedback_length'])
		self.block_duration = int(self.parameters_dict['block_duration'])
		self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
		self.session_duration = float(self.parameters_dict['session_duration'])
		
		self.block_multiplier = int(self.parameters_dict['block_multiplier'])

		self.dpal_trial_max = int(self.parameters_dict['dpal_trial_max'])
		self.spal_trial_max = int(self.parameters_dict['spal_trial_max'])
		self.recall_trial_max = int(self.parameters_dict['recall_trial_max'])

		self.training_block_max_correct = int(self.parameters_dict['training_block_max_correct'])

		self.recall_target_present_duration = float(self.parameters_dict['recall_target_present_duration'])
		
		self.num_stimuli_pal = int(self.parameters_dict['num_stimuli_pal'])
		self.num_stimuli_pa = int(self.parameters_dict['num_stimuli_pa'])
		self.num_rows = int(self.parameters_dict['num_rows'])

		self.training_image = self.parameters_dict['training_image']

		self.hold_image = config_file['Hold']['hold_image']
		self.mask_image = config_file['Mask']['mask_image']


		# Create stage list

		self.stage_list = list()


		# Define Language

		self.language = 'English'
		self.set_language(self.language)


		# Define Variables - Clock

		self.block_check_clock = Clock
		self.block_check_clock.interupt_next_only = False
		self.block_check_event = self.block_check_clock.create_trigger(self.block_contingency, 0, interval=True)
		self.stage_screen_event = self.block_check_clock.create_trigger(self.stage_screen, 0, interval=True)

		self.task_clock = Clock
		self.task_clock.interupt_next_only = True
		self.recall_instruction_target_present_event = self.task_clock.create_trigger(self.recall_target_screen, 0, interval=True)



		# Define Variables - Time

		self.stimulus_start_time = 0.0
		self.stimulus_press_time = 0.0
		self.response_latency = 0.0
		self.trial_end_time = 0.0
		self.tutorial_video_duration = 0.0
		
		self.iti_range = list()
		self.iti_length = 0.0

		self.recall_target_screen_start_time = 0.0


		# Define Variables - Numeric
		
		self.current_block = 0
		self.current_block_trial = 0
		
		self.stage_index = 0
		
		self.block_max_count = self.block_multiplier
		self.block_trial_max = 120

		self.last_response = 0

		self.response_tracking = list()

		self.target_loc = 0
		self.nontarget_loc = 1
		self.nontarget_image_loc = 2
		self.last_target_loc = -1
		self.last_nontarget_loc = -1

		self.recall_target_display_pos = 0


		# Define Variables - String

		self.current_stage = ''
		self.target_image = ''
		self.nontarget_image = ''
		self.blank_image = ''
		self.recall_image = ''


		# Define Widgets - Image Paths

		self.image_folder = self.protocol_path / 'Image'
		self.target_folder = str(self.image_folder / 'Targets')

		self.outline_image = 'whitesquare'

		self.hold_image_path = str(self.image_folder / str(self.hold_image + '.png'))
		self.mask_image_path = str(self.image_folder / str(self.mask_image + '.png'))
		self.outline_image_path = str(self.image_folder / str(self.outline_image + '.png'))


		# Define Widgets - Images

		self.stimulus_grid_list = list()
		self.recall_stimulus = ImageButton()


		# Define Widgets - Instructions
		
		self.instruction_path = str(pathlib.Path('Protocol', self.protocol_name, 'Language', self.language, 'Instructions.ini'))
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Training'] = {}
		self.instruction_dict['dPAL'] = {}
		self.instruction_dict['sPAL'] = {}
		self.instruction_dict['Recall'] = {}
		
		for stage in self.stage_list:
			
			self.instruction_dict[stage]['train'] = self.instruction_config[stage]['train']
			self.instruction_dict[stage]['task'] = self.instruction_config[stage]['task']



	# Initialization Functions #
		
	def load_parameters(self,parameter_dict):

		self.parameters_dict = parameter_dict
		
		self.participant_id = self.parameters_dict['participant_id']
		
		self.language = self.parameters_dict['language']

		self.skip_tutorial_video = int(self.parameters_dict['skip_tutorial_video'])
		self.tutorial_video_duration_PAL = float(self.parameters_dict['tutorial_video_duration_pal'])
		self.tutorial_video_duration_PA = float(self.parameters_dict['tutorial_video_duration_pa'])

		self.block_change_on_duration = int(self.parameters_dict['block_change_on_duration_only'])
		
		self.iti_fixed_or_range = self.parameters_dict['iti_fixed_or_range']
		
		iti_import = self.parameters_dict['iti_length']
		iti_import = iti_import.split(',')
		
		self.feedback_length = float(self.parameters_dict['feedback_length'])
		self.block_duration = int(self.parameters_dict['block_duration'])
		self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
		self.session_duration = float(self.parameters_dict['session_duration'])
		
		self.block_multiplier = int(self.parameters_dict['block_multiplier'])

		self.dpal_trial_max = int(self.parameters_dict['dpal_trial_max'])
		self.spal_trial_max = int(self.parameters_dict['spal_trial_max'])
		self.recall_trial_max = int(self.parameters_dict['recall_trial_max'])
		
		self.training_block_max_correct = int(self.parameters_dict['training_block_max_correct'])

		self.recall_target_present_duration = float(self.parameters_dict['recall_target_present_duration'])
		
		self.num_stimuli_pal = int(self.parameters_dict['num_stimuli_pal'])
		self.num_stimuli_pa = int(self.parameters_dict['num_stimuli_pa'])
		self.num_rows = int(self.parameters_dict['num_rows'])

		self.training_image = self.parameters_dict['training_image']
		

		config_path = str(pathlib.Path('Protocol', self.protocol_name, 'Configuration.ini'))
		config_file = configparser.ConfigParser()
		config_file.read(config_path)

		self.hold_image = config_file['Hold']['hold_image']
		self.mask_image = config_file['Mask']['mask_image']


		# Create stage list

		self.stage_list = list()
		
		if int(self.parameters_dict['training_task']) == 1:
			self.stage_list.append('Training')
		
		if int(self.parameters_dict['dpal_probe']) == 1:
			self.stage_list.append('dPAL')
		
		if int(self.parameters_dict['spal_probe']) == 1:
			self.stage_list.append('sPAL')
		
		if int(self.parameters_dict['recall_probe']) == 1:
			self.stage_list.append('Recall')


		# Define Language

		self.language = 'English'
		self.set_language(self.language)


		# Define Variables - Numeric
		
		self.current_block = 0
		self.current_block_trial = 0
		
		self.stage_index = 0
		
		self.block_max_count = self.block_multiplier
		self.block_trial_max = 120

		self.last_response = 0

		self.response_tracking = list()

		self.target_loc = 0
		self.nontarget_loc = 1
		self.nontarget_image_loc = 2

		self.recall_target_display_pos = 0


		# Define Variables - String

		self.current_stage = ''
		self.target_image = self.mask_image
		self.nontarget_image = self.mask_image
		self.blank_image = self.mask_image
		self.recall_image = self.mask_image


		# Define Variables - Boolean

		self.recall_instruction_target_display_started = False
		self.stage_screen_started = False


		# Define Variables - Time

		self.stimulus_start_time = 0.0
		self.stimulus_press_time = 0.0
		self.response_latency = 0.0
		self.trial_end_time = 0.0
		self.recall_target_screen_start_time = 0.0
		self.tutorial_video_duration = 0.0
		
		self.iti_range = [float(iNum) for iNum in iti_import]
		self.iti_length = self.iti_range[0]


		# Define Widgets - Images

		self.image_folder = self.protocol_path / 'Image'
		
		self.outline_image = 'whitecircle'

		self.hold_image_path = str(self.image_folder / str(self.hold_image + '.png'))
		self.mask_image_path = str(self.image_folder / str(self.mask_image + '.png'))
		self.outline_image_path = str(self.image_folder / str(self.outline_image + '.png'))
		self.training_image_path = str(self.image_folder / str(self.training_image + '.png'))

		self.stimulus_image_path_list = list()

		if any(True for stage in ['dPAL', 'sPAL', 'Training'] if stage in self.stage_list):
			stimulus_path_list = list(pathlib.Path(self.image_folder).glob(str(pathlib.Path('PAL-Targets', '*.png'))))
			stimulus_image_list = list()

			for filename in stimulus_path_list:
				self.stimulus_image_path_list.append(filename)
				stimulus_image_list.append(filename.stem)
			
			if self.num_stimuli_pal > len(stimulus_image_list):
				self.num_stimuli_pal = len(stimulus_image_list)
			
			self.target_image_list_pal = list()

			while len(self.target_image_list_pal) < self.num_stimuli_pal:
				new_target = random.choice(stimulus_image_list)
				self.target_image_list_pal.append(new_target)
				stimulus_image_list.remove(new_target)


		if 'Recall' in self.stage_list:
			stimulus_path_list = list(pathlib.Path(self.image_folder).glob(str(pathlib.Path('PA-Targets', '*.png'))))
			stimulus_image_list = list()

			for filename in stimulus_path_list:
				self.stimulus_image_path_list.append(filename)
				stimulus_image_list.append(filename.stem)
			
			if self.num_stimuli_pa > len(stimulus_image_list):
				self.num_stimuli_pa = len(stimulus_image_list)
			
			self.target_image_list_pa = list()

			while len(self.target_image_list_pa) < self.num_stimuli_pa:
				new_target = random.choice(stimulus_image_list)
				self.target_image_list_pa.append(new_target)
				stimulus_image_list.remove(new_target)

		self.total_image_list = self.stimulus_image_path_list

		self.total_image_list += [self.hold_image_path, self.mask_image_path, self.outline_image_path, self.training_image_path]
		# print('\n\nTotal image list: ', self.total_image_list, '\n\n')

		self.load_images(self.total_image_list)

		self.recall_stimulus = ImageButton(
			source = self.mask_image_path
			, size_hint = [0.3 * self.width_adjust, 0.3 * self.height_adjust]
			, pos_hint = {"center_x": 0.5, "center_y": 0.85}
			)
		
		self.hold_button.source = self.hold_image_path
		self.hold_button.bind(on_press=self.iti)
		self.hold_button.unbind(on_release=self.hold_remind)
		self.hold_button.bind(on_release=self.premature_response)

		self.text_button_size = [0.4, 0.15]
		self.text_button_pos_LL = {"center_x": 0.25, "center_y": 0.08}
		self.text_button_pos_LR = {"center_x": 0.75, "center_y": 0.08}

		# Define trial lists

		self.trial_list = list()
		self.trial_list_pal = list()
		self.trial_list_pa = list()
		self.trial_list_index = 0

		for iNum in range(15):
			self.trial_list_pal.append(iNum % self.num_stimuli_pal)
			self.trial_list_pa.append(iNum % self.num_stimuli_pa)


		# Instruction Import

		lang_folder_path = pathlib.Path('Protocol', self.protocol_name, 'Language', self.language)

		if (lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_PAL_path = str(list((lang_folder_path / 'Tutorial_Video').glob('*Part 1*'))[0])
			self.tutorial_video_PA_path = str(list((lang_folder_path / 'Tutorial_Video').glob('*Part 2*'))[0])

			# print(self.tutorial_video_PAL_path)
			# print(self.tutorial_video_PA_path)

			self.tutorial_video = Video(
				source = self.tutorial_video_PAL_path
				, allow_stretch = True
				, options = {'eos': 'stop'}
				, state = 'stop'
				)

			self.tutorial_video.pos_hint = {'center_x': 0.5, 'center_y': 0.6}
			self.tutorial_video.size_hint = (1, 1)
		
		
		# Instruction - Text Widget
		
		self.section_instr_string = self.instruction_label.text
		self.section_instr_label = Label(text=self.section_instr_string, font_size='44sp', markup=True)
		self.section_instr_label.size_hint = {0.9, 0.8}
		self.section_instr_label.pos_hint = {'center_x': 0.5, 'center_y': 0.4}
		
		self.stage_results_label = Label(text='', font_size='44sp', markup=True)
		self.stage_results_label.size_hint = {0.9, 0.8}
		self.stage_results_label.pos_hint = {'center_x': 0.5, 'center_y': 0.4}
		
		
		# Instruction - Button Widget
		
		self.instruction_button = Button(font_size='60sp')
		self.instruction_button.size_hint = self.text_button_size
		self.instruction_button.pos_hint =  {"center_x": 0.50, "center_y": 0.9}
		self.instruction_button.text = 'Start Section'
		self.instruction_button.bind(on_press=self.section_start)
		
		self.stage_continue_button = Button(font_size='60sp')
		self.stage_continue_button.size_hint = self.text_button_size
		self.stage_continue_button.pos_hint =  {"center_x": 0.50, "center_y": 0.9}
		self.stage_continue_button.text = 'Continue'
		self.stage_continue_button.bind(on_press=self.block_check_event)
		

		# Define Widgets - Stimulus Layout

		self.x_boundaries = [0.1, 0.9]
		self.y_boundaries = [0.1, 1]

		self.stimulus_image_x_size = (max(self.x_boundaries) - min(self.x_boundaries))/np.ceil(max(self.num_stimuli_pal, self.num_stimuli_pa)/self.num_rows)

		self.stimulus_x_boundaries = [
			(min(self.x_boundaries) + (self.stimulus_image_x_size/2))
			, (max(self.x_boundaries) - (self.stimulus_image_x_size/2))
			]

		if any(True for stage in ['dPAL', 'sPAL', 'Training'] if stage in self.stage_list):
			self.num_stimuli = self.num_stimuli_pal
		
		else:
			self.num_stimuli = self.num_stimuli_pa
		
		self.stimulus_x_loc = np.linspace(min(self.stimulus_x_boundaries), max(self.stimulus_x_boundaries), int(self.num_stimuli)).tolist()

		self.stimulus_grid_list = self.generate_stimulus_grid(
			self.stimulus_x_loc
			, self.num_rows
			, grid_gap = 0.1
			)
		

		# Instruction - Dictionary
		
		self.instruction_path = str(lang_folder_path / 'Instructions.ini')
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Training'] = {}
		self.instruction_dict['dPAL'] = {}
		self.instruction_dict['sPAL'] = {}
		self.instruction_dict['Recall'] = {}
		
		for stage in self.stage_list:
			self.instruction_dict[stage]['train'] = self.instruction_config[stage]['train']
			self.instruction_dict[stage]['task'] = self.instruction_config[stage]['task']

		for stimulus in self.stimulus_grid_list:
			self.protocol_floatlayout.add_widget(stimulus)
		
		self.protocol_floatlayout.add_widget(self.recall_stimulus)
		
		
		# Begin Task

		# print('End load parameters...')
		self.start_protocol_from_tutorial()
	


	# Protocol Staging	
	
	def start_protocol_from_tutorial(self, *args):
		
		self.generate_output_files()
		self.metadata_output_generation()
		self.start_protocol()

	
	
	# def protocol_load_images(self, image_list, *args):
	# 	# Load Images - Async
		
	# 	self.image_dict = {}
		
	# 	for image_file in image_list:
			
	# 		if pathlib.Path(self.image_folder / image_file).exists():
	# 			load_image = Loader.image(str(self.image_folder / image_file))
	# 			image_name = str(image_file.stem)
			
	# 		elif pathlib.Path(self.image_folder, str(image_file) + '.png').exists():
	# 			load_image = Loader.image((str(self.image_folder) + str(image_file) + '.png'))
	# 			image_name = str(image_file)

	# 		else:
	# 			image_file = pathlib.Path(image_file)
	# 			load_image = Loader.image(str(image_file))
	# 			image_name = str(image_file.stem)

	# 		self.image_dict[image_name] = load_image



	def generate_stimulus_grid(
			self
			, grid_x_pos_list
			, num_rows = 1
			, grid_gap = 0.1
			):
		
		grid_square_dim = (max(grid_x_pos_list) - min(grid_x_pos_list)) / (len(grid_x_pos_list) - 1)
		grid_square_fill = [(grid_square_dim * self.width_adjust) * (1 - grid_gap), (grid_square_dim * self.height_adjust) * (1 - grid_gap)]
		
		grid_x_squares = len(grid_x_pos_list)
		
		stimulus_grid_loc = [ImageButton() for position in range(int(grid_x_squares * num_rows))]
		
		x_pos = 0
		y_pos = 0
		
		for cell in stimulus_grid_loc:
			
			if x_pos >= grid_x_squares:
				x_pos = 0
				y_pos += 1
				
			grid_square_x_pos = grid_x_pos_list[x_pos]
			grid_square_y_pos = 0.3 + ((y_pos + 0.5) * (grid_square_dim * self.height_adjust))

			cell.source = self.mask_image_path
			cell.bind(on_press=self.nontarget_pressed)
			
			cell.size_hint = grid_square_fill
			cell.pos_hint = {"center_x": grid_square_x_pos, "center_y": grid_square_y_pos}
			
			x_pos += 1
		
		return stimulus_grid_loc



	def start_protocol(self, *args):
		
		self.protocol_floatlayout.clear_widgets()
		
		# print('Stage list: ', self.stage_list)
		
		self.start_clock()
		self.block_check_event()
	
	
	
	def stimulus_presentation(self, *args): # Stimulus presentation
		
		# print('Stimulus presentation')
		
		self.iti_event.cancel()

		self.hold_button.unbind(on_release=self.premature_response)
		
		self.protocol_floatlayout.clear_widgets()
		self.protocol_floatlayout.add_widget(self.recall_stimulus)
					
		for stimulus in self.stimulus_grid_list:
			self.protocol_floatlayout.add_widget(stimulus)
		
		self.stimulus_start_time = time.time()
		
		self.feedback_label.text = ''
		
		self.protocol_floatlayout.add_event([
			self.stimulus_start_time - self.start_time
			, 'State Change'
			, 'Object Display'
			])
		
		self.protocol_floatlayout.add_event([
			self.stimulus_start_time - self.start_time
			, 'Object Display'
			, 'Stimulus'
			, 'Target'
			, self.target_loc
			, 'Image Name'
			, self.target_image
			])

		if self.current_stage in ['dPAL', 'sPAL']:

			self.protocol_floatlayout.add_event([
				self.stimulus_start_time - self.start_time
				, 'Object Display'
				, 'Stimulus'
				, 'Nontarget'
				, self.nontarget_loc
				, 'Image Name'
				, self.nontarget_image
				])

		elif self.current_stage == 'Recall':

			self.protocol_floatlayout.add_event([
				self.stimulus_start_time - self.start_time
				, 'Object Display'
				, 'Stimulus'
				, 'Target'
				, 'Recall Location'
				, 'Image Name'
				, self.target_image
				])



	# Hold released too early
	
	def premature_response(self, *args):
		
		# print('Premature response')
		
		if self.stimulus_on_screen is True:
			return
		
		self.iti_event.cancel()
		
		self.protocol_floatlayout.add_event([
			time.time() - self.start_time
			, 'State Change'
			, 'Premature Response'
			])
		
		self.response_latency = np.nan
		
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
	
	
	
	# Target Pressed
	
	def target_pressed(self, *args):
		
		# print('Target pressed')

		self.protocol_floatlayout.add_event([
			time.time() - self.start_time
			, 'State Change'
			, 'Correct Response'
			])
		
		self.last_response = 1
		self.stimulus_press_time = time.time()
		self.response_latency = self.stimulus_press_time - self.stimulus_start_time

		self.protocol_floatlayout.clear_widgets()
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Last Response'
			, self.last_response
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Response Latency'
			, self.response_latency
			])

		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'State Change'
			, 'Object Remove'
			])

		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Object Remove'
			, 'Stimulus'
			, 'Target'
			, self.target_loc
			, 'Image Name'
			, self.target_image
			])

		if self.current_stage in ['dPAL', 'sPAL']:
		
			self.protocol_floatlayout.add_event([
				(self.stimulus_press_time - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Nontarget'
				, self.nontarget_loc
				, 'Image Name'
				, self.nontarget_image
				])

		elif self.current_stage == 'Recall':
		
			self.protocol_floatlayout.add_event([
				(self.stimulus_press_time - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Target'
				, 'Recall Location'
				, 'Image Name'
				, self.target_image
				])
		
		self.feedback_label.text = self.feedback_dict['correct']

		self.hold_button.bind(on_press=self.iti)
		self.hold_button.bind(on_release=self.premature_response)

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
		
		self.write_trial()
		self.trial_contingency()

		return
	
	
	
	# Nontarget Pressed
	
	def nontarget_pressed(self, *args):
		
		# print('Nontarget pressed')

		self.protocol_floatlayout.add_event([
			time.time() - self.start_time
			, 'State Change'
			, 'Incorrect Response'
			])
		
		self.last_response = 0

		self.stimulus_press_time = time.time()
		self.response_latency = self.stimulus_press_time - self.stimulus_start_time

		self.protocol_floatlayout.clear_widgets()
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Last Response'
			, self.last_response
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Response Latency'
			, self.response_latency
			])

		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'State Change'
			, 'Object Remove'
			])

		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Object Remove'
			, 'Stimulus'
			, 'Target'
			, self.target_loc
			, 'Image Name'
			, self.target_image
			])

		if self.current_stage in ['dPAL', 'sPAL']:
		
			self.protocol_floatlayout.add_event([
				(self.stimulus_press_time - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Nontarget'
				, self.nontarget_loc
				, 'Image Name'
				, self.nontarget_image
				])

		elif self.current_stage == 'Recall':
		
			self.protocol_floatlayout.add_event([
				(self.stimulus_press_time - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Target'
				, 'Recall Location'
				, 'Image Name'
				, self.target_image
				])

		self.feedback_label.text = self.feedback_dict['incorrect']

		self.hold_button.bind(on_press=self.iti)
		self.hold_button.bind(on_release=self.premature_response)

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
		
		self.write_trial()
		self.trial_contingency()

		return
	
	
	
	# Data Saving Function
	
	def write_trial(self, *args):
		
		# print('Write trial')

		if self.current_stage in ['dPAL', 'sPAL']:
			self.nontarget_image_string = self.nontarget_image
			self.nontarget_loc_string = self.nontarget_loc

		else:
			self.nontarget_image_string = 'Mask'
			self.nontarget_loc_string = '-1'

		trial_data = [
			self.current_trial
			, self.current_stage
			, self.current_block
			, self.current_block_trial
			, self.target_image
			, self.target_loc
			, self.nontarget_image_string
			, self.nontarget_loc_string
			, self.last_response
			, self.response_latency
			]
		
		self.write_summary_file(trial_data)
	
	
	
	# Trial Contingency Functions
	
	def trial_contingency(self, *args):
		
		try:

			if self.current_block_trial != 0:
				# print('\n\n\nTrial contingency start\n')
				# print('Current trial: ', self.current_trial)
				# print('Current stage: ', self.current_stage)
				# print('Current block: ', self.current_block)
				# print('Current block trial: ', self.current_block_trial)
				# print('Current task time: ', (time.time() - self.start_time))
				# print('Current block time: ', (time.time() - self.block_start), '\n')
				# print('ITI: ', self.iti_length)
				# print('Start target time: ', (self.stimulus_start_time - self.start_time))
				# print('Response latency: ', self.response_latency)
				# print('Last response: ', self.last_response, '\n')
				# print('Target loc: ', self.target_loc, '\n')
				# print('Target image: ', self.target_image, '\n')

				# if self.current_stage in ['dPAL', 'sPAL']:
					# print('Nontarget loc: ', self.nontarget_loc)
					# print('Nontarget image loc: ', self.nontarget_image_loc)
					# print('Nontarget image: ', self.nontarget_image, '\n')

				# elif self.current_stage == 'Recall':
					# print('Recall prompt: ', self.target_image_list[self.target_loc], '\n')
				
				# print('\n*************\n\n')

				self.response_tracking.append(self.last_response)

				# Check if block ended

				if (self.current_block_trial >= self.block_trial_max) \
					or (time.time() - self.block_start >= self.block_duration):

					# print('Block max duration/trials reached')

					self.iti_event.cancel()

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'State Change'
						, 'Block End'
						])
					
					# self.block_check_event()
					self.stage_screen_event()
				
				elif (self.current_stage == 'Training') \
					and (sum(self.response_tracking) >= self.training_block_max_correct):

					# print('Training block max correct reached')

					self.iti_event.cancel()
					self.hold_button.unbind(on_release=self.premature_response)

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'State Change'
						, 'Block End'
						])
					
					self.hold_button.bind(on_release=self.premature_response)
					
					self.block_check_event()				

				elif (len(self.response_tracking) > 10) \
					and (sum(self.response_tracking[-10:]) >= 6) \
					and not self.block_change_on_duration:

					# print('Criterion accuracy (0.8 or better) reached')
					
					self.iti_event.cancel()

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'State Change'
						, 'Block End'
						])
					
					# self.block_check_event()
					self.stage_screen_event()

				else:
					self.protocol_floatlayout.add_widget(self.hold_button)

			# Set next trial parameters
			
			for stimulus in self.stimulus_grid_list:
				stimulus.bind(on_press=self.target_pressed)
				stimulus.unbind(on_press=self.target_pressed)

				stimulus.bind(on_press=self.nontarget_pressed)
				stimulus.unbind(on_press=self.nontarget_pressed)

			self.current_trial += 1
			self.current_block_trial += 1
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Current Trial'
				, self.current_trial
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Current Block Trial'
				, self.current_block_trial
				])
			
			# Set ITI

			if len(self.iti_range) > 1:
				
				if self.iti_fixed_or_range == 'fixed':
					self.iti_length = random.choice(self.iti_range)
				
				else:
					self.iti_length = round(random.uniform(min(self.iti_range), max(self.iti_range)), 2)
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Parameter'
					, 'Current ITI'
					, self.iti_length
					])

			# Set target/nontarget stimuli

			if self.current_stage == 'Training':
				self.target_loc = random.choice(list(range(self.num_stimuli)))
				self.nontarget_loc = -1
				self.nontarget_image_loc = -1
				
				self.target_image = self.training_image
				self.nontarget_image = self.mask_image
				self.blank_image = self.mask_image
				self.recall_image = self.mask_image

			else:

				if self.trial_list_index >= len(self.trial_list):
					random.shuffle(self.trial_list)
					self.trial_list_index = 0
				
				new_target_loc = self.trial_list[self.trial_list_index]
				self.trial_list_index += 1
				
				if self.current_stage in ['dPAL', 'sPAL']:
					pos_list = list(range(self.num_stimuli))
					pos_list.remove(new_target_loc)
					random.shuffle(pos_list)

					new_nontarget_loc = pos_list[0]
					new_nontarget_image_loc = pos_list[1]

					if (new_target_loc == self.target_loc) \
						and (new_nontarget_loc == self.nontarget_loc):

						new_nontarget_loc = pos_list[1]
						new_nontarget_image_loc = pos_list[0]
					
					if self.current_stage == 'sPAL':
						new_nontarget_image_loc = new_target_loc
				
					self.target_loc = new_target_loc
					self.nontarget_loc = new_nontarget_loc
					self.nontarget_image_loc = new_nontarget_image_loc

					self.target_image = self.target_image_list[self.target_loc]
					self.nontarget_image = self.target_image_list[self.nontarget_image_loc]
					self.blank_image = self.mask_image
					self.recall_image = self.mask_image
				
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Stimulus'
						, self.target_image
						, 'Type'
						, 'Target'
						, 'Location'
						, self.target_loc
						])
				
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Stimulus'
						, self.nontarget_image
						, 'Type'
						, 'Nontarget'
						, 'Location'
						, self.nontarget_loc
						])

				elif self.current_stage == 'Recall':
					self.target_loc = new_target_loc
					self.nontarget_loc = -1
					self.nontarget_image_loc = -1

					self.target_image = self.outline_image
					self.nontarget_image = self.outline_image
					self.blank_image = self.outline_image
					self.recall_image = self.target_image_list[self.target_loc]
				
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Stimulus'
						, self.target_image
						, 'Type'
						, 'Target'
						, 'Location'
						, 'Recall Location'
						])


			for iLoc in list(range(0, self.num_stimuli)):

				if iLoc == self.target_loc:
					self.stimulus_grid_list[iLoc].texture = self.image_dict[self.target_image].image.texture
					self.stimulus_grid_list[iLoc].bind(on_press=self.target_pressed)
				
				elif iLoc == self.nontarget_loc:
					self.stimulus_grid_list[iLoc].texture = self.image_dict[self.nontarget_image].image.texture
					self.stimulus_grid_list[iLoc].bind(on_press=self.nontarget_pressed)
				
				else:
					self.stimulus_grid_list[iLoc].texture = self.image_dict[self.blank_image].image.texture

					if self.current_stage == 'Recall':
						self.stimulus_grid_list[iLoc].bind(on_press=self.nontarget_pressed)

			self.recall_stimulus.texture = self.image_dict[self.recall_image].image.texture
			
			self.last_response = 0
			
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
			, 'Object Remove'
			, 'Text'
			, 'Section'
			, 'Instructions'
			, 'Type'
			, 'Task'
			])
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Remove'
			, 'Button'
			, 'Section'
			, 'Instructions'
			, 'Type'
			, 'Continue'
			])
		
		self.block_end()



	def stage_screen(
		self
		, *args
		):		

		if not self.stage_screen_started:

			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'State Change'
				, 'Section End'
				])

			self.iti_event.cancel()

			self.protocol_floatlayout.clear_widgets()
			self.feedback_on_screen = False

			if len(self.response_tracking) <1:
				self.outcome_string = "Great job!\n\n"
			
			else:
				hit_accuracy = (sum(self.response_tracking)/len(self.response_tracking))
				self.outcome_string = 'Great job!\n\nYour overall accuracy was ' \
					+ str(round(hit_accuracy * 100)) \
					+ '%!'

			if self.stage_index < len(self.stage_list):
				self.stage_string = 'Please press "Continue" to start the next block.'

			else:
				self.stage_string = 'You have completed this task.\n\nPlease inform your researcher.'
			
			stage_text = self.outcome_string + '\n\n' + self.stage_string
			self.stage_results_label.text = stage_text

			self.protocol_floatlayout.add_widget(self.stage_results_label)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Display'
				, 'Text'
				, 'Stage'
				, 'Results'
				])

			self.stage_screen_time = time.time()
			self.stage_screen_started = True
			self.block_started = True

			self.stage_screen_event()


		if (time.time() - self.stage_screen_time) >= 1.0:
			self.stage_screen_event.cancel()
			self.stage_screen_started = False

			if self.stage_index >= (len(self.stage_list)):
				self.session_event.cancel()
				self.stage_continue_button.unbind(on_press=self.block_check_event)
				self.stage_continue_button.bind(on_press=self.protocol_end)
				self.stage_continue_button.text = 'End Task'
			
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'State Change'
					, 'Task End'
					])

			self.protocol_floatlayout.add_widget(self.stage_continue_button)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Display'
				, 'Button'
				, 'Stage'
				, 'Continue'
				])
	


	def recall_target_screen(self, *args):

		if not self.recall_instruction_target_display_started:

			for stimulus in self.stimulus_grid_list:
				stimulus.bind(on_press=self.target_pressed)
				stimulus.unbind(on_press=self.target_pressed)

				stimulus.bind(on_press=self.nontarget_pressed)
				stimulus.unbind(on_press=self.nontarget_pressed)

			self.protocol_floatlayout.clear_widgets()

			self.stimulus_grid_list[0].texture = self.image_dict[self.target_image_list[0]].image.texture

			for stimulus in self.stimulus_grid_list:
				self.protocol_floatlayout.add_widget(stimulus)
			
			self.recall_target_screen_start_time = time.time()
			self.recall_instruction_target_display_started = True
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'State Change'
				, 'Object Display'
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Display'
				, 'Stimulus'
				, 'Recall Target'
				, '0'
				, 'Image Name'
				, self.target_image_list[0]
				])


		if (time.time() - self.recall_target_screen_start_time) >= self.recall_target_present_duration:
			self.recall_instruction_target_present_event.cancel()

			if self.recall_target_display_pos < self.num_stimuli:
				self.protocol_floatlayout.remove_widget(self.stimulus_grid_list[self.recall_target_display_pos])
				self.stimulus_grid_list[self.recall_target_display_pos].texture = self.image_dict[self.outline_image].image.texture
				self.protocol_floatlayout.add_widget(self.stimulus_grid_list[self.recall_target_display_pos])
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Object Remove'
					, 'Stimulus'
					, 'Recall Target'
					, self.recall_target_display_pos
					, 'Image Name'
					, self.target_image_list[self.recall_target_display_pos]
					])

				self.recall_target_display_pos += 1

			if self.recall_target_display_pos == self.num_stimuli:

				for iLoc in list(range(0, self.num_stimuli)):
					self.protocol_floatlayout.remove_widget(self.stimulus_grid_list[iLoc])
					self.stimulus_grid_list[iLoc].texture = self.image_dict[self.target_image_list[iLoc]].image.texture
					self.protocol_floatlayout.add_widget(self.stimulus_grid_list[iLoc])

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Object Display'
						, 'Stimulus'
						, 'Recall Target'
						, iLoc
						, 'Image Name'
						, self.target_image_list[iLoc]
						])
				
				self.recall_target_display_pos += 1
				self.recall_target_screen_start_time = time.time()
				self.recall_instruction_target_present_event()

			elif self.recall_target_display_pos > self.num_stimuli:

				for iLoc in list(range(0, self.num_stimuli)):
					self.protocol_floatlayout.remove_widget(self.stimulus_grid_list[iLoc])
					self.stimulus_grid_list[iLoc].texture = self.image_dict[self.outline_image].image.texture

					if iLoc == self.target_loc:
						self.stimulus_grid_list[iLoc].bind(on_press=self.target_pressed)
					
					else:
						self.stimulus_grid_list[iLoc].bind(on_press=self.nontarget_pressed)

					self.protocol_floatlayout.add_widget(self.stimulus_grid_list[iLoc])

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Object Remove'
						, 'Stimulus'
						, 'Recall Target'
						, iLoc
						, 'Image Name'
						, self.target_image_list[iLoc]
						])

				self.hold_button.bind(on_press=self.iti)
				self.section_start()

			else:
				self.protocol_floatlayout.remove_widget(self.stimulus_grid_list[self.recall_target_display_pos])
				self.stimulus_grid_list[self.recall_target_display_pos].texture = self.image_dict[self.target_image_list[self.recall_target_display_pos]].image.texture
				self.protocol_floatlayout.add_widget(self.stimulus_grid_list[self.recall_target_display_pos])
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Object Display'
					, 'Stimulus'
					, 'Recall Target'
					, self.recall_target_display_pos
					, 'Image Name'
					, self.target_image_list[self.recall_target_display_pos]
					])

				self.recall_target_screen_start_time = time.time()
				self.recall_instruction_target_present_event()

		else:
			self.recall_instruction_target_present_event()
	


	def start_recall_block(self, *args):

		self.hold_button.unbind(on_press=self.start_recall_block)
		self.hold_button.bind(on_press=self.iti)

		self.protocol_floatlayout.remove_widget(self.hold_button)

		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Section Start'
			])

		self.trial_contingency()		
		self.iti()



	def present_tutorial_video(self, *args):

		self.protocol_floatlayout.clear_widgets()
		self.block_started = True

		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Object Display'
			])

		if self.current_stage == 'Recall':
			self.tutorial_video.source = self.tutorial_video_PA_path
			self.tutorial_video_duration = self.tutorial_video_duration_PA
		
		else:
			self.tutorial_video.source = self.tutorial_video_PAL_path
			self.tutorial_video_duration = self.tutorial_video_duration_PAL

		self.tutorial_video.state = 'stop'
		self.tutorial_video._video = None
		self.tutorial_video.reload()
		
		self.tutorial_start_button = Button(text='START TASK', font_size='48sp')
		self.tutorial_start_button.size_hint = self.text_button_size
		self.tutorial_start_button.pos_hint = self.text_button_pos_LR
		self.tutorial_start_button.bind(on_press=self.start_protocol_from_tutorial_video)
		
		self.tutorial_restart = Button(text='RESTART VIDEO', font_size='48sp')
		self.tutorial_restart.size_hint = self.text_button_size
		self.tutorial_restart.pos_hint = self.text_button_pos_LL
		self.tutorial_restart.bind(on_press=self.start_tutorial_video)
		
		self.tutorial_video_button = Button(text='TAP THE SCREEN\nTO START VIDEO', font_size='48sp', halign='center', valign='center')
		self.tutorial_video_button.background_color = 'black'
		self.tutorial_video_button.size_hint = (1, 1)
		self.tutorial_video_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
		self.tutorial_video_button.bind(on_press=self.start_tutorial_video)
				
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Display'
			, 'Video'
			, 'Section'
			, self.tutorial_video.source
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
	
	
	
	def start_protocol_from_tutorial_video(self, *args):

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

		if self.stage_index == 0:
			self.start_clock()
		
		self.block_start = time.time()

		self.hold_button.bind(on_press=self.iti)

		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Section Start'
			])

		if self.current_stage == 'Recall':
			self.recall_instruction_target_present_event()

		else:
			self.block_started = False
			self.trial_contingency()


	
	# Block Contingency Function
	
	def block_contingency(self, *args):
		
		try:

			self.iti_event.cancel()

			self.block_started = True
			
			self.hold_button.unbind(on_press=self.iti)
			self.hold_button.unbind(on_release=self.premature_response)

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
			self.feedback_label.text = ''
			# print('Clear widgets')
		
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'State Change'
				, 'Block Contingency'
				])

			self.protocol_floatlayout.clear_widgets()
		
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'State Change'
				, 'Screen Cleared'
				])

			self.current_block += 1
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'State Change'
				, 'Block Change'
				, 'Current Block'
				, self.current_block
				])
			
			# print('Current block: ', self.current_block)
			
			if (self.current_block > self.block_multiplier) or (self.current_block == -1):
				self.stage_index += 1
				self.current_block = 1
				# print('Stage index: ', self.stage_index)

			if self.stage_index >= len(self.stage_list): # Check if all stages complete
				# print('All stages complete')
			
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'State Change'
					, 'Task End'
					])
				
				self.session_event.cancel()
				self.protocol_end()
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


			if self.current_stage in ['Training', 'dPAL', 'sPAL']:
				self.num_stimuli = self.num_stimuli_pal
				self.target_image_list = self.target_image_list_pal
				self.trial_list = self.trial_list_pal

				if self.current_stage == 'dPAL':
					self.block_trial_max = self.dpal_trial_max

				elif self.current_stage == 'sPAL':
					self.block_trial_max = self.spal_trial_max

			elif self.current_stage == 'Recall':
				self.num_stimuli = self.num_stimuli_pa
				self.target_image_list = self.target_image_list_pa

				self.trial_list = self.trial_list_pa
				self.block_trial_max = self.recall_trial_max
				
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Stimulus Number'
				, self.current_stage
				, 'Value'
				, self.num_stimuli
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Target Image List'
				, self.current_stage
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Trial List'
				, self.current_stage
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Block Trial Max'
				, self.current_stage
				])
			
			self.stimulus_x_loc = np.linspace(min(self.stimulus_x_boundaries), max(self.stimulus_x_boundaries), int(self.num_stimuli)).tolist()

			self.stimulus_grid_list = self.generate_stimulus_grid(
				self.stimulus_x_loc
				, self.num_rows
				, grid_gap = 0.1
				)

			for stimulus in self.stimulus_grid_list:
				stimulus.bind(on_press=self.target_pressed)
				stimulus.unbind(on_press=self.target_pressed)
				stimulus.bind(on_press=self.nontarget_pressed)
				stimulus.unbind(on_press=self.nontarget_pressed)

			random.shuffle(self.trial_list)
			self.target_loc = self.trial_list[0]
			
			pos_list = list(range(self.num_stimuli))
			pos_list.remove(self.target_loc)
			random.shuffle(pos_list)

			self.nontarget_loc = pos_list[0]
			self.nontarget_image_loc = pos_list[1]

			self.response_tracking = list()
			self.last_response = 0
			self.current_block_trial = 0

			# print('Block contingency end')
			
			if self.current_block == 1: #and self.display_instructions:
				self.block_max_length = 360
				
				if self.current_stage == 'Training':
					self.block_max_length = self.training_block_max_correct

				if pathlib.Path('Protocol', self.protocol_name, 'Language', self.language, 'Tutorial_Video').is_dir() \
					and (self.skip_tutorial_video == 0) \
					and (self.current_stage != 'sPAL'):

					# print('Section Instruction Video')

					if self.current_stage == 'dPAL':
						self.tutorial_video.source = self.tutorial_video_PAL_path
					
					else:
						self.tutorial_video.source = self.tutorial_video_PA_path

					self.protocol_floatlayout.clear_widgets()
					self.present_tutorial_video()
				
				elif not pathlib.Path('Protocol', self.protocol_name, 'Language', self.language, 'Tutorial_Video').is_dir():
					# print('Section Task Instructions')
					self.section_instr_label.text = self.instruction_dict[str(self.current_stage)]['task']
					self.instruction_button.text = 'Start Section'

					if self.current_stage == 'Recall':
						self.instruction_button.unbind(on_press=self.section_start)
						self.instruction_button.bind(on_press=self.recall_instruction_target_present_event)
						self.instruction_button.text = 'See Image Locations'
					
					self.protocol_floatlayout.add_widget(self.section_instr_label)
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
					self.block_started = False
					self.block_event()
			
			else:
				# print('Else: Block Screen')
				self.block_started = False
				self.block_event()

			self.trial_contingency()
		
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()