# TouchCog

## Revisions from Master

This is an experimental fork of the TouchCog repository (https://github.com/dpalmer9/TouchCog) and should not be considered stable; one or more features may be incomplete or non-functional at any given time, and are subject to change without notice.

This code incorporates a number of changes to the CPT task, including:
- A different CPT stimulus set using Fribbles [Visual Cognition, 7(1/2/3), 2000, 297-322].
- Dynamic creation of multiple stimulus sets.
- Dynamic creation of CPT task lists.
- Independent parameter selection for each paradigm within CPT.
- Separate training blocks for each paradigm within CPT.
- Separate task and training instruction sets for each paradigm within CPT, including presentation of target images to improve learning of the task.

Note that this is an incomplete list and is subject to change without notice. For a stable release, please see the original TouchCog repository (https://github.com/dpalmer9/TouchCog).

## Hardware Requirements
Computer with 64-bit Windows, MacOS, or Linux Distribution (Debian, Ubuntu, Raspbian, etc.). ChromeOS Linux also supported.

For touch input, the system must utilize touchscreen technology (e.g. capacitive, IR, etc.)

## Software Requirements
In order to run the scripts, you will need to have Python 3, version 3.5 or greater.
Download: https://www.python.org/downloads/

All the scripts require the package Kivy in order to run. Instructions to install Kivy are below:
https://kivy.org/doc/stable/installation/installation-windows.html
https://kivy.org/doc/stable/installation/installation-linux.html
https://kivy.org/doc/stable/installation/installation-osx.html


## Setup
To start the software, you can launch the WindowLauncher.py or KivyMenuInterface.py file.

Window Launcher is used to set the screen resolution as well as choose to run in full-screen or window.

Kivy Menu Interface will launch the system and allow for the selection of a behavioural task.

## Current Tasks

### Image Continuous Performance Task (iCPT2GStim1 and iCPT2GStim2)
In this task, participants are required to rapidly respond to images presented at the center of the screen. These include
images that must be pressed (target) and images that responses must be withheld from (distractor).

### Paired Associate Learning (PAL)
In this task, participants are presented with two different images in two different spatial locations. The correct response
is determined by both the spatial and visual features of the stimuli.

### Visual Probabilistic/Deterministic Reversal Learning (vPRL)
In this task, participants must rapidly make decisions to select a correct stimulus against an incorrect one. During the
task, the stimuli can either have deterministic or probabilistic reward contingencies.

In the deterministic version, the responses to the correct stimuli are always reward cued. In the probabilistic version
the stimuli is reward cued only a percentage of the time.

Participants are given feedback in terms of a score displayed at the top of the screen. Once participants make a 
fixed number of correct responses, the reward contingency is reversed.

### Trial Unique Non-Match to Location (TUNL)
In this task, participants must respond to an illuminated location on an 8x8 spatial grid. Once participants respond,
they are required to complete a distractor task (pressing targets, ignoring distractors) to generate interference
and a working memory delay. Following the distractor task, two locations are illuminated. The previously seen sample
location as well as a novel location are illuminated. A reward cue is presented following responses
to the novel location.

### Progressive Ratio (PRHuman)
In this task, participants must correctly press illuminated squares in an 8x8 spatial grid. Reward cues are provided following a certain
number of responses. The number of required responses increases after each reward cue.
Once participants have completed a block of trials, the response requirement will reset, but the
reward valuation will decrease by 50%. Participants can choose to complete the task or prematurely terminate the protocol.

## Contact
Please feel free to reach out to me with suggestions, feedback, and ideas for new features!
