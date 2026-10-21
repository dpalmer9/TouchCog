# Headless check: output-path helpers reproduce the original file names; _log_touch row shape.
import datetime, os, pathlib, sys, tempfile
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from Classes.DataFiles import DATA_FOLDER, next_free_path, sanitize_participant_id
from Classes.Protocol import FloatLayoutLog

assert DATA_FOLDER == pathlib.Path.home() / 'Documents' / 'TouchCog' / 'Data'
assert sanitize_participant_id(' ab c/d-1 ') == 'ab_c_d-1'
assert sanitize_participant_id('   ') == 'Default' and sanitize_participant_id(12) == '12'

today = str(datetime.date.today())
with tempfile.TemporaryDirectory() as d:
	folder = pathlib.Path(d)
	stem = lambda i: '_'.join(['P1', 'Task', today, str(i)])
	summary = lambda i: folder / (stem(i) + '_Summary_Data.csv')
	assert next_free_path(summary) == (1, summary(1))
	summary(1).touch(); summary(2).touch()
	assert next_free_path(summary) == (3, folder / f'P1_Task_{today}_3_Summary_Data.csv')

	# metadata: no suffix first, then _2, _3 on the same file_index
	meta_stem = stem(3)
	meta = lambda i: folder / (meta_stem + ('' if i == 1 else '_' + str(i)) + '_Metadata.csv')
	assert next_free_path(meta)[1].name == f'P1_Task_{today}_3_Metadata.csv'
	meta(1).touch()
	assert next_free_path(meta) == (2, folder / f'P1_Task_{today}_3_2_Metadata.csv')
	meta(2).touch()
	assert next_free_path(meta)[1].name == f'P1_Task_{today}_3_3_Metadata.csv'

	survey = lambda i: folder / f'P1_Survey_{today}_{i}.csv'
	survey(1).touch()
	assert next_free_path(survey)[1].name == f'P1_Survey_{today}_2.csv'

# _log_touch builds the original 9-element row (no running app needed)
class Stub:
	touch_time, touch_pos = 1.5, [10, 20]
	rows = []
	def add_event(self, row): self.rows.append(row)

s = Stub()
FloatLayoutLog._log_touch(s, 'Touch Press (Blocked)', 'Multi-Touch')
assert s.rows == [[1.5, 'Screen', 'Touch Press (Blocked)', 'X Position', 10, 'Y Position', 20, 'Stimulus Name', 'Multi-Touch']]
print('ok')
