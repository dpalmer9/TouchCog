# Imports #

import configparser
import numpy as np
import os
import pathlib
import random
import statistics
import time

from Classes.Protocol import ImageButton, ProtocolBase, PreloadedVideo

from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.video import Video
from kivy.uix.image import Image


class ProtocolScreen(ProtocolBase):
	
	def __init__(self, **kwargs):	
		
		super(ProtocolScreen, self).__init__(**kwargs)
		
		self.protocol_name = 'TUNL'
		self.name = self.protocol_name + '_protocolscreen'
		self.update_task()

		# Define Data Columns
		
		self.data_cols = [
			'TrialNo'
			, 'Stage'
			, 'Block'
			, 'BlockTrial'
			, 'Separation'
			, 'Delay'
			, 'Cue_X'
			, 'Cue_Y'
			, 'Target_X'
			, 'Target_Y'
			, 'VideoTime'
			, 'Contingency'
			, 'Outcome'
			, 'LastResponse'
			, 'ResponseLatency'
			]
		
		self.metadata_cols = [
			'participant_id'
			, 'skip_tutorial_video'
			, 'training_block'
			, 'combined_probe'
			, 'delay_probe'
			, 'iti_length'
			, 'iti_fixed_or_range'
			, 'feedback_length'
			, 'block_duration_max'
			, 'block_multiplier'
			, 'session_duration'
			, 'screen_x_padding'
			, 'screen_y_padding_top'
			, 'screen_y_padding_bottom'
			, 'stimulus_gap'
			, 'x_boundaries'
			, 'y_boundaries'
			, 'stimulus_image'
			, 'distractor_video'
			, 'combined_probe_sep_list'
			, 'combined_probe_delay_limits'
			, 'combined_probe_delay_resolution'
			, 'delay_probe_separation'
			, 'delay_probe_separation_resolution'
			]
		
		
		# Define Variables - Config
		
		self.config_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Configuration.ini'
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
	
		self.participant_id = self.parameters_dict.get('participant_id', '')

		self.skip_tutorial_video = self.parameters_dict.get('skip_tutorial_video', 'False')
		self.tutorial_video_duration = float(self.parameters_dict.get('tutorial_video_duration', '68.5'))

		self.iti_fixed_or_range = self.parameters_dict.get('iti_fixed_or_range', 'range')
		
		self.iti_import = self.parameters_dict.get('iti_length', '0.75,1.25')
		self.iti_import = self.iti_import.split(',')
		
		self.stimdur_import = self.parameters_dict.get('stimulus_duration', '2.0')
		self.stimdur_import = self.stimdur_import.split(',')
		
		self.limhold_import = self.parameters_dict.get('limited_hold', '2.0')
		self.limhold_import = self.limhold_import.split(',')
		
		self.feedback_length = float(self.parameters_dict.get('feedback_length', '0.75'))
		self.block_duration = float(self.parameters_dict.get('block_duration_max', '1800'))
		self.block_min_rest_duration = float(self.parameters_dict.get('block_min_rest_duration', '2'))
		self.session_duration = float(self.parameters_dict.get('session_duration', '3600'))
		
		self.block_multiplier = int(self.parameters_dict.get('block_multiplier', '1'))

		self.stimulus_scale = float(self.parameters_dict.get('stimulus_scale', '0.35'))
		
		self.screen_x_padding = int(self.parameters_dict.get('screen_x_padding', '4'))
		self.screen_y_padding_t = int(self.parameters_dict.get('screen_y_padding_top', '2'))
		self.screen_y_padding_b = int(self.parameters_dict.get('screen_y_padding_bottom', '2'))

		self.stimulus_gap = float(self.parameters_dict.get('stimulus_gap', '0.1'))
		
		self.x_boundaries = self.parameters_dict.get('x_boundaries', '0,1')
		self.x_boundaries = self.x_boundaries.split(',')

		self.y_boundaries = self.parameters_dict.get('y_boundaries', '0.1,1')
		self.y_boundaries = self.y_boundaries.split(',')

		self.stimulus_image = self.parameters_dict.get('stimulus_image', 'circle')
		self.stimulus_button_image = self.parameters_dict.get('stimulus_button_image', 'blank')
		self.distractor_video = self.parameters_dict.get('distractor_video', 'waves2.mp4')

		self.combo_probe_sep_list = self.parameters_dict.get('combined_probe_sep_list', '2,1,0')
		self.combo_probe_sep_list = self.combo_probe_sep_list.split(',')
		
		self.combo_probe_delay_limit_import = self.parameters_dict.get('combined_probe_delay_limits', '2,16')
		self.combo_probe_delay_limit_import = self.combo_probe_delay_limit_import.split(',')
		
		self.combo_probe_delay_resolution = float(self.parameters_dict.get('combined_probe_delay_resolution', '1'))
		
		self.delay_probe_sep = float(self.parameters_dict.get('delay_probe_separation', '1'))

		self.delay_probe_sep_resolution = float(self.parameters_dict.get('delay_probe_separation_resolution', '0.2'))

		self.hold_image = self.config_file['Hold']['hold_image']

		# Create stage list
		
		self.stage_list = list()

		if self.parameters_dict.get('training_block', 'True'):
			self.stage_list.append('Train')
		
		# if self.parameters_dict['space_probe']:
		# 	self.stage_list.append('Space')

		# if self.parameters_dict['delay_probe']:
		# 	self.stage_list.append('Delay')
		
		# if len(self.stage_list) > 1:
		# 	self.stage_list = self.constrained_shuffle(self.stage_list)

		if self.parameters_dict.get('combined_probe', 'True'):
			self.stage_list.append('Combo')

		if self.parameters_dict.get('delay_probe', 'True'):
			self.stage_list.append('Delay')


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
		self.current_sep = 0		
		self.current_block = 1
		self.current_block_trial = 0
		self.last_response = 0

		self.max_blocks = self.block_multiplier

		self.contingency = np.nan # Trial Contingencies: 0-Incorrect; 1-Correct; 3-Premature/Abort
		self.trial_outcome = np.nan # Trial Outcomes: 0-Premature (ITI),1-Hit (target response),2-Miss (no response),3-False alarm (non-target response);7-Cue abort (lift hold button during cue display),8-Delay abort (lift hold button during delay display)

		# Define Variables - List
		self.response_tracking = list()

		# Define String

		self.section_instr_string = ''
		self.current_stage = self.stage_list[0]

	def _setup_session_stages(self):

		self.combo_probe_sep_index = 0
		self.combo_probe_sep_list = [int(iNum) for iNum in self.combo_probe_sep_list]
		self.combo_probe_sep_list.sort(reverse=True)
		self.combo_probe_delay_limit_import = [int(iNum) for iNum in self.combo_probe_delay_limit_import]
		self.combo_probe_delay_tracking_dict = {}
		self.combo_probe_delay_limit_dict = {}
		for iElem in self.combo_probe_sep_list:
			self.combo_probe_delay_tracking_dict[iElem] = list()
			self.combo_probe_delay_limit_dict[iElem] = {'min': min(self.combo_probe_delay_limit_import), 'max': max(self.combo_probe_delay_limit_import)}
		# self.combo_probe_delay_tracking_dict = {statistics.mean(self.combo_probe_delay_limit_import) for iElem in self.combo_probe_sep_list}
		# self.combo_probe_delay_min = [min(self.combo_probe_delay_limit_import) for iElem in self.combo_probe_sep_list]
		# self.combo_probe_delay_max = [max(self.combo_probe_delay_limit_import) for iElem in self.combo_probe_sep_list]

		self.delay_probe_sep_tracking = list()
		self.delay_probe_sep_limit_dict = {'min': min(self.combo_probe_sep_list), 'max': max(self.combo_probe_sep_list)}
		

		self.iti_range = [float(iNum) for iNum in self.iti_import]
		self.iti_length = self.iti_range[0]
		
		self.stimdur_list = [float(iNum) for iNum in self.stimdur_import]
		self.limhold_list = [float(iNum) for iNum in self.limhold_import]

		self.stimdur = self.stimdur_list[0]
		self.limhold = self.limhold_list[0]

		# If training block, set easiest parameters
		if self.current_stage == 'Train':
			self.current_sep = 2
			self.current_delay = 1
		
		# Else, default to easiest separation and middle delay
		else:
			self.current_sep = 2
			self.current_delay = 8
		
		


	def _setup_image_widgets(self):
		self.image_folder = self.app.app_root / 'Protocol' / self.protocol_name / 'Image'
		self.stimulus_image_path = str(self.image_folder / (self.stimulus_image + '.png'))
		self.stimulus_button_image_path = str(self.image_folder / (self.stimulus_button_image + '.png'))
		hold_button_top_loc = self.hold_button.pos_hint['center_y'] + (self.hold_button.size_hint[1]/2)

		self.x_boundaries = [float(iNum) for iNum in self.x_boundaries]
		self.y_boundaries = [float(iNum) for iNum in self.y_boundaries]
		if self.y_boundaries[0] < hold_button_top_loc:
			self.y_boundaries[0] = hold_button_top_loc
		
		elif self.y_boundaries[1] < hold_button_top_loc:
			self.y_boundaries[1] = hold_button_top_loc

		self.cue_image = ImageButton(source=str(self.stimulus_image_path))
		self.target_image = ImageButton(source=str(self.stimulus_image_path))
		
		# Calculate resolution scaling factor (baseline 1080p)
		resolution_scale = self.screen_resolution[1] / 1080.0

		self.stimulus_image_spacing = [
			((self.cue_image.texture_size[0]/self.screen_resolution[0]) * self.stimulus_scale * resolution_scale)
			, ((self.cue_image.texture_size[1]/self.screen_resolution[1]) * self.stimulus_scale * resolution_scale)
			]
		
		self.stimulus_image_size = (np.array(self.stimulus_image_spacing) * (1 - self.stimulus_gap)).tolist()
		self.stimulus_button_size = (np.array(self.stimulus_image_size) * 0.77).tolist()

		# Define Widgets - Buttons
		
		self.hold_button.source = str(self.image_folder / (self.hold_image + '.png'))
		self.hold_button.bind(on_press=self.iti_start)
				

		self.cue_image_button = ImageButton(source=str(self.stimulus_button_image_path))
		self.cue_image_button.bind(on_press=self.cue_pressed)
		self.target_image_button = ImageButton(source=str(self.stimulus_button_image_path))
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
		self.text_button_pos_LC = {"center_x": 0.50, "center_y": 0.08}
		self.text_button_pos_LR = {"center_x": 0.75, "center_y": 0.08}
		self.text_button_pos_UC = {"center_x": 0.50, "center_y": 0.92}

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

		button_lang_path = self.lang_folder_path / 'Button.ini'
		button_lang_config = configparser.ConfigParser()
		button_lang_config.read(button_lang_path, encoding='utf-8')

		self.end_task_str = button_lang_config.get('Button', 'end_task', fallback='End Task')

		self.outcome_dict = {}
		self.staging_dict = {}

		for file_path in self.lang_folder_path.glob('outcome_*.txt'):
			key = file_path.stem.replace('outcome_', '')
			with open(file_path, 'r', encoding='utf-8') as f:
				self.outcome_dict[key] = f.read()

		for file_path in self.lang_folder_path.glob('staging_*.txt'):
			key = file_path.stem.replace('staging_', '')
			with open(file_path, 'r', encoding='utf-8') as f:
				self.staging_dict[key] = f.read()

	def _load_video_and_instruction_components(self):
		# self.video_size = (1, 1)
		# self.video_pos = {"center_x": 0.5, "y": 0.125}
		self.lang_folder_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language

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


		if (self.lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_path = str(list((self.lang_folder_path / 'Tutorial_Video').glob('*.mp4'))[0])

			self.tutorial_video = PreloadedVideo(
				source_path=str(self.tutorial_video_path),
				pos_hint={'center_x': 0.5, 'center_y': 0.5 + self.text_button_size[1]},
				fit_mode='contain',
				loop=False
			)
	
			self.tutorial_continue_button.bind(on_press=self.stop_tutorial_video)


		# Instruction - Dictionary
		
		self.instruction_path = str(self.lang_folder_path / 'Instructions.ini')
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Train'] = {}
		self.instruction_dict['Combo'] = {}
		self.instruction_dict['Delay'] = {}
		
		for stage in self.stage_list:
			self.instruction_dict[stage]['train'] = self.instruction_config[stage]['train']
			self.instruction_dict[stage]['task'] = self.instruction_config[stage]['task']
		
		
		# Instruction - Text Widget
		
		self.section_instr_string = self.instruction_label.text
		self.section_instr_label = Label(text=self.section_instr_string, font_size='44sp', markup=True)
		self.section_instr_label.size_hint = {0.8, 0.5}
		self.section_instr_label.pos_hint = {'center_x': 0.5, 'center_y': 0.4}
		
		# Instruction - Button Widget
		
		self.instruction_button = Button(font_size='60sp')
		self.instruction_button.size_hint = self.text_button_size
		self.instruction_button.pos_hint =  self.text_button_pos_UC
		self.instruction_button.text = ''
		self.instruction_button.bind(on_press=self.section_start)
		
		
		# Define Widgets - Labels
		
		self.feedback_label.size_hint = (0.7, 0.3)
		self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.55}


		# Instruction - Dictionary
		
		self.instruction_path = str(self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language / 'Instructions.ini')
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Train'] = {}
		self.instruction_dict['Combo'] = {}
		self.instruction_dict['Delay'] = {}
		
		for stage in self.stage_list:
			self.instruction_dict[stage]['train'] = self.instruction_config[stage]['train']
			self.instruction_dict[stage]['task'] = self.instruction_config[stage]['task']		
		
		# Instruction - Button Widget
		
		self.instruction_button = Button()
		self.instruction_button.bind(on_press=self.section_start)
	
	# Initialization Functions
	
	def load_parameters(self, parameter_dict):
		self._load_config_parameters(parameter_dict)
		self._load_task_variables()
		self._setup_session_stages()
		self._setup_image_widgets()
		self._setup_language_localization()
		self._load_video_and_instruction_components()


		self.start_clock()
		if (self.lang_folder_path / 'Tutorial_Video').is_dir():

			self.protocol_floatlayout.clear_widgets()
			self.present_tutorial_video()
		
		else:
			self.present_tutorial_text()



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
		combined_coord = {'Cue': cue_coord, 'Target': target_coord}
		
		return combined_coord


	# Protocol Staging
	def present_tutorial_text(self, *args):

		self.protocol_floatlayout.clear_widgets()

		self.section_instr_label.text = self.instruction_dict[str(self.current_stage)]['task']
		
		self.instruction_button.text = 'Continue'
		self.instruction_button.bind(on_press=self.start_protocol_from_tutorial)
		
		self.protocol_floatlayout.add_widget(self.section_instr_label)
		self.protocol_floatlayout.add_widget(self.instruction_button)
		
		# Object display events: training text and continue button
		self.protocol_floatlayout.add_object_event('Display', 'Text', 'Instructions', 'Training')
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Instructions', 'Continue')
	
	
	def stop_tutorial_video(self, *args):
		self.tutorial_video.state = 'stop'
		self.tutorial_video.unload()
		self.protocol_floatlayout.add_object_event('Remove', 'Video', 'Section', 'Instructions')
		self.start_protocol_from_tutorial()
	
	def start_protocol_from_tutorial(self, *args):
		
		self.generate_output_files()
		self.metadata_output_generation()

		self.tutorial_video = PreloadedVideo(
			source_path=str(self.delay_video_path),
			pos_hint={'center_x': 0.5, 'center_y': 0.5 + self.text_button_size[1]},
			fit_mode='contain',
			loop=True
		)

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_stage_event('Section Start')
		self.protocol_floatlayout.add_stage_event('Instruction Presentation')
		self.protocol_floatlayout.add_text_event('Removed', 'Task Instruction')
		self.protocol_floatlayout.add_button_event('Removed', 'Task Start Button')
		self.protocol_floatlayout.add_button_event('Displayed', 'Hold Button')

		self.protocol_floatlayout.add_widget(self.hold_button)
		
		self.block_start_time = time.perf_counter()
		self.trial_end_time = time.perf_counter()
		
		self.feedback_label.text = ''
		self.block_contingency()

	def section_start(self, *args):

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_stage_event('Section Start')
		
		self.protocol_floatlayout.add_object_event('Remove', 'Text', 'Section', 'Instructions')
		
		self.protocol_floatlayout.add_button_event('Remove', 'Continue')
		
		self.block_end()
	


	def results_screen(self, *args):
		
		Clock.unschedule(self.iti_end)
		
		self.block_started = True
		Clock.unschedule(self.remove_feedback)
		self.remove_feedback()

		self.protocol_floatlayout.clear_widgets()
		self.feedback_label.text = ''

		# If training block, provide feedback
		if (self.current_stage == 'Train'):
			outcome_string = eval(f'f"""{self.outcome_dict.get("training", "")}"""')
			
		# Else, if combo probe, provide maximum delay based on current separation
		elif (self.current_stage == 'Combo') \
				and (len(self.combo_probe_delay_tracking_dict[self.current_sep]) > 0):
		
			if self.current_sep == max(self.combo_probe_sep_list):
				difficulty_string = 'Easy'
				
			elif self.current_sep == min(self.combo_probe_sep_list):
				difficulty_string = 'Hard'

			else:
				difficulty_string = 'Medium'

			outcome_string = eval(f'f"""{self.outcome_dict.get("comboresult", "")}"""')
			
		# Else, if delay probe, provide minimum distance based on current delay
		elif self.current_stage == 'Delay' \
				and (len(self.delay_probe_sep_tracking) > 0):

			outcome_string = eval(f'f"""{self.outcome_dict.get("delayresult", "")}"""')

		# Else, provide generic accuracy results
		elif (len(self.response_tracking) > 0):
			self.hit_accuracy = sum(self.response_tracking) / len(self.response_tracking)

			outcome_string = eval(f'f"""{self.outcome_dict.get("result", "")}"""')

		# Else, provide generic feedback
		else:
			outcome_string = eval(f'f"""{self.outcome_dict.get("gj", "")}"""')
		

		if self.stage_index < (len(self.stage_list) - 1) \
				or (self.current_block <= self.max_blocks):
			staging_string = eval(self.staging_dict.get('continue'))
			self.instruction_button.unbind(on_press=self.section_start)
			self.instruction_button.bind(on_press=self.block_contingency)
			self.instruction_button.text = 'Continue'

		else:
			staging_string = eval(self.staging_dict.get('end'))
			self.instruction_button.unbind(on_press=self.section_start)
			self.instruction_button.unbind(on_press=self.block_contingency)
			self.instruction_button.bind(on_press=self.protocol_end)
			self.instruction_button.text = self.end_task_str

		self.section_instr_label.size_hint = {0.8, 0.5}
		self.section_instr_label.pos_hint = {'center_x': 0.5, 'center_y': 0.4}

		self.instruction_button.size_hint = self.text_button_size
		self.instruction_button.pos_hint =  self.text_button_pos_UC

		self.section_instr_label.text = outcome_string + staging_string

		self.protocol_floatlayout.add_widget(self.section_instr_label)
		self.protocol_floatlayout.add_widget(self.instruction_button)
		
		self.protocol_floatlayout.add_text_event('Display', 'Results')

		self.protocol_floatlayout.add_button_event('Display', 'Continue')



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
		
		self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Cue Image', self.cue_image.pos_hint)

		Clock.schedule_once(self.delay_present, self.stimdur)
	


	# Display Distractor During Delay
	
	def delay_present(self, *args):
		self.protocol_floatlayout.clear_widgets()
		self.protocol_floatlayout.add_widget(self.hold_button)
		
		self.protocol_floatlayout.add_stage_event('Delay Start')

		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Cue Image', self.cue_image.pos_hint)

		self.delay_end_event = Clock.schedule_once(self.delay_end, self.current_delay)

		self.protocol_floatlayout.add_widget(self.tutorial_video)
		self.tutorial_video.state = 'play'

		self.video_start_time = time.perf_counter()

		self.delay_active = True

		self.protocol_floatlayout.add_stage_event('Object Display')

		self.protocol_floatlayout.add_object_event('Display', 'Video', str(self.tutorial_video.source), self.video_position)



	# Display Distractor During Delay
	
	def delay_end(self, *args):
		self.tutorial_video.state = 'stop'
		self.tutorial_video.reset()
		self.tutorial_video.unload()
		self.tutorial_video.reload()

		self.protocol_floatlayout.clear_widgets()

		self.video_end_time = time.perf_counter()
		self.video_time = self.video_end_time - self.video_start_time
		self.video_position += self.video_time

		self.delay_ended = True
		self.delay_active = False
		
		self.protocol_floatlayout.add_stage_event('Delay End')

		self.protocol_floatlayout.add_stage_event('Object Remove')

		self.protocol_floatlayout.add_object_event('Remove', 'Video', str(self.tutorial_video.source), self.video_position)

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

	def hold_released(self, *args): # Trial outcomes: 7-Cue abort,8-Delay abort
		Clock.unschedule(self.delay_present)
		Clock.unschedule(self.delay_end)
		Clock.unschedule(self.stimulus_presentation_end)
		self.hold_button_pressed = False
		
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

			self.contingency = 3 # 3-Premature/Abort
			self.trial_outcome = 7 # 7-Cue abort (lift hold button during cue display)

		elif self.delay_active:
			self.tutorial_video.state = 'pause'
			self.tutorial_video.reset()
			self.tutorial_video.unload()
			self.tutorial_video.reload()

			self.video_end_time = time.perf_counter()
			self.video_time = self.video_end_time - self.video_start_time
			self.video_position += self.video_time

			self.contingency = 3 # 3-Premature/Abort
			self.trial_outcome = 8 # 8-Delay abort (lift hold button during delay display)

			self.protocol_floatlayout.add_object_event('Remove', 'Video', str(self.tutorial_video.source), self.video_position)

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
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Contingency', self.contingency)
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Trial Outcome', self.trial_outcome)

		self.protocol_floatlayout.add_variable_event('Outcome', 'Last Response', self.last_response)

		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)
		
		self.write_trial()
		self.trial_contingency()
		
		return



	# Hold released too early
	
	def premature_response(self, *args): # Trial outcome: 0-Premature (ITI)
		
		if self.stimulus_on_screen is True:
			return
	
		self.hold_active = False
		Clock.unschedule(self.iti_end)
		
		self.protocol_floatlayout.add_stage_event('Premature Response')

		self.contingency = 3 # 3-Premature/Abort
		self.trial_outcome = 0 # 0-Premature (ITI)
		self.last_response = np.nan
		self.response_latency = np.nan
		self.iti_active = False
		self.feedback_label.text = self.feedback_dict['abort']

		if self.feedback_on_screen is False:	
			self.protocol_floatlayout.add_widget(self.feedback_label)
			self.feedback_on_screen = True
			self.feedback_start_time = time.perf_counter()

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback',self.feedback_label.text)
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Contingency', self.contingency)
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Trial Outcome', self.trial_outcome)

		self.protocol_floatlayout.add_variable_event('Outcome', 'Last Response', self.last_response)

		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)
		
		self.hold_button.unbind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.iti_start)
	
	
	
	# Cue Stimuli Pressed during Target
	
	def cue_pressed(self, *args): # Trial outcome: 3-False alarm (non-target response)
		Clock.unschedule(self.stimulus_presentation_end)
		Clock.unschedule(self.no_response)
		self.contingency = 0 # 0-Incorrect
		self.trial_outcome = 3 # 3-False alarm (non-target response)
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

		self.protocol_floatlayout.add_variable_event('Outcome', 'Stimulus Chosen', 'Cue')
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Contingency', self.contingency)
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Trial Outcome', self.trial_outcome)

		self.protocol_floatlayout.add_variable_event('Outcome', 'Last Response', self.last_response)

		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)
		
		self.feedback_label.text = self.feedback_dict['incorrect']

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
	
	
	
	# Target Stimuli Pressed during Target
	
	def target_pressed(self, *args): # Trial outcome: 1-Hit (target response)
		Clock.unschedule(self.stimulus_presentation_end)
		Clock.unschedule(self.no_response)
		self.contingency = 1 # 1-Correct
		self.trial_outcome = 1 # 1-Hit (target response)
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

		self.protocol_floatlayout.add_variable_event('Outcome', 'Stimulus Chosen', 'Target')
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Contingency', self.contingency)
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Trial Outcome', self.trial_outcome)
		
		self.protocol_floatlayout.add_variable_event('Outcome', 'Last Response', self.last_response)

		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)

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
	
	def no_response(self, *args): # Trial outcome: 2-Miss (no response)
		
		self.contingency = 0 # 0-Incorrect
		self.trial_outcome = 2 # 2-Miss (no response)
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
		self.protocol_floatlayout.add_variable_event('Outcome', 'Stimulus Chosen', 'None')
		
		# Variable change: Contingency
		self.protocol_floatlayout.add_variable_event('Outcome', 'Contingency', self.contingency)
		
		# Variable change: Trial Outcome
		self.protocol_floatlayout.add_variable_event('Outcome', 'Trial Outcome', self.trial_outcome)
		
		# Variable change: Last Response
		self.protocol_floatlayout.add_variable_event('Outcome', 'Last Response', self.last_response)
		
		# Variable change: Response Latency
		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)

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
			, self.current_stage
			, self.current_block
			, self.current_block_trial
			, self.current_sep
			, self.current_delay
			, (cue_x + 1)
			, (cue_y + 1)
			, (target_x + 1)
			, (target_y + 1)
			, self.video_position
			, self.contingency
			, self.trial_outcome
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

				# Track responses to check criteria
				if self.last_response in [0, 1]:
					self.response_tracking.append(self.last_response)


				# Check if training block
				if (self.current_stage == 'Train'):
					
					# If more than 8 trials done, trim early trials and use rolling window of last 8
					if (len(self.response_tracking) > 8):
						self.response_tracking = self.response_tracking[-8:]

					# If at least 7 hits in last 8 trials, go to results screen and advance block
					# Else, do nothing
					if (len(self.response_tracking) >= 8)\
							and sum(self.response_tracking) >= 7:

						self.current_block += 1
						self.results_screen()


				# Else, check for staircasing
				else:

					## Note: Staircase flag variable not required but makes for easier criteria/stage changes down the line

					# First, default staircase flag to 0
					self.staircase_flag = 0

					# Staircasing only relies on hits, so only need to check one variable
					# Staircasing up requires 7/8 hits; otherwise, staircase down
					# Hits reset at every staircase, so don't need to check for list length
					# Staircase up as soon as sum of hits >= 7
					# Staircase down as soon as two or more 0's in list

					# If minimum 7 trials correct, staircase up
					if sum(self.response_tracking) >= 7:
						self.staircase_flag = 1

					# Else, if two or more 0's present in list, staircase down
					# Else, do nothing
					elif self.response_tracking.count(0) >= 2:
						self.staircase_flag = -1


					# If non-zero staircase flag, change staircase level
					# Organized by stage
					if self.staircase_flag != 0:
							
						# If combo probe, check staircasing
						if (self.current_stage == 'Combo'):

							# Add current delay to delay tracking list for that separation
							self.combo_probe_delay_tracking_dict[self.current_sep].append(self.current_delay)

							# If staircasing up, set current delay to minimum
							# Min delay represents longest tested delay interval where criteria met
							if self.staircase_flag > 0:
								self.combo_probe_delay_limit_dict[self.current_sep]['min'] = self.current_delay

							# Else, if staircasing down, set current delay to maximum
							# Max delay represents shortest tested delay interval where criteria failed
							elif self.staircase_flag < 0:
								self.combo_probe_delay_limit_dict[self.current_sep]['max'] = self.current_delay
							

							# If difference between min and max delays is greater than delay resolution, take next midpoint
							if self.combo_probe_delay_limit_dict[self.current_sep]['max'] > self.combo_probe_delay_limit_dict[self.current_sep]['min'] + self.combo_probe_delay_resolution:
							
								self.current_delay = round(statistics.mean([self.combo_probe_delay_limit_dict[self.current_sep]['min'], self.combo_probe_delay_limit_dict[self.current_sep]['max']]))
					
							# Else, if difference between min and max delays is less than or equal to delay resolution, check whether min and max values have been tested
							elif self.combo_probe_delay_limit_dict[self.current_sep]['max'] <= self.combo_probe_delay_limit_dict[self.current_sep]['min'] + self.combo_probe_delay_resolution:
					
								# If minimum delay does not exist in delay tracking, set current delay to minimum
								if self.combo_probe_delay_limit_dict[self.current_sep]['min'] not in self.combo_probe_delay_tracking_dict[self.current_sep]:
									self.current_delay = self.combo_probe_delay_limit_dict[self.current_sep]['min']
					
								# Else, if maximum delay does not exist in delay tracking, set current delay to maximum
								elif self.combo_probe_delay_limit_dict[self.current_sep]['max'] not in self.combo_probe_delay_tracking_dict[self.current_sep]:
									self.current_delay = self.combo_probe_delay_limit_dict[self.current_sep]['max']

								# Else, if minimum and maximum delay exist, show results screen and proceed to next block
								elif (self.combo_probe_delay_limit_dict[self.current_sep]['min'] in self.combo_probe_delay_tracking_dict[self.current_sep]) \
										and (self.combo_probe_delay_limit_dict[self.current_sep]['max'] in self.combo_probe_delay_tracking_dict[self.current_sep]):

									self.current_block += 1
									self.results_screen()


						# Else, if delay probe, check staircasing
						elif (self.current_stage == 'Delay'):

							# Add current separation to separation tracking list
							self.delay_probe_sep_tracking.append(self.current_sep)

							# If staircasing up, set current separation to maximum
							# Max separation represents smallest tested separation where criteria met
							if self.staircase_flag > 0:
								self.delay_probe_sep_limit_dict['max'] = self.current_sep

							# Else, if staircasing down, set current separation to minimum
							# Min separation represents largest tested separation where criteria failed
							elif self.staircase_flag < 0:
								self.delay_probe_sep_limit_dict['min'] = self.current_sep

							# If difference between min and max separations is greater than separation resolution, take next midpoint
							if (self.delay_probe_sep_limit_dict['max'] - self.delay_probe_sep_limit_dict['min']) > self.delay_probe_sep_resolution:
								self.current_sep = round(statistics.mean([self.delay_probe_sep_limit_dict['min'], self.delay_probe_sep_limit_dict['max']]), 1)
					
							# Else, if difference between min and max separations is less than or equal to separation resolution, check whether min and max values have been tested
							elif (self.delay_probe_sep_limit_dict['max'] - self.delay_probe_sep_limit_dict['min']) <= self.delay_probe_sep_resolution:
					
								# If minimum separation does not exist in separation tracking, set current separation to minimum
								if self.delay_probe_sep_limit_dict['min'] not in self.delay_probe_sep_tracking:
									self.current_sep = self.delay_probe_sep_limit_dict['min']
					
								# Else, if maximum separation does not exist in separation tracking, set current separation to maximum
								elif self.delay_probe_sep_limit_dict['max'] not in self.delay_probe_sep_tracking:
									self.current_sep = self.delay_probe_sep_limit_dict['max']

								# Else, if minimum and maximum separations exist, proceed
								elif (self.delay_probe_sep_limit_dict['min'] in self.delay_probe_sep_tracking) \
										and (self.delay_probe_sep_limit_dict['max'] in self.delay_probe_sep_tracking):

									# Move to results screen
									self.current_block += 1
									self.results_screen()

						# Reset response_tracking list for next staircase
						self.response_tracking = list()


				if (time.perf_counter() - self.block_start_time >= self.block_duration):
					self.current_block += 1
					self.results_screen()

			# Set next trial parameters

			# Trial number and trial index

			self.current_trial += 1
			self.current_block_trial += 1
			
			# Variable changes: Current Trial and Current Block Trial
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Trial', str(self.current_trial))

			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Block Trial', str(self.current_block_trial))
			
			# Set ITI

			if len(self.iti_range) > 1:
				
				if self.iti_fixed_or_range == 'fixed':
					self.iti_length = random.choice(self.iti_range)
				
				else:
					self.iti_length = round(random.uniform(min(self.iti_range), max(self.iti_range)), 2)
				
				# Variable change: Current ITI
				self.protocol_floatlayout.add_variable_event('Parameter', 'Current ITI', self.iti_length)

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
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Delay', str(self.current_delay))

			# Variable change: Current Separation
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current Separation', str(self.current_sep))

			# Variable change: Cue Position
			self.protocol_floatlayout.add_variable_event('Parameter', 'Cue Position', self.cue_image.pos_hint)

			# Variable change: Target Position
			self.protocol_floatlayout.add_variable_event('Parameter', 'Target Position', self.cue_image.pos_hint)

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
			
			if (self.current_block > self.max_blocks) \
					or (self.current_block == 0) \
					or (self.stage_index == -1):
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
				self.protocol_floatlayout.add_variable_event('Parameter', 'Current Stage', self.current_stage)

				self.protocol_floatlayout.add_stage_event('Block Change')
				self.protocol_floatlayout.add_variable_event('Parameter', 'Current Block', self.current_block)

				self.max_blocks = self.block_multiplier

				# If training stage, set easy parameters
				if self.current_stage == 'Train':
					self.current_sep = 2
					self.current_delay = 1
				
					# Variable changes: Separation and Delay
					self.protocol_floatlayout.add_variable_event('Parameter', 'Separation', self.current_sep)
					self.protocol_floatlayout.add_variable_event('Parameter', 'Delay', self.current_delay)
				

				# If combination probe, set separation and delay parameters
				elif self.current_stage == 'Combo':
					self.combo_probe_sep_index = self.current_block - 1

					# If end of separation list reached, trigger block contingency
					if (self.combo_probe_sep_index >= len(self.combo_probe_sep_list)):
						self.current_block += 1
						self.block_contingency()

					self.current_sep = self.combo_probe_sep_list[self.combo_probe_sep_index]
					self.current_delay = round(statistics.mean([self.combo_probe_delay_limit_dict[self.current_sep]['min'], self.combo_probe_delay_limit_dict[self.current_sep]['max']]))
				
					# Variable changes: Separation and Delay
					self.protocol_floatlayout.add_variable_event('Parameter', 'Separation', self.current_sep)
					self.protocol_floatlayout.add_variable_event('Parameter', 'Delay', self.current_delay)

					self.max_blocks = len(self.combo_probe_sep_list) * self.block_multiplier
				

				# If delay probe, set separation and delay parameters
				# Separation set by config file; delay set to mean value from combo probe delay range
				elif self.current_stage == 'Delay':
					self.current_sep = self.delay_probe_sep
					self.current_delay = round(statistics.mean([min(self.combo_probe_delay_limit_import), max(self.combo_probe_delay_limit_import)]), 1)
				
					# Variable changes: Separation and Delay
					self.protocol_floatlayout.add_variable_event('Parameter', 'Separation', self.current_sep)
					self.protocol_floatlayout.add_variable_event('Parameter', 'Delay', self.current_delay)


			self.response_tracking = list()
			self.last_response = 0
			self.contingency = np.nan # Reset contingency
			self.trial_outcome = np.nan # Reset trial outcome
			self.current_block_trial = 0
			
			self.block_start_time = time.perf_counter()
			self.trial_end_time = time.perf_counter()
			
			self.feedback_label.text = ''

			self.protocol_floatlayout.add_widget(self.hold_button)
			
			self.trial_contingency()
		
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()