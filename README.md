# TouchCog

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

### Linux/Chromebook Setup
If the device is going to be running on a Chromebook or installation of Linux, the following command must be run prior to running the Python Code

sudo apt install -y \
  build-essential python3 python3-dev python3-pip python3-venv \
  libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
  libgles2-mesa-dev libgl1-mesa-dev libglew-dev \
  libgstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  libjpeg-dev libpng-dev libpulse-dev libudev-dev libx11-dev \
  libxrandr-dev libxcursor-dev libxinerama-dev pkg-config \
  ffmpeg git xclip


### Python Requirements
The project directory contains a requirements.txt file with the necessary Python packages (including Kivy). The requirements can be installed via:

pip install -r requirements.txt

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
