# Imports #

import configparser
import json
import math
import pathlib
import random
import time
import traceback

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.behaviors import DragBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget

from Classes.Protocol import ProtocolBase, PreloadedVideo
from Protocol.SST.Task.scoring import score_response




class WordTile(DragBehavior, Label):

	def __init__(self, text, builder, font_size, size, **kw):
		super(WordTile, self).__init__(
			text=text,
			font_size=font_size,
			size_hint=(None, None),
			size=size,
			halign='center',
			valign='middle',
			**kw
		)
		self.builder = builder
		self.home = (0, 0)
		self.slot = None
		self.drag_timeout = 10000000
		self.drag_distance = 5
		self.drag_rectangle = (self.x, self.y, self.width, self.height)
		self.text_size = self.size

		# ponytail: simple canvas instructions bound to pos/size for background and border
		with self.canvas.before:
			Color(0.18, 0.18, 0.18, 1)
			self._bg = Rectangle(pos=self.pos, size=self.size)
			Color(1, 1, 1, 1)
			self._border = Line(rectangle=(self.x, self.y, self.width, self.height), width=1.5)

		self.bind(pos=self._update_bounds, size=self._update_bounds)

	def _update_bounds(self, *args):
		self._bg.pos = self.pos
		self._bg.size = self.size
		self._border.rectangle = (self.x, self.y, self.width, self.height)
		self.drag_rectangle = (self.x, self.y, self.width, self.height)
		self.text_size = self.size

	def on_touch_down(self, touch):
		if self.disabled:
			return False
		result = super(WordTile, self).on_touch_down(touch)
		if result:
			self.builder.tile_picked(self)
		return result

	def on_touch_up(self, touch):
		dragged = getattr(self, '_drag_touch', None) is touch
		result = super(WordTile, self).on_touch_up(touch)
		if dragged:
			self.builder.tile_dropped(self)
		return result




class SentenceBuilder(Widget):

	def __init__(self, words, font_size, area, width_adjust, height_adjust, on_first_touch=None, on_change=None, slot_count=5, **kw):
		super(SentenceBuilder, self).__init__(size_hint=(None, None), size=area, pos=(0, 0), **kw)
		self.words = list(words)
		self.area = area
		self.width_adjust = width_adjust
		self.height_adjust = height_adjust
		self.on_first_touch = on_first_touch
		self.on_change = on_change
		self.slot_count = slot_count
		self.slots = [None] * slot_count

		w, h = area
		slot_w = 0.16 * w
		slot_h = 0.1 * h * height_adjust
		gap = 0.2 * slot_w

		total_slots_w = slot_count * slot_w + (slot_count - 1) * gap
		slot_start_x = (w - total_slots_w) / 2.0
		slot_y = 0.45 * h - slot_h / 2.0

		self.slot_rects = []
		for i in range(slot_count):
			sx = slot_start_x + i * (slot_w + gap)
			self.slot_rects.append((sx, slot_y, slot_w, slot_h))

		with self.canvas:
			Color(0.5, 0.5, 0.5, 1)
			for rect in self.slot_rects:
				Line(rectangle=rect, width=1.5)

		self.tiles = []
		# ponytail: tray layout places up to 6 tiles in 2 rows of 3 centered horizontally
		for idx, word in enumerate(self.words):
			row = idx // 3
			col = idx % 3
			row_center_y = 0.84 * h if row == 0 else 0.71 * h
			tx = (w - slot_w) / 2.0 + (col - 1) * 1.2 * slot_w
			ty = row_center_y - slot_h / 2.0

			tile = WordTile(
				text=word,
				builder=self,
				font_size=font_size,
				size=(slot_w, slot_h),
				pos=(tx, ty)
			)
			tile.home = (tx, ty)
			self.tiles.append(tile)
			self.add_widget(tile)

	@property
	def complete(self):
		return all(s is not None for s in self.slots)

	def placed_words(self):
		return [s.text for s in self.slots if s is not None]

	def tile_picked(self, tile):
		if tile.slot is not None:
			self.slots[tile.slot] = None
			tile.slot = None
			if self.on_change:
				self.on_change()
		self.remove_widget(tile)
		self.add_widget(tile)
		if self.on_first_touch:
			self.on_first_touch()

	def tile_dropped(self, tile):
		# ponytail: free previous slot in case tile_dropped was called directly without tile_picked
		if tile.slot is not None:
			self.slots[tile.slot] = None
			tile.slot = None

		tx = tile.x + tile.width / 2.0
		ty = tile.y + tile.height / 2.0
		slot_w = self.slot_rects[0][2]
		best_idx = None
		best_dist = float('inf')

		for i, (sx, sy, sw, sh) in enumerate(self.slot_rects):
			if self.slots[i] is None:
				scx = sx + sw / 2.0
				scy = sy + sh / 2.0
				dist = math.hypot(tx - scx, ty - scy)
				if dist < best_dist:
					best_dist = dist
					best_idx = i

		if best_idx is not None and best_dist <= slot_w:
			sx, sy, _, _ = self.slot_rects[best_idx]
			tile.pos = (sx, sy)
			self.slots[best_idx] = tile
			tile.slot = best_idx
		else:
			tile.pos = tile.home
			tile.slot = None

		if self.on_change:
			self.on_change()

	def lock(self):
		for tile in self.tiles:
			tile.disabled = True




class DigitRecall(Widget):

	def __init__(self, digit_count, area, width_adjust, height_adjust, font_size='48sp', on_change=None, **kw):
		super(DigitRecall, self).__init__(size_hint=(None, None), size=area, pos=(0, 0), **kw)
		self.digit_count = digit_count
		self.area = area
		self.width_adjust = width_adjust
		self.height_adjust = height_adjust
		self.on_change = on_change
		self.boxes = []

		w, h = area
		box_w = min(0.1 * w, 0.8 * w / digit_count)
		gap = 0.15 * box_w
		box_h = min(0.15 * h * height_adjust, box_w * 1.3)

		total_w = digit_count * box_w + (digit_count - 1) * gap
		start_x = (w - total_w) / 2.0
		box_y = 0.5 * h - box_h / 2.0

		# ponytail: Spinner dropdown used for touch entry; no custom numpad.
		for i in range(digit_count):
			bx = start_x + i * (box_w + gap)
			box = Spinner(
				text='',
				values=[str(d) for d in range(10)],
				background_normal='',
				background_color=(0.15, 0.15, 0.15, 1),
				font_size=font_size,
				size_hint=(None, None),
				size=(box_w, box_h),
				pos=(bx, box_y)
			)
			with box.canvas.after:
				Color(1, 1, 1, 1)
				box._border = Line(rectangle=(box.x, box.y, box.width, box.height), width=1.5)

			box.bind(
				pos=lambda inst, val: setattr(inst._border, 'rectangle', (inst.x, inst.y, inst.width, inst.height)),
				size=lambda inst, val: setattr(inst._border, 'rectangle', (inst.x, inst.y, inst.width, inst.height)),
				text=self._on_spinner_text
			)
			self.boxes.append(box)
			self.add_widget(box)

		Window.bind(on_key_down=self._on_key_down)
		self._window_bound = True

	def _on_spinner_text(self, instance, value):
		if self.on_change:
			self.on_change()

	@property
	def complete(self):
		return all(bool(box.text) for box in self.boxes)

	def value(self):
		return ''.join(box.text for box in self.boxes)

	def _on_key_down(self, window, key, scancode, codepoint, modifier):
		if codepoint and len(codepoint) == 1 and codepoint in '0123456789':
			for box in self.boxes:
				if not box.text:
					box.text = codepoint
					return True
			return None
		elif key == 8 or codepoint in ('\x08', '\b'):
			for box in reversed(self.boxes):
				if box.text:
					box.text = ''
					return True
			return None
		return None

	def close(self):
		if getattr(self, '_window_bound', False):
			Window.unbind(on_key_down=self._on_key_down)
			self._window_bound = False




class ProtocolScreen(ProtocolBase):

	def __init__(self, **kwargs):
		super(ProtocolScreen, self).__init__(**kwargs)
		self.protocol_name = 'SST'
		self.name = self.protocol_name + '_protocolscreen'
		self.update_task()

		# Define Data Columns
		self.data_cols = [
			'TrialNo',
			'Phase',
			'SentenceID',
			'SentenceType',
			'WordsPresented',
			'Response',
			'ResponseValence',
			'TimedOut',
			'Warned',
			'FirstTouchLatency',
			'ConstructionLatency',
			'DigitTarget',
			'DigitResponse',
			'DigitsCorrect',
			'DigitAllCorrect',
			'RecallLatency'
		]

		self.metadata_cols = [
			'participant_id',
			'skip_tutorial_video',
			'tutorial_video_filename',
			'training_trials',
			'probe_trials',
			'digit_count',
			'digit_display_duration',
			'sentence_time_limit',
			'iti_length',
			'feedback_length',
			'training_digit_feedback',
			'probe_digit_feedback',
			'max_consecutive_type',
			'word_font_size',
			'session_duration'
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
		self.parameters_dict = parameters_dict
		self.participant_id = self.parameters_dict.get('participant_id', 'Default')
		if 'participant_id' not in self.parameters_dict:
			try:
				self.parameters_dict['participant_id'] = str(self.participant_id)
			except Exception:
				pass

		self.skip_tutorial_video = self._safe_get_bool('skip_tutorial_video', True)
		self.tutorial_video_filename = self.parameters_dict.get('tutorial_video_filename', 'SST-Tutorial_Video.mp4')
		self.training_trials = int(self.parameters_dict.get('training_trials', 5))
		self.probe_trials = int(self.parameters_dict.get('probe_trials', 0))
		self.digit_count = int(self.parameters_dict.get('digit_count', 6))
		self.digit_display_duration = float(self.parameters_dict.get('digit_display_duration', 5.0))
		self.sentence_time_limit = float(self.parameters_dict.get('sentence_time_limit', 10.0))
		self.iti_length = float(self.parameters_dict.get('iti_length', 3.0))
		self.feedback_length = float(self.parameters_dict.get('feedback_length', 1.5))
		self.training_digit_feedback = self._safe_get_bool('training_digit_feedback', True)
		self.probe_digit_feedback = self._safe_get_bool('probe_digit_feedback', True)
		self.max_consecutive_type = int(self.parameters_dict.get('max_consecutive_type', 3))
		self.word_font_size = self.parameters_dict.get('word_font_size', '32sp')
		self.session_duration = float(self.parameters_dict.get('session_duration', 3600.0))
		self.session_event = self.session_clock.create_trigger(self.clock_monitor, self.session_duration, interval=False)

		# Ensure all metadata_cols keys exist in parameters_dict for metadata_output_generation
		for key in self.metadata_cols:
			if key not in self.parameters_dict and hasattr(self, key):
				try:
					self.parameters_dict[key] = str(getattr(self, key))
				except Exception:
					pass

	def _load_task_variables(self):
		self.digit_event = None
		self.sentence_event = None
		self.feedback_event = None
		self.iti_event = None

		self.digit_widget = None
		self.builder = None

		self.current_phase = ''
		self.trials = []
		self.trial_index = -1
		self.current_trial = 0
		self.current_item = None

		self.sentence_submitted = False
		self.digits_submitted = False
		self.trial_closed = False
		self.warned = False
		self.timed_out = False

		self.first_touch_time = None
		self.sentence_start_time = 0.0
		self.recall_start_time = 0.0

		self.placed = ''
		self.valence = ''
		self.digit_target = ''
		self.digit_response = ''
		self.digits_correct = math.nan
		self.digit_all_correct = math.nan
		self.first_touch_latency = math.nan
		self.construction_latency = math.nan
		self.recall_latency = math.nan

		self.tutorial_completed = False
		self.protocol_started_from_tutorial = False
		self.phase_continue_pressed = False

	def _setup_session_stages(self):
		# ponytail: simple timer slots; no block/rest timers or hold buttons
		self.digit_event = None
		self.sentence_event = None
		self.feedback_event = None
		self.iti_event = None

	def _setup_widgets(self):
		self.sentence_submit_button = Button(
			font_size='24sp',
			size_hint=(0.2, 0.1),
			pos_hint={'center_x': 0.5, 'center_y': 0.1},
			disabled=True
		)
		self.sentence_submit_button.bind(on_press=self.submit_sentence)

		self.digit_submit_button = Button(
			font_size='24sp',
			size_hint=(0.2, 0.1),
			pos_hint={'center_x': 0.5, 'center_y': 0.1},
			disabled=True
		)
		self.digit_submit_button.bind(on_press=self.submit_digits)

		self.digit_prompt_label = Label(
			font_size='28sp',
			size_hint=(0.8, 0.1),
			pos_hint={'center_x': 0.5, 'center_y': 0.7}
		)
		self.digit_display_label = Label(
			font_size='96sp',
			size_hint=(0.8, 0.2),
			pos_hint={'center_x': 0.5, 'center_y': 0.5}
		)

		self.unscramble_prompt_label = Label(
			font_size='24sp',
			size_hint=(0.9, 0.08),
			pos_hint={'center_x': 0.5, 'center_y': 0.95}
		)

		self.recall_prompt_label = Label(
			font_size='28sp',
			size_hint=(0.8, 0.1),
			pos_hint={'center_x': 0.5, 'center_y': 0.7}
		)

		self.warning_label = Label(
			font_size='28sp',
			markup=True,
			size_hint=(0.8, 0.1),
			pos_hint={'center_x': 0.5, 'center_y': 0.27}
		)

		self.stage_label = Label(
			font_size='36sp',
			size_hint=(0.8, 0.4),
			pos_hint={'center_x': 0.5, 'center_y': 0.55}
		)
		self.stage_continue_button = Button(
			font_size='24sp',
			size_hint=(0.4, 0.15),
			pos_hint={'center_x': 0.5, 'center_y': 0.1}
		)
		self.stage_continue_button.bind(on_press=self._on_stage_continue)

	def _setup_language_localization(self):
		self.set_language(self.language)

		feedback_lang_path = self.lang_folder_path / 'Feedback.ini'
		feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
		feedback_lang_config.read(feedback_lang_path, encoding='utf-8')

		defaults = {
			'digit_correct': 'Correct',
			'digit_incorrect': 'Incorrect',
			'too_slow_warning': 'Please try to finish the sentence faster'
		}
		for key, fallback in defaults.items():
			val = feedback_lang_config.get('Feedback', key, fallback=fallback)
			colour = feedback_lang_config.get('Feedback', key + '_colour', fallback='').strip()
			if colour:
				val = f'[color={colour}]{val}[/color]'
			self.feedback_dict[key] = val

		self.warning_label.text = self.feedback_dict['too_slow_warning']

		button_lang_path = self.lang_folder_path / 'Button.ini'
		button_lang_config = configparser.ConfigParser()
		button_lang_config.read(button_lang_path, encoding='utf-8')

		submit_text = button_lang_config.get('Button', 'submit', fallback='Submit')
		self.sentence_submit_button.text = submit_text
		self.digit_submit_button.text = submit_text

		stage_continue_text = button_lang_config.get('Button', 'stage_continue', fallback='Continue')
		self.stage_continue_button.text = stage_continue_text

		prompts_path = self.lang_folder_path / 'prompts.ini'
		prompts_config = configparser.ConfigParser()
		prompts_config.read(prompts_path, encoding='utf-8')

		self.prompt_remember_number = prompts_config.get('Prompts', 'remember_number', fallback='Remember this number')
		self.prompt_enter_number = prompts_config.get('Prompts', 'enter_number', fallback='Enter the number')
		self.prompt_unscramble = prompts_config.get('Prompts', 'unscramble', fallback='Unscramble the sentence using 5 of the 6 words')

		self.digit_prompt_label.text = self.prompt_remember_number
		self.recall_prompt_label.text = self.prompt_enter_number
		self.unscramble_prompt_label.text = self.prompt_unscramble

		self.staging_dict = {}
		for file_path in self.lang_folder_path.glob('staging_*.txt'):
			key = file_path.stem.replace('staging_', '')
			with open(file_path, 'r', encoding='utf-8') as f:
				self.staging_dict[key] = f.read()

		sentences_path = self.lang_folder_path / 'sentences.json'
		with open(sentences_path, 'r', encoding='utf-8') as f:
			self.sentences = json.load(f)

	def _load_video_and_instruction_components(self):
		self.lang_folder_path = self.app.app_root / 'Protocol' / self.protocol_name / 'Language' / self.language
		self.tutorial_video_path = self.lang_folder_path / 'Tutorial_Video' / self.tutorial_video_filename
		self.use_tutorial = (not self.skip_tutorial_video) and self.tutorial_video_path.is_file()

		if self.use_tutorial:
			self.tutorial_video = PreloadedVideo(
				source_path=str(self.tutorial_video_path),
				pos_hint={'center_x': 0.5, 'center_y': 0.55},
				size_hint=(0.95, 0.75),
				fit_mode='contain',
				loop=False
			)
			self.tutorial_continue_button.bind(on_press=self.stop_tutorial_video)

		self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.55}

	def load_parameters(self, parameter_dict):
		self._load_config_parameters(parameter_dict)
		self._load_task_variables()
		self._setup_session_stages()
		self._setup_widgets()
		self._setup_language_localization()
		self._load_video_and_instruction_components()

		# Begin Task
		self.start_clock()
		if self.use_tutorial:
			self.protocol_floatlayout.clear_widgets()
			self.trigger_tutorial_screen()
		else:
			try:
				self.start_button.unbind(on_press=self.start_protocol)
			except Exception:
				pass
			self.start_button.bind(on_press=self.start_task)
			self.present_instructions()

	def stop_tutorial_video(self, *args):
		try:
			if self.tutorial_completed or getattr(self, 'protocol_ended', False):
				return

			self.tutorial_completed = True
			self.tutorial_continue_button.disabled = True
			try:
				self.tutorial_continue_button.unbind(on_press=self.stop_tutorial_video)
			except Exception:
				pass
			if hasattr(self, 'tutorial_video') and self.tutorial_video:
				self.tutorial_video.state = 'stop'
			self.protocol_floatlayout.add_object_event('Remove', 'Video', 'Section', 'Instructions')
			self.start_protocol_from_tutorial()
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def start_protocol_from_tutorial(self, *args):
		try:
			if self.protocol_started_from_tutorial or getattr(self, 'protocol_ended', False):
				return

			self.protocol_started_from_tutorial = True
			self.protocol_floatlayout.clear_widgets()

			self.protocol_floatlayout.add_stage_event('Section Start')
			self.generate_output_files()
			self.metadata_output_generation()

			self.begin_phase('training')
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def start_task(self, *args):
		try:
			self.protocol_floatlayout.remove_widget(self.instruction_label)
			self.protocol_floatlayout.add_text_event('Removed', 'Task Instruction')
			self.protocol_floatlayout.remove_widget(self.start_button)
			self.protocol_floatlayout.add_button_event('Removed', 'Task Start Button')
			self.begin_phase('training')
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def begin_phase(self, phase):
		try:
			self.protocol_floatlayout.block_on_move_touch_down = True
			self.current_phase = phase

			if phase == 'training':
				items = list(self.sentences.get('training', []))
				if self.training_trials > 0:
					self.trials = items[:self.training_trials]
				else:
					self.trials = items
			elif phase == 'probe':
				pool = list(self.sentences.get('probe', []))
				if 0 < self.probe_trials < len(pool):
					pool = random.sample(pool, self.probe_trials)
				else:
					pool = list(pool)

				types = [it['type'] for it in pool]
				try:
					order = self.constrained_shuffle(types, max_run=self.max_consecutive_type)
				except ValueError:
					# ponytail: fallback to unconstrained random shuffle if constrained shuffle fails
					order = list(types)
					random.shuffle(order)

				by_type = {}
				for it in pool:
					by_type.setdefault(it['type'], []).append(it)
				for t in by_type:
					random.shuffle(by_type[t])

				self.trials = [by_type[t].pop() for t in order]

			self.trial_index = -1
			self.protocol_floatlayout.add_stage_event('Training Start' if phase == 'training' else 'Probe Start')
			self.next_trial()
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def next_trial(self):
		try:
			if getattr(self, 'protocol_ended', False):
				return

			self.trial_index += 1
			if self.trial_index >= len(self.trials):
				self.end_phase()
				return

			self.current_trial += 1
			self.current_item = self.trials[self.trial_index]
			self.digit_target = ''.join(random.choices('0123456789', k=self.digit_count))

			self.sentence_submitted = False
			self.digits_submitted = False
			self.trial_closed = False
			self.warned = False
			self.timed_out = False

			self.first_touch_time = None
			self.sentence_start_time = 0.0
			self.recall_start_time = 0.0

			self.placed = ''
			self.valence = ''
			self.digit_response = ''
			self.digits_correct = math.nan
			self.digit_all_correct = math.nan
			self.first_touch_latency = math.nan
			self.construction_latency = math.nan
			self.recall_latency = math.nan

			self.show_digits()
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def show_digits(self):
		try:
			self.protocol_floatlayout.clear_widgets()

			self.digit_prompt_label.text = self.prompt_remember_number
			self.digit_display_label.text = self.digit_target

			self.protocol_floatlayout.add_widget(self.digit_prompt_label)
			self.protocol_floatlayout.add_widget(self.digit_display_label)

			self.protocol_floatlayout.add_stage_event('Digit Display')
			self.protocol_floatlayout.add_variable_event('Parameter', 'Digit Target', self.digit_target)

			self.digit_event = Clock.schedule_once(self.start_sentence, self.digit_display_duration)
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def start_sentence(self, *args):
		try:
			if getattr(self, 'protocol_ended', False) or self.trial_closed:
				return

			if self.digit_event is not None:
				self.digit_event.cancel()
				self.digit_event = None

			self.protocol_floatlayout.clear_widgets()

			self.unscramble_prompt_label.text = self.prompt_unscramble
			self.protocol_floatlayout.add_widget(self.unscramble_prompt_label)

			area = tuple(self.protocol_floatlayout.size) if self.protocol_floatlayout.size[0] > 0 else self.screen_resolution
			self.builder = SentenceBuilder(
				words=self.current_item['words'],
				font_size=self.word_font_size,
				area=area,
				width_adjust=self.width_adjust,
				height_adjust=self.height_adjust,
				on_first_touch=self._note_first_touch,
				on_change=self._update_submit
			)
			self.protocol_floatlayout.add_widget(self.builder)

			self.sentence_submit_button.disabled = not self.builder.complete
			self.protocol_floatlayout.add_widget(self.sentence_submit_button)

			self.sentence_start_time = time.perf_counter()
			self.protocol_floatlayout.add_stage_event('Sentence Display')
			self.sentence_event = Clock.schedule_once(self.sentence_time_up, self.sentence_time_limit)
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def _note_first_touch(self):
		if self.first_touch_time is None:
			self.first_touch_time = time.perf_counter()

	def _update_submit(self):
		if self.builder is not None:
			self.sentence_submit_button.disabled = not self.builder.complete

	def sentence_time_up(self, *args):
		try:
			self.sentence_event = None
			if self.sentence_submitted or self.trial_closed or getattr(self, 'protocol_ended', False):
				return

			if self.current_phase == 'training':
				if not self.warned:
					self.warned = True
					self.warning_label.text = self.feedback_dict.get('too_slow_warning', '')
					if self.warning_label not in self.protocol_floatlayout.children:
						self.protocol_floatlayout.add_widget(self.warning_label)
					self.protocol_floatlayout.add_stage_event('Too Slow Warning')
					# the trial CONTINUES until Submit (no further timer)
			else:
				self.timed_out = True
				self.trial_closed = True
				if self.builder is not None:
					self.placed = ' '.join(self.builder.placed_words())
					self.builder.lock()
				else:
					self.placed = ''
				self.valence = 'timeout'
				if self.first_touch_time is not None:
					self.first_touch_latency = self.first_touch_time - self.sentence_start_time
				self.protocol_floatlayout.add_stage_event('Sentence Timeout')
				self.write_trial()
				self.trial_iti_start()
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def submit_sentence(self, *args):
		try:
			if self.sentence_submitted or self.trial_closed or getattr(self, 'protocol_ended', False):
				return
			if self.builder is None or not self.builder.complete:
				return

			self.sentence_submitted = True
			if self.sentence_event is not None:
				self.sentence_event.cancel()
				self.sentence_event = None

			submit_time = time.perf_counter()
			words = self.builder.placed_words()
			self.placed = ' '.join(words)
			self.valence = score_response(words, self.current_item['solutions'])
			self.construction_latency = submit_time - self.sentence_start_time
			self.first_touch_latency = (self.first_touch_time - self.sentence_start_time) if self.first_touch_time is not None else math.nan

			# log with add_variable_event (logs only; NEVER show any sentence/valence feedback to the participant anywhere)
			self.protocol_floatlayout.add_variable_event('Response', 'Sentence Response', self.placed)
			self.protocol_floatlayout.add_variable_event('Response', 'Response Valence', self.valence)
			self.protocol_floatlayout.add_variable_event('Latency', 'Construction Latency', self.construction_latency)
			if not math.isnan(self.first_touch_latency):
				self.protocol_floatlayout.add_variable_event('Latency', 'First Touch Latency', self.first_touch_latency)

			self.builder.lock()
			self.show_recall()
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def show_recall(self):
		try:
			self.protocol_floatlayout.clear_widgets()

			self.recall_prompt_label.text = self.prompt_enter_number
			self.protocol_floatlayout.add_widget(self.recall_prompt_label)

			area = tuple(self.protocol_floatlayout.size) if self.protocol_floatlayout.size[0] > 0 else self.screen_resolution
			self.digit_widget = DigitRecall(
				digit_count=self.digit_count,
				area=area,
				width_adjust=self.width_adjust,
				height_adjust=self.height_adjust,
				on_change=self._update_digit_submit
			)
			self.protocol_floatlayout.add_widget(self.digit_widget)

			self.digit_submit_button.disabled = not self.digit_widget.complete
			self.protocol_floatlayout.add_widget(self.digit_submit_button)

			self.recall_start_time = time.perf_counter()
			self.protocol_floatlayout.add_stage_event('Digit Recall')
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def _update_digit_submit(self):
		if self.digit_widget is not None:
			self.digit_submit_button.disabled = not self.digit_widget.complete

	def submit_digits(self, *args):
		try:
			if self.digits_submitted or self.trial_closed or getattr(self, 'protocol_ended', False):
				return
			if self.digit_widget is None or not self.digit_widget.complete:
				return

			self.digits_submitted = True
			submit_time = time.perf_counter()
			self.recall_latency = submit_time - self.recall_start_time
			self.digit_response = self.digit_widget.value()
			self.digit_widget.close()

			self.digits_correct = sum(a == b for a, b in zip(self.digit_target, self.digit_response))
			self.digit_all_correct = (self.digits_correct == len(self.digit_target))
			self.trial_closed = True

			self.protocol_floatlayout.add_variable_event('Response', 'Digit Response', self.digit_response)
			self.protocol_floatlayout.add_variable_event('Score', 'Digits Correct', self.digits_correct)
			self.protocol_floatlayout.add_variable_event('Score', 'Digit All Correct', self.digit_all_correct)
			self.protocol_floatlayout.add_variable_event('Latency', 'Recall Latency', self.recall_latency)

			self.write_trial()

			feedback_enabled = (self.training_digit_feedback if self.current_phase == 'training' else self.probe_digit_feedback)
			if feedback_enabled:
				self.protocol_floatlayout.clear_widgets()
				self.assign_feedback('digit_correct' if self.digit_all_correct else 'digit_incorrect')
				self.feedback_event = Clock.schedule_once(self.trial_iti_start, self.feedback_length)
			else:
				self.trial_iti_start()
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def trial_iti_start(self, *args):
		try:
			if getattr(self, 'protocol_ended', False):
				return

			if self.feedback_event is not None:
				self.feedback_event.cancel()
				self.feedback_event = None
			Clock.unschedule(self.remove_feedback)
			self.remove_feedback()

			self.protocol_floatlayout.clear_widgets()
			self.protocol_floatlayout.add_stage_event('ITI Start')
			self.iti_event = Clock.schedule_once(self.trial_iti_end, self.iti_length)
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def trial_iti_end(self, *args):
		try:
			if getattr(self, 'protocol_ended', False):
				return

			if self.iti_event is not None:
				self.iti_event.cancel()
				self.iti_event = None

			self.protocol_floatlayout.add_stage_event('ITI End')
			self.next_trial()
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def end_phase(self):
		try:
			self._cancel_events()
			if self.current_phase == 'training':
				self.protocol_floatlayout.clear_widgets()
				self.phase_continue_pressed = False
				self.stage_label.text = self.staging_dict.get('probe', '')
				self.protocol_floatlayout.add_widget(self.stage_label)
				self.stage_continue_button.disabled = False
				self.protocol_floatlayout.add_widget(self.stage_continue_button)
				self.protocol_floatlayout.add_stage_event('Training End')
			else:
				self.protocol_floatlayout.add_stage_event('Probe End')
				self.protocol_end()
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def _on_stage_continue(self, *args):
		try:
			if self.phase_continue_pressed or getattr(self, 'protocol_ended', False):
				return
			self.phase_continue_pressed = True
			self.stage_continue_button.disabled = True
			self.protocol_floatlayout.clear_widgets()
			self.begin_phase('probe')
		except Exception:
			traceback.print_exc()
			self.protocol_end()

	def write_trial(self):
		words_presented = ' '.join(self.current_item.get('words', [])) if self.current_item else ''
		sentence_id = self.current_item.get('id', '') if self.current_item else ''
		sentence_type = self.current_item.get('type', '') if self.current_item else ''

		row = [
			self.current_trial,
			self.current_phase,
			sentence_id,
			sentence_type,
			words_presented,
			self.placed,
			self.valence,
			self.timed_out,
			self.warned,
			self.first_touch_latency,
			self.construction_latency,
			str(self.digit_target),
			str(self.digit_response),
			self.digits_correct,
			self.digit_all_correct,
			self.recall_latency
		]
		self.write_summary_file(row)

	def _cancel_events(self):
		for attr in ('digit_event', 'sentence_event', 'feedback_event', 'iti_event'):
			ev = getattr(self, attr, None)
			if ev is not None:
				try:
					ev.cancel()
				except Exception:
					pass
				setattr(self, attr, None)
		Clock.unschedule(self.remove_feedback)

	def protocol_end(self, *args):
		self._cancel_events()
		if getattr(self, 'digit_widget', None) is not None:
			try:
				self.digit_widget.close()
			except Exception:
				pass
		return super(ProtocolScreen, self).protocol_end(*args)

