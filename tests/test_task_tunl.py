# Headless regression: TUNL write_trial stays in screen coordinates; Delay staircase tests both limits.
import importlib.util, os, random, statistics, sys, time, types
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, ROOT)

_P = os.path.join(ROOT, 'Protocol', 'TUNL', 'Task', 'Protocol.py')
_spec = importlib.util.spec_from_file_location('tunl_protocol', _P)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_cls = [v for v in vars(_mod).values() if isinstance(v, type) and hasattr(v, 'write_trial') and v.__module__ == 'tunl_protocol'][0]


# (a) write_trial writes the raw pos_hint values (all within 0..1) into Cue_X/Y, Target_X/Y.
class _Logger:
	def __init__(self):
		self.rows = []

	def write_summary_file(self, row):
		self.rows.append(row)


def check_write_trial():
	logger = _Logger()
	# raw pos_hint centres, each a screen fraction in 0..1
	raw = {'Cue': {'x': 0.25, 'y': 0.4}, 'Target': {'x': 0.75, 'y': 0.6}}
	stub = types.SimpleNamespace(
		trial_coord=raw,
		current_trial=1, current_stage='Train', current_block=1,
		current_block_trial=1, current_sep=2, current_delay=1,
		video_position=3.5, contingency=1, trial_outcome=1,
		last_response=0, response_latency=0.42,
	)
	stub.write_summary_file = logger.write_summary_file
	_cls.write_trial(stub)
	row = logger.rows[0]
	# data_cols: TrialNo,Stage,Block,BlockTrial,Separation,Delay,Cue_X,Cue_Y,Target_X,Target_Y,...
	assert row[6] == raw['Cue']['x']
	assert row[7] == raw['Cue']['y']
	assert row[8] == raw['Target']['x']
	assert row[9] == raw['Target']['y']
	for v in (raw['Cue']['x'], raw['Cue']['y'], raw['Target']['x'], raw['Target']['y']):
		assert 0.0 <= v <= 1.0
	return row[6:10]


check_write_trial()


# (b) short Delay-stage staircase simulation always ends with both limits tested.
class _Layout:
	def __getattr__(self, name):
		return lambda *a, **k: None


def run_staircase(p, seps=(0.0, 1.0, 2.0, 3.0, 4.0), res=1.0):
	ended = []
	s = types.SimpleNamespace(
		trial_resolution_active=False, hold_active=False, current_block_trial=1,
		contingency=1, response_tracking=[], current_stage='Delay',
		current_sep=2, current_delay=5, block_start_time=time.perf_counter(),
		block_duration=1e9, delay_probe_sep_tracking=[],
		delay_probe_sep_limit_dict={'min': min(seps), 'max': max(seps)},
		delay_probe_sep_resolution=res, current_block=1, staircase_flag=0,
		combo_probe_sep_list=list(seps), iti_range=[1], iti_fixed_or_range='fixed',
		iti_length=1, protocol_floatlayout=_Layout(), current_trial=1,
		section_advance_active=False, block_started=False, screen_x_padding=0,
	)
	s.results_screen = lambda: ended.append(1)
	s.protocol_end = lambda: (_ for _ in ()).throw(RuntimeError('protocol_end'))
	for a in ('cue_image', 'target_image', 'cue_image_button', 'target_image_button'):
		setattr(s, a, types.SimpleNamespace(pos_hint=None))
	s.generate_trial_pos_sep = lambda *a, **k: {'Cue': {'x': 0, 'y': 0}, 'Target': {'x': 0, 'y': 0}}
	for a in ('x_boundaries', 'y_boundaries', 'stimulus_image_spacing', 'screen_y_padding_t', 'screen_y_padding_b'):
		setattr(s, a, 0)
	s.current_sep = round(statistics.mean([min(seps), max(seps)]), 1)
	for _ in range(1000):
		s.contingency = 1 if random.random() < p else 0
		_cls.trial_contingency(s)
		if ended:
			break
	return s, bool(ended)


random.seed(1)
runs = 0
for p in (0.95, 0.5, 0.1, 0.7):
	for _ in range(100):
		s, ended = run_staircase(p)
		runs += 1
		assert ended, 'Delay staircase did not terminate'
		L, T = s.delay_probe_sep_limit_dict, s.delay_probe_sep_tracking
		assert L['min'] in T and L['max'] in T, (p, dict(L), T[:])

assert runs == 400
print('ok')
