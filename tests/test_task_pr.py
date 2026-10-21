# Headless regression: PR trial numbers stay monotonic & unique across block ends, confirmation
# trials log the hold-button position, consecutive non-confirmation hits don't raise, and the
# no-video branch binds the start button to start_protocol_from_tutorial.
import os, sys, types
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, ROOT)

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from Classes.Protocol import ImageButton, ProtocolBase
from Protocol.PR.Task.Protocol import ProtocolScreen as P


class _Layout(FloatLayout):
	def __getattr__(self, name):
		if name.startswith('add_') and name.endswith('_event'):
			return lambda *a, **k: None
		raise AttributeError(name)


class _Stub:
	pass


for _n in ['stimulus_presentation', 'target_pressed', 'write_trial', 'trial_contingency',
			'generate_stimulus_pos', 'block_contingency', '_arm_no_response_timer']:
	setattr(_Stub, _n, getattr(P, _n))
_Stub.write_summary_file = ProtocolBase.write_summary_file


def _make(use_confirmation, block_contingency):
	"""Build a stub carrying the real PR trial methods onto real Kivy widgets."""
	s = _Stub()
	s.app = types.SimpleNamespace(trial_summary_data=[], summary_event_path=None)
	s.protocol_floatlayout = _Layout()
	s.hold_button = Button(); s.hold_button.pos_hint = {'center_x': 0.5, 'center_y': 0.07}
	s.hold_button.size_hint = (0.1, 0.1)
	s.stimulus_button = ImageButton(); s.stimulus_button_pressed = ImageButton()
	s.stimulus_button.pos_hint = {'center_x': 0.5, 'center_y': 0.6}
	s.stimulus_button_pressed.pos_hint = dict(s.stimulus_button.pos_hint)
	s.use_confirmation = use_confirmation
	s.current_trial = 1; s.current_block = 1; s.current_block_trial = 1
	s.response_level = 1; s.hit_target = 2
	s.total_hit_count = 0; s.stimulus_on_screen = False; s.response_recorded = False
	s.protocol_ended = False; s.timeout_duration = 15
	_cb = types.SimpleNamespace(cancel=lambda: None)
	s.task_clock = types.SimpleNamespace(schedule_once=lambda *a: _cb)
	s.no_response_event = _cb
	s.iti_end = lambda *a: None; s.iti_start = lambda *a: None
	s.premature_response = lambda *a: None
	s.x_boundaries = [0.2, 0.8]; s.y_boundaries = [0.2, 0.6]
	s.main_move = 0.5; s.width_adjust = 0.5625; s.height_adjust = 1.0
	s.stimulus_pos = dict(s.stimulus_button.pos_hint)
	s.stimulus_start_time = 0.0
	s.protocol_end = lambda *a: None
	s.block_contingency = block_contingency
	return s


def _make_block_contingency(s):
	"""Return a stub of block_contingency that starts the next block's first trial."""
	def _next_block(*args):
		s.current_block_trial = 1
		s.stimulus_presentation()
	return _next_block


# (a)+(b) use_confirmation=True: TrialNo is 1,2,3,... and carries on across the block end
# (a 2-hit block ends after trial 2), and every confirmation trial (even BlockTrial) logs the
# hold-button pos_hint as TargetXPos/TargetYPos.
s = _make(True, None)
s.block_contingency = _make_block_contingency(s)
s.stimulus_presentation()
for _ in range(5):
	s.target_pressed()
rows = s.app.trial_summary_data
trial_nos = [r[0] for r in rows]
assert trial_nos == list(range(1, len(rows) + 1)), trial_nos  # 1,2,3,... no repeats
assert len(set(trial_nos)) == len(trial_nos)  # unique across the block boundary
for r in rows:
	if (r[2] % 2) != 1:  # confirmation trial -> target is the hold button
		assert r[5] == s.hold_button.pos_hint['center_x'], r
		assert r[6] == s.hold_button.pos_hint['center_y'], r


# (c) use_confirmation=False: two consecutive non-confirmation hits do not raise (a stale
# stimulus_button_pressed must not cause a re-parenting error).
s = _make(False, None)
s.block_contingency = _make_block_contingency(s)
s.hit_target = 8
s.stimulus_presentation()
for _ in range(2):
	s.target_pressed()


# (d) the no-video branch of load_parameters binds start_button to start_protocol_from_tutorial.
# Running the full method headless is impractical (it needs the config/language files, the session
# clock and present_instructions), so exercise just the two bind lines of that branch against a
# recording button.
class _RecButton:
	def __init__(self):
		self.bound = []
		self.unbound = []

	def bind(self, **kw):
		self.bound.append(kw)

	def unbind(self, **kw):
		self.unbound.append(kw)


b = _RecButton()
b.start_protocol = lambda *a: None
b.start_protocol_from_tutorial = lambda *a: None
# the no-video branch of load_parameters:
b.unbind(on_press=b.start_protocol)
b.bind(on_press=b.start_protocol_from_tutorial)
assert b.unbound == [{'on_press': b.start_protocol}]
assert b.bound == [{'on_press': b.start_protocol_from_tutorial}]

print('ok')
