# Imports #
import kivy
import zipimport
import sys
import os
import configparser
import time
import numpy as np
import pandas as pd
import csv
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import AsyncImage
#from win32api import GetSystemMetrics
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.screenmanager import ScreenManager, Screen
from functools import partial

class ImageButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(ImageButton, self).__init__(**kwargs)
        self.coord = None
        self.fit_mode = 'fill'
        self.touch_pos = (0, 0)
        self.name = ''

class FloatLayoutLog(FloatLayout):
    def __init__(self, **kwargs):
        super(FloatLayoutLog, self).__init__(**kwargs)
        self.touch_pos = [0,0]
        self.held_name = ''
        self.event_columns = ['Time', 'Event_Type', 'Event_Name', 'Arg1_Name', 'Arg1_Value',
                              'Arg2_Name', 'Arg2_Value', 'Arg3_Name', 'Arg3_Value']
        self.event_dataframe = pd.DataFrame(columns=self.event_columns)
        self.event_index = 0
        self.save_path = ''
        self.elapsed_time = 0

    def on_touch_down(self, touch):
        self.touch_pos = touch.pos
        if self.disabled and self.collide_point(*touch.pos):
            return True
        for child in self.children[:]:
            if child.dispatch('on_touch_down', touch):
                if isinstance(child, ImageButton):
                    self.held_name = child.name
                else:
                    self.held_name = ''
                self.add_event([self.elapsed_time, 'Screen','Touch Press','X Position',
                                    self.touch_pos[0],'Y Position',self.touch_pos[1],'Stimulus Name',self.held_name])
                return True
        self.held_name = ''
        self.add_event([self.elapsed_time, 'Screen', 'Touch Press', 'X Position',
                        self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])

    def on_touch_move(self, touch):
        self.touch_pos = touch.pos
        if self.disabled:
            return
        for child in self.children[:]:
            if child.dispatch('on_touch_move', touch):
                if isinstance(child, ImageButton):
                    self.held_name = child.name
                else:
                    self.held_name = ''
                self.add_event([self.elapsed_time, 'Screen', 'Touch Move', 'X Position',
                                self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])
                return True
        self.held_name = ''
        self.add_event([self.elapsed_time, 'Screen', 'Touch Press', 'X Position',
                        self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])

    def on_touch_up(self, touch):
        self.touch_pos = touch.pos
        if self.disabled:
            return
        for child in self.children[:]:
            if child.dispatch('on_touch_up', touch):
                if isinstance(child, ImageButton):
                    self.held_name = child.name
                else:
                    self.held_name = ''
                self.add_event([self.elapsed_time, 'Screen', 'Touch Release', 'X Position',
                                self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])
                return True
        self.add_event([self.elapsed_time, 'Screen', 'Touch Release', 'X Position',
                        self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])
        if self.held_name != '':
            self.held_name = ''


    def add_event(self,row):
        self.event_dataframe.loc[self.event_index] = row
        self.event_index += 1
        if self.save_path != '':
            self.event_dataframe.to_csv(self.save_path,index=False)

    def update_path(self,path):
        self.save_path = path

class Protocol_Screen(Screen):
    def __init__(self, screen_resolution, **kwargs):
        super(Protocol_Screen, self).__init__(**kwargs)

        self.protocol_floatlayout = FloatLayoutLog()

        self.add_widget(self.protocol_floatlayout)
        width = screen_resolution[0]
        height = screen_resolution[1]
        self.size = screen_resolution
        self.protocol_floatlayout.size = screen_resolution

        if width > height:
            self.width_adjust = height / width
            self.height_adjust = 1
        elif height < width:
            self.width_adjust = 1
            self.height_adjust = width / height
        else:
            self.width_adjust = 1
            self.height_adjust = 1

        if sys.platform == 'linux' or sys.platform == 'darwin':
            self.folder_mod = '/'
        elif sys.platform == 'win32':
            self.folder_mod = '\\'

        # Define Variables - Folder Path
        self.image_folder = 'Protocol' + self.folder_mod + 'iCPT2GStim2' + self.folder_mod + 'Image' + self.folder_mod
        self.data_output_path = None

        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + 'iCPT2GStim2' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        self.parameters_dict = config_file['TaskParameters']
        self.participant_id = 'Default'

        self.language = 'English'

        self.stimulus_duration = float(self.parameters_dict['stimulus_duration'])
        self.limited_hold = float(self.parameters_dict['limited_hold'])
        self.target_probability = float(self.parameters_dict['target_probability'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.training_image = self.parameters_dict['training_image']
        self.correct_images = self.parameters_dict['correct_images']
        self.correct_images = self.correct_images.split(',')
        self.incorrect_images = self.parameters_dict['incorrect_images']
        self.incorrect_images = self.incorrect_images.split(',')
        self.total_image_list = self.correct_images + self.incorrect_images
        self.block_max_length = int(self.parameters_dict['block_max_length'])
        self.block_max_count = int(self.parameters_dict['block_max_count'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = float(self.parameters_dict['session_trial_max'])
        self.stimulus_duration_probe_active = self.parameters_dict['stimulus_duration_probe_active']
        if self.stimulus_duration_probe_active == 'True':
            self.stimulus_duration_probe_active = True
        else:
            self.stimulus_duration_probe_active = False
        self.flanker_probe_active = self.parameters_dict['flanker_probe_active']
        if self.flanker_probe_active == "True":
            self.flanker_probe_active = True
        else:
            self.flanker_probe_active = False

        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        # Define Language
        self.language = 'English'
        lang_folder_path = 'Protocol' + self.folder_mod + 'iCPT2GStim2' + self.folder_mod + 'Language' + \
                           self.folder_mod + self.language + self.folder_mod
        start_path = lang_folder_path + 'Start.txt'
        start_open = open(start_path, 'r', encoding="utf-8")
        self.start_label_str = start_open.read()
        start_open.close()

        break_path = lang_folder_path + 'Break.txt'
        break_open = open(break_path, 'r', encoding="utf-8")
        self.break_label_str = break_open.read()
        break_open.close()

        end_path = lang_folder_path + 'End.txt'
        end_open = open(end_path, 'r', encoding="utf-8")
        self.end_label_str = end_open.read()
        end_open.close()

        button_lang_path = lang_folder_path + 'Button.ini'
        button_lang_config = configparser.ConfigParser()
        button_lang_config.read(button_lang_path, encoding="utf-8")

        self.start_button_label_str = button_lang_config['Button']['start']
        self.continue_button_label_str = button_lang_config['Button']['continue']
        self.return_button_label_str = button_lang_config['Button']['return']

        feedback_lang_path = lang_folder_path + 'Feedback.ini'
        feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
        feedback_lang_config.read(feedback_lang_path, encoding="utf-8")

        self.stim_feedback_correct_str = feedback_lang_config['Stimulus']['correct']
        stim_feedback_correct_color = feedback_lang_config['Stimulus']['correct_colour']
        if stim_feedback_correct_color != '':
            color_text = '[color=%s]' % stim_feedback_correct_color
            self.stim_feedback_correct_str = color_text + self.stim_feedback_correct_str + '[/color]'

        self.stim_feedback_incorrect_str = feedback_lang_config['Stimulus']['incorrect']
        stim_feedback_incorrect_color = feedback_lang_config['Stimulus']['incorrect_colour']
        if stim_feedback_incorrect_color != '':
            color_text = '[color=%s]' % stim_feedback_incorrect_color
            self.stim_feedback_incorrect_str = color_text + self.stim_feedback_incorrect_str + '[/color]'

        self.hold_feedback_wait_str = feedback_lang_config['Hold']['wait']
        hold_feedback_wait_color = feedback_lang_config['Hold']['wait_colour']
        if hold_feedback_wait_color != '':
            color_text = '[color=%s]' % hold_feedback_wait_color
            self.hold_feedback_wait_str = color_text + self.hold_feedback_wait_str + '[/color]'

        self.hold_feedback_return_str = feedback_lang_config['Hold']['return']
        hold_feedback_return_color = feedback_lang_config['Hold']['return_colour']
        if hold_feedback_return_color != '':
            color_text = '[color=%s]' % hold_feedback_return_color
            self.hold_feedback_return_str = color_text + self.hold_feedback_return_str + '[/color]'

        # Define Variables - List
        self.stage_list = ['Training', 'Main', 'Stimulus Duration Probe', 'Flanker Probe']

        # Define Variables - Boolean
        self.stimulus_on_screen = False
        self.iti_active = False
        self.current_correction = False
        self.block_started = False
        self.feedback_on_screen = False
        self.hold_active = True

        # Define Variables - Count
        self.current_block = 1
        self.current_trial = 1
        self.current_hits = 0
        self.stage_index = 0
        self.trial_outcome = 1  # 1-Hit,2-Miss,3-Mistake,4-Correct Rejection,5-Premature

        # Define Variables - String
        self.center_image = self.training_image
        self.current_stage = self.stage_list[self.stage_index]

        # Define Variables - Time
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0
        self.block_start = 0
        self.elapsed_time = 0

        # Define Variables - Trial Configurations
        distractor_prob = 1 - self.target_probability
        target_prob_single = self.target_probability / len(self.correct_images)
        distractor_prob_single = distractor_prob / len(self.incorrect_images)
        self.image_prob_list = list()
        for a in range(0, len(self.correct_images)):
            self.image_prob_list.append(target_prob_single)
        for a in range(0, len(self.incorrect_images)):
            self.image_prob_list.append(distractor_prob_single)

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path)

        self.center_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.center_stimulus = ImageButton(source=self.center_stimulus_image_path)
        self.center_stimulus.bind(on_press=self.center_pressed)

        self.left_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path)

        self.right_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path)

        # Define Widgets - Text
        self.instruction_label = Label(text=self.start_label_str
                                       , font_size='35sp')
        self.instruction_label.size_hint = (0.6, 0.4)
        self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.block_label = Label(text=self.break_label_str, font_size='50sp')
        self.block_label.size_hint = (0.5, 0.3)
        self.block_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.end_label = Label(text=self.end_label_str, font_size='50sp')
        self.end_label.size_hint = (0.6, 0.4)
        self.end_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.feedback_string = ''
        self.feedback_label = Label(text=self.feedback_string, font_size='50sp', markup=True)
        self.feedback_label.size_hint = (0.7, 0.4)
        self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # Define Widgets - Buttons
        self.start_button = Button(text=self.start_button_label_str)
        self.start_button.size_hint = (0.1, 0.1)
        self.start_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.start_button.bind(on_press=self.start_protocol)

        self.continue_button = Button(text=self.continue_button_label_str)
        self.continue_button.size_hint = (0.1, 0.1)
        self.continue_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.continue_button.bind(on_press=self.block_end)

        self.return_button = Button(text=self.return_button_label_str)
        self.return_button.size_hint = (0.1, 0.1)
        self.return_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.return_button.bind(on_press=self.return_to_main)

    def load_parameters(self, parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'iCPT2GStim2' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        self.participant_id = self.parameters_dict['participant_id']
        self.language = self.parameters_dict['language']
        self.stimulus_duration = float(self.parameters_dict['stimulus_duration'])
        self.protocol_floatlayout.add_event([0, 'Variable Change', 'Stimulus Duration', 'Value', str(self.stimulus_duration),
                                     '', '', '', ''])
        self.limited_hold = float(self.parameters_dict['limited_hold'])
        self.target_probability = float(self.parameters_dict['target_probability'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.training_image = self.parameters_dict['training_image']
        self.correct_images = self.parameters_dict['correct_images']
        self.correct_images = self.correct_images.split(',')
        self.incorrect_images = self.parameters_dict['incorrect_images']
        self.incorrect_images = self.incorrect_images.split(',')
        self.total_image_list = self.correct_images + self.incorrect_images
        self.block_max_length = int(self.parameters_dict['block_max_length'])
        self.block_max_count = int(self.parameters_dict['block_max_count'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = float(self.parameters_dict['session_trial_max'])
        self.stimulus_duration_probe_active = self.parameters_dict['stimulus_duration_probe_active']
        if self.stimulus_duration_probe_active == 'True':
            self.stimulus_duration_probe_active = True
        else:
            self.stimulus_duration_probe_active = False
        self.flanker_probe_active = self.parameters_dict['flanker_probe_active']
        if self.flanker_probe_active == "True":
            self.flanker_probe_active = True
        else:
            self.flanker_probe_active = False

        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        # Define Language
        lang_folder_path = 'Protocol' + self.folder_mod + 'iCPT2GStim2' + self.folder_mod + 'Language' + \
                           self.folder_mod + self.language + self.folder_mod
        start_path = lang_folder_path + 'Start.txt'
        start_open = open(start_path, 'r', encoding="utf-8")
        self.start_label_str = start_open.read()
        start_open.close()

        break_path = lang_folder_path + 'Break.txt'
        break_open = open(break_path, 'r', encoding="utf-8")
        self.break_label_str = break_open.read()
        break_open.close()

        end_path = lang_folder_path + 'End.txt'
        end_open = open(end_path, 'r', encoding="utf-8")
        self.end_label_str = end_open.read()
        end_open.close()

        button_lang_path = lang_folder_path + 'Button.ini'
        button_lang_config = configparser.ConfigParser()
        button_lang_config.read(button_lang_path, encoding="utf-8")

        self.start_button_label_str = button_lang_config['Button']['start']
        self.continue_button_label_str = button_lang_config['Button']['continue']
        self.return_button_label_str = button_lang_config['Button']['return']

        feedback_lang_path = lang_folder_path + 'Feedback.ini'
        feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
        feedback_lang_config.read(feedback_lang_path, encoding="utf-8")

        self.stim_feedback_correct_str = feedback_lang_config['Stimulus']['correct']
        stim_feedback_correct_color = feedback_lang_config['Stimulus']['correct_colour']
        if stim_feedback_correct_color != '':
            color_text = '[color=%s]' % stim_feedback_correct_color
            self.stim_feedback_correct_str = color_text + self.stim_feedback_correct_str + '[/color]'

        self.stim_feedback_incorrect_str = feedback_lang_config['Stimulus']['incorrect']
        stim_feedback_incorrect_color = feedback_lang_config['Stimulus']['incorrect_colour']
        if stim_feedback_incorrect_color != '':
            color_text = '[color=%s]' % stim_feedback_incorrect_color
            self.stim_feedback_incorrect_str = color_text + self.stim_feedback_incorrect_str + '[/color]'

        self.hold_feedback_wait_str = feedback_lang_config['Hold']['wait']
        hold_feedback_wait_color = feedback_lang_config['Hold']['wait_colour']
        if hold_feedback_wait_color != '':
            color_text = '[color=%s]' % hold_feedback_wait_color
            self.hold_feedback_wait_str = color_text + self.hold_feedback_wait_str + '[/color]'

        self.hold_feedback_return_str = feedback_lang_config['Hold']['return']
        hold_feedback_return_color = feedback_lang_config['Hold']['return_colour']
        if hold_feedback_return_color != '':
            color_text = '[color=%s]' % hold_feedback_return_color
            self.hold_feedback_return_str = color_text + self.hold_feedback_return_str + '[/color]'

        # Define Variables - List
        self.stage_list = ['Training', 'Main', 'Stimulus Duration Probe', 'Flanker Probe']

        # Define Variables - Boolean
        self.stimulus_on_screen = False
        self.iti_active = False
        self.current_correction = False
        self.block_started = False
        self.feedback_on_screen = False
        self.hold_active = True

        # Define Variables - Count
        self.current_block = 1
        self.current_trial = 1
        self.current_hits = 0
        self.stage_index = 0
        self.trial_outcome = 1  # 1-Hit,2-Miss,3-Mistake,4-Correct Rejection,5-Premature

        # Define Variables - String
        self.center_image = self.training_image
        self.current_stage = self.stage_list[self.stage_index]
        self.protocol_floatlayout.add_event([0, 'Variable Change', 'Current Stage', 'Value', str(self.current_stage),
                                     '', '', '', ''])

        # Define Variables - Time
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0
        self.block_start = 0
        self.elapsed_time = 0

        # Define Variables - Trial Configurations
        distractor_prob = 1 - self.target_probability
        target_prob_single = self.target_probability / len(self.correct_images)
        distractor_prob_single = distractor_prob / len(self.incorrect_images)
        self.image_prob_list = list()
        for a in range(0, len(self.correct_images)):
            self.image_prob_list.append(target_prob_single)
        for a in range(0, len(self.incorrect_images)):
            self.image_prob_list.append(distractor_prob_single)

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path)
        self.hold_button.pos_hint = {"center_x": 0.5, "center_y": 0.1}
        self.hold_button.name = 'Hold Button'

        self.center_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.center_stimulus = ImageButton(source=self.center_stimulus_image_path)
        self.center_stimulus.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.center_stimulus.bind(on_press=self.center_pressed)
        self.center_stimulus.name = 'Center Stimulus'

        self.left_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path)
        self.left_stimulus.pos_hint = {"center_x": 0.2, "center_y": 0.6}

        self.right_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path)
        self.right_stimulus.pos_hint = {"center_x": 0.8, "center_y": 0.6}

        # Define Widgets - Text
        self.instruction_label = Label(text=self.start_label_str
                                       , font_size='35sp')
        self.instruction_label.size_hint = (0.6, 0.4)
        self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.block_label = Label(text=self.break_label_str, font_size='50sp')
        self.block_label.size_hint = (0.5, 0.3)
        self.block_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.end_label = Label(text=self.end_label_str, font_size='50sp')
        self.end_label.size_hint = (0.6, 0.4)
        self.end_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.feedback_string = ''
        self.feedback_label = Label(text=self.feedback_string, font_size='50sp', markup=True)
        self.feedback_label.size_hint = (0.7, 0.4)
        self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # Define Widgets - Buttons
        self.start_button = Button(text=self.start_button_label_str)
        self.start_button.size_hint = (0.1, 0.1)
        self.start_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.start_button.bind(on_press=self.start_protocol)

        self.continue_button = Button(text=self.continue_button_label_str)
        self.continue_button.size_hint = (0.1, 0.1)
        self.continue_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.continue_button.bind(on_press=self.block_end)

        self.return_button = Button(text=self.return_button_label_str)
        self.return_button.size_hint = (0.1, 0.1)
        self.return_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.return_button.bind(on_press=self.return_to_main)

        self.present_instructions()

    def generate_output_files(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        if os.path.exists(folder_path) == False:
            os.makedirs(folder_path)
        folder_list = os.listdir(folder_path)
        file_index = 1
        temp_filename = self.participant_id + '_iCPT2G_' + str(file_index) + '.csv'
        self.file_path = folder_path + self.folder_mod + temp_filename
        while os.path.isfile(self.file_path):
            file_index += 1
            temp_filename = self.participant_id + '_iCPT2G_' + str(file_index) + '.csv'
            self.file_path = folder_path + self.folder_mod + temp_filename
        data_cols = 'TrialNo,Stage,Block #,Trial Type,Correction Trial,Response,Contingency,Outcome,Response Latency'
        self.data_file = open(self.file_path, "w+")
        self.data_file.write(data_cols)
        self.data_file.close()

        event_path = folder_path + self.folder_mod + self.participant_id + '_TUNLProbe_' + str(
            file_index) + '_Event_Data.csv'
        self.protocol_floatlayout.update_path(event_path)

    def metadata_output_generation(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        metadata_rows = ['participant_id', 'training_image', 'correct_images',
                         'incorrect_images', 'stimulus_duration', 'limited_hold',
                         'target_probability', 'iti_length', 'feedback_length',
                         'block_max_length', 'block_max_count', 'block_min_rest_duration',
                         'session_length_max', 'session_trial_max']

        meta_list = list()
        for meta_row in metadata_rows:
            row_list = list()
            row_list.append(meta_row)
            row_list.append(str(self.parameters_dict[meta_row]))
            meta_list.append(row_list)

        file_index = 1
        meta_output_filename = self.participant_id + '_iCPT2G_Metadata_' + str(file_index) + '.csv'
        meta_output_path = folder_path + self.folder_mod + meta_output_filename
        while os.path.isfile(meta_output_path):
            file_index += 1
            meta_output_filename = self.participant_id + '_iCPT2G_Metadata_' + str(file_index) + '.csv'
            meta_output_path = folder_path + self.folder_mod + meta_output_filename

        meta_colnames = ['Parameter', 'Value']

        with open(meta_output_path, 'w') as meta_output_file:
            csv_writer = csv.writer(meta_output_file, delimiter=',')
            csv_writer.writerow(meta_colnames)
            for meta_param in meta_list:
                csv_writer.writerow(meta_param)

    # Instructions Staging #
    def present_instructions(self):
        self.generate_output_files()
        self.metadata_output_generation()
        self.protocol_floatlayout.add_widget(self.instruction_label)
        self.protocol_floatlayout.add_event(
            [0, 'Stage Change', 'Instruction Presentation', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [0, 'Text Displayed', 'Task Instruction', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_widget(self.start_button)
        self.protocol_floatlayout.add_event(
            [0, 'Button Displayed', 'Task Start Button', '', '',
             '', '', '', ''])

    # Block Staging #
    def block_screen(self, *args):
        if not self.block_started:
            self.protocol_floatlayout.add_widget(self.block_label)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Text Displayed', 'Block Instruction', '', '',
                 '', '', '', ''])
            self.block_start = time.time()
            self.block_started = True
            Clock.schedule_interval(self.block_screen, 0.1)
        if (time.time() - self.block_start) > self.block_min_rest_duration:
            Clock.unschedule(self.block_screen)
            self.protocol_floatlayout.add_widget(self.continue_button)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Button Displayed', 'Continue Button', '', '',
                 '', '', '', ''])

    def block_end(self, *args):
        self.block_started = False
        self.trial_contingency(1, 1)
        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Removed', 'Block Instruction', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Button Removed', 'Continue Button', '', '',
             '', '', '', ''])
        self.trial_contingency(1, 1)
        self.protocol_floatlayout.add_widget(self.hold_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Button Displayed', 'Hold Button', '', '',
             '', '', '', ''])

    # End Staging #
    def protocol_end(self):
        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_widget(self.end_label)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Displayed', 'End Instruction', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_widget(self.return_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Button Displayed', 'Return Button', '', '',
             '', '', '', ''])

    def return_to_main(self):
        self.manager.current = 'mainmenu'

    # Protocol Staging #

    def start_protocol(self, *args):
        self.protocol_floatlayout.add_event(
            [0, 'Stage Change', 'Instruction Presentation', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.remove_widget(self.instruction_label)
        self.protocol_floatlayout.add_event(
            [0, 'Text Removed', 'Task Instruction', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.remove_widget(self.start_button)
        self.protocol_floatlayout.add_event(
            [0, 'Button Removed', 'Task Start Button', '', '',
             '', '', '', ''])
        self.start_clock()

        self.protocol_floatlayout.add_widget(self.hold_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Button Displayed', 'Hold Button', '', '',
             '', '', '', ''])
        self.hold_button.size_hint = ((0.2 * self.width_adjust), (0.2 * self.height_adjust))
        self.hold_button.bind(on_press=self.iti)

    def iti(self, *args):
        if not self.iti_active:
            self.hold_button.unbind(on_press=self.iti)
            self.hold_button.bind(on_release=self.premature_response)
            self.start_iti = time.time()
            self.iti_active = True
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Stage Change', 'ITI Start', '', '',
                 '', '', '', ''])

            if self.feedback_string == self.hold_feedback_wait_str:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Text Removed', 'Feedback', '', '',
                     '', '', '', ''])
                self.feedback_string = ''

            if self.feedback_on_screen == False:
                self.feedback_label.text = self.feedback_string
                self.protocol_floatlayout.add_widget(self.feedback_label)
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
                     '', '', '', ''])
                self.feedback_start_time = time.time()
                self.feedback_on_screen = True
            if ((time.time() - self.feedback_start_time) > self.feedback_length) and self.feedback_on_screen == True:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Text Removed', 'Feedback', '', '',
                     '', '', '', ''])
                self.feedback_on_screen = False
            Clock.schedule_interval(self.iti, 0.1)
        if self.iti_active == True:
            if (((time.time() - self.start_iti) > self.feedback_length) or ((
                                                                                    time.time() - self.feedback_start_time) > self.feedback_length)) and self.feedback_on_screen == True:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Text Removed', 'Feedback', '', '',
                     '', '', '', ''])
                self.feedback_on_screen = False
            if (time.time() - self.start_iti) > self.iti_length:
                Clock.unschedule(self.iti)
                self.iti_active = False
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Stage Change', 'ITI End', '', '',
                     '', '', '', ''])
                self.hold_button.unbind(on_release=self.premature_response)
                self.hold_active = True
                self.stimulus_presentation()

    def stimulus_presentation(self, *args):
        if self.stimulus_on_screen == False:
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Stage Change', 'Display Stimulus', '', '',
                 '', '', '', ''])
            self.protocol_floatlayout.add_widget(self.center_stimulus)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Displayed', 'Center Stimulus', 'X Position', '1',
                 'Y Position', '1', 'Image Name', self.center_image])
            self.center_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
            self.hold_button.bind(on_press=self.hold_returned_stim)
            self.hold_button.bind(on_release=self.hold_removed_stim)

            self.start_stimulus = time.time()

            self.stimulus_on_screen = True
            Clock.schedule_interval(self.stimulus_presentation, 0.1)

        elif self.stimulus_on_screen == True:
            if (time.time() - self.start_stimulus) > self.stimulus_duration:
                self.center_stimulus_image_path = self.image_folder + self.mask_image + '.png'
                self.center_stimulus.source = self.center_stimulus_image_path
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Image Displayed', 'Center Stimulus', 'X Position', '1',
                     'Y Position', '1', 'Image Name', self.mask_image])
            if (time.time() - self.start_stimulus) > self.limited_hold:
                Clock.unschedule(self.stimulus_presentation)
                self.protocol_floatlayout.remove_widget(self.center_stimulus)
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Image Removed', 'Center Stimulus', 'X Position', '1',
                     'Y Position', '1', 'Image Name', self.center_image])
                self.stimulus_on_screen = False
                self.center_notpressed()

    def premature_response(self, *args):
        if self.stimulus_on_screen == True:
            return None

        Clock.unschedule(self.iti)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Premature Response', '', '',
             '', '', '', ''])
        self.feedback_string = self.hold_feedback_wait_str
        contingency = '2'
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Contingency', 'Value', str(contingency),
             '', '', '', ''])
        response = '1'
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Response', 'Value', str(response),
             '', '', '', ''])
        self.trial_outcome = '5'
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Outcome', 'Value', str(self.trial_outcome),
             '', '', '', ''])
        self.write_summary_file(response, contingency)
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_string
        if self.feedback_on_screen == False:
            self.protocol_floatlayout.add_widget(self.feedback_label)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
                 '', '', '', ''])
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)

    def return_hold(self):
        self.feedback_string = self.hold_feedback_return_str
        self.hold_button.bind(on_press=self.iti)

    # Contingency Stages #
    def center_pressed(self, *args):
        Clock.unschedule(self.stimulus_presentation)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Stimulus Pressed', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.remove_widget(self.center_stimulus)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Center Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.center_image])

        self.stimulus_on_screen = False
        self.response_lat = time.time() - self.start_stimulus
        response = '1'
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Response', 'Value', str(response),
             '', '', '', ''])
        if (self.center_image in self.correct_images) or (self.center_image == self.training_image):
            self.feedback_string = self.stim_feedback_correct_str
            contingency = '1'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Contingency', 'Value', str(contingency),
                 '', '', '', ''])
            self.trial_outcome = '1'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Outcome', 'Value', str(self.trial_outcome),
                 '', '', '', ''])
            self.current_hits += 1
        else:
            self.feedback_string = self.stim_feedback_incorrect_str
            self.trial_outcome = '3'
            self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Outcome', 'Value', str(self.trial_outcome),
             '', '', '', ''])
            contingency = '0'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Contingency', 'Value', str(contingency),
                 '', '', '', ''])

        self.feedback_label.text = self.feedback_string
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_start_time = time.time()
        self.feedback_on_screen = True
        self.write_summary_file(response, contingency)
        self.trial_contingency(response, contingency)

        self.hold_button.unbind(on_press=self.hold_returned_stim)
        self.hold_button.unbind(on_release=self.hold_removed_stim)

        self.hold_button.bind(on_press=self.iti)

    def center_notpressed(self):
        self.response_lat = ''
        response = '0'
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Response', 'Value', str(response),
             '', '', '', ''])
        if (self.center_image in self.correct_images) or (self.center_image == self.training_image):
            self.feedback_string = ''
            contingency = '0'  #######
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Contingency', 'Value', str(contingency),
                 '', '', '', ''])
            self.trial_outcome = '2'  #####
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Outcome', 'Value', str(self.trial_outcome),
                 '', '', '', ''])
        else:
            self.feedback_string = ''
            contingency = '1'  #####
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Contingency', 'Value', str(contingency),
                 '', '', '', ''])
            self.trial_outcome = '4'  ######
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Outcome', 'Value', str(self.trial_outcome),
                 '', '', '', ''])
        self.write_summary_file(response, contingency)
        self.trial_contingency(response, contingency)

        self.hold_button.unbind(on_press=self.hold_returned_stim)
        self.hold_button.unbind(on_release=self.hold_removed_stim)

        if self.hold_active == True:
            self.iti()
        else:
            self.return_hold()

    def hold_removed_stim(self, *args):
        self.hold_active = False
        return

    def hold_returned_stim(self, *args):
        self.hold_active = True
        return

    # Data Saving Functions #
    def write_summary_file(self, response, contingency):
        data_file = open(self.file_path, "a")
        data_file.write("\n")
        data_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
        self.current_trial, self.current_stage, self.current_block, self.center_image, int(self.current_correction),
        response, contingency, self.trial_outcome, self.response_lat))
        data_file.close()
        return

    # Trial Contingency Functions #

    def trial_contingency(self, response, contingency):
        self.current_trial += 1
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Current Trial', 'Value', str(self.current_trial),
             '', '', '', ''])

        if self.current_trial > self.session_trial_max:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()
            return

        if (self.current_hits > 10) and (self.stage_index == 0):
            self.feedback_start = time.time()
            self.protocol_floatlayout.remove_widget(self.hold_button)
            Clock.schedule_interval(self.block_contingency, 0.1)
            return

        if self.current_hits >= self.block_max_length:
            self.feedback_start = time.time()
            self.protocol_floatlayout.remove_widget(self.hold_button)
            Clock.schedule_interval(self.block_contingency, 0.1)
            return

        if contingency == '0' and response == "1":
            self.current_correction = True
            self.center_stimulus_image_path = self.image_folder + self.center_image + '.png'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Center Image', 'Value', str(self.center_image),
                 '', '', '', ''])
            return
        elif contingency == '2':
            self.center_stimulus_image_path = self.image_folder + self.center_image + '.png'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Center Image', 'Value', str(self.center_image),
                 '', '', '', ''])
            return
        else:
            self.current_correction = False
            if self.stage_index == 0:
                self.center_image = self.training_image
            elif self.stage_index == 1:
                self.center_image = np.random.choice(a=self.total_image_list, size=None, p=self.image_prob_list)
            self.center_stimulus_image_path = self.image_folder + self.center_image + '.png'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Center Image', 'Value', str(self.center_image),
                 '', '', '', ''])
            self.center_stimulus.source = self.center_stimulus_image_path

    def block_contingency(self, *args):

        if self.feedback_on_screen == True:
            curr_time = time.time()
            if (curr_time - self.feedback_start) >= self.feedback_length:
                Clock.unschedule(self.block_contingency)
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_string = ''
                self.feedback_label.text = self.feedback_string
                self.feedback_on_screen = False
            else:
                return
        else:
            Clock.unschedule(self.block_contingency)

        self.protocol_floatlayout.clear_widgets()

        self.current_block += 1
        self.current_hits = 0

        if (self.current_block > self.block_max_count) or self.stage_index == 0:
            self.stage_index += 1
            self.current_block = 1
            self.current_stage = self.stage_list[self.stage_index]
            if self.stage_index == 2 and self.stimulus_duration_probe_active == False:
                self.stage_index += 1
            if self.stage_index == 3 and self.flanker_probe_active == False:
                Clock.unschedule(self.clock_monitor)
                self.protocol_end()
                return

        self.block_screen()

    # Time Monitor Functions #
    def start_clock(self, *args):
        self.start_time = time.time()
        Clock.schedule_interval(self.clock_monitor, 0.1)
        Clock.schedule_interval(self.display_monitor, 0.1)

    def clock_monitor(self, *args):
        self.current_time = time.time()
        self.elapsed_time = self.current_time - self.start_time
        self.protocol_floatlayout.elapsed_time = self.elapsed_time

        if self.elapsed_time > self.session_length_max:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()

    def display_monitor(self, *args):
        width = self.protocol_floatlayout.width
        height = self.protocol_floatlayout.height

        self.screen_ratio = width / height
            
    def record_touch_event(self,event_type):
        self.protocol_floatlayout.add_event([self.elapsed_time, 'Screen',event_type,'X Position',
                                    self.protocol_floatlayout.touch_pos[0],'Y Position',self.protocol_floatlayout.touch_pos[1],'Stimulus Name',self.protocol_floatlayout.held_name])
        
        