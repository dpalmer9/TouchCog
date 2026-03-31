# Imports #

import configparser
import numpy as np
import pandas as pd
import pathlib
import random
import statistics
import time

from Classes.Protocol import ImageButton, ProtocolBase, PreloadedVideo

from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.effectwidget import EffectWidget, HorizontalBlurEffect, VerticalBlurEffect


class ProtocolScreen(ProtocolBase):

	def __init__(self, **kwargs):

		super(ProtocolScreen, self).__init__(**kwargs)
		self.protocol_name = 'CPT'
		self.name = self.protocol_name + '_protocolscreen'
		self.update_task()
		
		# Define Data Columns

		self.data_cols = [
			'TrialNo'
			, 'Stage'
			, 'Substage'
			, 'TarProb'
			, 'Block'
			, 'BlockTrial'
			, 'Stimulus'
			, 'StimFrames'
			, 'StimSeconds'
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
			, 'block_change_on_duration_only'
			, 'training_task'
			, 'similarity_difficulty'
			, 'stimdur_probe'
			, 'flanker_probe'
			, 'tarprob_probe'
			, 'sart_probe'
			, 'iti_fixed_or_range'
			, 'iti_length'
			, 'limited_hold'
			, 'stimulus_duration'
			, 'feedback_length'
			, 'block_duration_max'
			, 'block_min_rest_duration'
			, 'session_duration'
			, 'block_multiplier'
			, 'block_trials_base'
			, 'block_trials_staircasing'
			, 'block_trials_per_flanker_type'
			, 'training_block_max_correct'
			, 'target_prob_base'
			, 'target_prob_hilo'
			, 'trial_list_length_base'
			, 'trial_list_length_hilo'
			, 'trial_list_max_run_base'
			, 'trial_list_max_run_hilo'
			, 'stimulus_family'
			, 'display_stimulus_outline'
			, 'mask_during_limhold'
			, 'limhold_mask_type'
			, 'staircase_hit_rate_criterion'
			, 'staircase_false_alarm_rate_criterion'
			, 'similarity_percentile_initial'
			, 'similarity_percentile_range'
			, 'stimdur_min_frames'
			, 'stimdur_max_seconds'
			]
		
		# Define Variables - Config Import
		
		self.config_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Configuration.ini'
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

		self.image_set_list = [{'name': 'set1','target': 'FA2-1', 'nontargets': ['FA3-2', 'FB1-1', 'FB2-2', 'FC1-1', 'FC3-2']},
					 {'name': 'set2','target': 'FB2-3', 'nontargets': ['FB3-1', 'FA2-2', 'FA4-1', 'FC1-1', 'FC2-2']},
					 {'name': 'set3','target': 'FC1-3', 'nontargets': ['FC4-1', 'FA1-2', 'FA3-3', 'FB2-2', 'FB4-3']},]
		
		self.cjb_image_set_list = [{'name': 'cjb_set1', 
							  		'target': 'left 45', 
									'nontargets': ['right 45'], 
									'neutrals': ['left 22.5', 'vert', 'right 22.5']}]
	
	def _load_config_parameters(self, parameters_dict):
		
		self.participant_id = parameters_dict.get('participant_id', '')

		self.skip_tutorial_video = parameters_dict.get('skip_tutorial_video', 'False')

		self.block_change_on_duration = parameters_dict.get('block_change_on_duration_only', 'True')
		
		self.iti_fixed_or_range = parameters_dict.get('iti_fixed_or_range', 'range')

		self.cjb_iti_length = parameters_dict.get('cjb_iti_length', '1.0,1.5')
		self.cjb_iti_length = self.cjb_iti_length.split(',')

		self.cjb_stimulus_duration = float(parameters_dict.get('cjb_stimulus_duration', '1.0'))
		self.cjb_target_prob = float(parameters_dict.get('cjb_target_prob', '0.33'))
		self.cjb_train_trials = int(parameters_dict.get('cjb_train_trials', '10'))
		self.cjb_discrimination_trials = int(parameters_dict.get('cjb_discrimination_trials', '20'))
		self.cjb_probe_trials = int(parameters_dict.get('cjb_probe_trials', '20'))
		self.cjb_probe_tar_nontar_prob = float(parameters_dict.get('cjb_probe_tar_nontar_prob', '0.33'))
		self.cjb_probe_neutral_prob = float(parameters_dict.get('cjb_probe_neut_prob', '0.34'))
		
		self.iti_temp = parameters_dict.get('iti_length', '0.75,1.25')
		self.iti_temp = self.iti_temp.split(',')
		
		self.stimdur_import = parameters_dict.get('stimulus_duration', '1.5')
		self.stimdur_import = self.stimdur_import.split(',')
		
		self.limhold_import = float(parameters_dict.get('limited_hold', '1.5'))

		self.feedback_length = float(parameters_dict.get('feedback_length', '0.75'))
		self.block_duration_max = int(parameters_dict.get('block_duration_max', '420'))
		self.block_min_rest_duration = float(parameters_dict.get('block_min_rest_duration', '2'))
		self.session_duration = float(parameters_dict.get('session_duration', '3600'))
		
		self.block_multiplier = int(parameters_dict.get('block_multiplier', '1'))
		self.block_trial_max_base = int(parameters_dict.get('block_trials_base', '120'))
		self.block_trial_max_staircase = int(parameters_dict.get('block_trials_staircasing', '180'))
		self.block_trial_max_flanker = int(parameters_dict.get('block_trials_per_flanker_type', '60')) * 3
		self.training_block_max_correct = int(parameters_dict.get('training_block_max_correct', '10'))

		self.target_prob_base = float(parameters_dict.get('target_prob_base', '0.33'))
		self.target_prob_hilo_import = parameters_dict.get('target_prob_hilo', '0.15, 0.85')
		self.target_prob_hilo_import = self.target_prob_hilo_import.split(',')
		
		self.trial_list_length_base = int(parameters_dict.get('trial_list_length_base', '15'))
		self.trial_list_length_hilo = int(parameters_dict.get('trial_list_length_hilo', '20'))
		
		self.trial_list_max_run_base = int(parameters_dict.get('trial_list_max_run_base', '3'))
		self.trial_list_max_run_hilo = int(parameters_dict.get('trial_list_max_run_hilo', '10'))
		
		self.stimulus_family = parameters_dict.get('stimulus_family', 'Blues')

		self.display_stimulus_outline = int(parameters_dict.get('display_stimulus_outline', 'True'))
		self.mask_during_limhold = int(parameters_dict.get('mask_during_limhold', 'True'))
		self.limhold_mask_type = parameters_dict.get('limhold_mask_type', 'noise')

		self.staircase_hr_criterion = float(parameters_dict.get('staircase_hit_rate_criterion', '0.80'))
		self.staircase_far_criterion = float(parameters_dict.get('staircase_false_alarm_rate_criterion', '0.40'))

		self.similarity_percentile_initial = float(parameters_dict.get('similarity_percentile_initial', '50'))
		self.similarity_percentile_range = float(parameters_dict.get('similarity_percentile_range', '5'))

		self.stimdur_frame_min = float(parameters_dict.get('stimdur_min_frames', '2'))
		self.stimdur_seconds_max = float(parameters_dict.get('stimdur_max_seconds', '2.00'))

		self.image_set = parameters_dict.get('image_set', 'rand')
		if self.image_set == None:
			self.image_set = 'rand'

		self.cjb_image_set = parameters_dict.get('cjb_image_set', 'cjb_set1')
		if self.cjb_image_set == None:
			self.cjb_image_set = 'cjb_set1'
		
		self.hold_image = self.config_file['Hold']['hold_image']
		self.mask_image = self.config_file['Mask']['mask_image']
		
		
		# Create stage list and import stage parameters
		
		self.stage_list = list()

		if parameters_dict.get('cjb_training_task', 'False'):
			self.stage_list.append('CJB_Training')
		
		if parameters_dict.get('cjb_discrimination_task', 'False'):
			self.stage_list.append('CJB_Discrimination')
		
		if parameters_dict.get('cjb_probe_task', 'False'):
			self.stage_list.append('CJB_Probe')

		# Check if one of the CJB tasks was appended to stage list. If so, set self.cjb_task to True
		self.cjb_task = any(stage in ['CJB_Training', 'CJB_Discrimination', 'CJB_Probe'] for stage in self.stage_list)
		
		if parameters_dict.get('training_task', 'True'):
			self.stage_list.append('Training')

		# if parameters_dict['limhold_difficulty']:
		# 	self.stage_list.append('LimHold_Staircase_Difficulty')

		if parameters_dict.get('similarity_difficulty', 'True'):
			self.stage_list.append('Similarity_Staircase_Difficulty')
			self.stimulus_family = 'Fb'
		
		else:
			self.stimulus_family = parameters_dict.get('stimulus_family', 'Blues')

		if parameters_dict.get('stimdur_probe', 'True'):
			self.stage_list.append('StimDur_Staircase_Probe')

		if parameters_dict.get('flanker_probe', 'True'):
			self.stage_list.append('Flanker_Fixed_Probe')

		if parameters_dict.get('tarprob_probe', 'True'):
			self.stage_list.append('TarProb_Fixed_Probe')

		if parameters_dict.get('sart_probe', 'False'):
			self.stage_list.append('SART_Fixed_Probe')

		self.image_set = parameters_dict.get('image_set', 'rand')
		if self.image_set == None and 'Similarity_Staircase_Difficulty' not in self.stage_list:
			self.image_set = 'set1'
		else:
			self.image_set = 'Fb2_1132'
	
	def _load_task_variables(self):
		# Set images

		self.similarity_data = pd.DataFrame({})

		self.target_image = ''
		self.target_image_path = ''

		self.cjb_target_image = ''
		self.cjb_nontarget_image = ''
		self.cjb_neutral_target_image = ''
		self.cjb_neutral_nontarget_image = ''
		self.cjb_neutral_true_image = ''

		self.similarity_index = 0
		
		
		# Define Language
		self.set_language(self.language)
		self.stage_instructions = ''
		
		
		# Define Variables - Boolean
		
		self.stimulus_on_screen = False
		self.limhold_started = False
		self.response_made = False
		self.stimulus_mask_on_screen = True
		self.training_complete = False
		self.premature_override = True
		self.stage_screen_started = False
		self.stimdur_video_played = False
		self.sim_scale_video_played = False
		self.tar_prob_video_played = False
		self.data_file_generated = False
		# Re-check if a CJB task is the first stage in self.stage_list. If so, set self.cjb_task to True
		self.cjb_task = self.stage_list[0] in ['CJB_Training', 'CJB_Discrimination', 'CJB_Probe']


		
		# Define Variables - Count
		
		self.current_block = -1
		self.current_block_trial = 0

		self.current_hits = 0
		
		self.stage_index = -1
		self.trial_index = 0
		
		self.block_max_count = self.block_multiplier
		self.block_trial_max = self.block_trial_max_base
		self.block_duration = self.block_duration_max

		self.trial_outcome = 0 # 0-Premature,1-Hit,2-Miss,3-False Alarm,4-Correct Rejection,5-Correct, no center tap,6-Incorrect, no center tap,7-Trial abort (lift and press hold button during stimulus display)
		self.contingency = 0
		self.response = 0

		self.target_probability = 1.0

		self.block_target_total = 0
		self.block_false_alarms = 0
		
		
		# Define Variables - Staircasing
		
		self.last_response = 0
		
		self.blur_tracking = list()
		self.noise_tracking = list()
		self.stimdur_frame_tracking = list()

		self.similarity_tracking = list()
		self.decision_point_tracking = list()

		self.hit_tracking = list()
		self.total_hit_tracking = list()
		self.false_alarm_tracking = list()
		self.total_false_alarm_tracking = list()
		self.staircase_index_tracking = list()

		self.staircase_flag = 0
		self.last_staircase = None

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
		self.current_stage = ''
		
		
		# Define Variables - Time
		
		self.stimulus_start_time = 0.0
		self.response_latency = 0.0
		self.stimulus_press_latency = 0.0
		self.movement_latency = 0.0
		self.frame_duration = 1/self.maxfps
		self.stimdur_actual = 0.0
		self.trial_end_time = 0.0

		self.stimulus_image_proportion = 0.35
		self.instruction_image_proportion = 0.25

	def _load_staircase_variables(self):

		self.iti_temp = [float(iNum) for iNum in self.iti_temp]
		self.iti_frame_range = sorted((np.array(self.iti_temp) // self.frame_duration).tolist(), reverse=True)
		self.iti_frame_range = [int(iNum) for iNum in self.iti_frame_range]
		self.iti_length = self.iti_frame_range[0] * self.frame_duration
		
		self.stimdur_import = [float(iNum) for iNum in self.stimdur_import]

		stimdur_frame_steps = np.round(np.array(self.stimdur_import) / self.frame_duration, decimals=0)
		
		if 0 in stimdur_frame_steps:
			stimdur_frame_steps += 1

		self.stimdur_frame_list = sorted(stimdur_frame_steps.tolist(), reverse=True)
		self.stimdur_index = 0

		self.stimdur_frames = self.stimdur_frame_list[self.stimdur_index]
		self.stimdur_seconds = self.stimdur_frames * self.frame_duration

		if self.stimdur_frame_min < 1:
			self.stimdur_frame_min = 1

		self.stimdur_base = self.stimdur_frames
		self.stimdur_change = self.stimdur_frames / 2

		self.limhold_seconds = self.limhold_import
		self.limhold_base = self.limhold_seconds
		
		if self.stimdur_seconds_max > self.limhold_seconds:
			self.stimdur_seconds_max = self.limhold_seconds
		
		self.stimdur_frame_max = self.stimdur_seconds_max // self.frame_duration
		
		self.stimdur_use_steps = True

		
	def _setup_session_stages(self):
		# General properties
		self.trial_list_base = list()
		self.staircase_min_target_trials = round((self.trial_list_length_base * self.target_prob_base))
		self.staircase_min_nontarget_trials = self.trial_list_length_base - self.staircase_min_target_trials

		for iTrial in range(self.staircase_min_target_trials):
			self.trial_list_base.append('Target')
		
		for iTrial in range(self.staircase_min_nontarget_trials):
			self.trial_list_base.append('Nontarget')

		# CJB discrimination trial list
		cjb_discrim_min_target_trials = round((self.cjb_discrimination_trials * self.cjb_target_prob))
		cjb_discrim_min_nontarget_trials = self.cjb_discrimination_trials - cjb_discrim_min_target_trials
		self.trial_list_cjb_discrimination = list()

		for iTrial in range(cjb_discrim_min_target_trials):
			self.trial_list_cjb_discrimination.append('Target')

		for iTrial in range(cjb_discrim_min_nontarget_trials):
			self.trial_list_cjb_discrimination.append('Nontarget')

		# CJB Probe Trial List - requires a third group of "Neutral" trials. Each of the three neutral images will be presented in equal proportion, and the target and nontarget will be presented in equal proportion to each other and to the neutrals.
		cjb_probe_min_target_trials = round((self.cjb_probe_trials * (self.cjb_probe_tar_nontar_prob / 2)))
		cjb_probe_min_nontarget_trials = round((self.cjb_probe_trials * (self.cjb_probe_tar_nontar_prob / 2)))
		cjb_probe_min_neutral_tar_trials = round((self.cjb_probe_trials * (self.cjb_probe_neutral_prob / 3)))
		cjb_probe_min_neutral_nontar_trials = round((self.cjb_probe_trials * (self.cjb_probe_neutral_prob / 3)))
		cjb_probe_min_neutral_true_trials = round((self.cjb_probe_trials * (self.cjb_probe_neutral_prob / 3)))
		self.trial_list_cjb_probe = list()
		for iTrial in range(cjb_probe_min_target_trials):
			self.trial_list_cjb_probe.append('Target')
		for iTrial in range(cjb_probe_min_nontarget_trials):
			self.trial_list_cjb_probe.append('Nontarget')
		for iTrial in range(cjb_probe_min_neutral_tar_trials):
			self.trial_list_cjb_probe.append('Neutral-Target')
		for iTrial in range(cjb_probe_min_neutral_nontar_trials):
			self.trial_list_cjb_probe.append('Neutral-Nontarget')
		for iTrial in range(cjb_probe_min_neutral_true_trials):
			self.trial_list_cjb_probe.append('Neutral-True')

		
		self.trial_list_max_run = self.trial_list_max_run_base
		self.trial_list = self.constrained_shuffle(self.trial_list_base, max_run=self.trial_list_max_run)
		
		if (any(['TarProb', 'SART']) in xStage for xStage in self.stage_list):
			self.trial_list_hilo = list()
			self.target_prob_hilo = sorted([float(iProb) for iProb in self.target_prob_hilo_import])
		
			# for iTrial in range(round((self.trial_list_length_hilo * self.target_prob_hilo[0]))):
			# 	self.trial_list_hilo.append('Target')
		
			# for iTrial in range(len(self.trial_list_hilo), self.trial_list_length_hilo):
			# 	self.trial_list_hilo.append('Nontarget')
				
		if 'Flanker_Fixed_Probe' in self.stage_list:
			self.flanker_stage_index = 0
			self.flanker_stage_list = ['non', 'con', 'inc', 'non', 'con', 'inc']
			self.flanker_stage_list = self.constrained_shuffle(self.flanker_stage_list, max_run=3)
			self.current_substage = ''
			self.flanker_image = ''
	
			self.trial_list_flanker_dict = {
				'non': self.constrained_shuffle(self.trial_list_base, max_run=self.trial_list_max_run)
				, 'con': self.constrained_shuffle(self.trial_list_base, max_run=self.trial_list_max_run)
				, 'inc': self.constrained_shuffle(self.trial_list_base, max_run=self.trial_list_max_run)
				}
			
			self.trial_list_flanker_index_dict = {'non': 0, 'con': 0, 'inc': 0}
	
	def _setup_image_widgets(self):
		# Set images
		self.image_folder = self.app.app_root / 'Protocol' / self.protocol_name / 'Image'

		self.mask_image_path = self.image_folder / str(self.mask_image + '.png')

		self.fribble_folder = pathlib.Path('Fribbles', self.stimulus_family)

		self.stimulus_image_path_list = sorted(list(self.image_folder.glob(str(self.fribble_folder / '*.png'))))

		if 'Similarity_Staircase_Difficulty' in self.stage_list:
			self.similarity_data = pd.read_csv(str(self.image_folder / self.fribble_folder / str(self.stimulus_family + '-SSIM_Data.csv')))

			stimulus_list = list(self.similarity_data.columns)
			stimulus_list.remove('Nontarget')
			if self.image_set == 'rand':
				self.target_image = random.choice(stimulus_list)
			else:
				self.target_image = self.image_set

			self.similarity_data = self.similarity_data.loc[:, ['Nontarget', self.target_image]]

			self.similarity_data = self.similarity_data.drop(
				self.similarity_data[
					self.similarity_data['Nontarget'] == self.target_image
					].index
				)

			self.similarity_data = self.similarity_data.sort_values(by=self.target_image, ascending=True)

			self.nontarget_images = self.similarity_data['Nontarget'].tolist()

			self.similarity_index_max = int(len(self.nontarget_images) * (self.similarity_percentile_initial / 100))
			self.similarity_index_range = int(len(self.nontarget_images) * (self.similarity_percentile_range/100))

			if self.similarity_index_max < self.similarity_index_range:
				self.similarity_index_max = self.similarity_index_range

			elif self.similarity_index_max > len(self.nontarget_images):
				self.similarity_index_max = len(self.nontarget_images)
			
			self.similarity_index_min = self.similarity_index_max - self.similarity_index_range
			
			self.current_nontarget_image_list = self.nontarget_images[self.similarity_index_min:self.similarity_index_max]

			self.current_similarity = 1.00

		else:
			stimulus_image_list = list()

			for filename in self.stimulus_image_path_list:
				stimulus_image_list.append(filename.stem)

			
			if self.image_set == 'rand':
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
			else:
				self.current_image_set = next((item for item in self.image_set_list if item["name"] == self.image_set), None)
				self.target_image = self.current_image_set['target']
				self.nontarget_images = self.current_image_set['nontargets']
				self.current_nontarget_image_list = self.nontarget_images
	

		total_image_list = self.stimulus_image_path_list

		# CJB Image Preparation
		if 'CJB_Training' in self.stage_list or 'CJB_Discrimination' in self.stage_list or 'CJB_Probe' in self.stage_list:
			self.cjb_current_image_set = next((item for item in self.cjb_image_set_list if item["name"] == self.cjb_image_set), None)
			self.cjb_target_image = self.cjb_current_image_set['target']
			self.cjb_nontarget_image = self.cjb_current_image_set['nontargets'][0]
			self.cjb_neutral_target_image = self.cjb_current_image_set['neutrals'][0]
			self.cjb_neutral_nontarget_image = self.cjb_current_image_set['neutrals'][2]
			self.cjb_neutral_true_image = self.cjb_current_image_set['neutrals'][1]

			cjb_total_images = [self.cjb_target_image,self.cjb_nontarget_image,self.cjb_neutral_target_image, self.cjb_neutral_nontarget_image, self.cjb_neutral_true_image]
			cjb_total_image_paths = [self.image_folder / 'CJB' / (str(image_name) + '.png') for image_name in cjb_total_images]
			total_image_list += cjb_total_image_paths

		# Staircasing - Noise Masks

		self.noise_mask_index = 0

		self.noise_mask_paths = sorted(list(self.image_folder.glob('Noise_Masks-Circle/*.png')))
		self.noise_mask_list = list()

		for filename in self.noise_mask_paths:
			self.noise_mask_list.append(filename.stem)

		self.noise_mask_value = self.noise_mask_list[self.noise_mask_index]

		total_image_list += self.noise_mask_paths

		# GUI Parameters
		self.stimulus_image_size = ((self.stimulus_image_proportion * self.width_adjust), (self.stimulus_image_proportion * self.height_adjust))
		self.instruction_image_size = ((self.instruction_image_proportion * self.width_adjust), (self.instruction_image_proportion * self.height_adjust))
		self.stimulus_mask_size = (self.stimulus_image_size[0] * 1.2, self.stimulus_image_size[1] * 1.2)
		self.text_button_size = [0.4, 0.15]

		self.stimulus_pos_C = {"center_x": 0.50, "center_y": 0.5}
		self.stimulus_pos_L = {"center_x": 0.20, "center_y": 0.5}
		self.stimulus_pos_R = {"center_x": 0.80, "center_y": 0.5}

		self.instruction_image_pos_C = {"center_x": 0.50, "center_y": 0.75}

		self.text_button_pos_UC = {"center_x": 0.50, "top": 0.99}
		self.text_button_pos_LL = {"center_x": 0.25, "y": 0.01}
		self.text_button_pos_LC = {"center_x": 0.50, "y": 0.01}
		self.text_button_pos_LR = {"center_x": 0.75, "y": 0.01}

		# Load images

		self.hold_image_path = self.image_folder / (self.hold_image + '.png')
		self.mask_image_path = self.image_folder / (self.mask_image + '.png')
		self.outline_mask_path = self.image_folder / 'whitecircle.png'

		total_image_list += [self.hold_image_path, self.mask_image_path]
		self.load_images(total_image_list)

		# Create ImageButton Widgets
		# Define Widgets - Images

		self.tutorial_stimulus_image = ImageButton(source=str(self.image_folder / self.fribble_folder / (self.target_image + '.png')))
		self.tutorial_continue_button.bind(on_press=self.tutorial_video_stop)
		
		self.hold_button.source = str(self.hold_image_path)
		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.unbind(on_release=self.hold_remind)
		self.hold_button.bind(on_release=self.premature_response)
		
		self.img_stimulus_C = ImageButton()
		self.img_stimulus_C.size_hint = self.stimulus_image_size
		self.img_stimulus_C.pos_hint = self.stimulus_pos_C
		self.img_stimulus_C.bind(on_press=self.center_pressed)
		self.img_stimulus_C.name = 'Center Stimulus'

		self.img_stimulus_L = ImageButton(source=str(self.mask_image_path))
		self.img_stimulus_L.size_hint = self.stimulus_image_size
		self.img_stimulus_L.pos_hint = self.stimulus_pos_L

		self.img_stimulus_R = ImageButton(source=str(self.mask_image_path))
		self.img_stimulus_R.size_hint = self.stimulus_image_size
		self.img_stimulus_R.pos_hint = self.stimulus_pos_R

		self.center_instr_image = ImageButton(source=str(self.mask_image_path))
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

		self.img_outline_C = ImageButton(source=str(self.outline_mask_path))
		self.img_outline_C.size_hint = self.stimulus_mask_size
		self.img_outline_C.pos_hint = self.stimulus_pos_C
		self.img_outline_C.bind(on_press=self.center_pressed)
		self.img_outline_C.name = 'Center Outline Mask'

		self.img_outline_L = ImageButton(source=str(self.outline_mask_path))
		self.img_outline_L.size_hint = self.stimulus_mask_size
		self.img_outline_L.pos_hint = self.stimulus_pos_L
		self.img_outline_L.name = 'Left Outline Mask'

		self.img_outline_R = ImageButton(source=str(self.outline_mask_path))
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


		if any(True for stage in ['Blur_Staircase_Difficulty', 'Blur_Staircase_Probe'] if stage in self.stage_list):
			self.blur_widget = EffectWidget()
			self.blur_widget.effects = [HorizontalBlurEffect(size=self.blur_level), VerticalBlurEffect(size=self.blur_level)]
	

	def _setup_language_localization(self):		
		self.set_language(self.language)
		self.stage_instructions = ''

		button_lang_path = self.lang_folder_path / 'Button.ini'
		button_lang_config = configparser.ConfigParser()
		button_lang_config.read(button_lang_path, encoding='utf-8')

		self.stage_continue_button.text = button_lang_config.get('Buttons', 'stage_continue', fallback='Continue')
		self.session_end_button.text = button_lang_config.get('Buttons', 'session_end', fallback='End Session')
		self.training_block_button_str = button_lang_config.get('Buttons', 'instruction_training', fallback='Begin Training Block')

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

		# Instruction Import

		self.lang_folder_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language


		if (self.lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_path = self.lang_folder_path / 'Tutorial_Video' / 'CPT-Tutorial_Video-2025-09-22.mp4'
			self.sim_scale_video_path = self.lang_folder_path / 'Tutorial_Video' / 'CPT-General-2025-09-18.mp4'
			self.stimdur_video_path = self.lang_folder_path / 'Tutorial_Video' / 'CPT-StimDur-2025-09-18.mp4'
			self.tar_prob_video_path = self.lang_folder_path / 'Tutorial_Video' / 'CPT-General-2025-09-18.mp4'

			self.tutorial_video = PreloadedVideo(
				source_path = str(self.tutorial_video_path)
				, pos_hint = {'center_x': 0.5, 'center_y': 0.5 + self.text_button_size[1]}
				, fit_mode = 'contain',
				loop=False
				)

		# Define Instruction Components
		
		# Instruction - Dictionary
		
		self.instruction_path = str(self.lang_folder_path / 'Instructions.ini')
		
		self.instruction_config = configparser.ConfigParser(allow_no_value = True)
		self.instruction_config.read(self.instruction_path, encoding = 'utf-8')
		
		self.instruction_dict = {}
		# self.instruction_dict['Training'] = {}
		# self.instruction_dict['LimHold_Staircase_Difficulty'] = {}
		# self.instruction_dict['Similarity_Staircase_Difficulty'] = {}
		# self.instruction_dict['Noise_Staircase_Difficulty'] = {}
		# self.instruction_dict['Blur_Staircase_Difficulty'] = {}
		# self.instruction_dict['Noise_Staircase_Probe'] = {}
		# self.instruction_dict['Blur_Staircase_Probe'] = {}
		# self.instruction_dict['StimDur_Staircase_Probe'] = {}
		# self.instruction_dict['TarProb_Fixed_Probe'] = {}
		# self.instruction_dict['Flanker_Fixed_Probe'] = {}
		# self.instruction_dict['SART_Fixed_Probe'] = {}
		
		for stage in self.stage_list:
			self.instruction_dict[stage] = {}
			self.instruction_dict[stage]['train'] = self.instruction_config.get(stage, 'train', fallback='')
			self.instruction_dict[stage]['task'] = self.instruction_config.get(stage, 'task', fallback='')


		feedback_lang_path = str(self.lang_folder_path / 'Feedback.ini')
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

		# Instruction - ImageButton
		self.tutorial_stimulus_image = ImageButton(source=str(self.image_folder / self.fribble_folder / (self.target_image + '.png')))
		self.tutorial_outline = ImageButton(source=str(self.outline_mask_path))
		self.tutorial_checkmark = ImageButton(source=str(self.image_folder / 'checkmark.png'))
		self.tutorial_continue_button.bind(on_press=self.tutorial_target_present_screen)
		self.tutorial_start_button.bind(on_press=self.section_start)
		
		
		self.tutorial_stimulus_image.size_hint = self.stimulus_image_size
		self.tutorial_stimulus_image.pos_hint = {'center_x': 0.5, 'center_y': 0.6}
		self.tutorial_outline.size_hint = self.stimulus_mask_size
		self.tutorial_outline.pos_hint = {'center_x': 0.5, 'center_y': 0.6}
		self.tutorial_checkmark.size_hint = ((0.2 * self.width_adjust), (0.2 * self.height_adjust))
		self.tutorial_checkmark.pos_hint = {'center_x': 0.52, 'center_y': 0.9}
		
		# Instruction - Text Widget
		self.section_instr_string = ''
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
		self.stage_continue_button.bind(on_release=self.block_contingency)
		
		self.session_end_button = Button(font_size='60sp')
		self.session_end_button.size_hint = self.text_button_size
		self.session_end_button.pos_hint = self.text_button_pos_LL
		self.session_end_button.bind(on_press=self.protocol_end)
		
		
		self.protocol_floatlayout.clear_widgets()

	def _constrained_shuffle_cjb(self, trial_list, max_run=3):
		# Create copy of trial list only containing target and nontarget trials
		target_nontarget_trials = [trial for trial in trial_list if trial in ['Target', 'Nontarget']]
		other_trials = [trial for trial in trial_list if trial not in ['Target', 'Nontarget']]

		# Use the constrained shuffle function to shuffle the target and nontarget trials
		shuffled_target_nontarget_trials = self.constrained_shuffle(target_nontarget_trials, max_run=max_run)
		# Use random to create a list of index positions to insert the other trials back into the shuffled list
		insert_positions = sorted(random.sample(range(len(shuffled_target_nontarget_trials) + len(other_trials)), len(other_trials)))
		# Create new list to hold the final shuffled trials
		final_shuffled_trials = []
		# Copy target_nontarget_trials into final list, then insert other trials at the randomly generated index positions
		target_nontarget_index = 0
		other_trials_index = 0
		for i in range(len(shuffled_target_nontarget_trials) + len(other_trials)):
			if i in insert_positions:
				final_shuffled_trials.append(other_trials[other_trials_index])
				other_trials_index += 1
			else:
				final_shuffled_trials.append(shuffled_target_nontarget_trials[target_nontarget_index])
				target_nontarget_index += 1
		return final_shuffled_trials

	def load_parameters(self, parameters_dict):
		self.parameters_dict = parameters_dict
		self._load_config_parameters(self.parameters_dict)
		self._load_task_variables()
		self._load_staircase_variables()
		self._setup_session_stages()
		self._setup_image_widgets()
		self._load_video_and_instruction_components()
		self._setup_language_localization()
		self.generate_output_files()
		self.metadata_output_generation()

		#self.start_button.bind(on_press=self.start_protocol_from_tutorial)

		self.start_clock()
		if (self.lang_folder_path / 'Tutorial_Video').is_dir():

			self.protocol_floatlayout.clear_widgets()
			self.trigger_tutorial_screen()
		
		else:
			self.present_tutorial_text()


	# Protocol Staging


	def present_tutorial_text(self, *args):

		self.protocol_floatlayout.clear_widgets()

		self.tutorial_continue_button.pos_hint = self.text_button_pos_LR

		self.instruction_label.pos_hint = {'center_x': 0.5, 'y': 0.35}
		self.instruction_label.text = self.instruction_config['Main']['no_video']
		
		self.protocol_floatlayout.add_widget(self.instruction_label)
		self.protocol_floatlayout.add_widget(self.tutorial_continue_button)

		self.protocol_floatlayout.add_stage_event('Instruction Presentation')
		self.protocol_floatlayout.add_text_event('Displayed', 'Task Instruction')
		self.protocol_floatlayout.add_stage_event('Object Display')
		return


	def tutorial_video_stop(self, *args):

		self.tutorial_video.state = 'stop'
		self.protocol_floatlayout.add_object_event('Remove', 'Video', 'Section', 'Instructions')
		self.tutorial_target_present_screen()



	def tutorial_target_present_screen(self, *args):
		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_widget(self.tutorial_checkmark)
		# Update the tutorial stimulus image to the target image depending on whether it is a CJB task
		if self.cjb_task:
			self.tutorial_stimulus_image.source = str(self.image_folder / 'CJB' / (str(self.cjb_target_image) + '.png'))
		else:
			self.tutorial_stimulus_image.source = str(self.image_folder / self.fribble_folder / (self.target_image + '.png'))
		self.protocol_floatlayout.add_widget(self.tutorial_stimulus_image)
		self.protocol_floatlayout.add_widget(self.tutorial_outline)
		self.protocol_floatlayout.add_widget(self.tutorial_start_button)
		return



	def start_protocol_from_tutorial(self, *args):

		self.protocol_floatlayout.clear_widgets()

		if not self.data_file_generated:
			self.generate_output_files()
			self.metadata_output_generation()
			self.data_file_generated = True

		self.block_contingency()
		return



	def blur_preload_start(self, *args):

		self.img_stimulus_C.texture = self.image_dict[self.mask_image].image.texture

		self.protocol_floatlayout.add_widget(self.blur_widget)
		self.blur_widget.add_widget(self.img_stimulus_C)

		self.blur_preload_end()



	def blur_preload_end(self, *args):
		self.protocol_floatlayout.remove_widget(self.blur_widget)
		self.blur_widget.remove_widget(self.img_stimulus_C)

		self.trial_contingency()



	def stimulus_present(self, *args): # Present stimulus
		if 'Blur_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Blur_Staircase_Probe':

			self.blur_widget.add_widget(self.img_stimulus_C)
			self.protocol_floatlayout.add_widget(self.img_noise_C)
			
			self.protocol_floatlayout.add_object_event('Display', 'Mask', 'Noise', 'Center', self.noise_mask_value)
		else:
			
			self.protocol_floatlayout.add_widget(self.img_stimulus_C)

		self.stimulus_start_time = time.perf_counter()
		
		self.stimulus_on_screen = True

		if 'Noise_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Noise_Staircase_Probe':

			self.protocol_floatlayout.add_widget(self.img_noise_C)

			self.protocol_floatlayout.add_object_event('Display', 'Mask', 'Noise', 'Center', self.noise_mask_value)
		

		if self.display_stimulus_outline == 1:
			
			self.protocol_floatlayout.add_widget(self.img_outline_C)
			
			self.protocol_floatlayout.add_object_event('Display', 'Mask', 'Outline', 'Center', self.display_stimulus_outline)
		

		if self.current_stage == 'Flanker_Fixed_Probe':
			
			self.protocol_floatlayout.add_widget(self.img_stimulus_L)
			self.protocol_floatlayout.add_widget(self.img_stimulus_R)
            
			self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Flanker', 'Left', self.img_stimulus_L)
			self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Flanker', 'Right', self.img_stimulus_R)


		Clock.schedule_once(self.stimulus_end, self.stimdur_seconds)

		Clock.schedule_once(self.center_notpressed, self.limhold_seconds)



	def stimulus_end(self, *args): # Remove stimulus

		if 'Blur_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Blur_Staircase_Probe':

			self.protocol_floatlayout.remove_widget(self.blur_widget)
			self.blur_widget.remove_widget(self.img_stimulus_C)
		
		else:
			
			self.protocol_floatlayout.remove_widget(self.img_stimulus_C)

		self.protocol_floatlayout.add_stage_event('Object Remove')

		if 'Noise_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Noise_Staircase_Probe':

			self.protocol_floatlayout.remove_widget(self.img_noise_C)
			self.protocol_floatlayout.add_object_event('Remove', 'Mask', 'Noise', 'Center', self.noise_mask_value)


		if (self.mask_during_limhold == 1) \
			and (self.current_stage == 'StimDur_Staircase_Probe'):
			
			self.protocol_floatlayout.remove_widget(self.img_outline_C)

			self.protocol_floatlayout.add_widget(self.img_stimulus_C_mask)
			self.protocol_floatlayout.add_widget(self.img_outline_C)

			self.stimulus_mask_on_screen = True

		self.stimdur_actual = time.perf_counter() - self.stimulus_start_time
		
		self.limhold_started = True

		if self.current_stage == 'Flanker_Fixed_Probe':
			
			self.protocol_floatlayout.remove_widget(self.img_stimulus_L)
			self.protocol_floatlayout.remove_widget(self.img_stimulus_R)
			
			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Flanker', 'Left', self.img_stimulus_L)
			
			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Flanker', 'Right', self.img_stimulus_R)



	def stimulus_presentation(self, *args): # Stimulus presentation by frame
		
		if not self.stimulus_on_screen \
			and not self.limhold_started:

			self.hold_button_pressed = True
		
			self.hold_button.unbind(on_press=self.iti_start)
			self.hold_button.unbind(on_release=self.premature_response)
			self.hold_button.bind(on_release=self.stimulus_response)
			
			self.stimulus_present()



	def premature_response(self, *args): # Trial Outcomes: 0-Premature

		self.hold_button_pressed = False
		if self.stimulus_on_screen:
			return None
		if self.stage_screen_started:
			return None
		if self.block_started:
			return None
		Clock.unschedule(self.iti_end)
		Clock.unschedule(self.remove_feedback)
		self.contingency = 3
		self.response = 1
		self.trial_outcome = 0
		self.response_latency = np.nan
		self.stimulus_press_latency = np.nan
		self.movement_latency = np.nan

		self.feedback_label.text = ''
		
		self.protocol_floatlayout.add_stage_event('Premature Response')
		
		self.protocol_floatlayout.add_variable_event('Outcome','Trial Contingency', self.contingency)
		
		self.protocol_floatlayout.add_variable_event('Outcome','Trial Response', self.response)
		
		self.protocol_floatlayout.add_variable_event('Outcome','Trial Outcome', self.trial_outcome)

		self.write_trial()

		self.iti_active = False

		self.feedback_label.text = self.feedback_dict['wait']
			
		if not self.feedback_on_screen:
			self.protocol_floatlayout.add_widget(self.feedback_label)

			self.feedback_start_time = time.perf_counter()
			self.feedback_on_screen = True

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback', self.feedback_label.text)
		
		self.hold_button.unbind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.premature_resolved)

	def premature_resolved(self, *args):
		Clock.unschedule(self.remove_feedback)
		self.remove_feedback()
		self.hold_button_pressed = True
		self.hold_button.unbind(on_press=self.premature_resolved)
		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.bind(on_release=self.premature_response)
		self.iti_start()
		return
	
	
	
	# Contingency Stages #
	# Tracks contingencies and outcomes based on removal of hold from hold_button
	def stimulus_response(self, *args): # Trial Outcomes: 1-Hit,3-False Alarm,5-Hit, no center press,6-False Alarm, no center press,7-Trial abort (lift and press hold button during stimulus display)
										# Contingencies: 0: Incorrect; 1: Correct; 2: Response, no center touch; 3: Premature response

		self.response_time = time.perf_counter()
		self.response_latency = self.response_time - self.stimulus_start_time
		
		self.response_made = True
		self.hold_button_pressed = False

		self.protocol_floatlayout.add_stage_event('Stimulus Response')
		
		self.response = 1

		self.feedback_label.text = ''
		
		if (self.current_stage == 'SART_Fixed_Probe'):

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
				
				if self.current_stage == 'LimHold_Staircase_Difficulty':
					self.feedback_label.text = self.feedback_dict['too_slow']
				
			else:
				self.contingency = 2
				self.trial_outcome = 6
		
		self.protocol_floatlayout.add_variable_event('Outcome','Trial Response', str(self.response))
			
		self.protocol_floatlayout.add_variable_event('Outcome','Trial Contingency', str(self.contingency))
		
		self.protocol_floatlayout.add_variable_event('Outcome','Trial Outcome', str(self.trial_outcome))
		
		self.protocol_floatlayout.add_variable_event('Outcome','Response Latency', str(self.response_latency))
		
		self.hold_button.bind(on_press=self.response_cancelled)
		self.hold_button.unbind(on_release=self.stimulus_response)
	
	
	# Tracks contingencies based on responses direectly to the stimulus image
	def center_pressed(self, *args): # Trial Outcomes: 1-Hit,3-False Alarm
		
		Clock.unschedule(self.stimulus_end)
		Clock.unschedule(self.center_notpressed)

		self.hold_button_pressed = False

		self.hold_button.unbind(on_press=self.response_cancelled)
		
		self.stimulus_press_time = time.perf_counter()
		self.stimulus_press_latency = self.stimulus_press_time - self.stimulus_start_time
		self.movement_latency = self.stimulus_press_latency - self.response_latency

		self.feedback_label.text = ''

		if 'Blur_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Blur_Staircase_Probe':

			self.protocol_floatlayout.remove_widget(self.blur_widget)
			self.blur_widget.remove_widget(self.img_stimulus_C)
		
		else:
			self.protocol_floatlayout.remove_widget(self.img_stimulus_C)


		if self.stimulus_mask_on_screen:
			self.protocol_floatlayout.remove_widget(self.img_stimulus_C_mask)
			self.stimulus_mask_on_screen = False
		
		self.protocol_floatlayout.add_stage_event('Stimulus Press')
		
		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Center', 'Center', self.center_image)

		if 'Noise_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Noise_Staircase_Probe':
			
			self.protocol_floatlayout.remove_widget(self.img_noise_C)
			
			self.protocol_floatlayout.add_object_event('Remove', 'Mask', 'Noise', 'Center', self.noise_mask_value)
		

		if self.display_stimulus_outline == 1:
			self.protocol_floatlayout.remove_widget(self.img_outline_C)
			
			self.protocol_floatlayout.add_object_event('Remove', 'Mask', 'Outline', 'Center', self.display_stimulus_outline)
		
		
		if self.current_stage == 'Flanker_Fixed_Probe':
			self.protocol_floatlayout.remove_widget(self.img_stimulus_L)
			self.protocol_floatlayout.remove_widget(self.img_stimulus_R)
			
			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Flanker', 'Left', self.img_stimulus_L)
			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Flanker', 'Right', self.img_stimulus_R)
		
		self.stimulus_on_screen = False
		self.limhold_started = False
		self.response_made = False

		self.feedback_label.text = ''
		
		if (self.current_stage == 'SART_Fixed_Probe') and not self.cjb_task:

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

		elif self.cjb_task:
			if (self.center_image == self.cjb_target_image):
				self.contingency = 1
				self.trial_outcome = 1
				self.feedback_label.text = self.feedback_dict['correct']
			elif (self.center_image == self.cjb_nontarget_image):
				self.contingency = 0
				self.trial_outcome = 3
				self.feedback_label.text = self.feedback_dict['incorrect']
			elif (self.center_image in [self.cjb_neutral_target_image, self.cjb_neutral_nontarget_image, self.cjb_neutral_true_image]):
				self.contingency = 0
				self.trial_outcome = 8
				self.feedback_label.text = ''

			
		
		else:

			if (self.center_image == self.target_image):
				self.contingency = 1
				self.trial_outcome = 1
				self.current_hits += 1
				
				self.feedback_label.text = self.feedback_dict['correct']
				
			else:
				self.contingency = 0
				self.trial_outcome = 3
				self.block_false_alarms += 1
				
				self.feedback_label.text = self.feedback_dict['incorrect']

		self.protocol_floatlayout.add_variable_event('Outcome','Trial Response', str(self.response))
		
		self.protocol_floatlayout.add_variable_event('Outcome','Trial Contingency', str(self.contingency))
		
		self.protocol_floatlayout.add_variable_event('Outcome','Trial Outcome', str(self.trial_outcome))
		
		self.protocol_floatlayout.add_variable_event('Outcome','Stimulus Press Latency', str(self.stimulus_press_latency))
		
		self.protocol_floatlayout.add_variable_event('Outcome','Movement Latency', str(self.movement_latency))
		
		if self.feedback_label.text != '' \
			and not self.feedback_on_screen:
			
			self.protocol_floatlayout.add_widget(self.feedback_label)

			self.feedback_start_time = time.perf_counter()
			self.feedback_on_screen = True

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback', self.feedback_label.text)

		self.write_trial()

		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.bind(on_release=self.premature_response)

		if 'Blur_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Blur_Staircase_Probe':

			self.blur_preload_start()
		
		else:
			self.trial_contingency()



	def center_notpressed(self, *args):

		if 'Blur_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Blur_Staircase_Probe':

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
		
		self.protocol_floatlayout.add_stage_event('No Stimulus Press')
		
		self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Center', 'Center', self.center_image)

		if 'Noise_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Noise_Staircase_Probe':
			
			self.protocol_floatlayout.remove_widget(self.img_noise_C)
			
			self.protocol_floatlayout.add_object_event('Remove', 'Mask', 'Noise', 'Center', self.noise_mask_value)


		if self.display_stimulus_outline == 1:
			self.protocol_floatlayout.remove_widget(self.img_outline_C)
			
			self.protocol_floatlayout.add_object_event('Remove', 'Mask', 'Outline', 'Center', self.display_stimulus_outline)
		
		
		if self.current_stage == 'Flanker_Fixed_Probe':
			self.protocol_floatlayout.remove_widget(self.img_stimulus_L)
			self.protocol_floatlayout.remove_widget(self.img_stimulus_R)
			
			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Flanker', 'Left', self.img_stimulus_L)
			self.protocol_floatlayout.add_object_event('Remove', 'Stimulus', 'Flanker', 'Right', self.img_stimulus_R)
		
		self.stimulus_on_screen = False
		self.limhold_started = False

		if not self.response_made:
			self.response = 0
			self.response_latency = np.nan

			self.feedback_label.text = ''
			
			if (self.current_stage == 'SART_Fixed_Probe') and not self.cjb_task:

				if (self.center_image == self.target_image):
					self.contingency = 1
					self.trial_outcome = 4
					self.current_hits += 1
					self.feedback_label.text = self.feedback_dict['correct']
				
				else:
					self.contingency = 0
					self.trial_outcome = 2
			
			elif self.cjb_task:
				if (self.center_image == self.cjb_target_image):
					self.contingency = 0
					self.trial_outcome = 2
					self.feedback_label.text = self.feedback_dict['miss']
				elif (self.center_image == self.cjb_nontarget_image):
					self.contingency = 1
					self.trial_outcome = 4
					self.feedback_label.text = ''
				elif (self.center_image in [self.cjb_neutral_target_image, self.cjb_neutral_nontarget_image, self.cjb_neutral_true_image]):
					self.contingency = 0
					self.trial_outcome = 8
					self.feedback_label.text = ''
			
			else:

				if (self.center_image == self.target_image):
					self.contingency = 0
					self.trial_outcome = 2

					if self.current_stage in ['Training', 'LimHold_Staircase_Difficulty', 'Similarity_Staircase_Difficulty', 'Blur_Staircase_Difficulty', 'Noise_Staircase_Difficulty', 'StimDur_Staircase_Probe', 'Blur_Staircase_Probe', 'Noise_Staircase_Probe']:
						self.feedback_label.text = self.feedback_dict['miss']
				
				else:
					self.contingency = 1
					self.trial_outcome = 4

			self.protocol_floatlayout.add_variable_event('Outcome','Trial Response', str(self.response))
			
			self.protocol_floatlayout.add_variable_event('Outcome','Trial Contingency', str(self.contingency))
			
			self.protocol_floatlayout.add_variable_event('Outcome','Trial Outcome', str(self.trial_outcome))
			
			self.protocol_floatlayout.add_variable_event('Outcome','Stimulus Press Latency', str(self.stimulus_press_latency))
			
			self.protocol_floatlayout.add_variable_event('Outcome','Movement Latency', str(self.movement_latency))

			self.hold_button.unbind(on_release=self.stimulus_response)

		else:
			self.hold_button.unbind(on_press=self.response_cancelled)
			

		if self.feedback_label.text != '' \
			and not self.feedback_on_screen:
			
			self.protocol_floatlayout.add_widget(self.feedback_label)

			self.feedback_start_time = time.perf_counter()
			self.feedback_on_screen = True

			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Feedback', self.feedback_label.text)

		self.response_made = False

		self.write_trial()

		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.bind(on_release=self.premature_response)

		if 'Blur_Staircase_Difficulty' in self.stage_list \
			or self.current_stage == 'Blur_Staircase_Probe':

			self.blur_preload_start()
		
		else:
			self.trial_contingency()
	
	
	
	def response_cancelled(self, *args):
		
		if self.trial_outcome == 5:
			self.feedback_label.text = self.feedback_dict['miss']

		else:
			self.feedback_label.text = self.feedback_dict['abort']

		Clock.unschedule(self.stimulus_end)
		Clock.unschedule(self.center_notpressed)

		self.trial_outcome = 7

		self.hold_button_pressed = True
		
		self.center_notpressed()


	def section_start(self, *args):

		self.block_started = False
		self.video_on_screen = False

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_stage_event('Section Start')
		
		self.protocol_floatlayout.add_object_event('Remove', 'Text', 'Instructions', 'Section')
		
		self.protocol_floatlayout.add_object_event('Remove', 'Button', 'Continue', 'Section')
		
		self.trial_end_time = time.perf_counter()
		self.block_contingency()
		self.block_end()



	# Data Saving Functions #

	def write_trial(self, *args):		
		trial_data = [
			self.current_trial
			, self.current_stage
			, self.current_substage
			, self.target_probability
			, self.current_block
			, self.current_block_trial
			, self.center_image
			, self.stimdur_frames
			, self.stimdur_seconds
			, self.limhold_seconds
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

	# --- Helpers extracted from trial_contingency ---

	def _encode_last_response(self):
		"""Set self.last_response (-1/0/1) based on previous trial outcome and current stage."""

		if (self.current_stage == 'Training') or (self.current_block == 0):
			self.last_response = 1 if self.trial_outcome == 1 else 0

		elif self.current_stage == 'Similarity_Staircase_Difficulty':
			if self.trial_outcome == 4:
				self.last_response = 1
				self.similarity_tracking.append(self.current_similarity)
			elif self.trial_outcome in [2, 3]:
				self.last_response = -1
			else:
				self.last_response = 0

		elif self.current_stage == 'StimDur_Staircase_Probe':
			if self.trial_outcome in [1, 5]:
				self.last_response = 1
				self.stimdur_frame_tracking.append(self.stimdur_frames)
			elif self.trial_outcome in [2, 3, 6]:
				self.last_response = -1
			else:
				self.last_response = 0

		elif (self.current_stage == 'SART_Fixed_Probe') \
			or ((self.current_stage == 'TarProb_Fixed_Probe')
				and (self.target_probability == max(self.target_prob_hilo))):
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

		self.protocol_floatlayout.add_variable_event('Outcome', 'Last Response', self.last_response)


	def _update_hit_false_alarm_tracking(self):
		"""Append current trial outcome to rolling hit/FA tracking lists."""

		if self.trial_outcome == 1:
			self.hit_tracking.append(1)
			self.total_hit_tracking.append(1)
			if self.response_latency != np.nan:
				self.decision_point_tracking.append(self.response_latency)

		elif self.trial_outcome == 2:
			self.hit_tracking.append(0)
			self.total_hit_tracking.append(0)

		elif self.trial_outcome == 3:
			if self.cjb_task:
				self.staircase_index_tracking.append(len(self.nontarget_images) + 1)
			else:
				self.staircase_index_tracking.append(int(self.nontarget_images.index(self.center_image)))
			self.false_alarm_tracking.append(1)
			self.total_false_alarm_tracking.append(1)

		elif self.trial_outcome == 4:
			if self.cjb_task:
				self.staircase_index_tracking.append(len(self.nontarget_images) + 1)
			else:
				self.staircase_index_tracking.append(int(self.nontarget_images.index(self.center_image)))
			self.false_alarm_tracking.append(0)
			self.total_false_alarm_tracking.append(0)


	def _build_similarity_baseline(self):
		"""Compute outcome_value and derive the baseline nontarget image list for similarity stages."""

		if len(self.similarity_tracking) > 0:
			self.outcome_value = max(self.similarity_tracking)
		else:
			self.outcome_value = float(self.similarity_data.loc[
				self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1]
				, self.target_image
				].to_numpy())

		base_nontarget_image_list = self.similarity_data.loc[
			(self.similarity_data[self.target_image] <= self.outcome_value)
			, 'Nontarget'
			].tolist()

		if len(base_nontarget_image_list) < self.similarity_index_range:
			base_nontarget_image_list = self.similarity_data.loc[0:(self.similarity_index_range - 1), 'Nontarget']

		self.current_nontarget_image_list = base_nontarget_image_list[-self.similarity_index_range:]


	def _run_similarity_staircase(self):
		"""Adjust similarity window based on staircase_flag; end block when oscillation or limit reached."""

		if self.staircase_flag > 0:

			if (self.last_staircase is not None and self.last_staircase < 0) \
				or (self.similarity_index_max >= len(self.similarity_data[self.target_image])):

				self._build_similarity_baseline()

				self.protocol_floatlayout.add_variable_event('Outcome', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])]), 'Baseline', 'Min')
				self.protocol_floatlayout.add_variable_event('Outcome', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])]), 'Baseline', 'Max')
				self.protocol_floatlayout.add_variable_event('Parameter', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])]), 'Baseline', 'Min')
				self.protocol_floatlayout.add_variable_event('Parameter', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])]), 'Baseline', 'Max')

				self.protocol_floatlayout.add_stage_event('Block End')
				self.current_block += 1
				self.start_stage_screen()

			else:
				self.similarity_index_min = max(self.staircase_index_tracking[-self.staircase_min_nontarget_trials:]) + 1
				self.similarity_index_max = self.similarity_index_min + self.similarity_index_range

				if self.similarity_index_max > len(self.similarity_data[self.target_image]):
					self.similarity_index_max = len(self.similarity_data[self.target_image])
					self.similarity_index_min = self.similarity_index_max - self.similarity_index_range

				self.current_nontarget_image_list = self.nontarget_images[self.similarity_index_min:self.similarity_index_max]

			self.last_staircase = self.staircase_flag

		elif self.staircase_flag < 0:

			if (self.last_staircase is not None and self.last_staircase > 0) \
				or (self.similarity_index_min <= 0):

				self._build_similarity_baseline()

				self.protocol_floatlayout.add_variable_event('Outcome', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])]), 'Baseline', 'Min')
				self.protocol_floatlayout.add_variable_event('Outcome', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])]), 'Baseline', 'Max')
				self.protocol_floatlayout.add_variable_event('Parameter', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])]), 'Baseline', 'Min')
				self.protocol_floatlayout.add_variable_event('Parameter', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])]), 'Baseline', 'Max')

				self.protocol_floatlayout.add_stage_event('Block End')
				self.current_block += 1
				self.start_stage_screen()

			else:
				self.similarity_index_max = min(self.staircase_index_tracking[-self.staircase_min_nontarget_trials:])
				self.similarity_index_min = self.similarity_index_max - self.similarity_index_range

				if self.similarity_index_min < 0:
					self.similarity_index_min = 0
					self.similarity_index_max = self.similarity_index_range

				self.current_nontarget_image_list = self.nontarget_images[self.similarity_index_min:self.similarity_index_max]

			self.last_staircase = self.staircase_flag

		self.protocol_floatlayout.add_variable_event('Parameter', 'Similarity',
			str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])]), 'Staircasing', 'Min')
		self.protocol_floatlayout.add_variable_event('Parameter', 'Similarity',
			str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])]), 'Staircasing', 'Max')


	def _run_stimdur_staircase(self):
		"""Adjust stimulus duration using binary search based on staircase_flag."""

		# End block when binary search has converged or duration equals/exceeds limited hold
		if (self.stimdur_frame_change == 1) \
			or (self.stimdur_seconds >= self.limhold_seconds):

			self.outcome_value = self.stimdur_frames
			self.current_block += 1

			self.protocol_floatlayout.add_variable_event('Outcome', 'Stimulus Duration', self.outcome_value, 'Min', 'Frames')
			self.protocol_floatlayout.add_variable_event('Outcome', 'Stimulus Duration', str(self.outcome_value * self.frame_duration), 'Min', 'Seconds')
			self.protocol_floatlayout.add_stage_event('Block End')
			self.start_stage_screen()
			return

		if self.staircase_flag > 0:
			if self.stimdur_frames > self.stimdur_frame_min:
				self.stimdur_frame_max = self.stimdur_frames
				self.stimdur_frame_change = (self.stimdur_frame_max - self.stimdur_frame_min) // 2
				if self.stimdur_frame_change < 1:
					self.stimdur_frame_change = 1
				self.stimdur_frames -= self.stimdur_frame_change
				if self.stimdur_frames < self.stimdur_frame_min:
					self.stimdur_frames = self.stimdur_frame_min

		elif self.staircase_flag < 0:
			self.stimdur_frame_min = self.stimdur_frames
			self.stimdur_frame_change = (self.stimdur_frame_max - self.stimdur_frame_min) // 2
			if self.stimdur_frame_change < 1:
				self.stimdur_frame_change = 1
			self.stimdur_frames += self.stimdur_frame_change
			if self.stimdur_frames > (self.limhold_seconds // self.frame_duration):
				self.stimdur_frames = self.limhold_seconds // self.frame_duration

		self.stimdur_seconds = self.stimdur_frames * self.frame_duration

		self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus Duration', self.stimdur_frames, 'Staircasing', 'Frames')
		self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus Duration', self.stimdur_seconds, 'Staircasing', 'Seconds')


	def _run_staircase(self):
		"""Evaluate staircasing criteria and adjust parameters if thresholds are met."""

		if 'Staircase' not in self.current_stage:
			return

		self.staircase_flag = 0

		if (len(self.hit_tracking) >= self.staircase_min_target_trials) \
			and (len(self.false_alarm_tracking) >= self.staircase_min_nontarget_trials):

			hr  = statistics.mean(self.hit_tracking[-(self.staircase_min_target_trials):])
			far = statistics.mean(self.false_alarm_tracking[-(self.staircase_min_nontarget_trials):])

			if (hr >= self.staircase_hr_criterion) and (far < self.staircase_far_criterion):
				self.staircase_flag = 1
				self.protocol_floatlayout.add_variable_event('Parameter', 'Staircasing', 'Increase')

			elif (hr < self.staircase_hr_criterion) and (far >= self.staircase_far_criterion):
				self.staircase_flag = -1
				self.protocol_floatlayout.add_variable_event('Parameter', 'Staircasing', 'Decrease')

			elif (statistics.mean(self.hit_tracking[-(2 * self.staircase_min_target_trials):]) < self.staircase_hr_criterion) \
				^ (statistics.mean(self.false_alarm_tracking[-(2 * self.staircase_min_nontarget_trials):]) >= self.staircase_far_criterion):
				self.staircase_flag = -2
				self.protocol_floatlayout.add_variable_event('Parameter', 'Staircasing', 'Decrease')

		if self.staircase_flag != 0:
			self.hit_tracking = []
			self.false_alarm_tracking = []

			if 'Similarity' in self.current_stage:
				self._run_similarity_staircase()
			elif 'StimDur' in self.current_stage:
				self._run_stimdur_staircase()


	def _advance_trial_counters_and_iti(self):
		"""Increment trial/block-trial counters and sample a new ITI length."""

		self.current_trial += 1
		self.current_block_trial += 1

		self.protocol_floatlayout.add_variable_event('Parameter', 'Current Trial', self.current_trial)
		self.protocol_floatlayout.add_variable_event('Parameter', 'Current Block Trial', self.current_block_trial)

		if len(self.iti_frame_range) > 1:
			if self.iti_fixed_or_range == 'fixed':
				self.iti_length = random.choice(self.iti_frame_range) * self.frame_duration
			else:
				self.iti_length = random.randint(min(self.iti_frame_range), max(self.iti_frame_range)) * self.frame_duration
			self.protocol_floatlayout.add_variable_event('Parameter', 'Current ITI', self.iti_length, 'Seconds')

		if self.current_block == 0:
			self.stimdur_frames  = self.stimdur_base
			self.stimdur_seconds = self.stimdur_frames * self.frame_duration
			self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus Duration', self.stimdur_frames, 'Training', 'Frames')
			self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus Duration', self.stimdur_seconds, 'Training', 'Seconds')


	def _select_nontarget_image(self):
		"""Pick a nontarget image and record its similarity value if applicable."""

		self.center_image = random.choice(self.current_nontarget_image_list)

		if 'Similarity_Staircase_Difficulty' in self.stage_list:
			self.current_similarity = float(self.similarity_data.loc[
				self.similarity_data['Nontarget'] == self.center_image
				, self.target_image
				].to_numpy())


	def _select_flanker_stimulus(self):
		"""Choose the center image and flanker images for a Flanker_Fixed_Probe trial."""

		if self.flanker_stage_index >= len(self.flanker_stage_list):
			self.flanker_stage_list = self.constrained_shuffle(self.flanker_stage_list, max_run=3)
			self.flanker_stage_index = 0

		self.current_substage = self.flanker_stage_list[self.flanker_stage_index]
		self.flanker_stage_index += 1

		if self.trial_list_flanker_index_dict[self.current_substage] >= len(list(self.trial_list_flanker_dict[self.current_substage])):
			self.trial_list_flanker_dict[self.current_substage] = self.constrained_shuffle(self.trial_list_base, max_run=self.trial_list_max_run)
			self.trial_list_flanker_index_dict[self.current_substage] = 0

		trial_type = list(self.trial_list_flanker_dict[self.current_substage])[self.trial_list_flanker_index_dict[self.current_substage]]

		if trial_type == 'Target':
			self.center_image = self.target_image
			self.current_similarity = 1.00
		else:
			self._select_nontarget_image()

		self.img_stimulus_C.texture = self.image_dict[self.center_image].image.texture
		self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus', self.center_image, 'Novel')

		if self.current_substage == 'non':
			self.flanker_image = 'black'
			self.protocol_floatlayout.add_variable_event('Parameter', 'Flanker', self.flanker_image, 'Blank')

		elif self.current_substage == 'con':
			self.flanker_image = self.center_image
			self.protocol_floatlayout.add_variable_event('Parameter', 'Flanker', self.flanker_image, 'Congruent')

		elif self.current_substage == 'inc':
			if self.center_image == self.target_image:
				self.flanker_image = random.choice(self.current_nontarget_image_list)
			else:
				self.flanker_image = self.target_image
			self.protocol_floatlayout.add_variable_event('Parameter', 'Flanker', self.flanker_image, 'Incongruent')

		self.trial_list_flanker_index_dict[self.current_substage] += 1

		self.img_stimulus_L.texture = self.image_dict[self.flanker_image].image.texture
		self.img_stimulus_R.texture = self.image_dict[self.flanker_image].image.texture


	def _select_standard_stimulus(self):
		"""Advance the trial list index and choose the center image for standard stages."""

		self.trial_index += 1

		if self.trial_index >= len(self.trial_list):
			if self.stage_list[self.stage_index] == 'CJB_Probe':
				self.trial_list = self._constrained_shuffle_cjb(self.trial_list, max_run=self.trial_list_max_run)
			else:
				self.trial_list = self.constrained_shuffle(self.trial_list, max_run=self.trial_list_max_run)
			self.trial_index = 0

		self.protocol_floatlayout.add_variable_event('Parameter', 'Trial Index', self.trial_index)
		self.protocol_floatlayout.add_variable_event('Parameter', 'Trial Type', self.trial_list[self.trial_index])

		if not self.cjb_task:
			if self.trial_list[self.trial_index] == 'Target':
				self.center_image = self.target_image
				self.current_similarity = 1.00
			else:
				self._select_nontarget_image()
		else:
			if self.trial_list[self.trial_index] == 'Target':
				self.center_image = self.cjb_target_image
				self.current_similarity = 1.00
			elif self.trial_list[self.trial_index] == 'Nontarget':
				self.center_image = self.cjb_nontarget_image
				self.current_similarity = 0.00
			elif self.trial_list[self.trial_index] == 'Neutral-Target':
				self.center_image = self.cjb_neutral_target_image
				self.current_similarity = 0.75
			elif self.trial_list[self.trial_index] == 'Neutral-Nontarget':
				self.center_image = self.cjb_neutral_nontarget_image
				self.current_similarity = 0.25
			elif self.trial_list[self.trial_index] == 'Neutral-True':
				self.center_image = self.cjb_neutral_true_image
				self.current_similarity = 0.50

		self.img_stimulus_C.texture = self.image_dict[self.center_image].image.texture
		self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus', self.center_image, 'Novel')


	def _select_next_stimulus(self):
		"""Choose the stimulus (and flankers) for the upcoming trial."""

		# SART miss correction — keep same stimulus
		if (self.contingency == 0) \
			and (self.response == 0) \
			and (self.current_stage == 'SART_Fixed_Probe'):
			self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus', self.center_image, 'SART Correction')
			return

		# Premature — keep same stimulus
		if self.contingency == 3:
			self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus', self.center_image, 'Premature')
			return

		if self.current_stage == 'Flanker_Fixed_Probe':
			self._select_flanker_stimulus()
		else:
			self._select_standard_stimulus()


	def _check_end_conditions(self):
		"""Check training/session/block exit criteria. Returns True if the trial loop should exit."""

		if self.trial_list[self.trial_index] == 'Target':
			self.block_target_total += 1

		# Training block — hit criterion met
		if (self.current_stage == 'Training') \
			and (sum(self.hit_tracking) >= self.training_block_max_correct):

			self.protocol_floatlayout.add_stage_event('Block End')
			self.hold_button.unbind(on_release=self.stimulus_response)
			self.contingency   = 0
			self.trial_outcome = 0
			self.last_response = 0
			self.current_block += 1
			self.protocol_floatlayout.remove_widget(self.hold_button)
			self.block_contingency()
			return True

		# Session limit
		if (self.current_trial > self.session_trial_max) \
			or ((time.perf_counter() - self.start_time) >= self.session_length_max):

			self.protocol_floatlayout.add_stage_event('Session End')
			self.hold_button.unbind(on_release=self.stimulus_response)
			self.session_event.cancel()
			self.protocol_end()
			return True

		# Block limit
		if (self.current_block_trial > self.block_trial_max) \
			or ((time.perf_counter() - self.block_start) >= self.block_duration):

			self.protocol_floatlayout.add_stage_event('Block End')
			self.hold_button.unbind(on_press=self.iti_start)
			self.hold_button.unbind(on_release=self.premature_response)
			self.hold_button_pressed = False
			self.hold_button.disabled = True
			self.hold_button.state = 'normal'
			self.contingency   = 0
			self.trial_outcome = 0
			self.last_response = 0

			if self.current_stage == 'Similarity_Staircase_Difficulty':

				if len(self.similarity_tracking) == 0:
					self.outcome_value = float(self.similarity_data.loc[
						self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1]
						, self.target_image
						].to_numpy())
				else:
					self.outcome_value = max(self.similarity_tracking)

				self.protocol_floatlayout.add_variable_event('Outcome', 'Similarity', self.outcome_value, 'Max')

				base_nontarget_image_list = self.similarity_data.loc[
					(self.similarity_data[self.target_image] <= self.outcome_value)
					, 'Nontarget'
					].tolist()

				if len(base_nontarget_image_list) < self.similarity_index_range:
					base_nontarget_image_list = self.similarity_data.loc[0:(self.similarity_index_range - 1), 'Nontarget']

				self.current_nontarget_image_list = base_nontarget_image_list[-self.similarity_index_range:]

				self.protocol_floatlayout.add_variable_event('Parameter', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[0])]), 'Baseline', 'Min')
				self.protocol_floatlayout.add_variable_event('Parameter', 'Similarity',
					str(self.similarity_data.loc[(self.similarity_data['Nontarget'] == self.current_nontarget_image_list[-1])]), 'Baseline', 'Max')

			elif self.current_stage == 'StimDur_Staircase_Probe':

				if len(self.stimdur_frame_tracking) < 1:
					self.outcome_value = self.stimdur_base
				else:
					self.outcome_value = min(self.stimdur_frame_tracking)

				self.protocol_floatlayout.add_variable_event('Outcome', 'Stimulus Duration', self.outcome_value, 'Min', 'Frames')
				self.protocol_floatlayout.add_variable_event('Outcome', 'Stimulus Duration', str(self.outcome_value * self.frame_duration), 'Min', 'Seconds')

			self.protocol_floatlayout.remove_widget(self.hold_button)

			self.current_block += 1

			if self.current_stage == 'Training':
				self.block_contingency()
			else:
				self.start_stage_screen()
			return True

		return False

	# --- End helpers ---

	def trial_contingency(self, *args):
		# Trial Contingencies: 0-Incorrect; 1-Correct; 2-Response, no center touch; 3-Premature
		# Trial Outcomes: 0-Premature,1-Hit,2-Miss,3-False Alarm,4-Correct Rejection,5-Hit, no center press,6-False Alarm, no center press,7-Trial abort (lift and press hold button during stimulus display)
		try:
			if self.current_block_trial != 0:
				self._encode_last_response()
				self._update_hit_false_alarm_tracking()
				self._run_staircase()

			self._advance_trial_counters_and_iti()
			self._select_next_stimulus()

			self.last_response = 0
			self.trial_outcome = 0

			if self._check_end_conditions():
				return

			self.trial_end_time = time.perf_counter()

			if not self.block_started:
				if self.hold_button_pressed:
					self.iti_start()
				else:
					Clock.schedule_once(self.hold_remind, 2.0)
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except:

			print('Error; program terminated by Trial Contingency.')
			self.protocol_end()

	def start_stage_screen(self, *args):
		self.protocol_floatlayout.add_stage_event('Stage End')

		# Cancel any scheduled timers that could present stimuli or noise on screen
		Clock.unschedule(self.iti_end)
		Clock.unschedule(self.stimulus_end)
		Clock.unschedule(self.center_notpressed)
		Clock.unschedule(self.hold_remind)
		Clock.unschedule(self.remove_feedback)
		Clock.unschedule(self.stage_screen_end)

    	# Reset 'in-progress' flags to avoid triggering any trial actions
		self.iti_active = False
		self.stimulus_on_screen = False
		self.limhold_started = False
		self.feedback_on_screen = False
		self.hold_button_pressed = False
		self.response_made = False
		self.stage_screen_started = True
		self.block_started = True
		
		self.protocol_floatlayout.clear_widgets()

		self.feedback_on_screen = False
			
		if self.current_stage == 'Similarity_Staircase_Difficulty':
			self.outcome_string = eval(f'f"""{self.outcome_dict.get("SSDiff", "")}"""')
			
		elif self.current_stage in ['Blur_Staircase_Difficulty', 'Blur_Staircase_Probe']:
			self.outcome_string = eval(f'f"""{self.outcome_dict.get("blur", "")}"""')
			
		elif self.current_stage in ['Noise_Staircase_Difficulty', 'Noise_Staircase_Probe']:
			self.outcome_string = eval(f'f"""{self.outcome_dict.get("noise", "")}"""')

		elif self.current_stage == 'LimHold_Staircase_Difficulty':
			self.outcome_string = eval(f'f"""{self.outcome_dict.get("limhold", "")}"""')
			
		elif self.current_stage == 'StimDur_Staircase_Probe':
			self.outcome_string = eval(f'f"""{self.outcome_dict.get("stimdur", "")}"""')

		elif self.current_stage in ['TarProb_Fixed_Probe', 'Flanker_Fixed_Probe']:

			if len(self.total_hit_tracking) == 0:
				self.outcome_string = eval(f'f"""{self.outcome_dict.get("gj", "")}"""')
				
			else:
				self.hit_accuracy = (sum(self.total_hit_tracking) / len(self.total_hit_tracking))
				self.outcome_string = eval(f'f"""{self.outcome_dict.get("probe", "")}"""')
			
		else:
			self.outcome_string = eval(f'f"""{self.outcome_dict.get("gj", "")}"""')


		if self.stage_index < (len(self.stage_list) - 1) \
			or (self.current_block <= self.block_max_count):

			self.stage_string = eval(f'f"""{self.staging_dict.get("continue", "")}"""')

		else:
			self.stage_string = eval(f'f"""{self.staging_dict.get("end", "")}"""') # 'Please press "End Session" to end the session.'
			self.session_end_button.pos_hint = self.text_button_pos_UC
			self.protocol_floatlayout.add_widget(self.session_end_button)
			
		self.stage_results_label.text = self.outcome_string + '\n\n' + self.stage_string
		self.protocol_floatlayout.add_widget(self.stage_results_label)
			
		self.protocol_floatlayout.add_object_event('Display', 'Text', 'Stage', 'Results')

		self.stage_screen_time = time.perf_counter()

		if (self.stage_index < (len(self.stage_list) - 1)) \
			or (self.current_block <= self.block_max_count):

			Clock.schedule_once(self.stage_screen_end, 1.0)

		else:
			self.stage_screen_started = False

	def stage_screen_end(self, *args):

		self.protocol_floatlayout.add_widget(self.stage_continue_button)
		self.hold_button.bind(on_press=self.iti_start)
		self.hold_button.bind(on_release=self.premature_response)
		self.stage_screen_started = False
		
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Stage', 'Continue')


	# --- block_contingency helpers ---

	def _block_init_screen(self):
		"""Clear the screen and reset per-block state flags."""
		self.protocol_floatlayout.clear_widgets()
		self.protocol_floatlayout.add_stage_event('Screen Cleared')
		self.previous_stage = self.current_stage
		self.feedback_label.text = ''
		self.hold_button_pressed = False
		self.block_started = True

	def _block_advance_stage(self):
		"""Advance to the next stage when the current block count is exhausted.

		Returns True if the protocol has ended and block_contingency should return immediately.
		"""
		if not ((self.current_block > self.block_max_count) or (self.current_block == -1)):
			return False

		if self.current_block == -1:
			self.protocol_floatlayout.add_widget(self.hold_button)

		self.total_hit_tracking = []
		self.total_false_alarm_tracking = []
		self.hit_tracking = []
		self.false_alarm_tracking = []
		self.stage_index += 1
		self.current_block = 1

		if self.stage_index >= len(self.stage_list):
			self.protocol_end()
			return True

		self.current_stage = self.stage_list[self.stage_index]
		self.current_substage = ''

		self.protocol_floatlayout.add_stage_event(self.current_stage)

		self.trial_list = ['Target']
		self.stimdur_frames = self.stimdur_base

		# If blur scaling active, reset blur level to base
		if 'Blur_Staircase_Difficulty' in self.stage_list \
				or self.current_stage == 'Blur_Staircase_Probe':
			self.blur_level = self.blur_base

		if self.current_stage == 'SART_Fixed_Probe': # Set SART probe params
			self.current_block = 0

		return False

	def _block_load_stage_video(self, stage_name, video_path_attr, played_flag_attr, stop_after_load=False):
		"""Check whether a tutorial video for *stage_name* still needs to be shown.

		If the tutorial-video directory exists, the current stage matches *stage_name*,
		and the corresponding played-flag is False, the video is loaded and the tutorial
		screen is triggered.

		Returns True if the video was triggered (block_contingency should return).
		"""
		video_dir = (
			self.app.app_root / 'Protocol' / self.protocol_name
			/ 'Language' / self.language / 'Tutorial_Video'
		)
		if not video_dir.is_dir():
			return False
		if self.stage_list[self.stage_index] != stage_name:
			return False
		if getattr(self, played_flag_attr):
			return False

		self.protocol_floatlayout.clear_widgets()
		self.current_stage = self.stage_list[self.stage_index]
		self.stage_index -= 1
		self.current_block = -1
		setattr(self, played_flag_attr, True)
		self.tutorial_video.state = 'stop'
		self.tutorial_video.unload()
		self.tutorial_video = None
		self.tutorial_video = PreloadedVideo(
			source_path=str(getattr(self, video_path_attr)),
			pos_hint={'center_x': 0.5, 'center_y': 0.5 + self.text_button_size[1]},
			fit_mode='contain',
			loop=False,
		)
		if stop_after_load:
			self.tutorial_video.state = 'stop'

		self.block_started = False
		# Trigger tutorial screen once all touches are released to avoid accidental skipping
		self.trigger_tutorial_screen()
		return True

	def _block_setup_block_parameters(self):
		"""Configure trial/block parameters for the upcoming block."""
		# If current stage is training and tutorial video has not been skipped and training not yet complete
		if (self.current_stage == 'Training') \
				and not self.skip_tutorial_video \
				and not self.training_complete:
			self._block_setup_training_preblock()

		# If current block is 0 (tutorial block for stage)
		elif self.current_block == 0:
			self._block_setup_tutorial_block()

		# If current block is 1 (first testing block for stage)
		elif self.current_block == 1:
			self._block_setup_first_testing_block()

		# If current block is greater than 1 (normal task block)
		else:
			self._block_setup_subsequent_block()

	def _block_setup_training_preblock(self):
		"""Set parameters for the initial Training stage."""
		self.block_max_count = 1
		self.trial_list = ['Target']
		if self.cjb_task:
			self.block_trial_max = self.cjb_train_trials
		else:
			self.block_trial_max = self.training_block_max_correct
		self.block_duration = 3*(self.block_trial_max)
		self.target_probability = 1.0

		self.block_start = time.perf_counter()
		self.training_complete = True

		self.hold_button.bind(on_press=self.iti_start)

	def _block_setup_tutorial_block(self):
		"""Set parameters and display for block 0 (stage tutorial block)."""
		self.protocol_floatlayout.clear_widgets()

		self.block_max_count = 1
		if self.cjb_task:
			self.block_trial_max = self.cjb_train_trials
		else:
			self.block_trial_max = self.training_block_max_correct
		self.block_duration = 3*(self.block_trial_max)
		self.instruction_button.text = self.training_block_button_str
		self.protocol_floatlayout.add_widget(self.instruction_button)

		self.protocol_floatlayout.add_object_event('Display', 'Image', 'Block', 'Instructions', self.target_image)

		self.protocol_floatlayout.add_object_event('Display', 'Text', 'Block', 'Instructions')
		self.protocol_floatlayout.add_event([
			(time.perf_counter() - self.start_time),
			'Object Attribute',
			'Text',
			'Block',
			'Instructions',
			'Type',
			'Training'
		])

		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Block', 'Instructions')
		self.protocol_floatlayout.add_event([
			(time.perf_counter() - self.start_time),
			'Object Attribute',
			'Button',
			'Block',
			'Instructions',
			'Type',
			'Continue'
		])

	def _block_setup_first_testing_block(self):
		"""Set parameters and display for block 1 (first testing block of each stage)."""
		self.protocol_floatlayout.clear_widgets()

		# Set default parameters for all blocks; only change what's needed
		self.block_max_count = self.block_multiplier
		self.block_trial_max = self.block_trial_max_base
		self.block_duration = self.block_duration_max
		self.stimdur_frames = self.stimdur_base
		self.stimdur_seconds = self.stimdur_frames * self.frame_duration
		self.trial_list = self.trial_list_base
		self.trial_list_max_run = self.trial_list_max_run_base
		self.target_probability = self.target_prob_base

		#CJB Training Stage
		if self.current_stage == 'CJB_Training':
			self.trial_list = ['Target']
			self.block_trial_max = self.cjb_train_trials
			self.block_duration = 3*(self.block_trial_max)
			self.target_probability = 1.0
			self.cjb_task = True

		elif self.current_stage == 'CJB_Discrimination':
			self.block_trial_max = self.cjb_discrimination_trials
			self.target_probability = self.cjb_target_prob
			self.trial_list = self.trial_list_cjb_discrimination
			self.trial_list = self._constrained_shuffle_cjb(self.trial_list, max_run=self.trial_list_max_run)
			self.cjb_task = True
		

		elif self.current_stage == 'CJB_Probe':
			self.block_trial_max = self.cjb_probe_trials
			self.target_probability = self.cjb_target_prob
			self.trial_list = self.trial_list_cjb_probe
			self.trial_list = self._constrained_shuffle_cjb(self.trial_list, max_run=self.trial_list_max_run)
			self.cjb_task = True

		elif self.current_stage == 'Training':
			self.trial_list = ['Target']
			self.block_trial_max = self.training_block_max_correct
			self.block_duration = 3*(self.block_trial_max)
			self.target_probability = 1.0
			self.cjb_task = False

		# Create initial non-target image list
		elif 'Similarity' in self.current_stage:
			self.current_nontarget_image_list = self.nontarget_images[self.similarity_index_min:self.similarity_index_max]
			self.block_trial_max = self.block_trial_max_staircase
			self.cjb_task = False

		# Set starting stimulus duration to mean decision point time (i.e., finger lift from hold button)
		elif 'StimDur' in self.current_stage:
			self.block_trial_max = self.block_trial_max_staircase

			if len(self.decision_point_tracking) > 0:
				self.stimdur_seconds = statistics.mean(self.decision_point_tracking)

			else:
				self.stimdur_seconds = round((self.limhold_seconds / 2), 3)

			self.stimdur_frames = self.stimdur_seconds // self.frame_duration
			self.stimdur_frame_change = (self.stimdur_frames - self.stimdur_frame_min) // 2

			self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus Duration', str(self.stimdur_frames), 'Frames')
			self.protocol_floatlayout.add_variable_event('Parameter', 'Stimulus Duration', str(self.stimdur_seconds), 'Seconds')
			self.cjb_task = False

		# Set maximum trial number for flanker probe
		elif self.current_stage == 'Flanker_Fixed_Probe':
			self.block_trial_max = self.block_trial_max_flanker

			self.trial_list_flanker_dict = {
				'non': self.constrained_shuffle(self.trial_list_base, max_run=self.trial_list_max_run)
				, 'con': self.constrained_shuffle(self.trial_list_base, max_run=self.trial_list_max_run)
				, 'inc': self.constrained_shuffle(self.trial_list_base, max_run=self.trial_list_max_run)
				}

			self.trial_list_flanker_index_dict = {'non': 0, 'con': 0, 'inc': 0}
			self.cjb_task = False

		# Set parameters for first target probability probe
		elif self.current_stage == 'TarProb_Fixed_Probe':
			self.block_max_count = len(self.target_prob_hilo)
			self.trial_list_max_run = self.trial_list_max_run_hilo
			self.target_prob_hilo_index = self.current_block - 1
			self.target_probability = self.target_prob_hilo[self.target_prob_hilo_index]

			self.trial_list = list()

			for iTrial in range(round((self.trial_list_length_hilo * self.target_probability))):
				self.trial_list.append('Target')

			for iTrial in range(len(self.trial_list), self.trial_list_length_hilo):
				self.trial_list.append('Nontarget')
			self.cjb_task = False

		# Set parameters for SART probe
		elif self.current_stage == 'SART_Fixed_Probe':
			self.trial_list_max_run = self.trial_list_max_run_hilo
			self.target_probability = max(self.target_prob_hilo)

			self.trial_list = list()

			for iTrial in range(round((self.trial_list_length_hilo * self.target_probability))):
				self.trial_list.append('Nontarget')

			for iTrial in range(len(self.trial_list_hilo), self.trial_list_length_hilo):
				self.trial_list.append('Target')
			self.cjb_task = False

		self.instruction_button.text = 'Press Here to Start'
		self.center_instr_image.texture = self.image_dict[self.target_image].image.texture

		self.protocol_floatlayout.add_widget(self.instruction_button)

		self.protocol_floatlayout.add_object_event('Display', 'Image', 'Block', 'Instructions', self.target_image)
		self.protocol_floatlayout.add_object_event('Display', 'Text', 'Block', 'Instructions')
		self.protocol_floatlayout.add_event([
			(time.perf_counter() - self.start_time),
			'Object Attribute',
			'Text',
			'Block',
			'Instructions',
			'Type',
			'Task'
		])

		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Block', 'Instructions')
		self.protocol_floatlayout.add_event([
			(time.perf_counter() - self.start_time),
			'Object Attribute',
			'Button',
			'Block',
			'Instructions',
			'Type',
			'Continue'
		])

	def _block_setup_subsequent_block(self):
		"""Set parameters for blocks beyond the first testing block (block > 1)."""
		# Set parameters for subsequent target probability probes
		if self.current_stage == 'TarProb_Fixed_Probe':
			self.block_max_count = len(self.target_prob_hilo)
			self.trial_list_max_run = self.trial_list_max_run_hilo
			self.target_prob_hilo_index = self.current_block - 1
			self.target_probability = self.target_prob_hilo[self.target_prob_hilo_index]

			self.trial_list = list()

			for iTrial in range(round((self.trial_list_length_hilo * self.target_probability))):
				self.trial_list.append('Target')

			for iTrial in range(len(self.trial_list), self.trial_list_length_hilo):
				self.trial_list.append('Nontarget')

		self.protocol_floatlayout.add_widget(self.hold_button)

	def _block_reset_and_start_trial(self):
		"""Emit the trial-list event, reset all per-block trial state, then dispatch to the next trial."""
		self.protocol_floatlayout.add_variable_event('Parameter', 'Trial List', self.current_stage, 'Probability', self.target_probability)

		self.current_hits = 0
		self.last_response = 0
		self.contingency = 0
		self.trial_outcome = 0
		self.current_block_trial = 0
		self.trial_index = -1

		self.hit_tracking = list()
		self.false_alarm_tracking = list()
		self.similarity_tracking = list()
		self.decision_point_tracking = list()
		self.stimdur_frame_tracking = [(self.limhold_seconds // self.frame_duration)]

		self.trial_list = self.constrained_shuffle(self.trial_list, max_run=self.trial_list_max_run)

		self.block_start = time.perf_counter()

		self.protocol_floatlayout.add_variable_event('Parameter', 'Block Start Time', str(self.block_start))

		self.block_started = False
		if self.hold_button.disabled:
			self.hold_button.disabled = False

		if 'Blur_Staircase_Difficulty' in self.stage_list \
				or self.current_stage == 'Blur_Staircase_Probe':
			self.blur_preload_start()

		else:
			self.trial_contingency()

	# --- End block_contingency helpers ---

	def block_contingency(self, *args):

		try:

			self.protocol_floatlayout.add_stage_event('Block Contingency')

			self._block_init_screen()

			if self._block_advance_stage():
				return

			if self.stage_index >= len(self.stage_list): # Check if all stages complete
				self.protocol_floatlayout.add_stage_event('Protocol End')
				self.protocol_end()

			if self._block_load_stage_video(
					'Similarity_Staircase_Difficulty', 'sim_scale_video_path',
					'sim_scale_video_played', stop_after_load=True):
				return

			if self._block_load_stage_video(
					'StimDur_Staircase_Probe', 'stimdur_video_path', 'stimdur_video_played'):
				return

			if self._block_load_stage_video(
					'TarProb_Fixed_Probe', 'tar_prob_video_path', 'tar_prob_video_played'):
				return

			self._block_setup_block_parameters()
			self._block_reset_and_start_trial()


		except KeyboardInterrupt:

			print('Program terminated by user.')
			self.protocol_end()

		except:

			print('Error; program terminated from Block Contingency.')
			self.protocol_end()