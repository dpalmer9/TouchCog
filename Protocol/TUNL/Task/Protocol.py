# Imports #

import configparser
import numpy as np
import os
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
		
		self.protocol_name = 'TUNL'
		self.name = self.protocol_name + '_protocolscreen'
		self.update_task()

		# Define Data Columns
		
		self.data_cols = [
			'TrialNo'
			, 'Current Block'
			, 'Probe Type'
			, 'Separation'
			, 'Delay'
			, 'Video Time'
			, 'Cue_X'
			, 'Cue_Y'
			, 'Target_X'
			, 'Target_Y'
			, 'Correct'
			, 'Target Latency'
			]
		
		self.metadata_cols = [
			'participant_id'
			, 'skip_tutorial_video'
			, 'block_change_on_duration_only'
			, 'iti_length'
			, 'iti_fixed_or_range'
			, 'feedback_length'
			, 'block_duration'
			, 'block_multiplier'
			, 'session_length_max'
			, 'screen_x_padding'
			, 'screen_y_padding_top'
			, 'screen_y_padding_bottom'
			, 'stimulus_gap'
			, 'x_boundaries'
			, 'y_boundaries'
			, 'stimulus_image'
			, 'distractor_video'
			, 'staircase_sep_initial'
			, 'staircase_delay_initial'
			, 'minimum_sep'
			, 'minimum_delay'
			, 'space_probe_sep_list'
			, 'delay_probe_delay_list'
			]
		
		
		# Define Variables - Config
		
		self.config_path = pathlib.Path('Protocol', self.protocol_name, 'Configuration.ini')
		self.config_file = configparser.ConfigParser()
		self.config_file.read(self.config_path)

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
		
		self.stimdur_import = self.parameters_dict['stimulus_duration']
		self.stimdur_import = self.stimdur_import.split(',')
		
		self.limhold_import = self.parameters_dict['limited_hold']
		self.limhold_import = self.limhold_import.split(',')
		
		self.feedback_length = float(self.parameters_dict['feedback_length'])
		self.block_duration = float(self.parameters_dict['block_duration'])
		self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
		self.session_duration = float(self.parameters_dict['session_length_max'])
		
		self.block_multiplier = int(self.parameters_dict['block_multiplier'])

		self.stimulus_scale = float(self.parameters_dict['stimulus_scale'])
		
		self.screen_x_padding = int(self.parameters_dict['screen_x_padding'])
		self.screen_y_padding_t = int(self.parameters_dict['screen_y_padding_top'])
		self.screen_y_padding_b = int(self.parameters_dict['screen_y_padding_bottom'])

		self.stimulus_gap = float(self.parameters_dict['stimulus_gap'])
		
		self.x_boundaries = self.parameters_dict['x_boundaries']
		self.x_boundaries = self.x_boundaries.split(',')

		self.y_boundaries = self.parameters_dict['y_boundaries']
		self.y_boundaries = self.y_boundaries.split(',')

		self.stimulus_image = self.parameters_dict['stimulus_image']
		self.stimulus_button_image = self.parameters_dict['stimulus_button_image']
		self.distractor_video = self.parameters_dict['distractor_video']

		self.staircase_sep_initial = int(self.parameters_dict['staircase_sep_initial'])
		self.staircase_delay_initial = float(self.parameters_dict['staircase_delay_initial'])
		
		self.min_sep = int(self.parameters_dict['minimum_sep'])
		self.max_sep = int(self.parameters_dict['maximum_sep'])
		self.min_delay = float(self.parameters_dict['minimum_delay'])
		self.max_delay = float(self.parameters_dict['maximum_delay'])
		
		self.space_probe_sep_list = self.parameters_dict['space_probe_sep_list']
		self.space_probe_sep_list = self.space_probe_sep_list.split(',')

		self.delay_probe_delay_list = self.parameters_dict['delay_probe_delay_list']
		self.delay_probe_delay_list = self.delay_probe_delay_list.split(',')

		self.hold_image = self.config_file['Hold']['hold_image']

		# Create stage list
		
		self.stage_list = list()
		
		if self.parameters_dict['space_probe']:
			self.stage_list.append('Space')

		if self.parameters_dict['delay_probe']:
			self.stage_list.append('Delay')
		
		if len(self.stage_list) > 1:
			self.stage_list = self.constrained_shuffle(self.stage_list)

		if self.parameters_dict['combined_probe']:
			self.stage_list.append('Combo')

	def _load_task_variables(self):
		# Define Variables - Time

		self.frame_duration = 0
		self.cue_start_time = 0.0
		self.target_start_time = 0.0
		self.response_latency = 0.0
		self.current_delay = 0.0
		self.video_start_time = 0.0
		self.video_end_time = 0.0
		self.video_position = 0.0
		self.trial_end_time = 0.0

		# Define Boolean
		
		self.hold_active = False
		self.cue_completed = False
		self.cue_on_screen = False
		self.target_on_screen = False
		self.video_on_screen = False
		self.limhold_started = False
		self.delay_active = False
		self.delay_ended = False

		# Define Variables - Numeric
		self.stage_index = -1
		self.trial_index = 0
		self.combo_trial_index = 0
		self.current_sep = 0		
		self.current_block = 1
		self.current_block_trial = 0
		self.max_blocks = len(self.stage_list) * self.block_multiplier
		self.last_response = 0

		# Define Variables - List
		self.response_tracking = list()
		self.accuracy_tracking = list()

		# Define String

		self.staircase_change = 'non'
		self.section_instr_string = ''
		self.current_stage = self.stage_list[self.stage_index]

	def _setup_session_stages(self):
		self.space_probe_sep_list = [int(iNum) for iNum in self.space_probe_sep_list]
		self.delay_probe_delay_list = [float(iNum) for iNum in self.delay_probe_delay_list]
		self.combo_probe_sep_list = [int(iNum) for iNum in self.space_probe_sep_list]
		self.combo_probe_sep_list.sort(reverse=True)

		self.space_probe_delay_list = [self.staircase_delay_initial for iElem in self.space_probe_sep_list]
		self.space_probe_staircase_list = [self.staircase_delay_initial for iElem in self.space_probe_sep_list]
		self.delay_probe_sep_list = [self.staircase_sep_initial for iElem in self.delay_probe_delay_list]
		self.combo_probe_delay_list = [self.staircase_delay_initial for iElem in self.space_probe_sep_list]
		self.combo_probe_staircase_list = [self.staircase_delay_initial for iElem in self.space_probe_sep_list]

		self.space_probe_response_list = [0 for iElem in self.space_probe_sep_list]
		self.delay_probe_response_list = [0 for iElem in self.delay_probe_delay_list]
		self.combo_probe_response_list = [0 for iElem in self.combo_probe_sep_list]

		self.combo_probe_delay_tracking_dict = {}
		
		for iSep in self.combo_probe_sep_list:
			self.combo_probe_delay_tracking_dict[iSep] = [0,0]

		self.space_trial_index_list = list(range(0, len(self.space_probe_sep_list)))
		self.delay_trial_index_list = list(range(0, len(self.delay_probe_delay_list)))
		self.space_trial_index = self.space_trial_index_list[0]
		self.delay_trial_index = self.delay_trial_index_list[0]

		self.space_trial_index_list = self.constrained_shuffle(self.space_trial_index_list)
		self.delay_trial_index_list = self.constrained_shuffle(self.delay_trial_index_list)

		self.last_staircase_time_increase = self.staircase_delay_initial

		self.combo_probe_max_section_dur = self.block_duration // 3
		
		self.iti_range = [float(iNum) for iNum in self.iti_import]
		self.iti_length = self.iti_range[0]
		
		self.stimdur_list = [float(iNum) for iNum in self.stimdur_import]
		self.limhold_list = [float(iNum) for iNum in self.limhold_import]

		self.stimdur = self.stimdur_list[0]
		self.limhold = self.limhold_list[0]

		if self.current_stage == 'Space':
			self.current_sep = self.space_probe_sep_list[self.space_trial_index]
			self.current_delay = self.space_probe_delay_list[self.space_trial_index]
		
		elif self.current_stage == 'Delay':
			self.current_sep = self.delay_probe_sep_list[self.delay_trial_index]
			self.current_delay = self.delay_probe_delay_list[self.delay_trial_index]
		
		elif self.current_stage == 'Combo':
			self.current_sep = self.combo_probe_sep_list[self.combo_trial_index]
			self.current_delay = self.combo_probe_delay_list[self.combo_trial_index]
		


	def _setup_image_widgets(self):
		self.image_folder = pathlib.Path('Protocol', self.protocol_name, 'Image')
		self.stimulus_image_path = str(self.image_folder / (self.stimulus_image + '.png'))
		self.stimulus_button_image_path = str(self.image_folder / (self.stimulus_button_image + '.png'))
		hold_button_top_loc = self.hold_button.pos_hint['center_y'] + (self.hold_button.size_hint[1]/2)

		self.x_boundaries = [float(iNum) for iNum in self.x_boundaries]
		self.y_boundaries = [float(iNum) for iNum in self.y_boundaries]
		if self.y_boundaries[0] < hold_button_top_loc:
			self.y_boundaries[0] = hold_button_top_loc
		
		elif self.y_boundaries[1] < hold_button_top_loc:
			self.y_boundaries[1] = hold_button_top_loc

		self.cue_image = ImageButton(source=self.stimulus_image_path)
		self.target_image = ImageButton(source=self.stimulus_image_path)
		
		self.stimulus_image_spacing = [
			((self.cue_image.texture_size[0]/self.screen_resolution[0]) * self.stimulus_scale)
			, ((self.cue_image.texture_size[1]/self.screen_resolution[1]) * self.stimulus_scale)
			]
		
		self.stimulus_image_size = (np.array(self.stimulus_image_spacing) * (1 - self.stimulus_gap)).tolist()
		self.stimulus_button_size = (np.array(self.stimulus_image_size) * 0.77).tolist()

		# Define Widgets - Buttons
		
		self.hold_button.source = str(self.image_folder / (self.hold_image + '.png'))
		self.hold_button.bind(on_press=self.iti_start)
				

		self.cue_image_button = ImageButton(source=self.stimulus_button_image_path)
		self.cue_image_button.bind(on_press=self.cue_pressed)
		self.target_image_button = ImageButton(source=self.stimulus_button_image_path)
		self.target_image_button.bind(on_press=self.target_pressed)

		self.cue_image.size_hint = self.stimulus_image_size
		self.target_image.size_hint = self.stimulus_image_size

		self.cue_image_button.size_hint = self.stimulus_button_size
		self.cue_image_button.bind(on_press=self.cue_pressed)
		self.cue_image_button.name = 'Cue Image'

		self.target_image_button.size_hint = self.stimulus_button_size
		self.target_image_button.bind(on_press=self.target_pressed)
		self.target_image_button.name = 'Target Image'

		self.text_button_size = [0.4, 0.15]
		self.text_button_pos_LL = {"center_x": 0.25, "center_y": 0.08}
		self.text_button_pos_LR = {"center_x": 0.75, "center_y": 0.08}

		self.trial_coord = self.generate_trial_pos_sep(
			self.x_boundaries
			, self.y_boundaries
			, self.current_sep
			, self.stimulus_image_spacing
			, self.screen_x_padding
			, self.screen_y_padding_t
			, self.screen_y_padding_b
			)
		
		self.cue_image.pos_hint = {
			"center_x": self.trial_coord['Cue']['x'], 
			"center_y": self.trial_coord['Cue']['y']
			}
		
		self.target_image.pos_hint = {
			"center_x": self.trial_coord['Target']['x'], 
			"center_y": self.trial_coord['Target']['y']
			}
		
		self.cue_image_button.pos_hint = {
			"center_x": self.trial_coord['Cue']['x'], 
			"center_y": self.trial_coord['Cue']['y']
			}
		
		self.target_image_button.pos_hint = {
			"center_x": self.trial_coord['Target']['x'], 
			"center_y": self.trial_coord['Target']['y']
			}
		
	def _setup_language_localization(self):
		self.set_language(self.language)

	def _load_video_and_instruction_components(self):
		self.video_size = (1, 1)
		self.video_pos = {"center_x": 0.5, "y": 0.125}
		self.lang_folder_path = pathlib.Path('Protocol', self.protocol_name, 'Language', self.language)

		self.delay_video_folder = pathlib.Path('Delay_Videos')

		if self.distractor_video == '':
			self.delay_video_path_list = list(self.image_folder.glob(str(self.delay_video_folder / '*.mp4')))
		
		else:
			self.delay_video_path_list = list(self.image_folder.glob(str(self.delay_video_folder / self.distractor_video)))
			
			if len(self.delay_video_path_list) == 0:
				self.delay_video_path_list = list(self.image_folder.glob(str(self.delay_video_folder / '*.mp4')))
		
		
		if len(self.delay_video_path_list) > 1:
			self.delay_video_path = random.choice(self.delay_video_path_list)
			self.delay_video_path_list.remove(self.delay_video_path)
		
		else:
			self.delay_video_path = self.delay_video_path_list[0]

		self.delay_video = Video(source = str(self.delay_video_path), options = {'eos': 'loop'})
		self.delay_video.fit_mode = 'fill'
		self.delay_video.state = 'stop'
		self.protocol_floatlayout.add_widget(self.delay_video)
		self.delay_video.state = 'pause'
		self.protocol_floatlayout.remove_widget(self.delay_video)

		if (self.lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_path = str(list((self.lang_folder_path / 'Tutorial_Video').glob('*.mp4'))[0])

			self.tutorial_video = Video(source = self.tutorial_video_path)
			self.tutorial_video.fit_mode = 'fill'

			self.tutorial_video.pos_hint = {'center_x': 0.5, 'center_y': 0.6}
			self.tutorial_video.size_hint = (1, 1)
		self.delay_video.pos_hint = self.video_pos
		self.delay_video.size_hint = self.video_size


		# Instruction - Dictionary
		
		self.instruction_path = str(self.lang_folder_path / 'Instructions.ini')
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Training'] = {}
		self.instruction_dict['Space'] = {}
		self.instruction_dict['Delay'] = {}
		self.instruction_dict['Combo'] = {}
		
		for stage in self.stage_list:
			self.instruction_dict[stage]['train'] = self.instruction_config[stage]['train']
			self.instruction_dict[stage]['task'] = self.instruction_config[stage]['task']
		
		
		# Instruction - Text Widget
		
		self.section_instr_string = self.instruction_label.text
		self.section_instr_label = Label(text=self.section_instr_string, font_size='44sp', markup=True)
		self.section_instr_label.size_hint = {0.58, 0.4}
		self.section_instr_label.pos_hint = {'center_x': 0.5, 'center_y': 0.35}
		
		# Instruction - Button Widget
		
		self.instruction_button = Button(font_size='60sp')
		self.instruction_button.size_hint = self.text_button_size
		self.instruction_button.pos_hint =  {"center_x": 0.50, "center_y": 0.92}
		self.instruction_button.text = ''
		self.instruction_button.bind(on_press=self.section_start)
		
		
		# Define Widgets - Labels
		
		self.feedback_label.size_hint = (0.7, 0.3)
		self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.55}


		# Instruction - Dictionary
		
		self.instruction_path = str(pathlib.Path('Protocol', self.protocol_name, 'Language', self.language, 'Instructions.ini'))
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Training'] = {}
		self.instruction_dict['Space'] = {}
		self.instruction_dict['Delay'] = {}
		self.instruction_dict['Combo'] = {}
		
		for stage in self.stage_list:
			self.instruction_dict[stage]['train'] = self.instruction_config[stage]['train']
			self.instruction_dict[stage]['task'] = self.instruction_config[stage]['task']		
		
		# Instruction - Button Widget
		
		self.instruction_button = Button()
		self.instruction_button.bind(on_press=self.section_start)
	
	def _check_delay_video_loaded(self, *args):
		if self.delay_video.loaded:
			Clock.unschedule(self._check_delay_video_loaded)
			self.delay_video.state = 'pause'
			self.protocol_floatlayout.remove_widget(self.feedback_label)
			self.feedback_label.text = ''

			if (self.lang_folder_path / 'Tutorial_Video').is_dir() \
			and not self.skip_tutorial_video:

				self.protocol_floatlayout.clear_widgets()
				self.present_tutorial_video()
		
			else:
				self.present_instructions()
		else:
			pass
	
	# Initialization Functions
	
	def load_parameters(self, parameter_dict):
		self._load_config_parameters(parameter_dict)
		self._load_task_variables()
		self._setup_session_stages()
		self._setup_image_widgets()
		self._setup_language_localization()
		self._load_video_and_instruction_components()

		

		# Begin Task
		self.start_clock()
		self.feedback_label.text = 'LOADING VIDEO... PLEASE WAIT'
		self.protocol_floatlayout.add_widget(self.feedback_label)
		self.delay_video.state = 'play'
		Clock.schedule_interval(self._check_delay_video_loaded, 0.5)



	def generate_trial_pos_sep(
		self
		, x_boundaries = [0, 1]
		, y_boundaries = [0.1, 1]
		, sep_level = 0
		, stimulus_size = [0.066, 0.1]
		, x_padding = 0
		, y_padding_t = 0
		, y_padding_b = 0
		):

		x_lim = [
			min(x_boundaries) + stimulus_size[0]*(x_padding + 0.5)
			, max(x_boundaries) - stimulus_size[0]*(x_padding + 0.5)
			]
		
		y_lim = [
			min(y_boundaries) + stimulus_size[1]*(y_padding_b + 0.5)
			, max(y_boundaries) - stimulus_size[1]*(y_padding_t + 0.5)
			]

		main_move = float(sep_level) + 1
		
		cue_xpos = random.uniform(min(x_lim), max(x_lim))
		cue_ypos = random.uniform(min(y_lim), max(y_lim))
		
		horz_dist = random.uniform(-main_move, main_move)
		horz_move = horz_dist * stimulus_size[0]
		
		target_xpos = cue_xpos + horz_move

		vert_dist = float(np.sqrt(main_move**2 - horz_dist**2))
		vert_move = (random.choice([-vert_dist, vert_dist])) * stimulus_size[1]
		
		target_ypos = cue_ypos + vert_move
		
		while (target_xpos < min(x_lim)) \
			or (target_xpos > max(x_lim)) \
			or (target_ypos < min(y_lim)) \
			or (target_ypos > max(y_lim)):

			if (target_xpos < min(x_lim)) \
				or (target_xpos > max(x_lim)):

				horz_move *= -1
			

			if (target_ypos < min(y_lim)) \
				or (target_ypos > max(y_lim)):

				vert_move *= -1

			target_xpos = cue_xpos + horz_move
			target_ypos = cue_ypos + vert_move

			if (target_xpos < min(x_lim)) \
				or (target_xpos > max(x_lim)) \
				or (target_ypos < min(y_lim)) \
				or (target_ypos > max(y_lim)):

				horz_dist = random.uniform(-main_move, main_move)
				horz_move = horz_dist * stimulus_size[0]
				target_xpos = cue_xpos + horz_move

				vert_dist = float(np.sqrt(main_move**2 - horz_dist**2))
				vert_move = (random.choice([-vert_dist, vert_dist])) * stimulus_size[1]
				target_ypos = cue_ypos + vert_move

		cue_coord = {'x': round(cue_xpos, 4), 'y': round(cue_ypos, 4)}
		target_coord = {'x': round(target_xpos, 4), 'y': round(target_ypos, 4)}
		trial_coord = {'Cue': cue_coord, 'Target': target_coord}
		
		return trial_coord


	# Protocol Staging

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
			
		self.protocol_floatlayout.add_stage_event('Object Display')

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
				
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Instructions', 'Section Start')
				
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Instructions', 'Video Restart')
	
	
	
	def start_protocol_from_tutorial(self, *args):
		self.tutorial_video.state = 'stop'
		
		self.generate_output_files()
		self.metadata_output_generation()

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_object_event('Remove', 'Video', 'Section', 'Instructions')
		self.protocol_floatlayout.add_stage_event('Section Start')
		self.protocol_floatlayout.add_stage_event('Instruction Presentation')
		self.protocol_floatlayout.add_text_event('Removed', 'Task Instruction')
		self.protocol_floatlayout.add_button_event('Removed', 'Task Start Button')
		self.protocol_floatlayout.add_button_event('Displayed', 'Hold Button')

		self.protocol_floatlayout.add_widget(self.hold_button)
		
		self.block_start_time = time.perf_counter()
		self.trial_end_time = time.perf_counter()
		
		self.feedback_label.text = ''

	def section_start(self, *args):

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_stage_event('Section Start')
		
		self.protocol_floatlayout.add_object_event('Remove', 'Text', 'Section', 'Instructions')
		
		self.protocol_floatlayout.add_button_event('Remove', 'Button', 'Continue')
		
		self.block_end()
	


	def results_screen(self, *args):
		
		Clock.unschedule(self.iti_end)
		
		self.protocol_floatlayout.clear_widgets()
		self.feedback_on_screen = False
		self.feedback_label.text = ''

		if len(self.accuracy_tracking) == 0:
			self.outcome_string = 'Great job!\n\nPlease inform the researcher that you have finished this task.'
		
		else:
			self.hit_accuracy = sum(self.accuracy_tracking) / len(self.accuracy_tracking)
			
			self.outcome_string = 'Great job!\n\nYour overall accuracy was ' \
				+ str(round(self.hit_accuracy * 100)) \
				+ '%!\n\nPlease inform the researcher that you have finished this task.'
		
		self.instruction_button.unbind(on_press=self.section_start)
		self.instruction_button.bind(on_press=self.protocol_end)
		self.instruction_button.text = 'End Task'

		self.section_instr_label.text = self.outcome_string

		self.protocol_floatlayout.add_widget(self.section_instr_label)
		self.protocol_floatlayout.add_widget(self.instruction_button)
		
		self.protocol_floatlayout.add_text_event('Display', 'Text', 'Results')

		self.protocol_floatlayout.add_button_event('Display', 'Button', 'Continue')



	def cue_present(self, *args): # Present cue
		self.hold_button.unbind(on_press=self.iti_start)
		self.hold_button.unbind(on_release=self.premature_response)

		self.hold_button.bind(on_release=self.hold_released)
		
		self.cue_image_button.unbind(on_press=self.cue_pressed)
		
		self.protocol_floatlayout.add_widget(self.cue_image)
		self.protocol_floatlayout.add_widget(self.cue_image_button)
		
		self.stimulus_on_screen = True
		self.cue_completed = True
		self.delay_active = False
		self.delay_ended = False
		self.limhold_started = False
		
		self.cue_start_time = time.perf_counter()
		
		self.protocol_floatlayout.add_stage_event('Cue Display')
		
		self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Cue Image',self.cue_image.pos_hint)

		Clock.schedule_once(self.delay_present, self.stimdur)
	


	# Display Distractor During Delay
	
	def delay_present(self, *args):
		self.protocol_floatlayout.clear_widgets()
		self.protocol_floatlayout.add_widget(self.hold_button)
		
		self.protocol_floatlayout.add_stage_event('Delay Start')

		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Cue Image', self.cue_image.pos_hint)

		self.delay_end_event = Clock.schedule_once(self.delay_end, self.current_delay)

		self.protocol_floatlayout.add_widget(self.delay_video)
		self.delay_video.state = 'play'

		self.video_start_time = time.perf_counter()

		self.delay_active = True

		self.protocol_floatlayout.add_stage_event('Object Display')

		self.protocol_floatlayout.add_object_event('Display', 'Video', str(self.delay_video.source), self.video_position)



	# Display Distractor During Delay
	
	def delay_end(self, *args):
		self.delay_video.state = 'pause'

		self.protocol_floatlayout.clear_widgets()

		self.video_end_time = time.perf_counter()
		self.video_time = self.video_end_time - self.video_start_time
		self.video_position += self.video_time

		self.delay_ended = True
		self.delay_active = False
		
		self.protocol_floatlayout.add_stage_event('Delay End')

		self.protocol_floatlayout.add_stage_event('Object Remove')

		self.protocol_floatlayout.add_object_event('Remove', 'Video', str(self.delay_video.source), self.video_position)

		self.target_present()
	
	
	
	def target_present(self, *args): # Present stimulus
		
		self.hold_button.unbind(on_release=self.hold_released)

		self.cue_image_button.bind(on_press=self.cue_pressed)
		
		self.protocol_floatlayout.add_widget(self.cue_image)
		self.protocol_floatlayout.add_widget(self.target_image)
		self.protocol_floatlayout.add_widget(self.cue_image_button)
		self.protocol_floatlayout.add_widget(self.target_image_button)
		
		self.target_start_time = time.perf_counter()
		
		self.stimulus_on_screen = True
		self.limhold_started = True
		self.cue_completed = False
		self.hold_active = False
		
		self.feedback_label.text = ''
		
		self.protocol_floatlayout.add_stage_event('Target Display')
		
		self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Cue Image', self.cue_image.pos_hint)
		
		self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Target Image', self.target_image.pos_hint)
			
		if self.limhold > self.stimdur:
			Clock.schedule_once(self.stimulus_presentation_end, self.stimdur)
		Clock.schedule_once(self.no_response, self.limhold)
	
	
	
	def stimulus_presentation(self, *args): # Stimulus presentation
		self.cue_present()
		return

	def stimulus_presentation_end(self, *args):
		self.protocol_floatlayout.remove_widget(self.cue_image)
		self.protocol_floatlayout.remove_widget(self.target_image)
		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Cue Image', self.cue_image.pos_hint)

		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Target Image', self.target_image.pos_hint)

	def hold_released(self, *args):
		Clock.unschedule(self.delay_present)
		Clock.unschedule(self.delay_end)
		
		self.protocol_floatlayout.clear_widgets()

		self.hold_button.unbind(on_release=self.hold_released)

		self.hold_active = False

		if self.stimulus_on_screen \
			and not self.cue_completed:

			return
		
		self.protocol_floatlayout.add_stage_event('Hold Released')
		
		self.protocol_floatlayout.add_stage_event('Trial Aborted')
		
		if self.stimulus_on_screen \
			and self.cue_completed:

			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Cue Image', self.cue_image.pos_hint)

		elif self.delay_active:
			self.delay_video.state = 'pause'

			self.video_end_time = time.perf_counter()
			self.video_time = self.video_end_time - self.video_start_time
			self.video_position += self.video_time

			self.protocol_floatlayout.add_object_event('Remove', 'Video', str(self.delay_video.source), self.video_position)

		self.feedback_label.text = self.feedback_dict['abort']

		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.bind(on_release=self.premature_response)

		self.protocol_floatlayout.add_widget(self.hold_button)

		if self.feedback_on_screen is False:	
			self.protocol_floatlayout.add_widget(self.feedback_label)
			self.feedback_on_screen = True
			self.feedback_start_time = time.perf_counter()

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback', self.feedback_label.text)
		
		self.stimulus_on_screen = False
		self.cue_completed = False
		self.delay_active = False
		self.delay_ended = False
		self.limhold_started = False
		
		self.last_response = np.nan
		self.response_latency = np.nan
		
		self.write_trial()
		self.trial_contingency()
		
		return



	# Hold released too early
	
	def premature_response(self, *args):
		
		if self.stimulus_on_screen is True:
			return
	
		self.hold_active = False
		Clock.unschedule(self.iti_end)
		
		self.protocol_floatlayout.add_stage_event('Premature Response')

		self.last_response = np.nan
		self.response_latency = np.nan
		self.iti_active = False
		self.feedback_label.text = self.feedback_dict['abort']

		if self.feedback_on_screen is False:	
			self.protocol_floatlayout.add_widget(self.feedback_label)
			self.feedback_on_screen = True
			self.feedback_start_time = time.perf_counter()

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback',self.feedback_label.text)
		
		self.hold_button.unbind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.iti_start)
	
	
	
	# Cue Stimuli Pressed during Target
	
	def cue_pressed(self, *args):
		Clock.unschedule(self.stimulus_presentation_end)
		Clock.unschedule(self.no_response)
		self.last_response = 0
		
		self.target_touch_time = time.perf_counter()
		self.response_latency = self.target_touch_time - self.target_start_time
		
		self.protocol_floatlayout.remove_widget(self.cue_image)
		self.protocol_floatlayout.remove_widget(self.target_image)
		self.protocol_floatlayout.remove_widget(self.cue_image_button)
		self.protocol_floatlayout.remove_widget(self.target_image_button)

		self.protocol_floatlayout.add_stage_event('Cue Pressed')

		self.protocol_floatlayout.add_stage_event('Incorrect Response')

		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Cue Image', self.cue_image.pos_hint)

		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Target Image', self.target_image.pos_hint)

		self.protocol_floatlayout.add_variable_event('Change', 'Outcome', 'Stimulus Chosen', 'Cue')

		self.protocol_floatlayout.add_variable_event('Change', 'Outcome', 'Last Response', self.last_response)

		self.protocol_floatlayout.add_variable_event('Change', 'Outcome', 'Response Latency', self.response_latency)
		
		self.feedback_label.text = self.feedback_dict['incorrect']

		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.bind(on_release=self.premature_response)

		self.protocol_floatlayout.add_widget(self.hold_button)

		if self.feedback_label.text != '' \
			and not self.feedback_on_screen:
			
			self.protocol_floatlayout.add_widget(self.feedback_label)

			self.feedback_start_time = time.perf_counter()
			self.feedback_on_screen = True

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback',self.feedback_label.text)
		
		self.hold_active = False
		self.stimulus_on_screen = False
		self.cue_completed = False
		self.delay_active = False
		self.delay_ended = False
		self.limhold_started = False
		
		self.write_trial()
		
		self.trial_contingency()
		
		return
	
	
	
	# Target Stimuli Pressed during Target
	
	def target_pressed(self, *args):
		Clock.unschedule(self.stimulus_presentation_end)
		Clock.unschedule(self.no_response)
		self.last_response = 1
		
		self.target_touch_time = time.perf_counter()
		self.response_latency = self.target_touch_time - self.target_start_time
		
		self.protocol_floatlayout.remove_widget(self.cue_image)
		self.protocol_floatlayout.remove_widget(self.target_image)
		self.protocol_floatlayout.remove_widget(self.cue_image_button)
		self.protocol_floatlayout.remove_widget(self.target_image_button)

		self.protocol_floatlayout.add_stage_event('Target Pressed')

		self.protocol_floatlayout.add_stage_event('Correct Response')

		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Cue Image', self.cue_image.pos_hint)

		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Target Image', self.target_image.pos_hint)

		self.protocol_floatlayout.add_variable_event('Change', 'Outcome', 'Stimulus Chosen', 'Target')
		
		self.protocol_floatlayout.add_variable_event('Change', 'Outcome', 'Last Response', self.last_response)

		self.protocol_floatlayout.add_variable_event('Change', 'Outcome', 'Response Latency', self.response_latency)

		self.feedback_label.text = self.feedback_dict['correct']

		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.bind(on_release=self.premature_response)

		self.protocol_floatlayout.add_widget(self.hold_button)

		if self.feedback_label.text != '' \
			and not self.feedback_on_screen:
			
			self.protocol_floatlayout.add_widget(self.feedback_label)

			self.feedback_start_time = time.perf_counter()
			self.feedback_on_screen = True

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback', self.feedback_label.text)

		self.hold_active = False
		self.stimulus_on_screen = False
		self.cue_completed = False
		self.delay_active = False
		self.delay_ended = False
		self.limhold_started = False
		
		self.write_trial()
		
		self.trial_contingency()
		
		return
	
	
	
	# No response during test phase limited hold
	
	def no_response(self, *args):
		
		self.last_response = np.nan

		self.target_touch_time = time.perf_counter()
		self.response_latency = np.nan
		
		self.protocol_floatlayout.remove_widget(self.cue_image)
		self.protocol_floatlayout.remove_widget(self.target_image)
		self.protocol_floatlayout.remove_widget(self.cue_image_button)
		self.protocol_floatlayout.remove_widget(self.target_image_button)

		# State change: No Response
		self.protocol_floatlayout.add_stage_event('No Response')

		# Object remove: Cue stimulus
		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Cue Image', self.cue_image.pos_hint)

		# Object remove: Target stimulus
		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Target Image', self.target_image.pos_hint)

		# Variable change: Stimulus Chosen -> None
		self.protocol_floatlayout.add_variable_event('Change', 'Outcome', 'Stimulus Chosen', 'None')
		
		# Variable change: Last Response
		self.protocol_floatlayout.add_variable_event('Change', 'Outcome', 'Last Response', self.last_response)
		
		# Variable change: Response Latency
		self.protocol_floatlayout.add_variable_event('Change', 'Outcome', 'Response Latency', self.response_latency)

		self.feedback_label.text = ''

		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.bind(on_release=self.premature_response)

		self.protocol_floatlayout.add_widget(self.hold_button)
		
		self.stimulus_on_screen = False
		self.cue_completed = False
		self.delay_active = False
		self.delay_ended = False
		self.limhold_started = False
		
		self.write_trial()
		
		self.trial_contingency()
		
		if self.hold_active == True:
			self.hold_active = False
			self.iti_start()

		return
	
	
	
	# Data Saving Function
	
	def write_trial(self):
		
		cue_x = self.trial_coord['Cue']['x']
		cue_y = self.trial_coord['Cue']['y']
		target_x = self.trial_coord['Target']['x']
		target_y = self.trial_coord['Target']['y']
		
		trial_data = [
			self.current_trial
			, self.current_block
			, self.current_stage
			, self.current_sep
			, self.current_delay
			, self.video_position
			, (cue_x + 1)
			, (cue_y + 1)
			, (target_x + 1)
			, (target_y + 1)
			, self.last_response
			, self.response_latency
			]
		
		self.write_summary_file(trial_data)
		
		return
	
	
	
	# Trial Contingency Functions
	
	def trial_contingency(self):
		
		try:
			
			if self.hold_active:
				self.hold_active = False

			if self.current_block_trial != 0:

				if self.last_response in [0, 1]:
					self.response_tracking.append(self.last_response)
					self.accuracy_tracking.append(self.last_response)


				if self.current_delay >= self.max_delay \
					and len(self.response_tracking) > 3:

					del self.response_tracking[1]


				if (len(self.response_tracking) >= 2) \
					and (sum(self.response_tracking) == 0):

					self.staircase_change = 'dec'
					self.response_tracking = list()
					# Variable change: Staircasing -> Decrease
					self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Staircasing', 'Decrease')

				elif (len(self.response_tracking) >= 2) \
					and (sum(self.response_tracking) > 0):

					self.staircase_change = 'inc'
					self.response_tracking = list()
					# Variable change: Staircasing -> Increase
					self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Staircasing', 'Increase')
				
				else:
					self.staircase_change = 'non'


				# Adjust staircasing
				
				if self.staircase_change == 'inc':
				
					if self.current_stage == 'Space':
						self.space_probe_delay_list[self.space_trial_index] += self.space_probe_staircase_list[self.space_trial_index]
						self.space_probe_response_list[self.space_trial_index] = self.last_response

					elif self.current_stage == 'Delay':
						self.delay_probe_sep_list[self.delay_trial_index] -= 1
						self.delay_probe_response_list[self.delay_trial_index] = self.last_response

						if self.delay_probe_sep_list[self.delay_trial_index] < self.min_sep:
							self.delay_probe_sep_list[self.delay_trial_index] = self.min_sep

					elif self.current_stage == 'Combo':
						self.combo_probe_delay_tracking_dict[self.current_sep].append(self.current_delay)
						self.combo_probe_delay_list[self.combo_trial_index] += self.combo_probe_staircase_list[self.combo_trial_index]

						self.last_staircase_time_increase = self.combo_probe_staircase_list[self.combo_trial_index]

						if self.combo_probe_delay_list[self.combo_trial_index] > self.max_delay:
							self.combo_probe_delay_list[self.combo_trial_index] = self.max_delay
						
						self.current_delay = self.combo_probe_delay_list[self.combo_trial_index]
						# State change: Combo Staircasing
						self.protocol_floatlayout.add_stage_event('Combo Staircasing')

						# Variable change: Delay
						self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Delay', self.current_delay)
						
						self.combo_probe_response_list[self.combo_trial_index] = self.last_response
				
				
				if self.staircase_change == 'dec':
				
					if self.current_stage == 'Space':

						if self.space_probe_response_list[self.space_trial_index] == 1:
							self.space_probe_staircase_list[self.space_trial_index] /= 2

						self.space_probe_delay_list[self.space_trial_index] -= self.space_probe_staircase_list[self.space_trial_index]
						self.space_probe_response_list[self.space_trial_index] = self.last_response

						if self.space_probe_delay_list[self.space_trial_index] < self.min_delay:
							self.space_probe_delay_list[self.space_trial_index] = self.min_delay

					elif self.current_stage == 'Delay':

						self.delay_probe_sep_list[self.delay_trial_index] += 1
						self.delay_probe_response_list[self.delay_trial_index] = self.last_response

						if self.delay_probe_sep_list[self.delay_trial_index] > self.max_sep:
							self.delay_probe_sep_list[self.delay_trial_index] = self.max_sep

					elif self.current_stage == 'Combo':

						if self.combo_probe_staircase_list[self.combo_trial_index] == self.last_staircase_time_increase:
							self.combo_probe_staircase_list[self.combo_trial_index] /= 2

						self.combo_probe_delay_list[self.combo_trial_index] -= self.combo_probe_staircase_list[self.combo_trial_index]

						if self.combo_probe_delay_list[self.combo_trial_index] < self.min_delay:
							self.combo_probe_delay_list[self.combo_trial_index] = self.min_delay
						
						self.current_delay = self.combo_probe_delay_list[self.combo_trial_index]

							# State change: Combo Staircasing
						self.protocol_floatlayout.add_stage_event('Combo Staircasing')

							# Variable change: Delay
						self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Delay', self.current_delay)

						self.combo_probe_response_list[self.combo_trial_index] = self.last_response
				

				if self.current_stage == 'Combo' \
					and ((time.perf_counter() - self.block_start_time) >= (self.combo_probe_max_section_dur * (self.combo_trial_index + 1))):

					self.combo_trial_index += 1

					if self.combo_trial_index < len(self.combo_probe_sep_list):
						self.current_sep = self.combo_probe_sep_list[self.combo_trial_index]
						self.combo_probe_delay_list[self.combo_trial_index] = self.current_delay

						# State change: Combo Staircasing
						self.protocol_floatlayout.add_stage_event('Combo Staircasing')

						# Variable changes: Separation and Delay
						self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Separation', self.current_sep)
						self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Delay', self.current_delay)

					else:
						self.block_contingency()


				if (time.perf_counter() - self.block_start_time >= self.block_duration):
					self.current_block += 1
					self.block_contingency()

			# Set next trial parameters

			# Trial number and trial index

			self.current_trial += 1
			self.current_block_trial += 1
			
			# Variable changes: Current Trial and Current Block Trial
			self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Current Trial', str(self.current_trial))

			self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Current Block Trial', str(self.current_block_trial))
			
			# Set ITI

			if len(self.iti_range) > 1:
				
				if self.iti_fixed_or_range == 'fixed':
					self.iti_length = random.choice(self.iti_range)
				
				else:
					self.iti_length = round(random.uniform(min(self.iti_range), max(self.iti_range)), 2)
				
				# Variable change: Current ITI
				self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Current ITI', self.iti_length)


			if self.current_stage == 'Space':
				
				if self.trial_index >= len(self.space_trial_index_list):
					self.trial_index = 0
					self.space_trial_index_list = self.constrained_shuffle(self.space_trial_index_list)
				
				self.space_trial_index = self.space_trial_index_list[self.trial_index]
				
				self.current_sep = self.space_probe_sep_list[self.space_trial_index]
				self.current_delay = self.space_probe_delay_list[self.space_trial_index]
			
			elif self.current_stage == 'Delay':
				
				if self.trial_index >= len(self.delay_trial_index_list):
					self.trial_index = 0
					self.delay_trial_index_list = self.constrained_shuffle(self.delay_trial_index_list)
				
				self.delay_trial_index = self.delay_trial_index_list[self.trial_index]
				
				self.current_sep = self.delay_probe_sep_list[self.delay_trial_index]
				self.current_delay = self.delay_probe_delay_list[self.delay_trial_index]
			
			# Set cue and target coordinates
			
			self.trial_coord = self.generate_trial_pos_sep(
				self.x_boundaries
				, self.y_boundaries
				, self.current_sep
				, self.stimulus_image_spacing
				, self.screen_x_padding
				, self.screen_y_padding_t
				, self.screen_y_padding_b
				)
			
			# Set cue and target locations
			
			self.cue_image.pos_hint = {
				"center_x": self.trial_coord['Cue']['x'], 
				"center_y": self.trial_coord['Cue']['y']
				}
			
			self.target_image.pos_hint = {
				"center_x": self.trial_coord['Target']['x'], 
				"center_y": self.trial_coord['Target']['y']
				}
			

			self.cue_image_button.pos_hint = {
				"center_x": self.trial_coord['Cue']['x'], 
				"center_y": self.trial_coord['Cue']['y']
				}
			
			self.target_image_button.pos_hint = {
				"center_x": self.trial_coord['Target']['x'], 
				"center_y": self.trial_coord['Target']['y']
				}
			

			# Variable change: Current Delay
			self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Current Delay', str(self.current_delay))

			# Variable change: Current Separation
			self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Current Separation', str(self.current_sep))

			# Variable change: Cue Position
			self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Cue Position', self.cue_image.pos_hint)

			# Variable change: Target Position
			self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Target Position', self.cue_image.pos_hint)

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

			self.block_started = True
			Clock.unschedule(self.remove_feedback)
			self.remove_feedback()

			self.protocol_floatlayout.clear_widgets()
			self.feedback_label.text = ''
		
			# State changes for block transition
			self.protocol_floatlayout.add_stage_event('Block Contingency')

			self.protocol_floatlayout.add_stage_event('Screen Cleared')
			
			if (self.current_block > self.block_multiplier) or (self.current_block == -1):
				self.stage_index += 1
				self.current_block = 1			
	
			if self.stage_index >= len(self.stage_list): # Check if all stages complete
				self.session_event.cancel()
				self.results_screen()

				return
			
			else:
				self.current_stage = self.stage_list[self.stage_index]
		
				# Stage and block change events
				self.protocol_floatlayout.add_stage_event('Stage Change')
				self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Current Stage', self.current_stage)

				self.protocol_floatlayout.add_stage_event('Block Change')
				self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Current Block', self.current_block)
			
			
			if self.current_stage == 'Space':
				self.space_trial_index_list = self.constrained_shuffle(self.space_trial_index_list)
			
			elif self.current_stage == 'Delay':
				self.delay_trial_index_list = self.constrained_shuffle(self.delay_trial_index_list)
						
			elif self.current_stage == 'Combo':	
				self.combo_trial_index = 0
				self.current_sep = self.combo_probe_sep_list[self.combo_trial_index]
				self.current_delay = self.combo_probe_delay_list[self.combo_trial_index]

				# Variable changes: Separation and Delay
				self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Separation', self.current_sep)
				self.protocol_floatlayout.add_variable_event('Change', 'Parameter', 'Delay', self.current_delay)


			if (self.current_block == 1) and (self.stage_index == 0):
				self.section_instr_label.text = self.instruction_dict[str(self.current_stage)]['task']

				self.instruction_button.text = 'Begin Section'
				
				self.protocol_floatlayout.add_widget(self.section_instr_label)
				self.protocol_floatlayout.add_widget(self.instruction_button)
				
				# Object display events: training text and continue button
				self.protocol_floatlayout.add_object_event('Display', 'Text', 'Block', 'Instructions', 'Training')

				self.protocol_floatlayout.add_object_event('Display', 'Button', 'Block', 'Instructions', 'Continue')
			
			else:
				self.block_started = False
				self.block_contingency()
			

			self.response_tracking = list()
			self.last_response = 0
			self.contingency = 0
			self.trial_outcome = 0
			self.current_block_trial = 0
			self.trial_index = 0
			
			self.trial_contingency()
		
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()