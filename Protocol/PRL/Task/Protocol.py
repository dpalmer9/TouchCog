"""PRL protocol task screen, defining the trial flow, outcomes and data output."""
# Imports #
import configparser
import numpy as np
import pathlib
import random
import time
import traceback

from Classes.Protocol import ImageButton, ProtocolBase, PreloadedVideo

from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.video import Video


class ProtocolScreen(ProtocolBase):
	"""Screen implementing the Probabilistic Reversal Learning (PRL) task.

	Extends :class:`Classes.Protocol.ProtocolBase` with PRL-specific configuration
	loading, task variables, reward stages and summary data columns.

	Attributes
	----------
	protocol_name : str
		Name of the active protocol, ``'PRL'``.
	name : str
		Screen name, ``'PRL_protocolscreen'``.
	data_cols : list of str
		Column names of the trial summary data file.
	metadata_cols : list of str
		Column names of the metadata output file.
	config_path : str
		Path of the protocol's ``Configuration.ini``.
	debug_mode : bool
		Whether debug parameters are used.
	parameters_dict : configparser.SectionProxy
		Configuration section supplying the task parameter values.
	"""

	def __init__(self, **kwargs):
		"""Initialise the PRL protocol screen and load its configuration.

		Sets the protocol name, screen name and data/metadata column names, reads
		``Configuration.ini`` and selects the ``DebugParameters`` or
		``TaskParameters`` section based on the ``debug_mode`` flag.

		Parameters
		----------
		**kwargs : dict
			Additional keyword arguments passed to
			:class:`Classes.Protocol.ProtocolBase`.
		"""

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
		"""Load task parameters from a configuration section into instance state.

		Reads participant, timing, block, reward-probability, reversal, image-set
		and stage values from ``parameters_dict`` (using the given defaults), creates
		the session-duration Clock trigger, loads the hold and mask image names, and
		builds ``stage_list`` (optionally prepending ``'Training'``).

		Parameters
		----------
		parameters_dict : dict
			Parameter name to value mapping, as built by the settings menu (a configuration section also works).
		"""
		self.parameters_dict = parameters_dict

		self.participant_id = self.parameters_dict.get('participant_id', '')

		self.skip_tutorial_video = self._safe_get_bool('skip_tutorial_video', False)

		self.block_change_on_duration = self._safe_get_bool('block_change_on_duration_only', True)

		self.iti_fixed_or_range = self.parameters_dict.get('iti_fixed_or_range', 'range')
		
		self.iti_import = self.parameters_dict.get('iti_length', '0.75,1.25')
		self.iti_import = self.iti_import.split(',')
		
		self.feedback_length = float(self.parameters_dict.get('feedback_length', '0.75'))
		self.block_duration = int(self.parameters_dict.get('block_duration', '360'))
		self.block_min_rest_duration = float(self.parameters_dict.get('block_min_rest_duration', '2'))
		self.session_duration = float(self.parameters_dict.get('session_duration', '3600'))
		self.session_event = self.session_clock.create_trigger(self.clock_monitor, self.session_duration, interval=False)
		
		self.block_multiplier = int(self.parameters_dict.get('block_multiplier', '1'))
		self.block_trial_max = int(self.parameters_dict.get('block_trial_max', '90'))
		
		self.target_reward_probability = float(self.parameters_dict.get('target_reward_probability', '0.8'))
		self.reversal_threshold = int(self.parameters_dict.get('reversal_threshold', '5'))
		self.max_reversals = int(self.parameters_dict.get('max_reversals', '18'))

		self.image_set = self.parameters_dict.get('image_set', 'circle')

		self.training_target_image = self.parameters_dict.get('training_target_image', 'snowflake')
		self.training_nontarget_image = self.parameters_dict.get('training_nontarget_image', 'grey')
		
		self.training_block_max_correct = int(self.parameters_dict.get('training_block_max_correct', '3'))

		self.hold_image = self.config_file['Hold']['hold_image']
		self.mask_image = self.config_file['Mask']['mask_image']

		# Define Variables - List

		self.stage_list = list()

		if self._safe_get_bool('training_task', False):
			self.stage_list.append('Training')

		self.stage_list.append('Test')

	def _load_task_variables(self):
		"""Initialise the per-task state that drives the PRL trial flow.

		Sets the language and image directory paths, timing values (seconds from
		``time.perf_counter``), counters and Boolean flags, and the string state for
		the current stage, target/nontarget images and their shuffled left/right
		locations.
		"""
		# Define Paths

		self.language_dir_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language
		self.image_dir_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Image'

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

		self.target_image_index = self.image_index_choice[0]
		self.nontarget_image_index = self.image_index_choice[1]


		# Define Boolean

		self.target_rewarded = True
		self.nontarget_rewarded = False
		self.choice_rewarded = True
		self.stimulus_on_screen = False
		self.tutorial_completed = False
		self.protocol_started_from_tutorial = False
		self.section_advance_active = False
		self.final_results_active = False
		self.end_protocol_active = False
		self.block_contingency_active = False
		self.trial_response_active = False


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

	def _set_hold_button_callbacks(self, on_press=None, on_release=None):
		"""Rebind the hold button's press and release callbacks.

		Unbinds ``iti_start`` from ``on_press`` and ``premature_response`` and
		``hold_remind`` from ``on_release``, then binds ``on_press`` and
		``on_release`` when they are not None.

		Parameters
		----------
		on_press : callable, optional
			Callback bound to the button's press event. Defaults to None.
		on_release : callable, optional
			Callback bound to the button's release event. Defaults to None.
		"""
		self.hold_button.unbind(on_press=self.iti_start)
		self.hold_button.unbind(on_release=self.premature_response)
		self.hold_button.unbind(on_release=self.hold_remind)

		if on_press is not None:
			self.hold_button.bind(on_press=on_press)
		if on_release is not None:
			self.hold_button.bind(on_release=on_release)

	def _set_choice_callbacks(self, enabled):
		"""Enable or disable the left and right stimulus press callbacks.

		Unbinds ``left_pressed`` from the left stimulus button and
		``right_pressed`` from the right one, and re-binds them only when ``enabled``
		is True.

		Parameters
		----------
		enabled : bool
			Whether the choice callbacks should be bound.
		"""
		self.left_stimulus.unbind(on_press=self.left_pressed)
		self.right_stimulus.unbind(on_press=self.right_pressed)
		if enabled:
			self.left_stimulus.bind(on_press=self.left_pressed)
			self.right_stimulus.bind(on_press=self.right_pressed)

	def end_protocol_pressed(self, *args):
		"""End the protocol when the end-protocol button is pressed.

		Ignores the call when ``end_protocol_active`` is set or the protocol has
		already ended. Otherwise marks the protocol as ended, disables the button
		and calls :meth:`protocol_end`.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		if self.end_protocol_active or getattr(self, 'protocol_ended', False):
			return

		self.end_protocol_active = True
		self.end_protocol_button.disabled = True
		self.protocol_end()

	def _setup_session_stages(self):
		"""Build the shuffled per-trial reward assignment list for the session.

		Sets ``nontarget_reward_probability`` to 1 minus
		``target_reward_probability`` rounded to 2 decimals, then appends
		``'Target'`` and ``'NonTarget'`` entries to ``trial_reward_list`` according
		to each probability times ``block_trial_max``, and constrained-shuffles the
		list with a maximum run of 5.
		"""
		self.nontarget_reward_probability = round(1 - self.target_reward_probability, 2)

		self.trial_reward_list = list()
		self.trial_reward_list_index = -1

		for iTrial in range(int(self.target_reward_probability * self.block_trial_max)):
			self.trial_reward_list.append('Target')
		

		for iTrial in range(int(self.nontarget_reward_probability * self.block_trial_max)):
			self.trial_reward_list.append('NonTarget')
		
		self.trial_reward_list = self.constrained_shuffle(self.trial_reward_list, max_run=5)

	def _setup_image_widgets(self):
		"""Create the stimulus, hold and instruction widgets for the task.

		Collects the stimulus PNGs from ``Targets/<image_set>``, sets the hold,
		mask and training image paths, binds the hold-button and choice callbacks,
		loads the images, builds the left and right stimulus buttons and the
		instruction button, and sets ``stimulus_image_source`` to the single
		stimulus file (or the mask path when there is more than one).
		"""
		# Define Widgets - Images

		self.stimulus_path_list = list(self.image_dir_path.glob(str(pathlib.Path('Targets', self.image_set, '*.png'))))
		self.target_image_list = list()

		for filename in self.stimulus_path_list:
			self.target_image_list.append(filename.stem)
		
		self.total_image_list = self.stimulus_path_list

		self.hold_image_path = str(self.image_dir_path / (self.hold_image + '.png'))
		self.mask_image_path = str(self.image_dir_path / (self.mask_image + '.png'))

		self._set_hold_button_callbacks(on_press=self.iti_start, on_release=self.premature_response)

		self.training_target_image_path = str(self.image_dir_path / (self.training_target_image + '.png'))
		self.training_nontarget_image_path = str(self.image_dir_path / (self.training_nontarget_image + '.png'))

		self.total_image_list += [self.hold_image_path, self.mask_image_path, self.training_target_image_path, self.training_nontarget_image_path]

		self.load_images(self.total_image_list)

		if len(self.target_image_list) == 1:
			self.stimulus_image_source = str(self.stimulus_path_list[0])
		
		else:
			self.stimulus_image_source = str(self.mask_image_path)

		self.hold_button.source = str(self.hold_image_path)

		self.text_button_size = [0.4, 0.15]
		self.text_button_pos_LL = {"center_x": 0.25, "center_y": 0.08}
		self.text_button_pos_LR = {"center_x": 0.75, "center_y": 0.08}

		self.stimulus_size = (0.4 * self.width_adjust, 0.4 * self.height_adjust)
		self.stimulus_pos_l = {'center_x': 0.25, 'center_y': 0.55}
		self.stimulus_pos_r = {'center_x': 0.75, 'center_y': 0.55}

		self.left_stimulus = ImageButton(source=str(self.stimulus_image_source))
		self.left_stimulus.size_hint = self.stimulus_size
		self.left_stimulus.pos_hint = self.stimulus_pos_l

		self.right_stimulus = ImageButton(source=str(self.stimulus_image_source))
		self.right_stimulus.size_hint = self.stimulus_size
		self.right_stimulus.pos_hint = self.stimulus_pos_r
		self._set_choice_callbacks(True)

		self.instruction_button = Button(font_size='60sp')
		self.instruction_button.size_hint = self.text_button_size
		self.instruction_button.pos_hint =  {"center_x": 0.5, "center_y": 0.9}
		self.instruction_button.unbind(on_press=self.section_start)
		self.instruction_button.bind(on_press=self.section_start)

	def _setup_language_localization(self):
		"""Load the localised button texts and outcome and staging dictionaries.

		Calls :meth:`set_language`, reads the end-task and begin-section button
		strings from ``Button.ini``, and populates ``outcome_dict`` from each
		``outcome_*.txt`` file (keyed by the part after ``outcome_``) and
		``staging_dict`` from each ``staging_*.txt`` file similarly.
		"""
		self.set_language(self.language)

		button_lang_path = self.lang_folder_path / 'Button.ini'
		button_lang_config = configparser.ConfigParser()
		button_lang_config.read(button_lang_path, encoding='utf-8')

		self.end_protocol_button_str = button_lang_config['Button']['end_task']
		self.begin_section_button_str = button_lang_config['Button']['begin_section']

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
		"""Load the tutorial video, feedback strings and instruction components.

		Builds the feedback ``'points_awarded'`` markup string from
		``Feedback.ini``, creates the tutorial :class:`PreloadedVideo` when a
		``Tutorial_Video`` folder exists, wires the tutorial continue button, and
		reads the Main train and task instructions from ``Instructions.ini`` plus the
		initial score label.
		"""
		# Tutorial Import

		self.lang_folder_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language

		feedback_lang_path = self.lang_folder_path / 'Feedback.ini'
		feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
		feedback_lang_config.read(feedback_lang_path, encoding='utf-8')

		points_awarded_feedback_string = '[color=%s]' \
			% feedback_lang_config['Stimulus']['points_awarded_colour'] \
			+ feedback_lang_config['Stimulus']['points_awarded'] \
			+ '[/color]'
		
		self.feedback_dict['points_awarded'] = points_awarded_feedback_string

		if (self.lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_path = self.lang_folder_path / 'Tutorial_Video' / 'PRL-Tutorial_Video-2025-09-18.mp4'
			self.tutorial_video = PreloadedVideo(
				source_path = str(self.tutorial_video_path)
				, pos_hint={'center_x': 0.5, 'center_y': 0.55},
				size_hint=(0.95, 0.75),
				fit_mode = 'contain',
				loop=False
				)
		
		self.tutorial_continue_button.unbind(on_press=self.stop_tutorial_video)
		self.tutorial_continue_button.bind(on_press=self.stop_tutorial_video)


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
		"""Load the protocol parameters and start the session clock.

		Runs the config, task-variable, session-stage, image-widget, language and
		video/instruction setup steps in turn, then starts the clock.

		Parameters
		----------
		parameter_dict : dict
			Parameter name to value mapping, as built by the settings menu (a configuration section also works).
		"""
		self._load_config_parameters(parameter_dict)
		self._load_task_variables()
		self._setup_session_stages()
		self._setup_image_widgets()
		self._setup_language_localization()
		self._load_video_and_instruction_components()

		self.start_clock()
		
		
		# Begin Task
		if (self.lang_folder_path / 'Tutorial_Video').is_dir():

			self.protocol_floatlayout.clear_widgets()
			self.trigger_tutorial_screen()
		
		else:
			self.present_instructions()
			self.start_button.unbind(on_press=self.start_protocol)
			self.start_button.bind(on_press=self.start_protocol_from_tutorial)
	
	
	def stop_tutorial_video(self, *args):
		"""Stop the tutorial video and begin the protocol.

		Return early when the tutorial is already complete or the protocol has
		ended. Otherwise marks the tutorial complete, disables and unbinds the
		continue button, stops the video, logs the ``Remove``/``Video``/
		``Section``/``Instructions`` event and calls ``self.start_protocol_from_tutorial``.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if self.tutorial_completed or getattr(self, 'protocol_ended', False):
			return

		self.tutorial_completed = True
		self.tutorial_continue_button.disabled = True
		self.tutorial_continue_button.unbind(on_press=self.stop_tutorial_video)
		self.tutorial_video.state = 'stop'
		self.protocol_floatlayout.add_object_event('Remove', 'Video', 'Section', 'Instructions')
		self.start_protocol_from_tutorial()
	
	
	
	def start_protocol_from_tutorial(self, *args):
		"""Begin the session from the tutorial screen.

		Return early when already started from the tutorial or the protocol has
		ended. Otherwise marks it started, clears the screen, logs the video
		removal and ``Section Start`` stage events, then generates the output and
		metadata files and calls ``self.block_contingency``.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		if self.protocol_started_from_tutorial or getattr(self, 'protocol_ended', False):
			return

		self.protocol_started_from_tutorial = True
		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_object_event('Remove', 'Video', 'Section', 'Instructions')

		self.protocol_floatlayout.add_stage_event('Section Start')

		self.generate_output_files()
		self.metadata_output_generation()
		self.block_contingency()


	def section_start(self, *args):
		"""Start a section by clearing the screen and ending the current block.

		Return early when a section advance is already active or the protocol has
		ended. Otherwise marks the advance active, disables the instruction
		button, clears the screen, logs the ``Section Start`` stage event and the
		instruction text/button ``Display`` object events (the widgets themselves
		are not added here), then calls ``block_end``.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		if self.section_advance_active or getattr(self, 'protocol_ended', False):
			return

		self.section_advance_active = True
		self.instruction_button.disabled = True

		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_stage_event('Section Start')
		self.protocol_floatlayout.add_object_event('Display', 'Text', 'Section', 'Instructions', 'Section Start')
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Section', 'Instructions', 'Continue')
		
		self.block_end()
	


	def final_results_screen(self, *args):
		"""Build and show the final results screen.

		Return early when already active or the protocol has ended. Sets the
		active flags, creates the end-protocol button and the result label from
		``self.outcome_dict['result']``, then logs the ``Display`` text/button and
		``Task End`` stage events.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		if self.final_results_active or getattr(self, 'protocol_ended', False):
			return

		self.final_results_active = True
		self.end_protocol_active = False

		self.end_protocol_button = Button(font_size='60sp')
		self.end_protocol_button.size_hint = [0.4, 0.15]
		self.end_protocol_button.pos_hint =  {"center_x": 0.50, "center_y": 0.1}
		self.end_protocol_button.text = self.end_protocol_button_str
		self.end_protocol_button.bind(on_press=self.end_protocol_pressed)

		self.result_label_str = eval(f'f"""{self.outcome_dict.get("result", "")}"""')
		self.result_label = Label(text=self.result_label_str, font_size='50sp', markup=True, halign='center')
		self.result_label.size_hint = (0.8, 0.3)
		self.result_label.pos_hint = {'center_x': 0.5, 'center_y': 0.6}

		self.protocol_floatlayout.add_widget(self.result_label)
		self.protocol_floatlayout.add_widget(self.end_protocol_button)
		
		self.protocol_floatlayout.add_object_event('Display', 'Text', 'Stage', 'Results')
		self.protocol_floatlayout.add_object_event('Display', 'Button', 'Stage', 'End Protocol')
		self.protocol_floatlayout.add_stage_event('Task End')



	def stimulus_presentation(self, *args): # Stimulus presentation
		"""Present the target and nontarget stimuli and record onset time.

		Disables the response flags, sets the hold-button and choice callbacks,
		swaps the hold button for the two stimulus widgets, records
		``self.stimulus_start_time`` with ``time.perf_counter`` and logs the
		``Object Display`` stage event plus both stimulus display events.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		self.trial_response_active = False
		self.stimulus_on_screen = True
		self._set_hold_button_callbacks()
		self._set_choice_callbacks(True)

		self.protocol_floatlayout.remove_widget(self.hold_button)
		self.protocol_floatlayout.add_widget(self.left_stimulus)
		self.protocol_floatlayout.add_widget(self.right_stimulus)
		
		self.stimulus_start_time = time.perf_counter()
		
		self.protocol_floatlayout.add_stage_event('Object Display')
		
		self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Target', self.target_loc, self.target_image)
		self.protocol_floatlayout.add_object_event('Display', 'Stimulus', 'Nontarget', self.nontarget_loc, self.nontarget_image)
		


	# Hold released too early
	
	def premature_response(self, *args):
		"""Handle a hold button release before the stimulus onset.

		Return early when a stimulus is on screen, a section advance is active, a
		block has started or the protocol has ended. Otherwise stops the
		scheduled ITI and feedback callbacks, clears the screen, records the
		response latency as ``np.nan``, logs the ``Premature Response`` stage
		event and the ``Outcome``/``Response Latency`` variable, assigns the wait
		feedback when none is shown, rebinds the hold button to ``iti_start`` and
		re-adds it.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		
		if self.stimulus_on_screen is True or self.section_advance_active or self.block_started or getattr(self, 'protocol_ended', False):
			return
		
		Clock.unschedule(self.iti_end)
		Clock.unschedule(self.remove_feedback)
		self.remove_feedback()
		
		self.protocol_floatlayout.clear_widgets()
		
		self.response_latency = np.nan
		
		self.protocol_floatlayout.add_stage_event('Premature Response')
		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)
		
		self.iti_active = False

		if self.feedback_on_screen is False:	
			self.assign_feedback(feedback_key='wait')
		
		self._set_hold_button_callbacks(on_press=self.iti_start)
	
		self.protocol_floatlayout.add_widget(self.hold_button)
	
	
	
	# Left Stimulus Pressed
	
	def left_pressed(self, *args):
		"""Handle a press on the left stimulus.

		Return early when a response is active, no stimulus is on screen or the
		protocol has ended. Records ``self.stimulus_press_time`` with
		``time.perf_counter``, sets the response latency as the elapsed seconds
		since ``self.stimulus_start_time``, stores ``self.side_chosen`` as 'Left',
		logs the ``Left Stimulus Pressed`` stage event and evaluates outcomes.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if self.trial_response_active or (not self.stimulus_on_screen) or getattr(self, 'protocol_ended', False):
			return

		self.trial_response_active = True

		self.stimulus_press_time = time.perf_counter()
		self.response_latency = self.stimulus_press_time - self.stimulus_start_time
		self.side_chosen = 'Left'
		self.protocol_floatlayout.add_stage_event('Left Stimulus Pressed')
		self.trial_outcomes()
	
	
	
	# Right Stimulus Pressed
	
	def right_pressed(self, *args):
		"""Handle a press on the right stimulus.

		Return early when a response is active, no stimulus is on screen or the
		protocol has ended. Records ``self.stimulus_press_time`` with
		``time.perf_counter``, sets the response latency as the elapsed seconds
		since ``self.stimulus_start_time``, stores ``self.side_chosen`` as 'Right',
		logs the ``Right Stimulus Pressed`` stage event and evaluates outcomes.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if self.trial_response_active or (not self.stimulus_on_screen) or getattr(self, 'protocol_ended', False):
			return

		self.trial_response_active = True

		self.stimulus_press_time = time.perf_counter()
		self.response_latency = self.stimulus_press_time - self.stimulus_start_time
		self.side_chosen = 'Right'
		self.protocol_floatlayout.add_stage_event('Right Stimulus Pressed')
		self.trial_outcomes()



	def trial_outcomes(self, *args):
		"""Score the stimulus response and set up the next trial.

		Marks the stimulus off screen and disables the choice callbacks. Compares
		``self.side_chosen`` with the target and nontarget locations: a target
		press sets ``last_response`` to 1, increments ``current_hits`` and sets
		``choice_rewarded`` to ``target_rewarded``, while a nontarget press sets
		``last_response`` to 0, resets ``current_hits`` to 0 and sets
		``choice_rewarded`` to the opposite of ``target_rewarded``. A
		rewarded choice adds 10 points (except in Training), logs ``Points
		Collected`` and logs ``Choice Rewarded``; an unrewarded choice logs
		``Choice Not Rewarded``. The outcome variables and removed stimulus
		events are logged, the hold button is re-added bound to
		``iti_start``/``premature_response``, feedback is assigned when the
		outcome has a label, and the trial is written and its contingency
		evaluated.

		Notes
		-----
		Outcome codes written to the summary (``Correct`` column): ``last_response`` is
		1 for a target press and 0 for a nontarget press. ``response_latency`` is
		seconds from stimulus onset to the press. The points (10 per rewarded
		non-training choice) appear only in the event log as the ``Points`` outcome
		variable, not in the summary row.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		self.stimulus_on_screen = False
		self._set_choice_callbacks(False)

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
				outcome_label = 'correct'




			else:
				outcome_label = 'correct'
				self.point_counter += 10

				self.protocol_floatlayout.add_stage_event('Points Collected')
				self.protocol_floatlayout.add_variable_event('Outcome', 'Points', self.point_counter)
		
		else:
			outcome_label = ''
			self.protocol_floatlayout.add_stage_event('Choice Not Rewarded')

		self.protocol_floatlayout.add_variable_event('Outcome', 'Side Chosen', self.side_chosen)
		self.protocol_floatlayout.add_variable_event('Outcome', 'Last Response', self.last_response)
		self.protocol_floatlayout.add_variable_event('Outcome', 'Current Hits', self.current_hits)
		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)

		self.protocol_floatlayout.remove_widget(self.left_stimulus)
		self.protocol_floatlayout.remove_widget(self.right_stimulus)

		self.protocol_floatlayout.add_object_event('Remove', 'Image', 'Target', 'Location', self.target_loc)
		self.protocol_floatlayout.add_object_event('Remove', 'Image', 'Nontarget', 'Location', self.nontarget_loc)

		self._set_hold_button_callbacks(on_press=self.iti_start, on_release=self.premature_response)

		if outcome_label != '' \
			and not self.feedback_on_screen:
			self.assign_feedback(feedback_key=outcome_label)
		
		self.protocol_floatlayout.add_widget(self.hold_button)
		
		self.write_trial()
		
		self.trial_contingency()
	
	
	
	# Data Saving Function
	
	def write_trial(self):
		"""Write the current trial's summary row to the summary data file.

		Collects the trial outcome and timing values into a row and passes it to
		``self.write_summary_file``.

		Notes
		-----
		The row has 13 fields in the order of ``self.data_cols`` (``TrialNo``,
		``Stage``, ``ReversalNo``, ``TargetImage``, ``TargetLoc``,
		``NontargetImage``, ``NontargetLoc``, ``TargetReward``,
		``NontargetReward``, ``SideChosen``, ``Correct``, ``Rewarded``,
		``ResponseLat``). ``Correct`` holds ``last_response`` (1 target chosen, 0
		nontarget chosen) and ``Rewarded`` holds ``choice_rewarded``.
		``ResponseLat`` is ``response_latency``, in seconds from stimulus onset to
		the press (``time.perf_counter``). Only stimulus responses are written;
		premature responses write no row.
		"""
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
		"""Evaluate trial outcomes, handle reversal and set up the next trial.

		Run inside a try/except that calls ``self.protocol_end`` on errors. Resets
		the response flags, appends ``self.last_response`` to
		``self.response_tracking`` and checks whether the block has ended (by
		duration, by trial count, or for training by reaching
		``training_block_max_correct``); if so it calls ``self.block_contingency``.
		Otherwise it resets the trial state, increments ``current_trial`` and
		``current_block_trial``, picks the next ITI length in seconds (fixed
		choice or a uniform draw within ``self.iti_range``), advances the reversal
		index and shifts the target/nontarget locations when ``current_hits``
		reaches ``reversal_threshold``, and sets the reward contingency for the
		next trial. Logs the matching ``Parameter`` events. Finalises with
		``self.trial_end_time`` from ``time.perf_counter``.

		Notes
		-----
		Training stages always reward the target; otherwise the rewarded side is
		taken from ``trial_reward_list`` (reshuffled with ``constrained_shuffle``
		``max_run=5``). A reversal swaps the target/nontarget location indices
		once ``current_hits`` (consecutive target choices) reaches
		``reversal_threshold``; if that pushes ``current_reversal`` past
		``max_reversals`` the block is advanced through ``block_contingency``
		instead. The block ends on ``block_duration`` seconds, ``block_trial_max``
		trials, or (Training only) when the number of target choices reaches
		``training_block_max_correct``.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		
		try:
			self.trial_response_active = False
			self.stimulus_on_screen = False
			if self.current_block_trial != 0:
				self.response_tracking.append(self.last_response)

				# Check if block ended

				if (time.perf_counter() - self.block_start >= self.block_duration) \
					or (self.current_block_trial >= self.block_trial_max):

					# block_contingency sets up the next trial itself
					self.block_contingency()
					return

				elif (self.current_stage == 'Training') \
					and (sum(self.response_tracking) >= self.training_block_max_correct):

					self.block_contingency()
					return

			# Set next trial parameters
			
			self.side_chosen = ''
			self.choice_rewarded = False
			self.last_response = 0
			self.block_started = False
			self.section_advance_active = False

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
					return

				else:
					self.target_loc_index += 1
					self.nontarget_loc_index += 1

					if self.target_loc_index >= len(self.target_loc_list):
						self.target_loc_index = 0

					if self.nontarget_loc_index >= len(self.target_loc_list):
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
					self.trial_reward_list = self.constrained_shuffle(self.trial_reward_list, max_run=5)
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
		
		except Exception as e:
			print(f"Critical Error encountered: {e}")
			traceback.print_exc() 
			self.protocol_end()

	
	# Block Contingency Function
	
	def block_contingency(self, *args):
		"""Advance to the next block or stage and set up its parameters.

		Return early when a block change is already active or the protocol has
		ended. Otherwise, inside a try/finally that clears the active flag, it
		unschedules pending callbacks, clears the screen and increments
		``current_block``; when it exceeds ``block_multiplier`` (or is 0) the stage
		index advances and ``current_block`` is reset to 1. If all stages are complete it cancels the session event
		and shows the final results screen; otherwise it sets ``current_stage``,
		resets the next block's counters, chooses the images and logs the
		block/stage/parameter events. Training uses the training target and
		nontarget images; with a single-image list both stimuli use that image and
		the location indices shift; otherwise the image indices advance and the
		reward list is reshuffled and its first entry sets which side is rewarded.
		For the first block of a stage it configures the instruction text
		and calls ``self.section_start``; otherwise it calls ``self.block_screen``.
		Finally it calls ``self.trial_contingency`` to continue the flow.

		Notes
		-----
		Runs ``self.protocol_end`` on ``KeyboardInterrupt``/``Exception`` and resets
		``block_contingency_active`` in a ``finally`` block.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch.
		"""
		if self.block_contingency_active or getattr(self, 'protocol_ended', False):
			return

		self.block_contingency_active = True
		
		try:

			Clock.unschedule(self.iti_end)
			self._set_hold_button_callbacks()
			self._set_choice_callbacks(False)

			self.block_started = True
			self.section_advance_active = False
			self.trial_response_active = False
			self.stimulus_on_screen = False

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

				if self.nontarget_loc_index >= len(self.target_loc_list):
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

				self.trial_reward_list = self.constrained_shuffle(self.trial_reward_list, max_run=5)
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

				self.instruction_button.text = self.begin_section_button_str
				self.instruction_button.disabled = False

				#self.protocol_floatlayout.add_widget(self.instruction_label)
				#self.protocol_floatlayout.add_widget(self.instruction_button)
				
				self.protocol_floatlayout.add_object_event('Display', 'Text', 'Block', 'Instructions', 'Task')
				self.protocol_floatlayout.add_object_event('Display', 'Button', 'Block', 'Instructions', 'Continue')

				self.section_start()
			
			else:
				self.block_started = False
				self.block_screen()

			self.trial_contingency()
		
		
		except KeyboardInterrupt:
			
			print('Program terminated by user.')
			self.protocol_end()
		
		except Exception as e:
			print(f"Critical Error encountered: {e}")
			traceback.print_exc() 
			self.protocol_end()
		finally:
			self.block_contingency_active = False