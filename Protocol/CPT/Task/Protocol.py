# Imports #

import configparser
import numpy as np
import pandas as pd
import pathlib
import random
import statistics
import time

from Classes.Protocol import ImageButton, ProtocolBase

from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.effectwidget import EffectWidget, HorizontalBlurEffect, VerticalBlurEffect
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.video import Video




class ProtocolScreen(ProtocolBase):

	def __init__(self, **kwargs):

		super(ProtocolScreen, self).__init__(**kwargs)
		self.protocol_name = 'CPT'
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
			# print('Width > Height')
		
		elif width < height:
			self.height_adjust = width / height
			# print('Width < Height')
		
		# print('Width adjust: ', self.width_adjust)
		# print('height adjust: ', self.height_adjust)
		
		
		# Define Data Columns

		self.data_cols = [
			'TrialNo'
			, 'Stage'
			, 'Substage'
			, 'TarProb_Probe'
			, 'Block'
			, 'CurrentBlockTrial'
			, 'Stimulus'
			, 'StimFrames'
			, 'StimDur'
			, 'LimHold'
			, 'Similarity'
			, 'BlurLevel'
			, 'NoiseMaskValue'
			, 'Response'
			, 'Contingency'
			, 'Outcome'
			, 'ResponseLatency'
			, 'StimulusPressLatency'
			, 'MovementLatency'
			]
		
		self.metadata_cols = [
			'participant_id'
			, 'skip_tutorial_video'
			, 'tutorial_video_duration'
			, 'block_change_on_duration_only'
			, 'training_task'
			, 'similarity_scaling'
			, 'limdur_scaling'
			, 'noise_scaling'
			, 'blur_scaling'
			, 'noise_probe'
			, 'blur_probe'
			, 'stimdur_probe'
			, 'flanker_probe'
			, 'tarprob_probe'
			, 'sart_probe'
			, 'iti_fixed_or_range'
			, 'iti_length'
			, 'stimulus_duration'
			, 'feedback_length'
			, 'block_duration-staircase'
			, 'block_duration-probe'
			, 'block_min_rest_duration'
			, 'session_duration'
			, 'block_multiplier'
			, 'block_trial_max'
			, 'training_block_max_correct'
			, 'target_prob_over_num_trials'
			, 'target_prob_list'
			, 'target_prob_similarity'
			, 'target_prob_flanker'
			, 'stimulus_family'
			, 'display_stimulus_outline'
			, 'mask_during_limhold'
			, 'limhold_mask_type'
			, 'similarity_percentile_initial'
			, 'similarity_percentile_range'
			, 'staircase_stimdur_min_frames'
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
		
		iti_temp = self.parameters_dict['iti_length']
		iti_temp = iti_temp.split(',')
		
		self.stimdur_import = self.parameters_dict['stimulus_duration']
		self.stimdur_import = self.stimdur_import.split(',')
		
		self.feedback_length = float(self.parameters_dict['feedback_length'])
		self.block_duration_staircase = int(self.parameters_dict['block_duration-staircase'])
		self.block_duration_probe = int(self.parameters_dict['block_duration-probe'])
		self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
		self.session_duration = float(self.parameters_dict['session_duration'])
		
		self.block_multiplier = int(self.parameters_dict['block_multiplier'])
		self.block_trial_max = int(self.parameters_dict['block_trial_max'])
		self.training_block_max_correct = int(self.parameters_dict['training_block_max_correct'])

		self.target_prob_trial_num = int(self.parameters_dict['target_prob_over_num_trials'])
		
		target_prob_import = self.parameters_dict['target_prob_list']
		target_prob_import = target_prob_import.split(',')

		self.target_prob_base = round(self.target_prob_trial_num * float(self.parameters_dict['target_prob_base']))
		self.target_prob_sim = round(self.target_prob_trial_num * float(self.parameters_dict['target_prob_similarity']))
		self.target_prob_flanker = round(self.target_prob_trial_num * float(self.parameters_dict['target_prob_flanker']))

		self.display_stimulus_outline = int(self.parameters_dict['display_stimulus_outline'])
		self.mask_during_limhold = int(self.parameters_dict['mask_during_limhold'])
		self.limhold_mask_type = self.parameters_dict['limhold_mask_type']
		
		self.similarity_percentile_initial = float(self.parameters_dict['similarity_percentile_initial'])
		self.similarity_percentile_range = float(self.parameters_dict['similarity_percentile_range'])
		self.staircase_stimdur_frame_min = float(self.parameters_dict['staircase_stimdur_min_frames'])
		staircase_stimdur_seconds_max = float(self.parameters_dict['staircase_stimdur_max_seconds'])
		
		self.hold_image = config_file['Hold']['hold_image']
		self.mask_image = config_file['Mask']['mask_image']
		
		
		# Create stage list
		
		self.stage_list = list()
		
		if int(self.parameters_dict['training_task']) == 1:
			self.stage_list.append('Training')
		
		if int(self.parameters_dict['limdur_scaling']) == 1:
			self.stage_list.append('LimDur_Scaling')
			
		if int(self.parameters_dict['similarity_scaling']) == 1:
			self.stage_list.append('Similarity_Scaling')
			self.stimulus_family = 'Fb'
		else:
			self.stimulus_family = self.parameters_dict['stimulus_family']
		
		if int(self.parameters_dict['noise_scaling']) == 1 \
			and 'Similarity_Scaling' not in self.stage_list:
			self.stage_list.append('Noise_Scaling')
		
		if int(self.parameters_dict['blur_scaling']) == 1 \
			and 'Similarity_Scaling' not in self.stage_list:
			self.stage_list.append('Blur_Scaling')
		
		if int(self.parameters_dict['noise_probe']) == 1:
			self.stage_list.append('Noise_Probe')
		
		if int(self.parameters_dict['blur_probe']) == 1:
			self.stage_list.append('Blur_Probe')
		
		if int(self.parameters_dict['stimdur_probe']) == 1:
			self.stage_list.append('StimDur_Probe')
		
		if int(self.parameters_dict['flanker_probe']) == 1:
			self.stage_list.append('Flanker_Probe')
		
		if int(self.parameters_dict['tarprob_probe']) == 1:
			self.stage_list.append('TarProb_Probe')
		
		if int(self.parameters_dict['sart_probe']) == 1:
			self.stage_list.append('SART_Probe')
		
		
		# Set images

		self.similarity_data = pd.DataFrame({})

		self.target_image = ''
		self.target_image_path = ''

		self.similarity_index = 0
		
		
		# Define Language
		
		self.language = 'English'
		self.set_language(self.language)
		self.stage_instructions = ''
		
		
		# Define Variables - Boolean
		
		self.stimulus_on_screen = False
		self.limhold_started = False
		self.response_made = False
		self.hold_active = False
		self.stimulus_mask_on_screen = True
		self.training_complete = False
		
		# Define Variables - Count
		
		self.current_block = -1
		self.current_block_trial = 0

		self.current_hits = 0
		
		self.stage_index = -1
		self.trial_index = 0
		
		self.block_max_count = self.block_multiplier

		self.trial_outcome = 0 # 0-Premature,1-Hit,2-Miss,3-False Alarm,4-Correct Rejection,5-Correct, no center tap,6-Incorrect, no center tap
		self.contingency = 0
		self.response = 0

		self.target_probability = 1.0

		self.block_target_total = 0
		self.block_false_alarms = 0
		self.block_hits = 0
		
		
		# Define Variables - Staircasing
		
		self.last_response = 0
		
		self.response_tracking = list()
		self.blur_tracking = list()
		self.noise_tracking = list()
		self.stimdur_frame_tracking = list()

		self.similarity_tracking = list()

		self.current_similarity = 0.0
		
		self.outcome_value = 0.0

		self.noise_mask_index_change = 2

		self.blur_level = 0
		self.blur_base = 0
		self.blur_change = 30
		
		
		# Define Variables - String
		
		self.center_image = self.mask_image
		self.left_image = self.mask_image
		self.right_image = self.mask_image

		self.current_substage = ''
		self.outcome_string = ''
		self.stage_string = ''
		
		
		# Define Variables - Time
		
		self.stimulus_start_time = 0.0
		self.response_latency = 0.0
		self.stimulus_press_latency = 0.0
		self.movement_latency = 0.0
		self.frame_duration = 1/self.maxfps
		self.stimdur_actual = 0.0
		self.trial_end_time = 0.0

		self.staircase_stimdur_frame_max = staircase_stimdur_seconds_max/self.frame_duration
		
		iti_temp = [float(iNum) for iNum in iti_temp]
		self.iti_frame_range = sorted((np.array(iti_temp) // self.frame_duration).tolist(), reverse=True)
		self.iti_frame_range = [int(iNum) for iNum in self.iti_frame_range]
		self.iti_length = self.iti_frame_range[0] * self.frame_duration
		
		self.stimdur_import = [float(iNum) for iNum in self.stimdur_import]

		stimdur_frame_steps = np.round(np.array(self.stimdur_import) / self.frame_duration, decimals=0)
		
		if 0 in stimdur_frame_steps:
			stimdur_frame_steps += 1

		self.stimdur_frames = sorted(stimdur_frame_steps.tolist(), reverse=True)
		self.stimdur_index = 0

		self.stimdur_current_frames = self.stimdur_frames[self.stimdur_index]
		self.stimdur = self.stimdur_current_frames * self.frame_duration

		if self.staircase_stimdur_frame_min < 1:
			self.staircase_stimdur_frame_min = 1

		self.stimdur_base = self.stimdur_current_frames
		self.stimdur_change = self.stimdur_current_frames
		
		self.stimdur_use_steps = True
		

		# Define Clock
		
		self.block_check_clock = Clock
		self.block_check_clock.interupt_next_only = False
		self.block_check_event = self.block_check_clock.create_trigger(self.block_contingency, 0, interval=True)
		self.stage_screen_event = self.block_check_clock.create_trigger(self.stage_screen, 0, interval=True)
		
		self.task_clock = Clock
		self.task_clock.interupt_next_only = True

		self.tutorial_video_end_event = self.task_clock.create_trigger(self.present_tutorial_video_start_button, 0)
		self.stimdur_event = self.task_clock.create_trigger(self.stimulus_presentation, 0, interval=True)
		self.trial_contingency_event = self.task_clock.create_trigger(self.trial_contingency, 0)
		self.stimulus_present_event = self.task_clock.create_trigger(self.stimulus_present, -1)
		self.stimulus_end_event = self.task_clock.create_trigger(self.stimulus_end, 0)
		self.blur_preload_start_event = self.task_clock.create_trigger(self.blur_preload_start, 0)
		self.blur_preload_end_event = self.task_clock.create_trigger(self.blur_preload_end, 0)


		# Define Variables

		self.target_prob_list = [int(float(iProb) * self.target_prob_trial_num) for iProb in target_prob_import]
		
		self.nontarget_prob_base = self.target_prob_trial_num - self.target_prob_base
		
		if 'Similarity_Scaling' in self.stage_list:
			self.nontarget_prob_sim = self.target_prob_trial_num - self.target_prob_sim
		
		if 'Flanker_Probe' in self.stage_list:
			self.flanker_stage_index = 0
			self.flanker_stage_list = ['none', 'same', 'diff', 'none', 'same', 'diff']
			random.shuffle(self.flanker_stage_list)
			self.current_substage = ''
			self.flanker_image = ''
		
		if 'SART_Probe' in self.stage_list:
			self.target_prob_SART = max(self.target_prob_list)
			self.nontarget_prob_SART = self.target_prob_trial_num - self.target_prob_SART
		
		
		# Define Widgets - Images

		self.image_folder = pathlib.Path('Protocol', self.protocol_name, 'Image')

		self.mask_image_path = str(self.image_folder / str(self.mask_image + '.png'))
		
		self.img_stimulus_C = ImageButton()
		self.img_stimulus_L = ImageButton(source=self.mask_image_path)
		self.img_stimulus_R = ImageButton(source=self.mask_image_path)

		self.center_instr_image = ImageButton(source=self.mask_image_path)
		self.left_instr_image = ImageButton(source=self.mask_image_path)
		self.right_instr_image = ImageButton(source=self.mask_image_path)

		self.img_noise_C = ImageButton()
		self.img_outline_C = ImageButton()
		
		
		# Define Instruction Components

		# Instruction - Dictionary
		
		self.instruction_path = str(pathlib.Path('Protocol', self.protocol_name, 'Language', self.language, 'Instructions.ini'))
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		
		for stage in self.stage_list:

			self.instruction_dict[stage] = {}
			
			self.instruction_dict[stage]['train'] = self.instruction_config[stage]['train']
			self.instruction_dict[stage]['task'] = self.instruction_config[stage]['task']

		
		lang_folder_path = str(pathlib.Path('Protocol', self.protocol_name, 'Language', self.language))
		feedback_lang_path = str(pathlib.Path(lang_folder_path, 'Feedback.ini'))
		feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
		feedback_lang_config.read(feedback_lang_path, encoding="utf-8")

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
		
		
		# Instruction - Text Widget
		
		self.section_instr_string = ''
		
		
		# Instruction - Button Widget
		
		self.instruction_button = Button()
		self.instruction_button.bind(on_press=self.section_start)
		self.instruction_button_str = ''
		
		
		# Stage Results - Button Widget
		
		self.stage_continue_button = Button()
		self.stage_continue_button.bind(on_press=self.block_contingency)
		
		self.session_end_button = Button()
		self.session_end_button.bind(on_press=self.protocol_end)
	
	
	
	def load_parameters(self, parameter_dict):
		
		# Import parameters from config file
		
		self.parameters_dict = parameter_dict
		
		self.participant_id = self.parameters_dict['participant_id']
		
		self.language = self.parameters_dict['language']

		self.skip_tutorial_video = int(self.parameters_dict['skip_tutorial_video'])
		self.tutorial_video_duration = int(self.parameters_dict['tutorial_video_duration'])

		self.block_change_on_duration = int(self.parameters_dict['block_change_on_duration_only'])
		
		self.iti_fixed_or_range = self.parameters_dict['iti_fixed_or_range']
		
		
		iti_temp = self.parameters_dict['iti_length']
		iti_temp = iti_temp.split(',')
		
		self.stimdur_import = self.parameters_dict['stimulus_duration']
		self.stimdur_import = self.stimdur_import.split(',')
		
		self.feedback_length = float(self.parameters_dict['feedback_length'])
		self.block_duration_staircase = int(self.parameters_dict['block_duration-staircase'])
		self.block_duration_probe = int(self.parameters_dict['block_duration-probe'])
		self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
		self.session_duration = float(self.parameters_dict['session_duration'])
		
		self.block_multiplier = int(self.parameters_dict['block_multiplier'])
		self.block_trial_max = int(self.parameters_dict['block_trial_max'])
		self.training_block_max_correct = int(self.parameters_dict['training_block_max_correct'])

		self.target_prob_trial_num = int(self.parameters_dict['target_prob_over_num_trials'])
		
		target_prob_import = self.parameters_dict['target_prob_list']
		target_prob_import = target_prob_import.split(',')
		
		self.target_prob_base = round(self.target_prob_trial_num * float(self.parameters_dict['target_prob_base']))
		self.target_prob_sim = round(self.target_prob_trial_num * float(self.parameters_dict['target_prob_similarity']))
		self.target_prob_flanker = round(self.target_prob_trial_num * float(self.parameters_dict['target_prob_flanker']))
		
		self.stimulus_family = self.parameters_dict['stimulus_family']

		self.display_stimulus_outline = int(self.parameters_dict['display_stimulus_outline'])
		self.mask_during_limhold = int(self.parameters_dict['mask_during_limhold'])
		self.limhold_mask_type = self.parameters_dict['limhold_mask_type']

		self.similarity_percentile_initial = float(self.parameters_dict['similarity_percentile_initial'])
		self.similarity_percentile_range = float(self.parameters_dict['similarity_percentile_range'])

		self.staircase_stimdur_frame_min = float(self.parameters_dict['staircase_stimdur_min_frames'])
		staircase_stimdur_seconds_max = float(self.parameters_dict['staircase_stimdur_max_seconds'])
		
		
		config_path = str(pathlib.Path('Protocol', self.protocol_name, 'Configuration.ini'))
		config_file = configparser.ConfigParser()
		config_file.read(config_path)
		
		self.hold_image = config_file['Hold']['hold_image']
		self.mask_image = config_file['Mask']['mask_image']
		
		
		# Create stage list and import stage parameters
		
		self.stage_list = list()
		
		if int(self.parameters_dict['training_task']) == 1:
			self.stage_list.append('Training')
		
		if int(self.parameters_dict['limdur_scaling']) == 1:
			self.stage_list.append('LimDur_Scaling')
			
		if int(self.parameters_dict['similarity_scaling']) == 1:
			self.stage_list.append('Similarity_Scaling')
			self.stimulus_family = 'Fb'
		
		else:
			self.stimulus_family = self.parameters_dict['stimulus_family']
		
		if int(self.parameters_dict['noise_scaling']) == 1 \
			and 'Similarity_Scaling' not in self.stage_list:
			self.stage_list.append('Noise_Scaling')
		
		if int(self.parameters_dict['blur_scaling']) == 1 \
			and 'Similarity_Scaling' not in self.stage_list:
			self.stage_list.append('Blur_Scaling')
		
		if int(self.parameters_dict['noise_probe']) == 1:
			self.stage_list.append('Noise_Probe')
		
		if int(self.parameters_dict['blur_probe']) == 1:
			self.stage_list.append('Blur_Probe')
		
		if int(self.parameters_dict['stimdur_probe']) == 1:
			self.stage_list.append('StimDur_Probe')
		
		if int(self.parameters_dict['flanker_probe']) == 1:
			self.stage_list.append('Flanker_Probe')
		
		if int(self.parameters_dict['tarprob_probe']) == 1:
			self.stage_list.append('TarProb_Probe')
		
		if int(self.parameters_dict['sart_probe']) == 1:
			self.stage_list.append('SART_Probe')

		
		# Convert parameters to useable types
		
		# General properties
		
		self.trial_list = list()
		self.trial_list_base = list()

		self.target_prob_list = [int(float(iProb) * self.target_prob_trial_num) for iProb in target_prob_import]
		random.shuffle(self.target_prob_list)

		self.nontarget_prob_base = self.target_prob_trial_num - self.target_prob_base
		
		for iTrial in range(self.target_prob_base):
			self.trial_list_base.append('Target')
		
		for iTrial in range(self.nontarget_prob_base):
			self.trial_list_base.append('Nontarget')
		
		random.shuffle(self.trial_list_base)
		
		self.trial_list = self.trial_list_base
		# print('Trial list mid prob: ', self.trial_list)
		
		if 'Similarity_Scaling' in self.stage_list:
			self.trial_list_sim = list()
			self.nontarget_prob_sim = self.target_prob_trial_num - self.target_prob_sim
		
			for iTrial in range(self.target_prob_sim):
				self.trial_list_sim.append('Target')
			
			for iTrial in range(self.nontarget_prob_sim):
				self.trial_list_sim.append('Nontarget')
			
			random.shuffle(self.trial_list_sim)
		
		if 'SART_Probe' in self.stage_list:
			self.trial_list_SART = list()
			self.nontarget_prob_SART = max(self.target_prob_list)
			self.target_prob_SART = self.target_prob_trial_num - self.nontarget_prob_SART
		
			for iTrial in range(self.target_prob_SART):
				self.trial_list_SART.append('Target')
			
			for iTrial in range(self.nontarget_prob_SART):
				self.trial_list_SART.append('Nontarget')
			
			random.shuffle(self.trial_list_SART)
		
		if 'Flanker_Probe' in self.stage_list:
			self.trial_list_flanker = list()
			self.nontarget_prob_flanker = self.target_prob_trial_num - self.target_prob_flanker
		
			for iTrial in range(self.target_prob_flanker):
				self.trial_list_flanker.append('Target')
			
			for iTrial in range(self.nontarget_prob_flanker):
				self.trial_list_flanker.append('Nontarget')
			
			random.shuffle(self.trial_list_flanker)
			
			self.flanker_stage_index = 0
			self.flanker_stage_list = ['none', 'same', 'diff', 'none', 'same', 'diff']
			random.shuffle(self.flanker_stage_list)
			self.current_substage = ''
			self.flanker_image = ''
		
		
		# Set images

		self.fribble_folder = pathlib.Path('Fribbles', self.stimulus_family)

		self.stimulus_image_path_list = sorted(list(self.image_folder.glob(str(self.fribble_folder / '*.png'))))

		if 'Similarity_Scaling' in self.stage_list:
			self.similarity_data = pd.read_csv(str(self.image_folder / self.fribble_folder / str(self.stimulus_family + '-SSIM_Data.csv')))

			stimulus_list = list(self.similarity_data.columns)
			stimulus_list.remove('Nontarget')
			# print('\n\nStimulus list: ', stimulus_list, '\n\n')
			self.target_image = random.choice(stimulus_list)
			# print('Target image: ', self.target_image)

			self.similarity_data = self.similarity_data.loc[:, ['Nontarget', self.target_image]]

			self.similarity_data = self.similarity_data.drop(
				self.similarity_data[
					self.similarity_data['Nontarget'] == self.target_image
					].index
				)

			self.similarity_data = self.similarity_data.sort_values(by=self.target_image, ascending=True)

			self.nontarget_images = self.similarity_data['Nontarget'].tolist()

			self.similarity_index_range = int(len(self.nontarget_images) * (self.similarity_percentile_range/100))

			if (self.similarity_percentile_initial - self.similarity_percentile_range/2) < 0:
				self.similarity_index_min = 0
				self.similarity_index_max = self.similarity_index_range

			elif (self.similarity_percentile_initial + self.similarity_percentile_range/2) > 100:
				self.similarity_index_max = len(self.nontarget_images) - 1
				self.similarity_index_min = self.similarity_index_max - self.similarity_index_range
			
			else:
				self.similarity_index_min = (int(len(self.nontarget_images) * (self.similarity_percentile_initial/100))) \
					- (self.similarity_index_range//2)
				
				self.similarity_index_max = (int(len(self.nontarget_images) * (self.similarity_percentile_initial/100))) \
					+ (self.similarity_index_range//2)
			
			self.current_nontarget_image_list = self.nontarget_images[self.similarity_index_min:self.similarity_index_max]
			# print(self.current_nontarget_image_list)

			self.current_similarity = 1.00

		else:
			stimulus_image_list = list()

			for filename in self.stimulus_image_path_list:
				stimulus_image_list.append(filename.stem)

			# print('\n\nStimulus image list: ', stimulus_image_list, '\n\n')

			self.target_image = random.choice(stimulus_image_list)
			self.nontarget_images = list()

			stimulus_image_list.remove(self.target_image)

			subfamily_string = self.target_image[:3]

			while len(stimulus_image_list) > 0:
				iElem = 0

				while iElem < len(stimulus_image_list):

					if stimulus_image_list[iElem].startswith(subfamily_string):
						stimulus_image_list.pop(iElem)

					else:
						iElem += 1

				if len(stimulus_image_list) > 0:
					nontarget_image = random.choice(stimulus_image_list)
					self.nontarget_images.append(nontarget_image)
					subfamily_string = nontarget_image[:3]

			self.nontarget_images.sort()
			self.current_nontarget_image_list = self.nontarget_images
		
		# print('Target image: ', self.target_image)
		# print('Nontarget image list: ', self.nontarget_images)
		# print('Current nontarget image list: ', self.current_nontarget_image_list)

		total_image_list = self.stimulus_image_path_list


		# Staircasing - Noise Masks

		self.noise_mask_index = 0

		self.noise_mask_paths = sorted(list(self.image_folder.glob('Noise_Masks-Circle/*.png')))
		self.noise_mask_list = list()

		for filename in self.noise_mask_paths:
			self.noise_mask_list.append(filename.stem)

		self.noise_mask_value = self.noise_mask_list[self.noise_mask_index]

		# print(self.noise_mask_paths)
		# print(self.noise_mask_list)

		total_image_list += self.noise_mask_paths

		
		# Load images

		self.hold_image_path = str(self.image_folder / (self.hold_image + '.png'))
		self.mask_image_path = str(self.image_folder / (self.mask_image + '.png'))
		self.outline_mask_path = str(self.image_folder / 'whitecircle.png')

		total_image_list += [self.hold_image_path, self.mask_image_path]
		# print('\n\nTotal image list: ', total_image_list, '\n\n')
		self.load_images(total_image_list)
		
		
		# Define Language
		
		self.set_language(self.language)
		self.stage_instructions = ''
		
		
		# Define Variables - Boolean
		
		self.stage_screen_started = False
		self.limhold_started = False
		self.response_made = False
		self.hold_active = False
		self.stimulus_mask_on_screen = False
		self.training_complete = False
		
		
		# Define Variables - Count
		
		self.current_block = -1
		self.current_block_trial = 0
		self.current_hits = 0
		self.block_max_count = self.block_multiplier
		self.trial_outcome = 0 # 0-Premature,1-Hit,2-Miss,3-False Alarm,4-Correct Rejection,5-Correct, no center touch,6-Incorrect, no center touch
		self.contingency = 0
		self.response = 0
		self.stage_index = -1
		self.trial_index = 0

		self.target_probability = 1.0

		self.block_target_total = 0
		self.block_false_alarms = 0
		self.block_hits = 0
		
		
		# Define Variables - Staircasing
		
		self.last_response = 0
		
		self.response_tracking = list()
		self.blur_tracking = list()
		self.noise_tracking = list()
		self.stimdur_frame_tracking = list()

		self.similarity_tracking = list()

		self.current_similarity = 0.0
		
		self.outcome_value = 0.0

		self.noise_mask_index_change = 2

		image_texture_for_size = Image(source=str(self.stimulus_image_path_list[0]))
		self.image_texture_size = image_texture_for_size.texture_size

		# print(self.image_texture_size)

		self.blur_level = 0
		self.blur_base = 0
		self.blur_change = 30
		
		
		# Define Variables - String
		
		self.center_image = self.mask_image
		self.left_image = self.mask_image
		self.right_image = self.mask_image
		
		self.current_stage = ''
		self.current_substage = ''
		self.outcome_string = ''
		self.stage_string = ''
		
		
		# Define Variables - Time
		
		self.stimulus_start_time = 0.0
		self.response_latency = 0.0
		self.stimulus_press_latency = 0.0
		self.movement_latency = 0.0
		self.frame_duration = 1/self.maxfps
		self.stimdur_actual = 0.0
		self.trial_end_time = 0.0

		self.staircase_stimdur_frame_max = staircase_stimdur_seconds_max/self.frame_duration
		
		iti_temp = [float(iNum) for iNum in iti_temp]
		self.iti_frame_range = sorted((np.array(iti_temp) // self.frame_duration).tolist(), reverse=True)
		self.iti_frame_range = [int(iNum) for iNum in self.iti_frame_range]
		self.iti_length = self.iti_frame_range[0] * self.frame_duration
		
		self.stimdur_import = [float(iNum) for iNum in self.stimdur_import]

		stimdur_frame_steps = np.round(np.array(self.stimdur_import) / self.frame_duration)
		
		if 0 in stimdur_frame_steps:
			stimdur_frame_steps += 1
		

		self.stimdur_frames = sorted(stimdur_frame_steps.tolist(), reverse=True)
		self.stimdur_index = 0

		self.stimdur_current_frames = self.stimdur_frames[self.stimdur_index]

		self.stimdur = self.stimdur_current_frames * self.frame_duration

		if self.staircase_stimdur_frame_min < 1:
			self.staircase_stimdur_frame_min = 1
		

		self.stimdur_base = self.stimdur_current_frames
		self.stimdur_change = self.stimdur_current_frames//2
		
		self.stimdur_use_steps = True

		self.limhold = self.stimdur
		self.limhold_base = self.limhold
		
		
		# Define Session Event
		
		self.session_event = self.session_clock.create_trigger(self.clock_monitor, self.session_duration, interval=False)


		# Define GUI Sizes and Pos

		self.stimulus_image_proportion = 0.35
		self.instruction_image_proportion = 0.25

		self.stimulus_image_size = ((self.stimulus_image_proportion * self.width_adjust), (self.stimulus_image_proportion * self.height_adjust))
		self.instruction_image_size = ((self.instruction_image_proportion * self.width_adjust), (self.instruction_image_proportion * self.height_adjust))
		self.stimulus_mask_size = (self.stimulus_image_size[0] * 1.2, self.stimulus_image_size[1] * 1.2)
		self.text_button_size = [0.4, 0.15]

		self.stimulus_pos_C = {"center_x": 0.50, "center_y": 0.5}
		self.stimulus_pos_L = {"center_x": 0.20, "center_y": 0.5}
		self.stimulus_pos_R = {"center_x": 0.80, "center_y": 0.5}

		self.instruction_image_pos_C = {"center_x": 0.50, "center_y": 0.75}

		self.text_button_pos_UC = {"center_x": 0.50, "center_y": 0.92}
		self.text_button_pos_LL = {"center_x": 0.25, "center_y": 0.08}
		self.text_button_pos_LR = {"center_x": 0.75, "center_y": 0.08}
		
		
		# Define Widgets - Images
		
		self.hold_button.source = self.hold_image_path
		self.hold_button.bind(on_press=self.iti)
		self.hold_button.bind(on_release=self.premature_response)
		
		self.img_stimulus_C = ImageButton()
		self.img_stimulus_C.size_hint = self.stimulus_image_size
		self.img_stimulus_C.pos_hint = self.stimulus_pos_C
		self.img_stimulus_C.bind(on_press=self.center_pressed)
		self.img_stimulus_C.name = 'Center Stimulus'

		self.img_stimulus_L = ImageButton(source=self.mask_image_path)
		self.img_stimulus_L.size_hint = self.stimulus_image_size
		self.img_stimulus_L.pos_hint = self.stimulus_pos_L
		
		self.img_stimulus_R = ImageButton(source=self.mask_image_path)
		self.img_stimulus_R.size_hint = self.stimulus_image_size
		self.img_stimulus_R.pos_hint = self.stimulus_pos_R

		self.center_instr_image = ImageButton(source=self.mask_image_path)
		self.center_instr_image.size_hint = self.instruction_image_size
		self.center_instr_image.pos_hint = self.instruction_image_pos_C

		self.img_noise_C = ImageButton(source=str(self.noise_mask_paths[0]))
		self.img_noise_C.size_hint = self.stimulus_mask_size
		self.img_noise_C.pos_hint = self.stimulus_pos_C
		self.img_noise_C.bind(on_press=self.center_pressed)
		self.img_noise_C.name = 'Center Noise Mask'

		self.img_noise_L = ImageButton(source=str(self.noise_mask_paths[0]))
		self.img_noise_L.size_hint = self.stimulus_mask_size
		self.img_noise_L.pos_hint = self.stimulus_pos_L
		self.img_noise_L.name = 'Left Noise Mask'

		self.img_noise_R = ImageButton(source=str(self.noise_mask_paths[0]))
		self.img_noise_R.size_hint = self.stimulus_mask_size
		self.img_noise_R.pos_hint = self.stimulus_pos_R
		self.img_noise_R.name = 'Right Noise Mask'

		self.img_outline_C = ImageButton(source=self.outline_mask_path)
		self.img_outline_C.size_hint = self.stimulus_mask_size
		self.img_outline_C.pos_hint = self.stimulus_pos_C
		self.img_outline_C.bind(on_press=self.center_pressed)
		self.img_outline_C.name = 'Center Outline Mask'

		self.img_outline_L = ImageButton(source=self.outline_mask_path)
		self.img_outline_L.size_hint = self.stimulus_mask_size
		self.img_outline_L.pos_hint = self.stimulus_pos_L
		self.img_outline_L.name = 'Left Outline Mask'

		self.img_outline_R = ImageButton(source=self.outline_mask_path)
		self.img_outline_R.size_hint = self.stimulus_mask_size
		self.img_outline_R.pos_hint = self.stimulus_pos_R
		self.img_outline_R.name = 'Right Outline Mask'


		if self.mask_during_limhold == 1:

			if self.limhold_mask_type == 'noise':
				self.stimulus_mask_path = str(self.noise_mask_paths[-1])

			self.img_stimulus_C_mask = ImageButton(source=self.stimulus_mask_path)
			self.img_stimulus_C_mask.size_hint = self.stimulus_mask_size
			self.img_stimulus_C_mask.pos_hint = self.stimulus_pos_C
			self.img_stimulus_C_mask.bind(on_press=self.center_pressed)
			self.img_stimulus_C_mask.name = 'Center Stimulus Mask'


		if any(True for stage in ['Blur_Scaling', 'Blur_Probe'] if stage in self.stage_list):
			self.blur_widget = EffectWidget()
			self.blur_widget.effects = [HorizontalBlurEffect(size=self.blur_level), VerticalBlurEffect(size=self.blur_level)]
		

		# Instruction Import

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

		
		# Define Instruction Components
		
		# Instruction - Dictionary
		
		self.instruction_path = str(lang_folder_path / 'Instructions.ini')
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		self.instruction_dict['Training'] = {}
		self.instruction_dict['LimDur_Scaling'] = {}
		self.instruction_dict['Similarity_Scaling'] = {}
		self.instruction_dict['Noise_Scaling'] = {}
		self.instruction_dict['Blur_Scaling'] = {}
		self.instruction_dict['Noise_Probe'] = {}
		self.instruction_dict['Blur_Probe'] = {}
		self.instruction_dict['StimDur_Probe'] = {}
		self.instruction_dict['TarProb_Probe'] = {}
		self.instruction_dict['Flanker_Probe'] = {}
		self.instruction_dict['SART_Probe'] = {}
		
		for stage in self.stage_list:
			
			self.instruction_dict[stage]['train'] = self.instruction_config[stage]['train']
			self.instruction_dict[stage]['task'] = self.instruction_config[stage]['task']


		feedback_lang_path = str(lang_folder_path / 'Feedback.ini')
		feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
		feedback_lang_config.read(feedback_lang_path, encoding="utf-8")


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
		
		
		# Instruction - Text Widget
		
		self.section_instr_string = self.instruction_label.text
		self.section_instr_label = Label(text=self.section_instr_string, font_size='44sp', markup=True)
		self.section_instr_label.size_hint = {0.58, 0.7}
		self.section_instr_label.pos_hint = {'center_x': 0.5, 'center_y': 0.35}
		
		# Instruction - Button Widget
		
		self.instruction_button = Button(font_size='60sp')
		self.instruction_button.size_hint = self.text_button_size
		self.instruction_button.pos_hint = self.text_button_pos_UC
		self.instruction_button.text = ''
		self.instruction_button.bind(on_press=self.section_start)
		self.instruction_button_str = ''
		
		
		# Stage Results - Text Widget
		
		self.stage_results_label = Label(text='', font_size='48sp', markup=True)
		self.stage_results_label.size_hint = (0.85, 0.8)
		self.stage_results_label.pos_hint = {'center_x': 0.5, 'center_y': 0.35}
		
		
		# Stage Results - Button Widget
		
		self.continue_button.font_size = '60sp'
		self.continue_button.size_hint = self.text_button_size
		self.continue_button.pos_hint = self.text_button_pos_UC
		
		self.stage_continue_button = Button(font_size='60sp')
		self.stage_continue_button.size_hint = self.text_button_size
		self.stage_continue_button.pos_hint = self.text_button_pos_UC
		self.stage_continue_button.text = 'CONTINUE'
		self.stage_continue_button.bind(on_press=self.block_check_event)
		
		self.session_end_button = Button(font_size='60sp')
		self.session_end_button.size_hint = self.text_button_size
		self.session_end_button.pos_hint = self.text_button_pos_LL
		self.session_end_button.text = 'END SESSION'
		self.session_end_button.bind(on_press=self.protocol_end)
		
		
		self.protocol_floatlayout.clear_widgets()
		
		
		# Begin Task

		if (lang_folder_path / 'Tutorial_Video').is_dir() \
			and (self.skip_tutorial_video == 0):

			self.protocol_floatlayout.clear_widgets()
			self.present_tutorial_video()
		
		else:
			
			self.present_instructions()



	# Protocol Staging

	def present_tutorial_video(self, *args):

		self.protocol_floatlayout.clear_widgets()

		self.tutorial_stimulus_image = ImageButton(source=str(self.image_folder / self.fribble_folder / (self.target_image + '.png')))
		self.tutorial_stimulus_image.size_hint = self.stimulus_image_size
		self.tutorial_stimulus_image.pos_hint = {'center_x': 0.5, 'center_y': 0.6}

		self.tutorial_outline = ImageButton(source=self.outline_mask_path)
		self.tutorial_outline.size_hint = self.stimulus_mask_size
		self.tutorial_outline.pos_hint = {'center_x': 0.5, 'center_y': 0.6}

		self.tutorial_checkmark = ImageButton(source=str(self.image_folder / 'checkmark.png'))
		self.tutorial_checkmark.size_hint = ((0.2 * self.width_adjust), (0.2 * self.height_adjust))
		self.tutorial_checkmark.pos_hint = {'center_x': 0.52, 'center_y': 0.9}
		
		self.tutorial_continue = Button(text='CONTINUE', font_size='48sp')
		self.tutorial_continue.size_hint = self.text_button_size
		self.tutorial_continue.pos_hint = self.text_button_pos_LR
		self.tutorial_continue.bind(on_press=self.tutorial_target_present_screen)
		
		self.tutorial_restart = Button(text='RESTART VIDEO', font_size='48sp')
		self.tutorial_restart.size_hint = self.text_button_size
		self.tutorial_restart.pos_hint = self.text_button_pos_LL
		self.tutorial_restart.bind(on_press=self.start_tutorial_video)
		
		self.tutorial_start_button = Button(text='START TASK', font_size='48sp')
		self.tutorial_start_button.size_hint = self.text_button_size
		self.tutorial_start_button.pos_hint = {'center_x': 0.5, 'center_y': 0.3}
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

		# self.tutorial_video.state = 'pause'

		self.protocol_floatlayout.add_widget(self.tutorial_continue)
		self.protocol_floatlayout.add_widget(self.tutorial_restart)





	def tutorial_target_present_screen(self, *args):

		self.tutorial_video_end_event.cancel()

		self.tutorial_video.state = 'stop'

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_widget(self.tutorial_checkmark)
		self.protocol_floatlayout.add_widget(self.tutorial_stimulus_image)
		self.protocol_floatlayout.add_widget(self.tutorial_outline)
		self.protocol_floatlayout.add_widget(self.tutorial_start_button)



	def start_protocol_from_tutorial(self, *args):

		self.protocol_floatlayout.clear_widgets()

		self.generate_output_files()
		self.metadata_output_generation()

		self.start_clock()
		self.block_contingency()



	def blur_preload_start(self, *args):

		self.blur_preload_start_event.cancel()

		self.img_stimulus_C.texture = self.image_dict[self.mask_image].image.texture

		self.protocol_floatlayout.add_widget(self.blur_widget)
		self.blur_widget.add_widget(self.img_stimulus_C)

		self.blur_preload_end_event()



	def blur_preload_end(self, *args):

		self.blur_preload_end_event.cancel()

		self.protocol_floatlayout.remove_widget(self.blur_widget)
		self.blur_widget.remove_widget(self.img_stimulus_C)

		self.trial_contingency_event()



	def stimulus_present(self, *args): # Present stimulus

		# print('Present stimulus')

		if 'Blur_Scaling' in self.stage_list \
			or self.current_stage == 'Blur_Probe':

			self.blur_widget.add_widget(self.img_stimulus_C)
			self.protocol_floatlayout.add_widget(self.blur_widget)
		
		else:
			
			self.protocol_floatlayout.add_widget(self.img_stimulus_C)
		

		self.stimulus_start_time = time.time()
		
		self.stimulus_on_screen = True
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_start_time - self.start_time)
			, 'State Change'
			, 'Object Display'
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_start_time - self.start_time)
			, 'Object Display'
			, 'Stimulus'
			, 'Center'
			, 'Center'
			, 'Image Name'
			, self.center_image
			])
		

		if 'Noise_Scaling' in self.stage_list \
			or self.current_stage == 'Noise_Probe':
			
			self.protocol_floatlayout.add_widget(self.img_noise_C)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Display'
				, 'Mask'
				, 'Noise'
				, 'Center'
				, 'Image Name'
				, self.noise_mask_value
				])
		

		if self.display_stimulus_outline == 1:
			
			self.protocol_floatlayout.add_widget(self.img_outline_C)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Display'
				, 'Mask'
				, 'Outline'
				, 'Center'
				, 'Image Name'
				, self.display_stimulus_outline
				])
		

		if self.current_stage == 'Flanker_Probe':
			
			self.protocol_floatlayout.add_widget(self.img_stimulus_L)
			self.protocol_floatlayout.add_widget(self.img_stimulus_R)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Display'
				, 'Stimulus'
				, 'Flanker'
				, 'Left'
				, 'Image Name'
				, self.img_stimulus_L
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Display'
				, 'Stimulus'
				, 'Flanker'
				, 'Right'
				, 'Image Name'
				, self.img_stimulus_R
				])


		self.stimdur_event()



	def stimulus_end(self, *args): # Remove stimulus
		
		self.stimulus_present_event.cancel()

		if 'Blur_Scaling' in self.stage_list \
			or self.current_stage == 'Blur_Probe':

			self.protocol_floatlayout.remove_widget(self.blur_widget)
			self.blur_widget.remove_widget(self.img_stimulus_C)
		
		else:
			
			self.protocol_floatlayout.remove_widget(self.img_stimulus_C)
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Object Remove'
			])

		if 'Noise_Scaling' in self.stage_list \
			or self.current_stage == 'Noise_Probe':

			self.protocol_floatlayout.remove_widget(self.img_noise_C)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Mask'
				, 'Noise'
				, 'Center'
				, 'Image Name'
				, self.noise_mask_value
				])


		if (self.mask_during_limhold == 1) \
			and (self.current_stage == 'StimDur_Probe'):
			
			self.protocol_floatlayout.remove_widget(self.img_outline_C)

			self.protocol_floatlayout.add_widget(self.img_stimulus_C_mask)
			self.protocol_floatlayout.add_widget(self.img_outline_C)

			self.stimulus_mask_on_screen = True

		self.stimdur_actual = time.time() - self.stimulus_start_time
		
		self.stimulus_on_screen = False
		self.limhold_started = True

		if self.current_stage == 'Flanker_Probe':
			
			self.protocol_floatlayout.remove_widget(self.img_stimulus_L)
			self.protocol_floatlayout.remove_widget(self.img_stimulus_R)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Flanker'
				, 'Left'
				, 'Image Name'
				, self.img_stimulus_L
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Flanker'
				, 'Right'
				, 'Image Name'
				, self.img_stimulus_R
				])
		
		self.stimdur_event()



	def stimulus_presentation(self, *args): # Stimulus presentation by frame
		
		if not self.stimulus_on_screen \
			and not self.limhold_started:

			# print('Stimulus not on screen')

			self.hold_remind_event.cancel()

			self.hold_active = True
		
			self.hold_button.unbind(on_press=self.iti)
			self.hold_button.unbind(on_release=self.premature_response)
			self.hold_button.bind(on_release=self.stimulus_response)
			
			self.stimulus_present_event()
		
		elif (time.time() - self.stimulus_start_time < self.stimdur):
			self.stimdur_event()
		
		elif ((time.time() - self.stimulus_start_time) < self.limhold) \
			and self.limhold_started:

			self.stimdur_event()
		
		elif ((time.time() - self.stimulus_start_time) >= self.stimdur) \
			and not self.limhold_started:
			
			self.stimulus_end_event()

		else:
			self.center_notpressed()



	def premature_response(self, *args): # Trial Outcomes: 0-Premature,1-Hit,2-Miss,3-False Alarm,4-Correct Rejection,5-Hit, no center touch,6-False Alarm, no center touch

		if self.stimulus_on_screen:
			return None
		
		if self.iti_active:
			self.iti_event.cancel()
		
		self.contingency = 3
		self.response = 1
		self.trial_outcome = 0
		self.response_latency = np.nan
		self.stimulus_press_latency = np.nan
		self.movement_latency = np.nan

		self.feedback_label.text = ''
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Premature Response'
			])
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Trial Contingency'
			, self.contingency
			])
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Trial Response'
			, self.response
			])
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Trial Outcome'
			, self.trial_outcome
			])

		self.write_trial()

		self.iti_active = False
		
		if (self.current_block == 0) \
			or (self.current_stage == 'Training'):

			self.feedback_label.text = self.feedback_dict['wait']
			
			if not self.feedback_on_screen:
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
		
		self.hold_button.unbind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.iti)
	
	
	
	# Contingency Stages #
	
	def stimulus_response(self, *args): # Trial Outcomes: 0-Premature,1-Hit,2-Miss,3-False Alarm,4-Correct Rejection,5-Hit, no center press,6-False Alarm, no center press
										# Contingencies: 0: Incorrect; 1: Correct; 2: Response, no center touch; 3: Premature response
		
		self.iti_event.cancel()

		self.response_time = time.time()
		self.response_latency = self.response_time - self.stimulus_start_time
		
		self.response_made = True
		self.hold_active = False

		self.protocol_floatlayout.add_event([
			(self.response_time - self.start_time)
			, 'State Change'
			, 'Stimulus Response'
			])
		
		self.response = 1

		self.feedback_label.text = ''
		
		if (self.current_stage == 'SART_Probe'):

			if (self.center_image in self.current_nontarget_image_list):
				self.contingency = 2
				self.trial_outcome = 5
				
			else:
				self.contingency = 2
				self.trial_outcome = 6

		else:

			if (self.center_image == self.target_image):
				self.contingency = 2
				self.trial_outcome = 5
				
				if self.current_stage == 'LimDur_Scaling':
					self.feedback_label.text = self.feedback_dict['too_slow']
				
			else:
				self.contingency = 2
				self.trial_outcome = 6
		
		self.protocol_floatlayout.add_event([
			(self.response_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Trial Response'
			, str(self.response)
			])
			
		self.protocol_floatlayout.add_event([
			(self.response_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Trial Contingency'
			, str(self.contingency)
			])
		
		self.protocol_floatlayout.add_event([
			(self.response_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Trial Outcome'
			, str(self.trial_outcome)
			])
		
		self.protocol_floatlayout.add_event([
			(self.response_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Response Latency'
			, str(self.response_latency)
			])
		
		self.hold_button.bind(on_press=self.response_cancelled)
		self.hold_button.unbind(on_release=self.stimulus_response)
	
	
	
	def center_pressed(self, *args): # Trial Outcomes: 1-Hit,2-Miss,3-False Alarm,4-Correct Rejection,5-Premature,6-Dual Image, wrong side
		
		self.stimulus_present_event.cancel()
		self.stimulus_end_event.cancel()
		self.stimdur_event.cancel()
		self.iti_event.cancel()

		self.hold_active = False

		self.hold_button.unbind(on_press=self.response_cancelled)
		
		self.stimulus_press_time = time.time()
		self.stimulus_press_latency = self.stimulus_press_time - self.stimulus_start_time
		self.movement_latency = self.stimulus_press_latency - self.response_latency

		self.feedback_label.text = ''

		if 'Blur_Scaling' in self.stage_list \
			or self.current_stage == 'Blur_Probe':

			self.protocol_floatlayout.remove_widget(self.blur_widget)
			self.blur_widget.remove_widget(self.img_stimulus_C)
		
		else:
			self.protocol_floatlayout.remove_widget(self.img_stimulus_C)


		if self.stimulus_mask_on_screen:
			self.protocol_floatlayout.remove_widget(self.img_stimulus_C_mask)
			self.stimulus_mask_on_screen = False
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'State Change'
			, 'Stimulus Press'
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Object Remove'
			, 'Stimulus'
			, 'Center'
			, 'Center'
			, 'Image Name'
			, self.center_image
			])

		if 'Noise_Scaling' in self.stage_list \
			or self.current_stage == 'Noise_Probe':
			
			self.protocol_floatlayout.remove_widget(self.img_noise_C)
			
			self.protocol_floatlayout.add_event([
				(self.stimulus_press_time - self.start_time)
				, 'Object Remove'
				, 'Mask'
				, 'Noise'
				, 'Center'
				, 'Image Name'
				, self.noise_mask_value
				])
		

		if self.display_stimulus_outline == 1:
			self.protocol_floatlayout.remove_widget(self.img_outline_C)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Mask'
				, 'Outline'
				, 'Center'
				, 'Image Name'
				, self.display_stimulus_outline
				])
		
		
		if self.current_stage == 'Flanker_Probe':
			self.protocol_floatlayout.remove_widget(self.img_stimulus_L)
			self.protocol_floatlayout.remove_widget(self.img_stimulus_R)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Flanker'
				, 'Left'
				, 'Image Name'
				, self.img_stimulus_L
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Flanker'
				, 'Right'
				, 'Image Name'
				, self.img_stimulus_R
				])
		
		self.stimulus_on_screen = False
		self.limhold_started = False
		self.response_made = False

		self.feedback_label.text = ''
		
		if (self.current_stage == 'SART_Probe'):

			if (self.center_image in self.current_nontarget_image_list):
				self.contingency = 1
				self.trial_outcome = 1
				
				if self.current_block == 0:
					self.feedback_label.text = self.feedback_dict['correct']
			
			else:
				self.contingency = 0
				self.trial_outcome = 3
				
				if self.current_block == 0:
					self.feedback_label.text = self.feedback_dict['incorrect']
		
		else:

			if (self.center_image == self.target_image):
				self.contingency = 1
				self.trial_outcome = 1
				self.current_hits += 1
				self.block_hits += 1
				
				self.feedback_label.text = self.feedback_dict['correct']
				
			else:
				self.contingency = 0
				self.trial_outcome = 3
				self.block_false_alarms += 1
				
				self.feedback_label.text = self.feedback_dict['incorrect']

		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Trial Response'
			, str(self.response)
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Trial Contingency'
			, str(self.contingency)
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Trial Outcome'
			, str(self.trial_outcome)
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Stimulus Press Latency'
			, str(self.stimulus_press_latency)
			])
		
		self.protocol_floatlayout.add_event([
			(self.stimulus_press_time - self.start_time)
			, 'Variable Change'
			, 'Outcome'
			, 'Movement Latency'
			, str(self.movement_latency)
			])
		
		if self.feedback_label.text != '' \
			and not self.feedback_on_screen:
			
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

		self.write_trial()

		if 'Blur_Scaling' in self.stage_list \
			or self.current_stage == 'Blur_Probe':

			self.blur_preload_start_event()
		
		else:
			self.trial_contingency_event()



	def center_notpressed(self, *args):
		
		self.stimulus_present_event.cancel()
		self.stimulus_end_event.cancel()
		self.stimdur_event.cancel()
		self.iti_event.cancel()

		if 'Blur_Scaling' in self.stage_list \
			or self.current_stage == 'Blur_Probe':

			self.protocol_floatlayout.remove_widget(self.blur_widget)
			self.blur_widget.remove_widget(self.img_stimulus_C)
		
		else:
			self.protocol_floatlayout.remove_widget(self.img_stimulus_C)
		

		if self.stimulus_mask_on_screen:
			self.protocol_floatlayout.remove_widget(self.img_stimulus_C_mask)
			self.stimulus_mask_on_screen = False

		self.stimulus_press_time = np.nan
		self.stimulus_press_latency = np.nan
		self.movement_latency = np.nan
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'No Stimulus Press'
			])
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Remove'
			, 'Stimulus'
			, 'Center'
			, 'Center'
			, 'Image Name'
			, self.center_image
			])

		if 'Noise_Scaling' in self.stage_list \
			or self.current_stage == 'Noise_Probe':
			
			self.protocol_floatlayout.remove_widget(self.img_noise_C)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Mask'
				, 'Noise'
				, 'Center'
				, 'Image Name'
				, self.noise_mask_value
				])


		if self.display_stimulus_outline == 1:
			self.protocol_floatlayout.remove_widget(self.img_outline_C)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Mask'
				, 'Outline'
				, 'Center'
				, 'Image Name'
				, self.display_stimulus_outline
				])
		
		
		if self.current_stage == 'Flanker_Probe':
			self.protocol_floatlayout.remove_widget(self.img_stimulus_L)
			self.protocol_floatlayout.remove_widget(self.img_stimulus_R)
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Flanker'
				, 'Left'
				, 'Image Name'
				, self.img_stimulus_L
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Object Remove'
				, 'Stimulus'
				, 'Flanker'
				, 'Right'
				, 'Image Name'
				, self.img_stimulus_R
				])
		
		self.stimulus_on_screen = False
		self.limhold_started = False

		if not self.response_made:
			self.response = 0
			self.response_latency = np.nan

			self.feedback_label.text = ''
			
			if (self.current_stage == 'SART_Probe'):

				if (self.center_image == self.target_image):
					self.contingency = 1
					self.trial_outcome = 4
					self.current_hits += 1
					self.feedback_label.text = self.feedback_dict['correct']
				
				else:
					self.contingency = 0
					self.trial_outcome = 2
			
			else:

				if (self.center_image == self.target_image):
					self.contingency = 0
					self.trial_outcome = 2

					if self.current_stage in ['Training', 'LimDur_Scaling', 'Similarity_Scaling', 'Blur_Scaling', 'Noise_Scaling', 'StimDur_Probe', 'Blur_Probe', 'Noise_Probe']:
						self.feedback_label.text = self.feedback_dict['miss']
				
				else:
					self.contingency = 1
					self.trial_outcome = 4

			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Outcome'
				, 'Trial Response'
				, str(self.response)
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Outcome'
				, 'Trial Contingency'
				, str(self.contingency)
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Outcome'
				, 'Trial Outcome'
				, str(self.trial_outcome)
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Outcome'
				, 'Stimulus Press Latency'
				, str(self.stimulus_press_latency)
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Outcome'
				, 'Movement Latency'
				, str(self.movement_latency)
				])

			self.hold_button.unbind(on_release=self.stimulus_response)

		else:
			self.hold_button.unbind(on_press=self.response_cancelled)
			

		if self.feedback_label.text != '' \
			and not self.feedback_on_screen:
			
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

		self.response_made = False

		self.write_trial()

		if 'Blur_Scaling' in self.stage_list \
			or self.current_stage == 'Blur_Probe':

			self.blur_preload_start_event()
		
		else:
			self.trial_contingency_event()
	
	
	
	def response_cancelled(self, *args):
		
		if self.trial_outcome == 5:
			self.feedback_label.text = self.feedback_dict['miss']

		else:
			self.feedback_label.text = self.feedback_dict['abort']

		self.trial_outcome = 7

		self.hold_active = True
		
		self.center_notpressed()



	def hold_removed_stim(self, *args):
		
		self.hold_active = False
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'State Change'
			, 'Hold Removed'
			])



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
			, 'Instructions'
			, 'Section'
			])
		
		self.protocol_floatlayout.add_event([
			(time.time() - self.start_time)
			, 'Object Remove'
			, 'Button'
			, 'Continue'
			, 'Section'
			])
		
		self.trial_end_time = time.time()
		self.block_end()



	# Data Saving Functions #

	def write_trial(self, *args):

		# self.data_cols = [
		# 	'TrialNo'
		# 	, 'Stage'
		# 	, 'Substage'
		# 	, 'TarProb_Probe'
		# 	, 'Block'
		# 	, 'CurrentBlockTrial'
		# 	, 'Stimulus'
		# 	, 'StimFrames'
		# 	, 'StimDur'
		# 	, 'LimHold'
		# 	, 'Similarity'
		# 	, 'BlurLevel'
		# 	, 'NoiseMaskValue'
		# 	, 'Response'
		# 	, 'Contingency'
		# 	, 'Outcome'
		# 	, 'ResponseLatency'
		# 	, 'StimulusPressLatency'
		# 	, 'MovementLatency'
		# 	]
		
		trial_data = [
			self.current_trial
			, self.current_stage
			, self.current_substage
			, self.target_probability
			, self.current_block
			, self.current_block_trial
			, self.center_image
			, self.stimdur_current_frames
			, self.stimdur
			, self.limhold
			, self.current_similarity
			, self.blur_level
			, self.noise_mask_value
			, self.response
			, self.contingency
			, self.trial_outcome
			, self.response_latency
			, self.stimulus_press_latency
			, self.movement_latency
			]

		self.write_summary_file(trial_data)

		return



	# Trial Contingency Functions #

	def trial_contingency(self, *args):
		# Trial Contingencies: 0-Incorrect; 1-Correct; 2-Response, no center touch; 3-Premature
		# Trial Outcomes: 0-Premature; 1-Hit; 2-Miss; 3-False Alarm; 4-Correct Rejection; 5-Hit, no center touch; 6-False Alarm, no center touch
		
		try:

			self.trial_contingency_event.cancel()

			if self.current_block_trial != 0:
				# print('\n\n\n')
				# print('Trial contingency start')
				# print('')
				# print('Current stage: ', self.current_stage)
				# print('Current block: ', self.current_block)
				
				# if self.current_substage != '':
					# print('Current substage: ', self.current_substage)				
				
				# print('Current trial: ', self.current_trial)
				# print('')
				# print('Trial type: ', self.trial_list[self.trial_index])
				# print('ITI: ', self.iti_length)
				# print('Stimulus duration expected frames: ', self.stimdur_current_frames)
				# print('Stimulus duration expected time: ', self.stimdur)
				# print('Stimulus duration actual time: ', self.stimdur_actual)
				# print('Limited hold: ', self.limhold)

				# if 'Similarity_Scaling' in self.stage_list:
					# print('Similarity value: ', self.current_similarity)

				# if self.current_stage == 'Similarity_Scaling':
					# print('Current similarity min: ', self.similarity_index_min)
					# print('Current similarity max: ', self.similarity_index_max)
					# print('Current similarity range: ', self.similarity_index_range)

				# if 'Blur_Scaling' in self.stage_list \
				# 	or self.current_stage == 'Blur_Probe':

					# print('Blur level (percent): ', self.blur_level)
				
				# if 'Noise_Scaling' in self.stage_list \
				# 	or self.current_stage == 'Noise_Probe':

					# print('Noise level: ', self.noise_mask_value)
				
				# print('')
				# print('Trial outcome: ', self.trial_outcome)
				# print('Response latency: ', self.stimulus_press_latency)
				# print('Center image is: ', self.center_image)
				
				# Trial Outcomes: 0-Premature; 1-Hit; 2-Miss; 3-False Alarm; 4-Correct Rejection; 5-Premature; 6-Dual Image, wrong side
				
				# print('Trial outcome: ', self.trial_outcome)
				
				if (self.current_stage == 'Training') \
					or (self.current_block == 0):
					
					if self.trial_outcome == 1:
						self.last_response = 1
					
					else:
						self.last_response = 0
				
				elif self.current_stage == 'Similarity_Scaling':
					
					if self.trial_outcome == 4:
						self.last_response = 1
					
					elif self.trial_outcome in [2, 3]:
						self.last_response = -1
					
					else:
						self.last_response = 0
				
				elif self.current_stage in ['Blur_Scaling', 'Noise_Scaling', 'Blur_Probe', 'Noise_Probe']:
					
					if self.trial_outcome == 1:
						self.last_response = 1
					
					elif self.trial_outcome in [2, 3]:
						self.last_response = -1
					
					else:
						self.last_response = 0
				
				elif self.current_stage == 'LimDur_Scaling':
					
					if self.trial_outcome == 1:
						self.last_response = 1
					
					elif self.trial_outcome in [2, 3, 5, 6]:
						self.last_response = -1
					
					else:
						self.last_response = 0
				
				elif self.current_stage == 'StimDur_Probe':
					
					if self.trial_outcome in [1, 5]:
						self.last_response = 1
					
					elif self.trial_outcome in [2, 3, 6]:
						self.last_response = -1
					
					else:
						self.last_response = 0
				
				elif (self.current_stage == 'SART_Probe') \
					or ((self.current_stage == 'TarProb_Probe') and (self.target_probability >= 0.75)):
					
					if self.trial_outcome == 4:
						self.last_response = 1
					
					elif self.trial_outcome in [3, 6]:
						self.last_response = -1
					
					else:
						self.last_response = 0

				else:

					if self.trial_outcome == 1:
						self.last_response = 1
					
					elif self.trial_outcome in [3, 6]:
						self.last_response = -1
					
					else:
						self.last_response = 0
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Outcome'
					, 'Last Response'
					, self.last_response
					])

				# if self.last_response != 0:
				self.response_tracking.append(self.last_response)
				
				# print('Last response: ', self.last_response)
				# print('Response tracking: ', self.response_tracking)
				
				if self.last_response == 1:
					# print('Last response correct.')

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Staircasing'
						, 'Increase'
						])

					if self.current_stage == 'Similarity_Scaling':
						self.similarity_tracking.append(self.current_similarity)
						# print('Similarity tracking: ', self.similarity_tracking)

						if len(self.similarity_tracking) >= 20 \
							and self.block_change_on_duration != 1:

							if len(self.similarity_tracking) == 0:
								self.outcome_value = float(
									self.similarity_data.loc[
										self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1]
										, self.target_image
										].to_numpy()
									)
								
							else:
								self.outcome_value = max(self.similarity_tracking)
				
							if (sum(self.response_tracking[-10:]) <= 4) \
								or ((sum(self.response_tracking[-10:] >= 6)) and (statistics.mean(self.similarity_tracking[-10:]) > 0.90)):
						
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Outcome'
									, 'Similarity'
									, self.outcome_value
									, 'Type'
									, 'Mode'
									])

								# print('Similarity Outcome Value: ', self.outcome_value)
								
								baseline_nontarget_image_list = self.similarity_data.loc[
									(self.similarity_data[self.target_image] <= self.outcome_value)
									, 'Nontarget'
									].tolist()
								
								if len(baseline_nontarget_image_list) < (self.similarity_index_range * 2):
									self.current_nontarget_image_list = self.similarity_data.loc[0:(self.similarity_index_range * 2), 'Nontarget']

								else:
									self.current_nontarget_image_list = baseline_nontarget_image_list[-(self.similarity_index_range * 2):]
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Parameter'
									, 'Similarity'
									, str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])])
									, 'Type'
									, 'Baseline'
									, 'Units'
									, 'Min'
									])
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Parameter'
									, 'Similarity'
									, str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])])
									, 'Type'
									, 'Baseline'
									, 'Units'
									, 'Max'
									])

								# print('Baseline nontarget image list: ', self.current_nontarget_image_list)

								self.current_block += 1
								self.protocol_floatlayout.remove_widget(self.hold_button)
								self.stage_screen_event()

						self.similarity_index_min = int(self.nontarget_images.index(self.center_image))
						self.similarity_index_max = self.similarity_index_min + self.similarity_index_range

						if self.similarity_index_max >= len(self.nontarget_images):
							self.similarity_index_max = len(self.nontarget_images) - 1
							self.similarity_index_min = self.similarity_index_max - self.similarity_index_range

						self.current_nontarget_image_list = self.nontarget_images[self.similarity_index_min:self.similarity_index_max]
							
						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Parameter'
							, 'Similarity'
							, str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])])
							, 'Type'
							, 'Staircasing'
							, 'Units'
							, 'Min'
							])
						
						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Parameter'
							, 'Similarity'
							, str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])])
							, 'Type'
							, 'Staircasing'
							, 'Units'
							, 'Max'
							])

					elif self.current_stage in ['Blur_Scaling', 'Blur_Probe']:
						self.blur_tracking.append(self.blur_level)

						if (len(self.blur_tracking) >= 20) \
							and ((max(self.blur_tracking[-6:]) - min(self.blur_tracking[-6:])) <= 2) \
							and (self.block_change_on_duration != 1):

							block_outcome = statistics.multimode(self.blur_tracking)

							if len(block_outcome) != 1:
								self.outcome_value = max(block_outcome)

							else:
								self.outcome_value = int(block_outcome[0])

							self.protocol_floatlayout.add_event([
								(time.time() - self.start_time)
								, 'Variable Change'
								, 'Outcome'
								, 'Blur'
								, self.outcome_value
								, 'Type'
								, 'Mode'
								])

							# print('Blur Outcome Value: ', self.outcome_value)

							if self.current_stage == 'Blur_Scaling':
								self.blur_base = int(self.outcome_value * 0.9)

								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Parameter'
									, 'Blur'
									, self.blur_base
									, 'Type'
									, 'Baseline'
									])

							self.blur_tracking = list()
							self.last_response = 0
							self.current_block += 1
							self.protocol_floatlayout.remove_widget(self.hold_button)
							self.stage_screen_event()

						self.blur_level += self.blur_change

						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Parameter'
							, 'Blur'
							, self.blur_level
							, 'Type'
							, 'Staircasing'
							])

						self.blur_widget.effects = [HorizontalBlurEffect(size=self.blur_level), VerticalBlurEffect(size=self.blur_level)]

					elif self.current_stage in ['Noise_Scaling', 'Noise_Probe']:
						self.noise_tracking.append(int(self.noise_mask_value))

						if len(self.noise_tracking) >= 20 \
							and ((max(self.noise_tracking[-6:]) - min(self.noise_tracking[-6:])) <= 15) \
							and self.block_change_on_duration != 1:

							block_outcome = statistics.multimode(self.noise_tracking)

							if len(block_outcome) != 1:
								self.outcome_value = max(block_outcome)
							
							else:
								self.outcome_value = float(block_outcome[0])

							self.protocol_floatlayout.add_event([
								(time.time() - self.start_time)
								, 'Variable Change'
								, 'Outcome'
								, 'Noise'
								, self.outcome_value
								, 'Type'
								, 'Mode'
								])
							
							# print('Noise Outcome Value: ', self.outcome_value)
							
							if self.current_stage == 'Noise_Scaling':
								self.noise_base = int(self.outcome_value) - 10

								if self.noise_base < 0:
									self.noise_base = 0
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Parameter'
									, 'Noise'
									, self.noise_base
									, 'Type'
									, 'Baseline'
									])

							self.noise_mask_index = round(self.noise_base/5) - 1

							if self.noise_mask_index < 0:
								self.noise_mask_index = 0

							self.noise_tracking = list()
							
							self.last_response = 0
							self.current_block += 1
							self.protocol_floatlayout.remove_widget(self.hold_button)
							self.stage_screen_event()
						
						if self.noise_mask_index < len(self.noise_mask_list) - 1:
							self.noise_mask_index += self.noise_mask_index_change

							if self.noise_mask_index >= len(self.noise_mask_list):
								self.noise_mask_index = len(self.noise_mask_list) - 1

							self.img_noise_C_path = str(self.noise_mask_paths[self.noise_mask_index])
							self.noise_mask_value = self.noise_mask_list[self.noise_mask_index]

						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Parameter'
							, 'Noise'
							, self.noise_mask_value
							, 'Type'
							, 'Staircasing'
							])

						self.img_noise_C.texture = self.image_dict[self.noise_mask_value].image.texture

					elif self.current_stage in ['LimDur_Scaling', 'StimDur_Probe']:
						self.stimdur_frame_tracking.append(self.stimdur_current_frames)

						if (len(self.stimdur_frame_tracking) > 20) \
							and ((max(self.stimdur_frame_tracking[-10:]) - min(self.stimdur_frame_tracking[-10:])) <= 12) \
							and self.block_change_on_duration != 1:

							block_outcome = statistics.multimode(self.stimdur_frame_tracking)

							if len(self.stimdur_frame_tracking) == 0:
								self.outcome_value = 240

							elif len(block_outcome) == 0:
								self.outcome_value = min(self.stimdur_frame_tracking)

							elif len(block_outcome) != 1:
								self.outcome_value = min(block_outcome)
							
							else:
								self.outcome_value = float(block_outcome[0])
							
							# print('StimDur Outcome Value: ', self.outcome_value)

							if self.current_stage == 'LimDur_Scaling':
								self.stimdur_base = self.outcome_value + round(0.100/self.frame_duration)

								if self.stimdur_base > self.staircase_stimdur_frame_max:
									self.stimdur_base = self.staircase_stimdur_frame_max

								self.limhold_base = self.stimdur_base * self.frame_duration

								self.limhold = self.limhold_base
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Outcome'
									, 'Stimulus Duration'
									, self.outcome_value
									, 'Type'
									, 'Mode'
									, 'Units'
									, 'Frames'
									])
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Outcome'
									, 'Stimulus Duration'
									, str(self.outcome_value * self.frame_duration)
									, 'Type'
									, 'Mode'
									, 'Units'
									, 'Seconds'
									])
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Outcome'
									, 'Limited Hold'
									, str(self.outcome_value * self.frame_duration)
									, 'Type'
									, 'Mode'
									, 'Units'
									, 'Seconds'
									])
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Parameter'
									, 'Stimulus Duration'
									, self.stimdur_base
									, 'Type'
									, 'Baseline'
									, 'Units'
									, 'Frames'
									])
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Parameter'
									, 'Stimulus Duration'
									, str(self.stimdur_base * self.frame_duration)
									, 'Type'
									, 'Baseline'
									, 'Units'
									, 'Seconds'
									])
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Parameter'
									, 'Limited Hold'
									, self.limhold
									, 'Type'
									, 'Baseline'
									, 'Units'
									, 'Seconds'
									])

							else:
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Outcome'
									, 'Stimulus Duration'
									, self.outcome_value
									, 'Type'
									, 'Mode'
									, 'Units'
									, 'Frames'
									])
								
								self.protocol_floatlayout.add_event([
									(time.time() - self.start_time)
									, 'Variable Change'
									, 'Outcome'
									, 'Stimulus Duration'
									, str(self.outcome_value * self.frame_duration)
									, 'Type'
									, 'Mode'
									, 'Units'
									, 'Seconds'
									])

							self.stimdur_frame_tracking = list()
							
							self.last_response = 0
							self.current_block += 1
							self.protocol_floatlayout.remove_widget(self.hold_button)
							self.stage_screen_event()

						elif (self.stimdur_use_steps) \
							and (self.stimdur_index < len(self.stimdur_frames) - 1):
							
							self.stimdur_index += 1
							self.stimdur_current_frames = self.stimdur_frames[self.stimdur_index]
							self.stimdur_change = self.stimdur_frames[self.stimdur_index - 1] - self.stimdur_frames[self.stimdur_index]
						
						else:
							
							if (len(self.response_tracking) >= 3) \
								and (sum(self.response_tracking[-3:]) == 3) \
								and (self.stimdur_current_frames > min(self.stimdur_frames)):
								
								# print('Last 3 responses correct; increase stimdur frame change.')

								self.stimdur_index = 0

								while self.stimdur_current_frames < self.stimdur_frames[self.stimdur_index] \
									and self.stimdur_index < len(self.stimdur_frames) - 1:

									self.stimdur_index += 1
								
								self.stimdur_current_frames = self.stimdur_frames[self.stimdur_index]
								self.stimdur_change = self.stimdur_frames[self.stimdur_index - 1] - self.stimdur_frames[self.stimdur_index]
								self.stimdur_use_steps = True
								
								self.response_tracking.append(0)
								self.response_tracking.append(0)							

							else:

								if self.stimdur_current_frames < min(self.stimdur_frames) \
									and self.stimdur_change not in [1, 2]:

									self.stimdur_change = 2

								self.stimdur_current_frames -= self.stimdur_change
						
						
						if self.stimdur_current_frames < self.staircase_stimdur_frame_min:
							self.stimdur_current_frames = self.staircase_stimdur_frame_min
						
						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Outcome'
							, 'Stimulus Duration'
							, self.outcome_value
							, 'Type'
							, 'Staircasing'
							, 'Units'
							, 'Frames'
							])
						
						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Outcome'
							, 'Stimulus Duration'
							, str(self.outcome_value * self.frame_duration)
							, 'Type'
							, 'Staircasing'
							, 'Units'
							, 'Seconds'
							])

						if self.current_stage == 'LimDur_Scaling':
							self.limhold = self.stimdur_current_frames * self.frame_duration
							
							self.protocol_floatlayout.add_event([
								(time.time() - self.start_time)
								, 'Variable Change'
								, 'Outcome'
								, 'Limited Hold'
								, self.limhold
								, 'Type'
								, 'Staircasing'
								, 'Units'
								, 'Seconds'
								])
				
				elif self.last_response == -1:
					# print('Last response incorrect.')

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Staircasing'
						, 'Decrease'
						])

					if self.current_stage == 'Similarity_Scaling':

						if self.center_image != self.target_image:
							self.similarity_index_max = int(self.nontarget_images.index(self.center_image))
							self.similarity_index_min = self.similarity_index_max - self.similarity_index_range
						
						else:
							self.similarity_index_max -= int(self.similarity_index_range//2)
							self.similarity_index_min = self.similarity_index_max - self.similarity_index_range
						

						if self.similarity_index_min < 0:
							self.similarity_index_min = 0
							self.similarity_index_max = self.similarity_index_range

						self.current_nontarget_image_list = self.nontarget_images[self.similarity_index_min:self.similarity_index_max]
							
						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Parameter'
							, 'Similarity'
							, str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])])
							, 'Type'
							, 'Staircasing'
							, 'Units'
							, 'Min'
							])

						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Parameter'
							, 'Similarity'
							, str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])])
							, 'Type'
							, 'Staircasing'
							, 'Units'
							, 'Max'
							])

					elif self.current_stage in ['Blur_Scaling', 'Blur_Probe']:

						if (len(self.response_tracking) >= 2) \
							and (self.response_tracking[-2] in [0, 1]):

							if self.blur_change > 1:
								self.blur_change //= 2

								if self.blur_change < 1:
									self.blur_change = 1

						self.blur_level -= self.blur_change

						if self.blur_level < 0:
							self.blur_level = 0

						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Parameter'
							, 'Blur'
							, self.blur_level
							, 'Type'
							, 'Staircasing'
							])

						self.blur_widget.effects = [HorizontalBlurEffect(size=self.blur_level), VerticalBlurEffect(size=self.blur_level)]


					if self.current_stage in ['Noise_Scaling', 'Noise_Probe']:

						if (len(self.response_tracking) >= 2) \
							and (self.response_tracking[-2] in [0, 1]):

							if self.noise_mask_index_change > 1:
								self.noise_mask_index_change //= 2

								if self.noise_mask_index_change < 1:
									self.noise_mask_index_change = 1

						self.noise_mask_index -= self.noise_mask_index_change
						
						if self.noise_mask_index < 0:
							self.noise_mask_index = 0

						self.img_noise_C_path = str(self.noise_mask_paths[self.noise_mask_index])
						self.noise_mask_value = self.noise_mask_list[self.noise_mask_index]

						self.img_noise_C.texture = self.image_dict[self.noise_mask_value].image.texture
						
						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Parameter'
							, 'Noise'
							, self.noise_mask_value
							, 'Type'
							, 'Staircasing'
							])
					
					elif self.current_stage in ['LimDur_Scaling', 'StimDur_Probe']:
						self.stimdur_use_steps = False
						
						if (len(self.response_tracking) >= 2) \
							and (self.response_tracking[-2] in [0, 1]):
							
							self.stimdur_change //= 2
							
							if self.stimdur_change < 1:
								self.stimdur_change = 1
						
						self.stimdur_current_frames += self.stimdur_change

						if (self.stimdur_current_frames > self.stimdur_base) \
							or (self.stimdur_current_frames > (self.limhold_base/self.frame_duration)):

							if self.stimdur_base > (self.limhold_base/self.frame_duration):
								self.stimdur_current_frames = (self.limhold_base/self.frame_duration)
							
							else:
								self.stimdur_current_frames = self.stimdur_base
						
						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Outcome'
							, 'Stimulus Duration'
							, self.outcome_value
							, 'Type'
							, 'Staircasing'
							, 'Units'
							, 'Frames'
							])
						
						self.protocol_floatlayout.add_event([
							(time.time() - self.start_time)
							, 'Variable Change'
							, 'Outcome'
							, 'Stimulus Duration'
							, str(self.outcome_value * self.frame_duration)
							, 'Type'
							, 'Staircasing'
							, 'Units'
							, 'Seconds'
							])
						

						if self.current_stage == 'LimDur_Scaling':
							self.limhold = self.stimdur_current_frames * self.frame_duration
							
							self.protocol_floatlayout.add_event([
								(time.time() - self.start_time)
								, 'Variable Change'
								, 'Outcome'
								, 'Limited Hold'
								, self.limhold
								, 'Type'
								, 'Staircasing'
								, 'Units'
								, 'Seconds'
								])

			# Set next trial parameters

			# Trial number and trial index

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

			# ITI
			
			if len(self.iti_frame_range) > 1:
				
				if self.iti_fixed_or_range == 'fixed':
					self.iti_length = random.choice(self.iti_frame_range) * self.frame_duration
				
				else:
					self.iti_length = random.randint(min(self.iti_frame_range), max(self.iti_frame_range)) * self.frame_duration

				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Parameter'
					, 'Current ITI'
					, self.iti_length
					])

			# Stimulus duration/limited hold frames

			if self.current_block == 0:				
				self.stimdur_current_frames = self.stimdur_base
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Outcome'
					, 'Stimulus Duration'
					, self.outcome_value
					, 'Type'
					, 'Training'
					, 'Units'
					, 'Frames'
					])
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Outcome'
					, 'Stimulus Duration'
					, str(self.outcome_value * self.frame_duration)
					, 'Type'
					, 'Training'
					, 'Units'
					, 'Seconds'
					])

			if self.current_stage == 'LimDur_Scaling':
				self.limhold = self.stimdur_current_frames * self.frame_duration
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Outcome'
					, 'Limited Hold'
					, self.limhold
					, 'Type'
					, 'Training'
					, 'Units'
					, 'Seconds'
					])

			self.stimdur = self.stimdur_current_frames * self.frame_duration

			if self.stimdur > self.limhold:
				self.limhold = self.stimdur

			# Set next trial type and stimulus
			
			# SART miss (nontarget + no response)
			if (self.contingency == 0) \
				and (self.response == 0) \
				and (self.current_stage == 'SART_Probe'):
				
				# print('Miss (SART)')
				# print('Correction trial initiated...')
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Parameter'
					, 'Stimulus'
					, self.center_image
					, 'Type'
					, 'SART Correction'
					])
			
			# Premature response
			elif self.contingency == 3:
				# print('Premature response')
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Parameter'
					, 'Stimulus'
					, self.center_image
					, 'Type'
					, 'Premature'
					])
			
			# Hit or miss
			else: # Set next stimulus image
				# print('Next trial (hit or miss)')
				# print('Set next stimulus image')

				self.trial_index += 1
				
				if self.trial_index >= len(self.trial_list):
					random.shuffle(self.trial_list)
					self.trial_index = 0
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Parameter'
					, 'Trial Index'
					, self.trial_index
					])
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Parameter'
					, 'Trial Type'
					, self.trial_list[self.trial_index]
					])
				
				if self.trial_list[self.trial_index] == 'Target':
					self.center_image = self.target_image
					self.current_similarity = 1.00
				
				else:
					self.center_image = random.choice(self.current_nontarget_image_list)

					if self.current_stage == 'Similarity_Scaling':

						self.current_similarity = float(self.similarity_data.loc[
								self.similarity_data['Nontarget'] == self.center_image
								, self.target_image
								].to_numpy())
				
				self.img_stimulus_C_image_path = str(self.image_folder / self.center_image) + '.png'
				self.img_stimulus_C.texture = self.image_dict[self.center_image].image.texture
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Parameter'
					, 'Stimulus'
					, self.center_image
					, 'Type'
					, 'Novel'
					])
			
			# Flanker probe - set flankers

			if self.current_stage == 'Flanker_Probe':
				# print('Set flankers.')
				
				if self.flanker_stage_index >= len(self.flanker_stage_list):
					random.shuffle(self.flanker_stage_list)
					self.flanker_stage_index = 0
				
				self.current_substage = self.flanker_stage_list[self.flanker_stage_index]

				# print('Current flanker substage: ', self.current_substage)

				self.flanker_stage_index += 1
				
				if self.current_substage == 'none':
					self.flanker_image = 'black'
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Flanker'
						, self.flanker_image
						, 'Type'
						, 'Blank'
					])

				elif self.current_substage == 'same':
					self.flanker_image = self.center_image
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Flanker'
						, self.flanker_image
						, 'Type'
						, 'Congruent'
					])
				
				elif self.current_substage == 'diff':
					
					if self.trial_list[self.trial_index] == 'Target':
						self.flanker_image = random.choice(self.current_nontarget_image_list)
					
					else:
						self.flanker_image = self.target_image
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Flanker'
						, self.flanker_image
						, 'Type'
						, 'Incongruent'
					])
				
				self.img_stimulus_L.texture = self.image_dict[self.flanker_image].image.texture
				self.img_stimulus_R.texture = self.image_dict[self.flanker_image].image.texture			
			
			self.last_response = 0
			self.trial_outcome = 0

			if self.trial_list[self.trial_index] == 'Target':
				self.block_target_total += 1
			
			# Over session length/duration?
			
			if (self.current_stage == 'Training') \
				and (sum(self.response_tracking) >= self.training_block_max_correct):

				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'State Change'
					, 'Block End'
					])
				
				self.hold_button.unbind(on_release=self.stimulus_response)
				self.contingency = 0
				self.trial_outcome = 0
				self.last_response = 0
				self.current_block += 1

				self.protocol_floatlayout.remove_widget(self.hold_button)
				
				self.block_check_event()
			
			elif (self.current_trial > self.session_trial_max) \
				or ((time.time() - self.start_time) >= self.session_length_max):

				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'State Change'
					, 'Session End'
					])

				# print('Trial/time over session max; end session.')
				self.hold_button.unbind(on_release=self.stimulus_response)
				self.session_event.cancel()
				self.protocol_end()
			
			# Over block length/duration?
			
			elif (self.current_block_trial > self.block_trial_max) \
				or ((time.time() - self.block_start) >= self.block_duration):

				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'State Change'
					, 'Block End'
					])
				
				self.hold_button.unbind(on_release=self.stimulus_response)
				self.contingency = 0
				self.trial_outcome = 0
				self.last_response = 0

				# print('Max trials/duration reached for block')
				
				if self.current_stage == 'Similarity_Scaling':

					if len(self.similarity_tracking) == 0:
						self.outcome_value = float(
							self.similarity_data.loc[
								self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1]
								, self.target_image
								].to_numpy()
							)
					
					else:
						self.outcome_value = max(self.similarity_tracking)

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Outcome'
						, 'Similarity'
						, self.outcome_value
						, 'Type'
						, 'Mode'
						])

					baseline_nontarget_image_list = self.similarity_data.loc[
						(self.similarity_data[self.target_image] <= self.outcome_value)
						, 'Nontarget'
						].tolist()
					
					self.current_nontarget_image_list = baseline_nontarget_image_list[-self.similarity_index_range:]
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Similarity'
						, str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])])
						, 'Type'
						, 'Baseline'
						, 'Units'
						, 'Min'
						])
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Similarity'
						, str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])])
						, 'Type'
						, 'Baseline'
						, 'Units'
						, 'Max'
						])

					self.similarity_tracking = list()

				elif self.current_stage in ['Blur_Scaling', 'Blur_Probe']:
					block_outcome = statistics.multimode(self.blur_tracking)

					if len(block_outcome) == 0:
						self.outcome_value = 0

					elif len(block_outcome) != 1:
						self.outcome_value = max(block_outcome)

					else:
						self.outcome_value = float(block_outcome[0])

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Outcome'
						, 'Blur'
						, self.outcome_value
						, 'Type'
						, 'Mode'
						])

					self.blur_base = int(self.outcome_value * 0.9)
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Blur'
						, self.blur_base
						, 'Type'
						, 'Baseline'
						])

					self.blur_tracking = list()

				elif self.current_stage == 'Noise_Scaling':
					block_outcome = statistics.multimode(self.noise_tracking)

					if len(block_outcome) == 0:
						self.outcome_value = 0

					elif len(block_outcome) != 1:
						self.outcome_value = max(block_outcome)
					
					else:
						self.outcome_value = float(block_outcome[0])
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Outcome'
						, 'Noise'
						, self.outcome_value
						, 'Type'
						, 'Mode'
						])

					self.noise_base = int(self.outcome_value - 10)

					if self.noise_base < 0:
						self.noise_base = 0

					self.noise_mask_index = round(self.noise_base//5) - 1

					if self.noise_mask_index < 0:
						self.noise_mask_index = 0
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Noise'
						, str(self.noise_base)
						, 'Type'
						, 'Baseline'
						])

					self.noise_tracking = list()

				elif self.current_stage == 'LimDur_Scaling':
					block_outcome = statistics.multimode(self.stimdur_frame_tracking)

					if len(self.stimdur_frame_tracking) == 0:
						self.outcome_value = 240

					elif len(block_outcome) == 0:
						self.outcome_value = min(self.stimdur_frame_tracking)

					elif len(block_outcome) != 1:
						self.outcome_value = min(block_outcome)
					
					else:
						self.outcome_value = int(block_outcome[0])
					
					self.stimdur_base = self.outcome_value + int(0.100/self.frame_duration)

					self.limhold_base = self.stimdur_base * self.frame_duration
					self.limhold = self.limhold_base
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Outcome'
						, 'Stimulus Duration'
						, self.outcome_value
						, 'Type'
						, 'Mode'
						, 'Units'
						, 'Frames'
						])
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Outcome'
						, 'Stimulus Duration'
						, str(self.outcome_value * self.frame_duration)
						, 'Type'
						, 'Mode'
						, 'Units'
						, 'Seconds'
						])
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Outcome'
						, 'Limited Hold'
						, str(self.outcome_value * self.frame_duration)
						, 'Type'
						, 'Mode'
						, 'Units'
						, 'Seconds'
						])
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Stimulus Duration'
						, self.stimdur_base
						, 'Type'
						, 'Baseline'
						, 'Units'
						, 'Frames'
						])
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Stimulus Duration'
						, str(self.stimdur_base * self.frame_duration)
						, 'Type'
						, 'Baseline'
						, 'Units'
						, 'Seconds'
						])
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Limited Hold'
						, self.limhold
						, 'Type'
						, 'Baseline'
						, 'Units'
						, 'Seconds'
						])
					
					self.stimdur_frame_tracking = list()

				elif self.current_stage == 'Noise_Probe':
					block_outcome = statistics.multimode(self.noise_tracking)

					if len(block_outcome) == 0:
						self.outcome_value = 0

					elif len(block_outcome) != 1:
						self.outcome_value = max(block_outcome)
					
					else:
						self.outcome_value = float(block_outcome[0])
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Outcome'
						, 'Noise'
						, self.outcome_value
						, 'Type'
						, 'Mode'
						])
					
					self.noise_tracking = list()

				elif self.current_stage == 'StimDur_Probe':
					block_outcome = statistics.multimode(self.stimdur_frame_tracking)

					if len(self.stimdur_frame_tracking) == 0:
						self.outcome_value = self.stimdur_base

					elif len(block_outcome) == 0:
						self.outcome_value = min(self.stimdur_frame_tracking)

					elif len(block_outcome) != 1:
						self.outcome_value = min(block_outcome)
					
					else:
						self.outcome_value = int(block_outcome[0])

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Outcome'
						, 'Stimulus Duration'
						, self.outcome_value
						, 'Type'
						, 'Mode'
						, 'Units'
						, 'Frames'
						])
					
					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Outcome'
						, 'Stimulus Duration'
						, str(self.outcome_value * self.frame_duration)
						, 'Type'
						, 'Mode'
						, 'Units'
						, 'Seconds'
						])
					
					self.stimdur_frame_tracking = list()
				
				self.protocol_floatlayout.remove_widget(self.hold_button)
				
				if self.current_stage == 'Training':
					self.block_check_event()

				else:
					self.current_block += 1
					self.stage_screen_event()

			# print('Trial contingency end')

			self.hold_button.bind(on_press=self.iti)

			self.trial_end_time = time.time()
			
			if self.hold_active == True:
				self.iti()

			elif not self.block_started:
				self.hold_remind_event()
		
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()



	def stage_screen(
		self
		, *args
		):		

		if not self.stage_screen_started:
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'State Change'
				, 'Stage End'
				])

			self.iti_event.cancel()
			self.stimdur_event.cancel()
			self.stimulus_present_event.cancel()
			self.stimulus_end_event.cancel()
			self.hold_remind_event.cancel()

			self.protocol_floatlayout.clear_widgets()
			self.feedback_on_screen = False
			
			if self.current_stage == 'Similarity_Scaling':
				self.outcome_string = 'Great job!\n\nYou were able to correctly discriminate between stimuli\nwith ' + str(int(self.outcome_value*100)) + '%' + ' similarity.'
			
			elif self.current_stage in ['Blur_Scaling', 'Blur_Probe']:
				self.outcome_string = 'Great job!\n\nYou were able to correctly discriminate between stimuli\nwith ' + str(int(self.outcome_value)) + ' pixels of blur.'
			
			elif self.current_stage in ['Noise_Scaling', 'Noise_Probe']:
				self.outcome_string = 'Great job!\n\nYou were able to correctly identify stimuli with \n' + str(100 - self.outcome_value) + '%' + ' of the image visible.'

			elif self.current_stage == 'LimDur_Scaling':
				self.outcome_string = 'Great job!\n\nYou were able to correctly respond to stimuli\nwithin ' + str(round((self.outcome_value * self.frame_duration), 3)) + ' seconds.'
			
			elif self.current_stage == 'StimDur_Probe':
				self.outcome_string = 'Great job!\n\nYou were able to correctly identify stimuli presented\nfor ' + str(int(self.outcome_value)) + ' frames (' + str(round((self.outcome_value * self.frame_duration), 3)) + ' seconds).'

			elif self.current_stage in ['TarProb_Probe', 'Flanker_Probe']:

				if self.block_target_total == 0:
					self.outcome_string = 'Great job!\n\n'
				
				else:
					self.hit_accuracy = (self.block_hits / self.block_target_total)
					self.outcome_string = 'Great job!\n\nYour accuracy on that block was ' + str(round(self.hit_accuracy, 2) * 100) + '%!\n\nYou made ' + str(self.block_false_alarms) + ' false alarms (responses to nontarget images).'
			
			else:
				self.outcome_string = "Great job!\n\n"


			if self.stage_index < len(self.stage_list):
				self.stage_string = 'Please press "CONTINUE" to start the next block.'

			else:
				self.stage_string = 'You have completed this task.\n\nPlease inform your researcher.' # 'Please press "END SESSION" to end the session.'
				self.session_end_button.pos_hint = self.text_button_pos_UC
				self.protocol_floatlayout.add_widget(self.session_end_button)
			
			self.stage_results_label.text = self.outcome_string + '\n\n' + self.stage_string
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

			if self.stage_index < (len(self.stage_list)):
				self.protocol_floatlayout.add_widget(self.stage_continue_button)
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Object Display'
					, 'Button'
					, 'Stage'
					, 'Continue'
					])
	
	
	
	def block_contingency(self, *args):
		
		try:
			
			self.stimulus_present_event.cancel()
			self.stimulus_end_event.cancel()
			self.stimdur_event.cancel()
			self.iti_event.cancel()
			self.hold_remind_event.cancel()
			
			if self.feedback_on_screen:
				
				if (time.time() - self.feedback_start_time) >= self.feedback_length:
					# print('Feedback over')
					self.block_check_event.cancel()
					self.protocol_floatlayout.remove_widget(self.feedback_label)
					self.feedback_label.text = ''
					self.feedback_on_screen = False

				else:
					return
				
			else:
				# print('Block check event cancel')
				self.block_check_event.cancel()
			
			# print('\n\n\n')
			# print('Block contingency start')
			# print('Current block: ', self.current_block)
			# print('Current trial: ', self.current_trial)
		
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

			self.previous_stage = self.current_stage

			self.feedback_label.text = ''

			self.hold_active = False
			self.block_started = True
			
			if (self.current_block > self.block_max_count) or (self.current_block == -1):
				self.stage_index += 1
				self.current_block = 1
				
				# print('Stage index: ', self.stage_index)
	
				if self.stage_index >= len(self.stage_list): # Check if all stages complete
					# print('All stages complete')
					self.session_event.cancel()
					self.protocol_end()

				else:
					self.current_stage = self.stage_list[self.stage_index]
					self.current_substage = ''
					# print('Current stage: ', self.current_stage)
			
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'State Change'
					, 'Stage Change'
					, 'Current Stage'
					, self.current_stage
					])
				
				self.trial_list = ['Target']

				self.stimdur_current_frames = self.stimdur_base

				if 'Blur_Scaling' in self.stage_list \
					or self.current_stage == 'Blur_Probe':

					self.blur_level = self.blur_base
				
				if self.current_stage == 'SART_Probe': # Set SART probe params
					self.current_block = 0
					# print('SART task initialized')
			
			
			if self.stage_index >= len(self.stage_list): # Check if all stages complete again
			
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'State Change'
					, 'Protocol End'
					])
				
				# print('All stages complete')
				self.session_event.cancel()
				self.protocol_end()
			

			if (self.current_stage == 'Training') \
				and (self.skip_tutorial_video == 0) \
				and not self.training_complete:

				self.trial_list = ['Target']
				self.block_trial_max = 2*(self.training_block_max_correct)
				self.block_duration = 3*(self.block_trial_max)
				self.target_probability = 1.0

				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Variable Change'
					, 'Parameter'
					, 'Trial List'
					, self.current_stage
					, 'Probability'
					, self.target_probability
					])
				
				self.block_start = time.time()
				self.block_started = False
				self.training_complete = True

				self.hold_button.bind(on_press=self.iti)
				
				self.protocol_floatlayout.add_widget(self.hold_button)
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Button Displayed'
					, 'Hold Button'
					])

			elif self.current_block == 0:
				# print('Section Training Instructions')
				self.block_trial_max = 2*(self.training_block_max_correct)
				self.block_duration = 3*(self.block_trial_max)
				# print(self.trial_list)
				self.section_instr_label.text = self.instruction_dict[str(self.current_stage)]['train']
				self.instruction_button.text = 'Begin Training Block'
				self.center_instr_image.texture = self.image_dict[self.target_image].image.texture
				
				self.protocol_floatlayout.add_widget(self.center_instr_image)
				self.protocol_floatlayout.add_widget(self.section_instr_label)
				self.protocol_floatlayout.add_widget(self.instruction_button)
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Object Display'
					, 'Image'
					, 'Block'
					, 'Instructions'
					, 'Type'
					, 'Target'
					])
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Object Display'
					, 'Text'
					, 'Block'
					, 'Instructions'
					, 'Type'
					, 'Training'
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
			
			elif self.current_block == 1:
				# print('Section Task Instructions')
				self.section_instr_label.text = self.instruction_dict[str(self.current_stage)]['task']
				
				self.block_trial_max = int(self.parameters_dict['block_trial_max'])
				self.block_duration = self.block_duration_staircase
				self.stimdur_current_frames = self.stimdur_base
				
				if self.current_stage == 'Training':
					self.trial_list = ['Target']
					self.block_trial_max = 2*(self.training_block_max_correct)
					self.block_duration = 3*(self.block_trial_max)
					self.target_probability = 1.0

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Trial List'
						, self.current_stage
						, 'Probability'
						, self.target_probability
						])
				
				elif self.current_stage == 'Similarity_Scaling':
					self.trial_list = self.trial_list_sim
					self.target_probability = self.target_prob_sim / self.target_prob_trial_num

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Trial List'
						, self.current_stage
						, 'Probability'
						, self.target_probability
						])
				
				elif self.current_stage in ['Blur_Scaling', 'Noise_Scaling', 'LimDur_Scaling', 'Noise_Probe', 'Blur_Probe', 'StimDur_Probe', 'MidProb']:
					self.trial_list = self.trial_list_base
					self.target_probability = self.target_prob_base / self.target_prob_trial_num

					if self.current_stage == 'MidProb':
						self.block_duration = self.block_duration_probe

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Trial List'
						, self.current_stage
						, 'Probability'
						, self.target_probability
						])
				
				elif self.current_stage == 'Flanker_Probe':
					self.trial_list = self.trial_list_flanker
					self.target_probability = self.target_prob_sim / self.target_prob_trial_num

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Trial List'
						, self.current_stage
						, 'Probability'
						, self.target_probability
						])
				
				elif self.current_stage == 'TarProb_Probe':
					self.block_max_count = len(self.target_prob_list)
					self.block_duration = self.block_duration_probe
					trial_multiplier = self.block_trial_max / self.target_prob_trial_num

					self.target_prob_list_index = self.current_block - 1
					self.trial_list = list()
					self.target_probability = self.target_prob_list[self.target_prob_list_index] / self.target_prob_trial_num

					self.block_target_total = trial_multiplier * self.target_prob_list[self.target_prob_list_index]

					for iTrial in range(self.target_prob_list[self.target_prob_list_index]):
						self.trial_list.append('Target')

					for iTrial in range((self.target_prob_trial_num - self.target_prob_list[self.target_prob_list_index])):
						self.trial_list.append('Nontarget')

					random.shuffle(self.trial_list)

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Trial List'
						, self.current_stage
						, 'Probability'
						, self.target_probability
						])
				
				elif self.current_stage == 'SART_Probe':
					self.trial_list = self.trial_list_SART
					self.target_probability = self.target_prob_SART / self.target_prob_trial_num
					self.block_duration = self.block_duration_probe

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Trial List'
						, self.current_stage
						, 'Probability'
						, self.target_probability
						])
				
				else:
					# print('Unknown stage!')
					self.trial_list = self.trial_list_base
					self.target_probability = self.target_prob_base / self.target_prob_trial_num

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Trial List'
						, self.current_stage
						, 'Probability'
						, self.target_probability
						])


				self.instruction_button.text = 'Press Here to Start'
				self.center_instr_image.texture = self.image_dict[self.target_image].image.texture
				
				self.protocol_floatlayout.add_widget(self.center_instr_image)
				self.protocol_floatlayout.add_widget(self.section_instr_label)
				self.protocol_floatlayout.add_widget(self.instruction_button)
				
				self.protocol_floatlayout.add_event([
					(time.time() - self.start_time)
					, 'Object Display'
					, 'Image'
					, 'Block'
					, 'Instructions'
					, 'Type'
					, 'Target'
					])
				
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

				if self.current_stage == 'TarProb_Probe':
					self.block_max_count = len(self.target_prob_list)
					self.block_duration = self.block_duration_probe
					trial_multiplier = self.block_trial_max / self.target_prob_trial_num

					self.target_prob_list_index = self.current_block - 1
					self.trial_list = list()
					self.target_probability = self.target_prob_list[self.target_prob_list_index] / self.target_prob_trial_num

					self.block_target_total = trial_multiplier * self.target_prob_list[self.target_prob_list_index]

					for iTrial in range(self.target_prob_list[self.target_prob_list_index]):
						self.trial_list.append('Target')

					for iTrial in range((self.target_prob_trial_num - self.target_prob_list[self.target_prob_list_index])):
						self.trial_list.append('Nontarget')

					random.shuffle(self.trial_list)

					self.protocol_floatlayout.add_event([
						(time.time() - self.start_time)
						, 'Variable Change'
						, 'Parameter'
						, 'Trial List'
						, self.current_stage
						, 'Probability'
						, self.target_probability
						])
				
				# print('Else: Block Screen')
				self.block_started = False
				self.block_event()

			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Stimulus Duration'
				, str(self.stimdur_current_frames)
				, 'Type'
				, 'Staircasing'
				, 'Units'
				, 'Frames'
				])

			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Stimulus Duration'
				, str(self.stimdur_current_frames * self.frame_duration)
				, 'Type'
				, 'Staircasing'
				, 'Units'
				, 'Seconds'
				])
			
			self.protocol_floatlayout.add_event([
				(time.time() - self.start_time)
				, 'Variable Change'
				, 'Outcome'
				, 'Limited Hold'
				, str(self.limhold)
				, 'Type'
				, 'Staircasing'
				, 'Units'
				, 'Seconds'
				])

			self.current_hits = 0
			self.last_response = 0
			self.contingency = 0
			self.trial_outcome = 0
			self.current_block_trial = 0
			self.trial_index = -1
			self.block_target_total = 0
			self.block_false_alarms = 0
			self.block_hits = 0

			self.response_tracking = list()
			
			random.shuffle(self.trial_list)
			# print('Trial list: ', self.trial_list)
			
			self.block_start = time.time()
			
			self.protocol_floatlayout.add_event([
				(self.block_start - self.start_time)
				, 'Variable Change'
				, 'Parameter'
				, 'Block Start Time'
				, str(self.block_start)
				])
			
			# print('Block contingency end')

			if 'Blur_Scaling' in self.stage_list \
				or self.current_stage == 'Blur_Probe':

				self.blur_preload_start_event()
			
			else:
				self.trial_contingency_event()
		

		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:
			
			print('Error; program terminated.')
			self.protocol_end()