# Headless regression tests for the PAL task fixes (Protocol/PAL/Task/Protocol.py, Menu.py).
# Mirrors the working verify reproduction: stubs ProtocolScreen methods so no Kivy UI and no
# real Documents/TouchCog/Data writes occur.
import os, sys, tempfile, pathlib
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from unittest.mock import MagicMock
import Classes.Protocol as CP
import Protocol.PAL.Task.Protocol as P

P.PreloadedVideo = MagicMock()
Cls = P.ProtocolScreen

# ---- metadata_cols: gather the real column list headlessly (skip heavy base __init__) ----
_cfg = pathlib.Path(tempfile.mkdtemp())
(_cfg / 'Protocol' / 'PAL').mkdir(parents=True)
(_cfg / 'Protocol' / 'PAL' / 'Configuration.ini').write_text('[TaskParameters]\n', encoding='utf-8')
_orig_init = CP.ProtocolBase.__init__
CP.ProtocolBase.__init__ = lambda self, **kw: None
try:
    meta_screen = P.ProtocolScreen.__new__(P.ProtocolScreen)
    meta_screen.app = MagicMock(); meta_screen.app.app_root = _cfg
    P.ProtocolScreen.__init__(meta_screen)
finally:
    CP.ProtocolBase.__init__ = _orig_init

# (c) metadata_cols contains the three image-set/duration names; they are attribute names so the
# base metadata writer can fall back to the resolved values (getattr) when the menu/config omits them
for name in ('image_set_dspal', 'image_set_recall', 'recall_target_present_duration'):
    assert name in meta_screen.metadata_cols, name

# ---- method-copy stubs mirroring the verify reproduction ----
names = ['block_contingency','trial_contingency','_is_final_block','_clear_grid_press_bindings','_bind_instruction_button',
 '_set_hold_button_callbacks','constrained_shuffle','write_trial','_prepare_stage_continue_button','stage_continue_pressed',
 'stop_tutorial_video','start_protocol_from_tutorial']
def make(mult, stages, video):
    tmp = pathlib.Path(tempfile.mkdtemp())
    if video: (tmp/'Protocol'/'PAL'/'Language'/'English'/'Tutorial_Video').mkdir(parents=True)
    class S: pass
    for n in names: setattr(S, n, getattr(Cls, n))
    s = S()
    s.app = MagicMock(); s.app.app_root = tmp
    s.protocol_name='PAL'; s.language='English'
    s.events=[]; s.widgets=[]
    fl = MagicMock()
    fl.add_variable_event.side_effect = lambda *a, **k: s.events.append(('var',)+a)
    fl.add_stage_event.side_effect = lambda *a, **k: s.events.append(('stage',)+a)
    fl.add_widget.side_effect = lambda w: s.widgets.append(w)
    fl.clear_widgets.side_effect = lambda: s.widgets.clear()
    s.protocol_floatlayout = fl
    for n in ['hold_button','instruction_button','tutorial_video','section_instr_label','stage_continue_button','tutorial_continue_button','recall_stimulus']:
        setattr(s, n, MagicMock(name=n))
    s.stimulus_grid_list=[MagicMock() for _ in range(5)]
    s.image_dict=MagicMock(); s.session_event=MagicMock()
    for n in ['remove_feedback','trigger_tutorial_screen','start_stage_screen','_reset_tutorial_continue_button','iti_start','premature_response','hold_remind','start_recall_target_screen','start_recall_block','section_start','protocol_end','target_pressed','nontarget_pressed']:
        setattr(s, n, MagicMock(name=n))
    s.rows=[]; s.write_summary_file = s.rows.append
    s.stage_list=stages; s.block_multiplier=mult
    s.current_block=-1; s.stage_index=-1; s.current_block_trial=0; s.current_trial=0; s.current_correction_trial=0
    s.block_duration=600; s.block_trial_max=120; s.block_start=0.0
    s.num_stimuli_pal=3; s.num_stimuli_pa=5; s.num_rows=1; s.num_stimuli=3
    s.stimulus_x_boundaries=[0.1,0.9]; s.width_adjust=1; s.height_adjust=1
    s.generate_stimulus_grid = lambda *a, **k: [MagicMock() for _ in range(s.num_stimuli)]
    s.target_image_list_pal=['zigzags','shapes','ghost']; s.target_image_list_pa=['1','2','4','5','6']
    s.trial_list_pal=[0,1,2]*3; s.trial_list_pa=[0,1,2,3,4]*2
    s.dpal_trial_max=s.spal_trial_max=s.recall_trial_max=9
    s.training_block_max_correct=3; s.training_image='snowflake'; s.mask_image='mask'; s.outline_image='whitecircle'
    s.use_correction_trials=False; s.iti_range=[1.0]; s.iti_fixed_or_range='fixed'
    s.response_tracking=[]; s.last_response=-1; s.trial_list_index=0; s.trial_list=[]
    s.spal_video_presented=s.recall_video_presented=False
    s.block_contingency_active=False; s.protocol_ended=False; s.protocol_end=MagicMock()
    s.instruction_section_button_str='go'; s.image_recall_button_str='show'
    s.tutorial_video_sPAL_path='x'; s.tutorial_video_PA_path='y'
    s.target_loc=0; s.nontarget_loc=1; s.nontarget_image_loc=2
    s.target_image='mask'; s.nontarget_image='mask'; s.recall_image='mask'; s.blank_image='mask'
    s.current_stage=''; s.tutorial_advance_active=False; s.stimulus_on_screen=False
    s.text_button_size=[0.4,0.15]
    s.data_cols = meta_screen.data_cols
    return s

def run(mult, stages, video, nblocks_guard=12):
    s = make(mult, stages, video)
    seq=[]
    s.block_contingency()
    for _ in range(nblocks_guard):
        if s.protocol_ended or s.protocol_end.called: break
        seq.append((s.stage_index, s.current_stage, s.current_block))
        vis = [getattr(w,'_mock_name',str(w)) for w in s.widgets]
        seq[-1] += (vis,)
        if s.trigger_tutorial_screen.called:
            s.trigger_tutorial_screen.reset_mock()
            s.tutorial_advance_active=False
            s.stop_tutorial_video()
            continue
        s.block_contingency_active=False
        s.block_contingency()
    return s, seq

# (a) Recall write_trial row ends with RecallImage == recall_image and has len(data_cols) values
s = make(1, ['Recall'], False)
s.block_contingency()
s.last_response=1; s.response_latency=0.9
s.write_trial()
row = s.rows[-1]
assert len(row) == len(s.data_cols), (row, s.data_cols)
assert row[-1] == s.recall_image and s.recall_image != '', (row, s.recall_image)

# (a) non-Recall rows end with ''
s = make(1, ['dPAL'], False)
s.block_contingency()
s.last_response=1; s.response_latency=0.9; s.recall_image='mask'
s.write_trial()
assert s.rows[-1][-1] == '', s.rows[-1]

# (b) block_contingency logs 'Current Block' equal to the new block number
s = make(2, ['dPAL','sPAL','Recall'], False)
s.block_contingency()
cb = [e[3] for e in s.events if e[0]=='var' and e[2]=='Current Block']
assert cb and cb[-1] == s.current_block, (cb, s.current_block)

# (b) the four parameter events no longer log the stage name
for pname in ('Stimulus Number','Target Image List','Trial List','Block Trial Max'):
    for e in s.events:
        if e[0]=='var' and e[1]=='Parameter' and e[2]==pname:
            assert s.current_stage not in [str(v) for v in e[3:]], (pname, e)

# (d) block_multiplier=2 with video re-entry: no repeated block, Recall block 2 reaches section_start
s, seq = run(2, ['dPAL','sPAL','Recall'], True)
seen = {(st, bl) for _, st, bl, _ in seq}
# each stage runs exactly blocks 1..block_multiplier (no repeated/extra block), dPAL->sPAL->Recall
assert seen == {('dPAL',1),('dPAL',2),('sPAL',1),('sPAL',2),('Recall',1),('Recall',2)}, seen
# Recall block 2 reaches section_start (trial screen shown, not the block-1 instruction screen)
recall2 = [x for x in seq if x[1]=='Recall' and x[2]==2]
assert recall2 and recall2[-1][3] == [], recall2

print('ok')
