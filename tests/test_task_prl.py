# Headless regression: PRL block/reversal accounting at block start and stimulus image
# sources (run directly as a script; importable for the test runner).
import importlib.util, os, pathlib, sys, time, types
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, ROOT)

from unittest.mock import MagicMock
from Protocol.PRL.Task.Protocol import ProtocolScreen as P
from Classes.Protocol import ProtocolBase


class Stub:
	def __getattr__(self, name):
		return MagicMock()


for _n in ('block_contingency', 'trial_contingency', 'constrained_shuffle',
		   'stimulus_presentation', '_set_hold_button_callbacks', '_set_choice_callbacks'):
	if hasattr(P, _n):
		setattr(Stub, _n, getattr(P, _n))
Stub.section_start = lambda self, *a: None   # real one drives the UI
Stub.block_screen = lambda self, *a: None


def make_stub(images):
	s = Stub()
	s.block_contingency_active = False
	s.protocol_ended = False
	s.target_image_list = images
	s.training_target_image = 'snow'
	s.training_nontarget_image = 'grey'
	s.block_multiplier = 3
	s.block_trial_max = 10
	s.block_duration = 10 ** 6
	s.block_start = time.perf_counter()
	s.stage_list = ['Test']
	s.stage_index = -1
	s.current_block = -1
	s.current_stage = 'Test'
	s.current_hits = 0
	s.current_reversal = 0
	s.current_trial = 0
	s.current_block_trial = 0
	s.reversal_threshold = 2
	s.max_reversals = 3
	s.target_image_index = 0
	s.nontarget_image_index = 1
	s.target_loc_list = ['Left', 'Right']
	s.target_loc_index = 0
	s.nontarget_loc_index = 1
	s.target_loc = 'Left'
	s.nontarget_loc = 'Right'
	s.target_rewarded = True
	s.nontarget_rewarded = False
	s.iti_range = [0.75, 1.25]
	s.iti_fixed_or_range = 'range'
	s.trial_reward_list = ['Target'] * 7 + ['NonTarget'] * 3
	s.trial_reward_list = s.constrained_shuffle(s.trial_reward_list, max_run=5)
	s.trial_reward_list_index = -1
	s.instruction_dict = {'Main': {'train': 't', 'task': 'k'}}
	s.begin_section_button_str = 'b'
	s.session_event = MagicMock()
	s.final_results_screen = lambda *a: setattr(s, 'done', True)
	s.protocol_end = lambda *a: setattr(s, 'done', True)
	s.done = False
	return s


def run(images):
	s = make_stub(images)
	s.block_contingency()
	log = []
	for _ in range(3 * 10 + 5):
		if s.done:
			break
		log.append((s.current_block, s.current_block_trial, s.trial_reward_list_index,
				   s.target_rewarded, s.current_reversal, s.current_hits,
				   s.target_image, s.nontarget_image))
		s.current_hits += 1   # always-target participant
		s.last_response = 1
		s.trial_contingency()
	return s, log


# --- (a),(b) counters and reward index at the start of block 2 -------------------
s, log = run(['horizontal', 'vertical'])
block2 = next(i for i, r in enumerate(log) if r[0] == 2)

# (a) current_reversal and current_hits are 0 at the start of block 2
assert log[block2][4] == 0 and log[block2][5] == 0, log[block2]
# ... and they stay reset until the first block-2 reversal, not ending block 2 there
first_rev_b2 = next(i for i in range(block2, len(log))
				   if log[i][0] == 2 and log[i][4] == 1)
assert log[first_rev_b2 + 1][0] == 2, 'block 2 ended at its first reversal'
assert log[first_rev_b2][4] == 1 and log[first_rev_b2][5] == 0

# (b) the first trial of block 2 uses reward-list index 0
assert log[block2][2] == 0, log[block2]
assert s.trial_reward_list[log[block2][2]] in ('Target', 'NonTarget')


# --- (c) stimulus sources follow target/nontarget (not the mask) ----------------
def button():
	return types.SimpleNamespace(source='mask', unbind=lambda *a, **k: None, bind=lambda *a, **k: None)


def img_path(img):
	return str(pathlib.Path('Protocol') / 'PRL' / 'Image' / 'Targets' / 'shapes' / (img + '.png'))


# two images: target on the left
s = make_stub(['horizontal', 'vertical'])
s.image_dir_path = pathlib.Path('Protocol') / 'PRL' / 'Image'
s.image_set = 'shapes'
s.current_stage = 'Test'
s.target_image = 'horizontal'
s.nontarget_image = 'vertical'
s.target_loc = 'Left'
s.nontarget_loc = 'Right'
s.left_stimulus = button()
s.right_stimulus = button()
Stub.stimulus_presentation(s)
assert s.left_stimulus.source == img_path('horizontal')
assert s.right_stimulus.source == img_path('vertical')

# two images: target on the right
s = make_stub(['horizontal', 'vertical'])
s.image_dir_path = pathlib.Path('Protocol') / 'PRL' / 'Image'
s.image_set = 'shapes'
s.current_stage = 'Test'
s.target_image = 'horizontal'
s.nontarget_image = 'vertical'
s.target_loc = 'Right'
s.nontarget_loc = 'Left'
s.left_stimulus = button()
s.right_stimulus = button()
Stub.stimulus_presentation(s)
assert s.left_stimulus.source == img_path('vertical')
assert s.right_stimulus.source == img_path('horizontal')

# single image: both stimuli show the single configured image, even after a Training stage changed them
s = make_stub(['circle'])
s.stimulus_image_source = 'circle.png'
s.image_dir_path = pathlib.Path('Protocol') / 'PRL' / 'Image'
s.image_set = 'shapes'
s.current_stage = 'Test'
s.target_image = 'circle'
s.nontarget_image = 'circle'
s.target_loc = 'Left'
s.nontarget_loc = 'Right'
s.left_stimulus = button()
s.right_stimulus = button()
s.left_stimulus.source = s.right_stimulus.source = 'snowflake.png'  # left over from Training
Stub.stimulus_presentation(s)
assert s.left_stimulus.source == 'circle.png'
assert s.right_stimulus.source == 'circle.png'

print('ok')
