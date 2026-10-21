# Headless regression test for the recent CPT fixes in Protocol/CPT/Task/Protocol.py and Menu.py.
import os, sys, time, types
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import numpy as np
from Protocol.CPT.Task.Protocol import ProtocolScreen as P
from Protocol.CPT.Task.Menu import ConfigureScreen as C


class Rec:
	def __init__(self): self.ev = []
	def __getattr__(self, n):
		if n.startswith('add_'):
			return lambda *a, **k: self.ev.append((n[4:],) + a)
		return lambda *a, **k: None

class Obj:  # tolerant widget
	def __getattr__(self, n): return lambda *a, **k: None
	def __setattr__(self, n, v): object.__setattr__(self, n, v)

class Stub: pass

for n in ['stimulus_response', 'center_notpressed', 'response_cancelled', 'write_trial', 'trial_contingency',
		  '_encode_last_response', '_update_hit_false_alarm_tracking', '_update_cjb_discrimination_history',
		  '_run_staircase', '_run_cjb_discrimination_staircase',
		  '_advance_trial_counters_and_iti', '_select_next_stimulus', '_check_end_conditions', 'start_stage_screen']:
	setattr(Stub, n, P.__dict__[n])


def mk(center, full=False):
	s = Stub(); s.protocol_floatlayout = Rec(); s.hold_button = Obj(); s.rows = []; s.feedback = []
	s.write_summary_file = lambda r: s.rows.append(r)
	s._set_hold_button_callbacks = lambda **k: None
	s.assign_feedback = lambda feedback_key=None: s.feedback.append(feedback_key)
	s.feedback_dict = {'too_slow': 'TS', 'miss': 'MISS', 'abort': 'ABORT'}
	s.response_made = False; s.protocol_ended = False; s.stage_list = ['CJB_Discrimination']; s.stage_index = 0
	s.current_stage = 'CJB_Discrimination'; s.cjb_task = True; s.center_image = center; s.target_image = 'Fb2_1132'
	s.cjb_target_image = 'left 45'; s.cjb_nontarget_image = 'right 45'; s.cjb_neutral_target_image = 'left 22.5'
	s.cjb_neutral_nontarget_image = 'right 22.5'; s.cjb_neutral_true_image = 'vert'
	s.stimulus_start_time = time.perf_counter(); s.stimulus_on_screen = True; s.stimulus_mask_on_screen = False
	s.display_stimulus_outline = 0; s.img_stimulus_C = Obj(); s.limhold_started = True; s.feedback_on_screen = False
	s.stage_screen_started = False; s.hold_button_pressed = True; s.trial_outcome = 0; s.contingency = 0; s.response = 0
	s.current_substage = ''; s.noise_mask_value = 0; s.blur_level = 0; s.current_similarity = 1; s.current_trial = 1
	s.current_block = 1; s.current_block_trial = 1; s.target_probability = .5; s.stimdur_frames = 1; s.stimdur_seconds = 1; s.limhold_seconds = 1
	s.response_latency = np.nan; s.stimulus_press_latency = np.nan; s.movement_latency = np.nan
	s.pending_feedback_key = ''
	s.write_trial = types.MethodType(P.write_trial, s)
	s.stimulus_end = lambda *a: None; s.iti_start = lambda *a: None; s.premature_response = lambda *a: None
	s.blur_preload_start = lambda *a: None
	if not full:
		s.trial_contingency = lambda *a: None
	return s


def outcome_events(s):
	return [e[3] for e in s.protocol_floatlayout.ev if e[0] == 'variable_event' and e[1] == 'Outcome' and e[2] == 'Trial Outcome']


# (a) CJB release-without-press outcomes, plus the non-CJB target reference.
for img, exp in [('left 45', 5), ('right 45', 6), ('vert', 8)]:
	s = mk(img); s.stimulus_response(); s.center_notpressed()
	assert s.rows[0][15] == exp, (img, s.rows[0][15])  # trial_outcome column
	# non-CJB target still scores 5 (hold released, no center press)
	s = mk(img); s.cjb_task = False; s.center_image = s.target_image; s.stimulus_response(); s.center_notpressed()
	assert s.rows[0][15] == 5, (img, s.rows[0][15])

# (b) response_cancelled logs Trial Outcome 7 and center_notpressed feeds back 'miss'/'abort'.
s = mk('left 45'); s.stimulus_response(); s.response_cancelled()
assert s.rows[0][15] == 7 and s.rows[0][14] == 2, s.rows[0][13:16]
assert '7' in outcome_events(s), outcome_events(s)
assert s.feedback == ['miss'], s.feedback  # outcome was 5 before abort

s = mk('vert'); s.stimulus_response(); s.response_cancelled()
assert s.rows[0][15] == 7 and s.feedback == ['abort'], (s.rows[0][15], s.feedback)

# (c) CJB_Discrimination 3x-failure path: trial_contingency does not advance current_trial or trial_index.
s = mk('left 45', full=True)
s.trial_list = ['Target', 'Nontarget']; s.trial_index = 0; s.cjb_discrimination_count = 6; s.cjb_discrimination_history = []
s.cjb_discrimination_trials = 30; s.staircase_hr_criterion = .8; s.staircase_far_criterion = .2
s.stage_list = ['CJB_Discrimination', 'CJB_Probe']
s.hit_tracking = []; s.total_hit_tracking = []; s.false_alarm_tracking = []; s.total_false_alarm_tracking = []; s.decision_point_tracking = []
s.staircase_index_tracking = []; s.nontarget_images = ['a']; s.similarity_tracking = []; s.stimdur_frame_tracking = []
s.last_response = 0; s.iti_frame_range = [1]; s.frame_duration = .0167; s.stimdur_base = 1
s.block_target_total = 0; s.session_trial_max = 999; s.session_duration = 1e9; s.start_time = time.perf_counter()
s.block_trial_max = 999; s.block_duration = 1e9; s.block_start = time.perf_counter()
s.block_started = False; s.hold_button_pressed = False
s.trial_outcome = 1; s.contingency = 1; s.response = 1
s.image_dict = {k: types.SimpleNamespace(image=types.SimpleNamespace(texture=None)) for k in ['left 45', 'right 45']}
s.session_event = Obj(); s.protocol_end = lambda: None; s.schedule_hold_remind = lambda x: None
s.cancel_hold_remind = lambda: None; s.iti_active = False; s.premature_response_active = False
s.session_end_button = Obj(); s.stage_results_label = Obj(); s.outcome_dict = {'gj': 'x'}; s.staging_dict = {'continue': 'c', 'end': 'e'}
s.stage_continue_active = False; s.end_session_active = False; s.block_max_count = 1; s.text_button_pos_UC = {}
s.remove_feedback = lambda *a: None; s.stage_screen_end = lambda *a: None; s.iti_end = lambda *a: None
s.outcome_string = ''; s.cjb_probe_target_feedback = []; s.cjb_probe_nontarget_feedback = []
before = (s.current_trial, s.trial_index)
s.trial_contingency()
after = (s.current_trial, s.trial_index)
assert after == before, (before, after)

# (d) TarProb/SART stage-list condition.
for lst, exp in [(['Training', 'CJB_Training'], False), (['Training', 'TarProb_Block'], True), (['SART_Fixed_Probe'], True)]:
	assert any(k in st for st in lst for k in ('TarProb', 'SART')) == exp, lst

# (e) Menu.update_image_widget with an empty grid in non-battery mode does not raise.
m = types.SimpleNamespace(
	app=types.SimpleNamespace(battery_active=False),
	setting_gridlayout=types.SimpleNamespace(children=[]),
	parameters_config=types.SimpleNamespace(getboolean=lambda k: False),
	image_set_similarity_targets=[],
	image_set_standard=[],
	image_selector=types.SimpleNamespace(
		options=[], dropdown=types.SimpleNamespace(clear_widgets=lambda: None, add_widget=lambda w: None),
		thumb_size=0, selected_value=None, button=types.SimpleNamespace(text='')),
)
C.update_image_widget(m)

print('ok')
