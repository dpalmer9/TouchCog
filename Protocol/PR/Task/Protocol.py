"""Task screen for the PR (progressive ratio) protocol."""
# Imports #

import configparser
import numpy as np
import pathlib
import random
import statistics
import traceback
import time

from Classes.Protocol import ImageButton, ProtocolBase, PreloadedVideo

from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.video import Video




class ProtocolScreen(ProtocolBase):
	"""Task screen for the PR (progressive ratio) protocol.

	Builds the PR task widgets, state and trial-flow handlers, extending
	:class:`Classes.Protocol.ProtocolBase`.

	Attributes
	----------
	protocol_name : str
		The protocol identifier, ``'PR'``.
	data_cols : list of str
		Columns of the trial summary CSV row (TrialNo, CurrentBlock, BlockTrial,
		TotalHitCount, ResponseLevel, TargetXPos, TargetYPos, Latency).
	metadata_cols : list of str
		Columns of the metadata CSV header.
	parameters_dict : configparser.SectionProxy
		Active parameter section; DebugParameters in debug mode, else TaskParameters.
	response_level : int
		Current response level.
	stimulus_pos : dict
		Current stimulus position as a pos_hint mapping of center_x/center_y.
	"""

	def __init__(self, **kwargs):
		"""Initialize the PR protocol screen and load task configuration.

		Sets the protocol and screen names, refreshes the task via
		:meth:`update_task`, defines the trial and metadata column lists, reads the
		configuration file, selects the debug or task parameter section, and leaves
		other widget setup to :meth:`load_parameters`.

		Parameters
		----------
		**kwargs : dict
			Keyword arguments forwarded to the base screen.
		"""
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
		"""Load task parameters from the given configuration section.

		Reads participant and option flags, ITI length (comma-separated range),
		feedback, timeout, hold-button delay, block and session durations, stimulus
		and response-level settings, and (from the ``Hold`` and ``Mask`` sections of
		the config file, not from ``parameters_dict``) the hold and mask image names. Creates the
		session-events trigger from ``session_duration``.

		Parameters
		----------
		parameters_dict : dict
			Parameter name to value mapping, as built by the settings menu (a configuration section also works).

		Notes
		-----
		Defaults used when a key is absent: ITI ``'0.75,1.25'``, feedback
		``'0.75'``, timeout ``'15'``, hold button delay ``'1'``, block duration
		``'1200'``, min rest ``'1'``, session ``'3600'``, stimulus
		``'whitecircle'``, pressed ``'greycircle'``, size ``'0.08'``, distance
		``'0.6'``, response levels start 1 and end 10.
		"""
		self.parameters_dict = parameters_dict
		self.participant_id = self.parameters_dict.get('participant_id', '')
		self.skip_tutorial_video = self._safe_get_bool('skip_tutorial_video', False)

		self.block_change_on_duration = self._safe_get_bool('block_change_on_duration_only', True)

		self.iti_fixed_or_range = self.parameters_dict.get('iti_fixed_or_range', 'range')
		
		self.iti_import = self.parameters_dict.get('iti_length', '0.75,1.25')
		self.iti_import = self.iti_import.split(',')

		self.feedback_length = float(self.parameters_dict.get('feedback_length', '0.75'))
		self.timeout_duration = int(self.parameters_dict.get('timeout_duration', '15'))
		self.hold_button_delay = float(self.parameters_dict.get('hold_button_delay', '1'))
		self.block_duration = int(self.parameters_dict.get('block_duration', '1200'))
		self.block_min_rest_duration = float(self.parameters_dict.get('block_min_rest_duration', '1'))
		self.session_duration = float(self.parameters_dict.get('session_duration', '3600'))
		self.session_event = self.session_clock.create_trigger(self.clock_monitor, self.session_duration, interval=False)
		
		self.block_multiplier = int(self.parameters_dict.get('block_multiplier', '1'))

		self.stimulus_image = self.parameters_dict.get('stimulus_image', 'whitecircle')
		self.stimulus_pressed_image = self.parameters_dict.get('stimulus_pressed_image', 'greycircle')
		self.stimulus_size = float(self.parameters_dict.get('stimulus_size', '0.08'))
		self.stimulus_distance = float(self.parameters_dict.get('stimulus_distance', '0.6'))
		
		self.response_level = int(self.parameters_dict.get('response_level_start', '1'))
		self.response_level_end = int(self.parameters_dict.get('response_level_end', '10'))

		self.use_confirmation = self._safe_get_bool('use_confirmation', 'True')

		self.hold_image = self.config_file['Hold']['hold_image']
		self.mask_image = self.config_file['Mask']['mask_image']

	def _load_task_variables(self):
		"""Initialize counters, timing and boolean task state.

		Sets the hit target (``2 ** response_level``) from the response level, resets
		``total_hit_count``, ``current_block`` (-1) and the timing values, and initializes the flags that drive task flow (feedback
		and stimulus on screen, participant stopped, tutorial state, results active,
		response recorded, awaiting restart).
		"""
		# Define Variables - Count

		self.hit_target = 2 ** self.response_level
		self.total_hit_count = 0
		self.response_count_list = list()

		self.current_block = -1

		self.current_trial = 1


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
		self.tutorial_completed = False
		self.protocol_started_from_tutorial = False
		self.results_active = False
		self.block_start_active = False
		self.response_recorded = False
		self.awaiting_restart = False

	def _setup_session_stages(self):
		"""Assign the Kivy task clock and create the no-response timer.

		Sets ``self.task_clock`` to Kivy's ``Clock``, schedules ``protocol_end``
		after ``self.timeout_duration`` seconds, and immediately cancels that event
		so it only fires once re-armed.
		"""
		self.task_clock = Clock
		self.no_response_event = self.task_clock.schedule_once(self.protocol_end, self.timeout_duration)
		self.no_response_event.cancel()

	def _setup_image_widgets(self):
		"""Build the PR task buttons, images and stimulus position boundaries.

		Creates the quit, confirm and block-start buttons, resolves the stimulus,
		hold, mask and checkmark image paths, computes x/y stimulus boundaries from
		the stimulus size and distance (clamping them so the stimulus stays on
		screen), creates the stimulus button images and reward image, and re-binds
		the hold button release to ``premature_response``.
		"""
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
		
		# Clamp the boundaries
		min_x = max(min(self.x_boundaries), (((self.stimulus_size * self.width_adjust) / 2) + 0.005))
		max_x = min(max(self.x_boundaries), (1 - ((self.stimulus_size * self.width_adjust) / 2) - 0.005))

		self.x_boundaries = [round(min_x, 3), round(max_x, 3)]

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
		"""Configure the feedback label, language feedback text and outcome text dicts.

		Sets the active language via ``self.set_language``, creates the feedback
		label and reads ``Feedback.ini`` for the ``start_block`` and ``mid_block``
		feedback strings (falling back to defaults and converting ``\\n`` to
		newlines). Resets ``self.outcome_dict`` and ``self.staging_dict`` and
		populates them from the language folder's ``outcome_*.txt`` and
		``staging_*.txt`` files keyed by their suffixes.
		"""
		self.set_language(self.language)
		self.feedback_label = Label(font_size='32sp')
		self.feedback_label.size_hint = (0.8, 0.4)
		self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.55}
		outcome_feedback = ''

		feedback_lang_path = self.lang_folder_path / 'Feedback.ini'
		feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
		feedback_lang_config.read(feedback_lang_path, encoding='utf-8')

		self.feedback_dict['start_block'] = feedback_lang_config.get('Feedback', 'start_block', fallback='Press and hold the white button to start the first \ntrial, or press "End Task" to end the task.').replace('\\n', '\n')
		self.feedback_dict['mid_block'] = feedback_lang_config.get('Feedback', 'mid_block', fallback='Block complete!\n\nPress and hold the white button to start the next \ntrial, or press "End Task" to end the task.').replace('\\n', '\n')

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
		"""Resolve the language folder and load the tutorial video and instructions.

		Sets ``self.lang_folder_path`` from the protocol language folder. When a
		``Tutorial_Video`` folder exists a :class:`Classes.Protocol.PreloadedVideo`
		is created from the bundled MP4 and the tutorial continue button is bound to
		:meth:`stop_tutorial_video`. Positions the instruction label at
		``center_x``/``center_y`` 0.5/0.55.
		"""
		self.lang_folder_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language

		if (self.lang_folder_path / 'Tutorial_Video').is_dir():
			self.tutorial_video_path = self.lang_folder_path / 'Tutorial_Video' / 'PR-Tutorial_Video-2025-11-19.mp4'
			self.tutorial_video = PreloadedVideo(
				source_path = str(self.tutorial_video_path)
				, pos_hint={'center_x': 0.5, 'center_y': 0.55},
				size_hint=(0.95, 0.75),
				fit_mode = 'contain',
				loop=False
				)


		self.tutorial_continue_button.bind(on_press=self.stop_tutorial_video)

		
		# Define Instruction Components

		self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.55}

	# Initialization Functions #
		
	def load_parameters(self,parameter_dict):
		"""Set up the task state and begin the protocol with the given parameters.

		Runs the parameter, state, session-stage, image-widget, language and
		video/instruction setup steps, then starts the clock. When a
		``Tutorial_Video`` folder exists the layout is cleared and the tutorial screen
		is triggered; otherwise the instructions are presented and the start button is
		unbound from :meth:`start_protocol` and bound to
		:meth:`start_protocol_from_tutorial` so that the contingency runs.

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
		
		# Begin Task
		
		self.start_clock()
		if (self.lang_folder_path / 'Tutorial_Video').is_dir():

			self.protocol_floatlayout.clear_widgets()
			self.trigger_tutorial_screen()
		
		else:
			self.present_instructions()
			self.start_button.unbind(on_press=self.start_protocol)
			self.start_button.bind(on_press=self.start_protocol_from_tutorial)



	def generate_stimulus_pos(
		self
		, *args
		):
		"""Choose a random stimulus position at a fixed distance from the hold button.

		Draws an x position from ``self.x_boundaries`` (re-selecting up to 50 times
		while it stays within 0.1 of the current ``center_x``), derives the y
		position from the hold button center plus the vertical component of the fixed
		``main_move`` distance (``sqrt(main_move**2 - x_move**2)``, so every position
		lies at the same distance from the hold button), and
		re-draws until the y position falls inside ``self.y_boundaries``.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).

		Returns
		-------
		dict
			The stimulus ``pos_hint`` mapping with ``center_x`` and ``center_y`` keys.
		"""

		# This function requires task-level x and y boundary and main_move variables (can be adjusted to take all of these as arguments instead)
		# Stimulus Y position is always positive relative to hold button
		# Select X position from x boundaries, then derive Y postion from there
		# Every X position has only one Y location associated with it to equal Euclidean distance

		x_pos = random.uniform(min(self.x_boundaries), max(self.x_boundaries))

		# If difference between existing and new x position is less than 10% of screen width, select new location
		pos_attempts = 0
		while abs(x_pos - self.stimulus_pos['center_x']) < 0.1 and pos_attempts < 50:
			x_pos = random.uniform(min(self.x_boundaries), max(self.x_boundaries))
			pos_attempts += 1

		x_move = (self.hold_button.pos_hint['center_x'] - x_pos) / self.width_adjust

		y_move = float(np.sqrt(max(self.main_move**2 - x_move**2, 0)))
		y_pos = self.hold_button.pos_hint['center_y'] + y_move

		while (y_pos < min(self.y_boundaries)) \
			or (y_pos > max(self.y_boundaries)):

			x_pos = random.uniform(min(self.x_boundaries), max(self.x_boundaries))

			# If difference between existing and new x position is less than 10% of screen width, select new location
			pos_attempts = 0
			while abs(x_pos - self.stimulus_pos['center_x']) < 0.1 and pos_attempts < 50:
				x_pos = random.uniform(min(self.x_boundaries), max(self.x_boundaries))
				pos_attempts += 1

			x_move = (self.hold_button.pos_hint['center_x'] - x_pos) / self.width_adjust

			y_move = float(np.sqrt(max(self.main_move**2 - x_move**2, 0)))
			y_pos = self.hold_button.pos_hint['center_y'] + y_move
		
		stimulus_pos = {'center_x': x_pos, 'center_y': y_pos}

		return stimulus_pos
	
	
	def stop_tutorial_video(self, *args):
		"""Stop the tutorial video and begin the protocol.

		Returns early when the tutorial is already complete or the protocol has ended.
		Otherwise marks the tutorial complete, disables and unbinds the continue
		button, stops the video, queues a ``('Remove', 'Video', 'Section',
		'Instructions')`` object event and calls :meth:`start_protocol_from_tutorial`.

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

		Returns early when already started from the tutorial or the protocol has ended.
		Otherwise marks it started, clears the screen, logs the ``'Section Start'``
		stage event, generates the output and metadata files and calls
		:meth:`block_contingency`.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if self.protocol_started_from_tutorial or getattr(self, 'protocol_ended', False):
			return

		self.protocol_started_from_tutorial = True
		self.protocol_floatlayout.clear_widgets()

		self.protocol_floatlayout.add_stage_event('Section Start')
		self.generate_output_files()
		self.metadata_output_generation()

		self.block_contingency()


	def results_screen(self, *args):
			"""Display the final outcome screen once, guarding against repeats.

			Clears the widgets, marks the participant as stopped, and evaluates the
			``result`` entry of ``self.outcome_dict`` into ``self.outcome_string``.
			Re-binds the quit button to end the protocol and assigns the outcome
			string as feedback. Does nothing when ``self.results_active`` is already
			true or the protocol has ended.

			Parameters
			----------
			*args : tuple
				Ignored; supplied by Kivy event dispatch (e.g. the button instance).

			Notes
			-----
			Queues a ``('Display', 'Text', 'Stage', 'Results')`` object event.
			"""
			if self.results_active or getattr(self, 'protocol_ended', False):
				return

			self.results_active = True
			self.protocol_floatlayout.clear_widgets()
			self.participant_stopped = True
			self.feedback_on_screen = False

			self.outcome_string = eval(f'f"""{self.outcome_dict.get("result", "")}"""')
			
			self.quit_button.unbind(on_press=self.results_screen)
			self.quit_button.unbind(on_press=self.protocol_end)
			self.quit_button.bind(on_press=self.protocol_end)
			self.quit_button.pos_hint = {'center_x': 0.5, 'center_y': 0.07}
			self.quit_button.disabled = False

			self.assign_feedback(override_text=self.outcome_string)
			self.protocol_floatlayout.add_widget(self.quit_button)
			self.protocol_floatlayout.add_object_event('Display', 'Text', 'Stage', 'Results')


	def _arm_no_response_timer(self):
		"""End the task after ``timeout_duration`` seconds without a response.

		Cancels the pending ``self.no_response_event`` and schedules
		``self.protocol_end`` on ``self.task_clock`` after
		``self.timeout_duration`` seconds; re-armed at each wait point.
		"""
		# End the task after timeout_duration without a response; re-armed at each wait point
		self.no_response_event.cancel()
		self.no_response_event = self.task_clock.schedule_once(self.protocol_end, self.timeout_duration)

	def stimulus_presentation(self, *args): # Stimulus presentation
		"""Reset the trial and present the stimulus for the current trial.

		Clears response bookkeeping, unbinds and removes the hold button, records
		``self.stimulus_start_time = time.perf_counter()`` and logs a ``'State
		Change'`` stage event. On a confirmation trial (``current_block_trial`` even
		and ``use_confirmation``) the hold button is shown as the target; otherwise
		the stimulus button is added. Sets ``stimulus_on_screen`` and arms the
		no-response timer.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).

		Notes
		-----
		Queues a ``('Display', 'Stimulus', 'Target', ...)`` object event naming
		``'Hold Button'`` or the stimulus button ``pos_hint``.
		"""
		self.response_recorded = False
		self.awaiting_restart = False
		self.hold_button.unbind(on_press=self.iti_start)
		self.hold_button.unbind(on_press=self.target_pressed)
		self.hold_button.unbind(on_release=self.premature_response)

		self.protocol_floatlayout.remove_widget(self.hold_button)

		self.stimulus_start_time = time.perf_counter()
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

		self._arm_no_response_timer()
	
				
	
	def premature_response(self, *args): # Trial Outcomes: 0-Premature,1-Hit,2-Miss,3-False Alarm,4-Correct Rejection,5-Hit, no center touch,6-False Alarm, no center touch
		"""Handle a hold release before the stimulus appears.

		Guards on ``awaiting_restart`` or ``protocol_ended`` and returns early when
		the stimulus is on screen. Unschedules ``self.iti_end``, marks
		``awaiting_restart``, clears the widgets, sets ``self.response_latency =``
		``np.nan`` and logs ``'Premature Response'`` and the NaN response latency.
		Sets ``iti_active`` False and shows ``'wait'`` feedback when none is on
		screen, then rebinds the hold button to ``start_block`` and re-adds the hold
		and quit buttons.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if self.awaiting_restart or getattr(self, 'protocol_ended', False):
			return

		self.hold_button_pressed = False
		if self.stimulus_on_screen:
			return
		
		Clock.unschedule(self.iti_end)
		self.awaiting_restart = True
		
		self.protocol_floatlayout.clear_widgets()
		
		self.response_latency = np.nan

		self.protocol_floatlayout.add_stage_event('Premature Response')

		self.protocol_floatlayout.add_variable_event('Outcome', 'Response Latency', self.response_latency)
		
		self.iti_active = False

		if self.feedback_on_screen is False:	
			self.assign_feedback(feedback_key='wait')
		
		self.hold_button.unbind(on_press=self.iti_start)
		self.hold_button.unbind(on_press=self.start_block)
		self.hold_button.unbind(on_release=self.premature_response)
		self.hold_button.bind(on_press=self.start_block)

		self.protocol_floatlayout.add_widget(self.hold_button)
		self.protocol_floatlayout.add_widget(self.quit_button)
	
	
	
	# Target Pressed
	
	def target_pressed(self, *args):
		"""Record a hit response to the presented stimulus.

		Guards when a response was already recorded, no stimulus is on screen or the
		protocol has ended. Sets ``response_recorded``, unschedules the
		no-response timer, records ``stimulus_press_time = time.perf_counter()`` and
		the ``response_latency`` as press minus stimulus start, and logs
		``'Target Pressed'`` and the response latency. On confirmation trials it removes
		the hold button (acting as the target) and the pressed-stimulus image; on other
		trials it removes the stimulus button and adds the pressed-stimulus image. Then
		increments ``total_hit_count`` and logs block and total hit
		counts. Sets ``stimulus_on_screen`` False and calls :meth:`write_trial` and
		:meth:`trial_contingency`.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if self.response_recorded or (not self.stimulus_on_screen) or getattr(self, 'protocol_ended', False):
			return

		self.response_recorded = True
	
		Clock.unschedule(self.no_response_event)

		self.stimulus_press_time = time.perf_counter()
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
			self.protocol_floatlayout.remove_widget(self.stimulus_button_pressed)
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
		"""Write the current trial's summary row to the summary data file.

		Notes
		-----
		Builds a row of ``current_trial`` (the 1-based, block-unique trial number),
		``current_block``, ``current_block_trial``, ``total_hit_count``,
		``response_level``, the target button ``pos_hint`` x and y, and
		``response_latency``, then passes it to :meth:`write_summary_file`. On a
		confirmation trial (``current_block_trial`` even and ``use_confirmation``) the
		target is the hold button, otherwise the stimulus button.
		"""

		target = self.hold_button if (self.current_block_trial % 2) != 1 \
			and self.use_confirmation else self.stimulus_button

		trial_data = [
			self.current_trial
			, self.current_block
			, self.current_block_trial
			, self.total_hit_count
			, self.response_level
			, target.pos_hint['center_x']
			, target.pos_hint['center_y']
			, self.response_latency
			]
		
		self.write_summary_file(trial_data)
	
	
	
	# Trial Contingency Functions
	
	def trial_contingency(self):
		"""Advance the block or trial and start the next presentation.

		Increments ``current_trial`` at the start of every trial, giving a 1-based
		number that stays unique across blocks (the block-ending trial advances it
		too). When ``current_block_trial`` reaches ``self.hit_target`` the block
		ends: unschedules ``iti_end``, increments ``current_block`` and
		``response_level``, sets ``hit_target = 2 ** response_level`` and
		``block_end_time``, logs ``'Block End'`` with the response level and hit
		target, and calls :meth:`block_contingency`. Otherwise, increments
		``current_block_trial`` and logs both ``current_trial`` and
		``current_block_trial``; on confirmation trials no stimulus position is
		chosen, else a position is generated via :meth:`generate_stimulus_pos`,
		applied to both stimulus buttons and logged as ``'Target Location'``.
		Finally calls :meth:`stimulus_presentation`.

		Notes
		-----
		Any ``KeyboardInterrupt`` or other exception is caught and ends the
		protocol through :meth:`protocol_end` (the error is printed with a traceback).
		"""
		
		try:

			self.current_trial += 1

			if self.current_block_trial >= self.hit_target:
				Clock.unschedule(self.iti_end)

				self.current_block += 1
				self.response_level += 1

				self.hit_target = 2 ** self.response_level

				self.block_end_time = time.perf_counter()

				self.protocol_floatlayout.add_stage_event('Block End')

				self.protocol_floatlayout.add_variable_event('Parameter', 'Response Level', self.response_level)
				self.protocol_floatlayout.add_variable_event('Parameter', 'Hit Target', self.hit_target)
				
				self.block_contingency()
				return
			

			else:
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
		
		except Exception as e:
			print(f"Critical Error encountered: {e}")
			traceback.print_exc() 
			self.protocol_end()
	


	def block_screen_display_hold_button(self, *args):
		"""Add the hold button back when a block rest ends, unless the participant stopped.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance or dt).
		"""
		if not self.participant_stopped:
			self.protocol_floatlayout.add_widget(self.hold_button)
		else:
			return


	# Block start function (add widgets and set block start time)

	def start_block(self, *args):
		"""Begin a new block, resetting flag state and re-binding the hold button.

		Returns early while a block is already starting, the ITI is active, a
		stimulus is on screen or the protocol has ended. Otherwise sets
		``block_start_active`` True, ``hold_button_pressed`` True and
		``awaiting_restart`` False, removes the feedback label (and the reward image
		when not block 1) and logs the ``'Results'`` text removal. Records
		``block_start_time = time.perf_counter()``, rebinds the hold button so
		``iti_start`` runs on press and ``premature_response`` on release, then calls
		:meth:`iti_start` straight away (``hold_button_pressed`` was just set True)
		and clears ``block_start_active``.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance).
		"""
		if self.block_start_active or self.iti_active or self.stimulus_on_screen or getattr(self, 'protocol_ended', False):
			return

		self.block_start_active = True
		self.hold_button_pressed = True
		self.awaiting_restart = False
		self.protocol_floatlayout.remove_widget(self.feedback_label)
		outcome_feedback = ''
		
		self.protocol_floatlayout.add_object_event('Remove', 'Text', 'Stage', 'Results')

		if self.current_block != 1:
			self.protocol_floatlayout.remove_widget(self.reward_image)

		self.block_start_time = time.perf_counter()

		self.hold_button.unbind(on_press=self.start_block)
		self.hold_button.unbind(on_press=self.iti_start)
		self.hold_button.bind(on_press=self.iti_start)

		self.hold_button.bind(on_release=self.premature_response)

		if self.hold_button_pressed:
			self.iti_start()

		self.block_start_active = False


	# Block Contingency Function
	
	def block_contingency(self, *args):
		"""Complete a block and prepare the next block's hold and stimulus stage.

		Resets the block flow flags (``block_start_active``, ``awaiting_restart``,
		``response_recorded``), unbinds the hold-button handlers (``iti_start``,
		``start_block``, ``premature_response``), unschedules and runs feedback
		removal, clears the widgets, and promotes ``current_block`` from -1 to 1.
		When ``response_level > response_level_end`` the session event is cancelled,
		:meth:`results_screen` is called and the method returns early. Otherwise the
		no-response timer is re-armed; block 1 shows the quit button and
		``'start_block'`` feedback, while later blocks show ``'mid_block'`` feedback
		and the reward image, each logging a ``'Start'`` text-display event. A new
		ITI is drawn from ``iti_range`` when it holds more than one value
		(``random.choice`` for a ``'fixed'`` range, else a rounded ``random.uniform``
		of the range) and logged as ``'Current ITI'``. A stimulus position is
		generated, applied to both stimulus buttons and logged as ``'Target
		Location'``, ``current_block_trial`` is reset to 1, and
		:meth:`block_screen_display_hold_button` is scheduled after
		``self.block_min_rest_duration`` seconds on the Kivy Clock.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (e.g. the button instance or dt).

		Notes
		-----
		The ITI is only redrawn when ``iti_range`` has more than one value. Any
		``KeyboardInterrupt`` or other exception is caught and ends the protocol
		through :meth:`protocol_end` (the error is printed with a traceback).
		"""
		
		try:			
			self.block_start_active = False
			self.awaiting_restart = False
			self.response_recorded = False
			self.hold_button.unbind(on_press=self.iti_start)
			self.hold_button.unbind(on_press=self.start_block)
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

				self._arm_no_response_timer()

				if self.current_block == 1:
					self.hold_button.bind(on_press=self.start_block)
					
					self.protocol_floatlayout.add_widget(self.quit_button)
					self.assign_feedback(feedback_key='start_block')

					self.protocol_floatlayout.add_object_event('Display', 'Text', 'Stage', 'Start')
					
				else:
					self.assign_feedback(feedback_key='mid_block')

					self.hold_button.bind(on_press=self.start_block)
					
					self.protocol_floatlayout.add_widget(self.reward_image)
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
		
		except Exception as e:
			print(f"Critical Error encountered: {e}")
			traceback.print_exc() 
			self.protocol_end()