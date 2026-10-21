# Changelog

## 2.1.0 (2026-10-21)

### Data output changes (read before pooling data across versions)

Files written by 2.1.0 differ from earlier versions as follows. Use the `TouchCog` version, or the session date, to tell old files from new ones.

**All tasks (event file)**
- `Variable Change` events now always record the value. Previously, when a type or units was given (e.g. CPT stimulus duration in frames/seconds, CJB discrimination values, PAL stimulus image names), the value was dropped and the Type/Units cells were shifted one column left. New layout: `Arg1_Name` = variable, `Arg1_Value` = value, `Arg2` = `Type`/type, `Arg3` = `Units`/units.

**CPT**
- Outcome coding for CJB trials where the hold button is released without touching the stimulus:
  - CJB target: now **5** (hit, no center press). Previously mis-coded as 6.
  - CJB nontarget: **6** (false alarm, no center press), unchanged.
  - CJB neutral image: now **8** (CJB neutral), consistent with the pressed and not-pressed paths. Previously 6.
  - Non-CJB stages are unchanged.
- Outcome 7 (trial abort) is now logged as a `Trial Outcome` event. Previously it appeared only in the summary file.
- `too_slow`, `miss` and `abort` feedback is now shown to participants (it was configured but never displayed). This changes what participants see on release-only and abort trials.
- After the CJB discrimination 3x-failure exit, the trial counter no longer skips a number and no stray post-stage parameter events are logged.
- Outcome codes for reference: 0 premature/reset, 1 hit, 2 miss, 3 false alarm, 4 correct rejection, 5 hit without center press, 6 false alarm without center press, 7 trial abort, 8 CJB neutral.

**PAL**
- New summary column `RecallImage`, appended at the **end** of the row: the image the participant had to recall (Recall stage only; empty otherwise). Existing column positions are unchanged. `TargetImage` in Recall still holds the outline image.
- Recall target display/remove events now name the recalled image instead of the outline.
- Block parameter events (`Stimulus Number`, `Target Image List`, `Trial List`, `Block Trial Max`) now log their real values (previously the stage name). `Current Block` is logged after the block number is incremented (previously one block behind).
- Metadata now records `image_set_dspal`, `image_set_recall` and `recall_target_present_duration`.
- dsPAL image sets 2 and 3 are now selectable in the menu.

**PR**
- `TrialNo` is now 1-based and continuous across blocks (matching TUNL). Previously it started at 0 and the first trial of each block repeated the previous block's last number.
- On confirmation trials (`use_confirmation` on, even block trials), `TargetXPos`/`TargetYPos` now hold the hold button's position. Previously they repeated the previous stimulus position.

**PRL**
- `ReversalNo` and the `max_reversals` limit are now counted **per block** (reset at each block start); the hit streak also resets per block. Previously they accumulated across blocks, so with more than one block every later block ended at its first reversal.
- Multi-image sets (e.g. `image_set = lines`) and the Training stage now display the images that are logged. Previously participants saw the mask image (multi-image) or the default image (Training) while the data recorded other images. The default single-image mode is unchanged.
- Multi-image mode no longer skips the first entry of each block's reward list.

**TUNL**
- `Cue_X`, `Cue_Y`, `Target_X`, `Target_Y` are now written as raw screen fractions (0-1), matching the event file. Previously 1 was added (range 1-2). Cue-target distances are unaffected; any analysis that subtracted 1 must be updated for 2.1.0 files.

### Fixes
- PR no longer crashes on the second hit when `use_confirmation` is off, or at the first trial when the language has no tutorial video (e.g. French).
- PAL with `block_multiplier` > 1: Recall blocks 2+ no longer show a blank screen, and returning from a tutorial video no longer repeats the previous stage's block.
- TUNL Delay-stage staircase end condition now matches the Combo stage (both limits tested); no behaviour change was found in simulation.
- CPT menu no longer crashes when the similarity setting is absent; a stage-type check that was always true now works as intended.
- Platform: input now lines up with the display on Windows at any display scaling (125-200%, 4K), fullscreen uses the desktop resolution instead of switching display modes, and many stability fixes (duplicate screens, battery double-advance, double button releases, silent load failures, participant ID sanitising).

### Internal
- `KivyMenuInterface.py` split into the `Interface/` package; `TouchCog.spec` updated (relative paths, runtime task imports).
- numpy-style docstrings across the codebase; headless regression tests in `tests/`.

### Open question
- CPT: the CJB discrimination failure count is not reset when a CJB_Discrimination block restarts. Left unchanged pending confirmation of whether the 3-failure rule counts per block or across the stage.
