# TouchCog

## Hardware Requirements
Computer with 64-bit Windows, MacOS, or Linux Distribution (Debian, Ubuntu, Raspbian, etc.). ChromeOS Linux also supported.

For touch input, the system must utilize touchscreen technology (e.g. capacitive, IR, etc.)

## Software Requirements
In order to run the scripts, you will need to have Python 3, version 3.10 or greater.
Download: https://www.python.org/downloads/

All the scripts require the package Kivy in order to run. Instructions to install Kivy are below:
https://kivy.org/doc/stable/installation/installation-windows.html
https://kivy.org/doc/stable/installation/installation-linux.html
https://kivy.org/doc/stable/installation/installation-osx.html


## Setup
To start the software, you can launch the KivyMenuInterface.py file.

A local copy of your Config.ini file will be moved to your OS's documents folder in the TouchCog directory, along with a Data folder.

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

### Cognitive Judgement Bias Task (CPT)
In this task, participants are required to rapidly respond to line stimuli located at the center of the screen. These include images that must be pressed, images that must be witheld from, and additional ambiguous stimuli. 

### Image Continuous Performance Task (CPT)
In this task, participants are required to rapidly respond to images presented at the center of the screen. These include
images that must be pressed (target) and images that responses must be withheld from (distractor).

### Paired Associate Learning (PAL)
In this task, participants are presented with two different images in two different spatial locations. The correct response
is determined by both the spatial and visual features of the stimuli.
The included Recall task requires participants to remember five image-location pairs and make decisions about the location associated with presented images.

### Visual Probabilistic/Deterministic Reversal Learning (PRL)
In this task, participants must rapidly make decisions to select a correct stimulus against an incorrect one. During the
task, the stimuli can either have deterministic or probabilistic reward contingencies.

In the deterministic version, the responses to the correct stimuli are always reward cued. In the probabilistic version
the stimuli is reward cued only a percentage of the time.

Participants are given feedback in terms of whether a positive feedback trial has been triggered. Once participants correctly press the target a fixed number of times, the contingency will reverse.

### Trial Unique Non-Match to Location (TUNL)
In this task, participants must respond to an illuminated location on an screen. Once participants respond,
they are presented with a distracting video to generate interference
and a working memory delay. Following the distractor task, two locations are illuminated. The previously seen sample
location as well as a novel location are illuminated. A reward cue is presented following responses
to the novel location.

### Progressive Ratio (PR)
In this task, participants must correctly press illuminated circles on a screen. The participant is reqired to alternate multiple times between the circle targets and the hold button. Reward cues are provided following a certain
number of responses. The number of required responses increases after each reward cue.
Participants can choose to complete the task or prematurely terminate the protocol.

## Contact
Please feel free to reach out to me with suggestions, feedback, and ideas for new features!
