# Imports #
import sys
import os
import configparser
import time
import numpy as np
import pandas as pd
import csv
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from Classes.Protocol import ImageButton, ProtocolBase

class ProtocolScreen(ProtocolBase):
    def __init__(self, screen_resolution, **kwargs):
        super(ProtocolScreen, self).__init__(**kwargs)
        self.protocol_name = 'iCPT2GStim1'
        self.update_task()
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

        # Define Data Columns
        self.data_cols = ['TrialNo','Stage','Sub Stage','Block #','Trial Type','Correction Trial','Response',
                          'Contingency','Outcome','Response Latency']
        self.metadata_cols = ['participant_id', 'training_image', 'correct_images',
                         'incorrect_images', 'stimulus_duration', 'limited_hold',
                         'target_probability', 'iti_length', 'feedback_length',
                         'block_max_length', 'block_max_count', 'block_min_rest_duration',
                         'session_length_max', 'session_trial_max']
        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + self.protocol_name + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        self.parameters_dict = config_file['TaskParameters']
        self.probability_probe_low_active = self.parameters_dict['probability_probe_low ']
        if self.probability_probe_low_active == 'Enabled':
            self.probability_probe_low_active = True
        else:
            self.probability_probe_low_active = False

        self.probability_probe_mid_active = self.parameters_dict['probability_probe_mid ']
        if self.probability_probe_mid_active == 'Enabled':
            self.probability_probe_mid_active = True
        else:
            self.probability_probe_mid_active = False

        self.probability_probe_high_active = self.parameters_dict['probability_probe_high ']
        if self.probability_probe_hugh_active == 'Enabled':
            self.probability_probe_low_active = True
        else:
            self.probability_probe_low_active = False
        self.stimulus_duration = float(self.parameters_dict['probability_probe_stimulus_duration'])
        self.limited_hold = float(self.parameters_dict['probability_probe_limited_hold'])
        self.target_probability = float(self.parameters_dict['probability_probe_low_prob'])
        self.iti_length = float(self.parameters_dict['probability_iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.training_image = self.parameters_dict['training_image']
        self.block_max_length = int(self.parameters_dict['probability_probe_length'])
        self.block_max_count = int(self.parameters_dict['probability_probe_low_block_count'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = float(self.parameters_dict['session_trial_max'])

        self.probability_probe_mid_prob = float(self.parameters_dict['probability_probe_mid_prob'])
        self.probability_probe_mid_block_count = int(self.parameters_dict['probability_probe_low_block_count'])
        self.probability_probe_high_prob = float(self.parameters_dict['probability_probe_mid_prob'])
        self.probability_probe_high_block_count = int(self.parameters_dict['probability_probe_low_block_count'])

        self.flanker_probe_active = self.parameters_dict['flanker_probe']
        if self.flanker_probe_active == "Enabled":
            self.flanker_probe_active = True
        else:
            self.flanker_probe_active = False
        self.flanker_probe_stimulus_duration = float(self.parameters_dict['flanker_probe_stimulus_duration'])
        self.flanker_probe_limited_hold = float(self.parameters_dict['flanker_probe_limited_hold'])
        self.flanker_probe_target_probability = float(self.parameters_dict['flanker_probe_prob'])
        self.flanker_probe_iti_length = float(self.parameters_dict['flanker_probe_iti_length'])
        self.flanker_probe_block_length = int(self.parameters_dict['flanker_probe_block_length'])
        self.flanker_probe_block_count = int(self.parameters_dict['flanker_probe_block_count'])

        self.stimulus_duration_probe_active = self.parameters_dict['stimulus_duration_probe']
        if self.stimulus_duration_probe_active == 'Enabled':
            self.stimulus_duration_probe_active = True
        else:
            self.stimulus_duration_probe_active = False
        self.stimulus_duration_probe_stimulus_list = self.parameters_dict['stimulus_duration_probe_stimulus_durations']
        self.stimulus_duration_list = self.stimulus_duration_list.split(',')
        self.stimulus_duration_list = [eval(i) for i in self.stimulus_duration_list]
        self.stimulus_duration_probe_limited_hold_list = self.parameters_dict['stimulus_duration_probe_limited_holds']
        self.stimulus_duration_probe_limited_hold_list = self.limited_hold_list.split(',')
        self.stimulus_duration_probe_limited_hold_list = [eval(i) for i in self.limited_hold_list]
        self.stimulus_duration_probe_target_probability = float(self.parameters_dict['stimulus_duration_probe_prob'])
        self.stimulus_duration_probe_iti_length = float(self.parameters_dict['stimulus_duration_probe_iti_length'])
        self.stimulus_duration_block_length = int(self.parameters_dict['stimulus_duration_probe_block_length'])
        self.stimulus_duration_block_count = int(self.parameters_dict['stimulus_duration_probe_block_count'])


        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        # Define Language
        self.language = 'English'
        self.set_language(self.language)


        # Define Variables - List
        self.stage_list = ['Probability Low','Probability Medium', 'Probability High', 'Flanker', 'Stimulus Duration']
        self.correct_images = os.listdir(self.image_folder + 'Probability Probe' + self.folder_mod + 'Low' +
                                          self.folder_mod + 'Target' + self.folder_mod)
        self.incorrect_images = os.listdir(self.image_folder + 'Probability Probe' + self.folder_mod + 'Low' +
                                            self.folder_mod + 'NonTarget' + self.folder_mod)
        self.total_image_list = self.correct_images + self.incorrect_images

        # Define Variables - Boolean
        self.current_correction = False

        # Define Variables - Count
        self.current_hits = 0
        self.current_misses = 0
        self.current_mistakes = 0
        self.current_correct_rejections = 0
        self.trial_outcome = 1  # 1-Hit,2-Miss,3-Mistake,4-Correct Rejection,5-Premature

        # Define Variables - String
        self.center_image = ''
        self.current_stage = self.stage_list[self.stage_index]
        self.current_substage = ''

        # Define Variables - Time
        self.start_stimulus = 0
        self.response_lat = 0

        # Define Variables - Trial Configurations
        distractor_prob = 1 - self.target_probability
        target_prob_single = self.target_probability / len(self.correct_images)
        distractor_prob_single = distractor_prob / len(self.incorrect_images)
        self.image_prob_list = list()
        for a in range(0, len(self.correct_images)):
            self.image_prob_list.append(target_prob_single)
        for a in range(0, len(self.incorrect_images)):
            self.image_prob_list.append(distractor_prob_single)
        

        # Define Variables - Stimulus Duration Probe
        self.stimulus_duration_list += self.stimulus_duration_list
        self.limited_hold_list += self.limited_hold_list
        self.stimulus_duration_pos = 0
        self.stimulus_duration_index_list = np.random.choice(len(self.stimulus_duration_list),len(self.stimulus_duration_list),replace=False)
        
        # Define Variables - Flanker Probe
        self.distractor_stage = 'No Distractor'
        self.distractor = ''
        self.distractor_stage_list = ['No Distractor','Congruent Distractor','Incongruent Distractor','No Distractor','Congruent Distractor','Incongruent Distractor']
        self.distractor_stage_pos = 0
        self.distractor_stage_index_list = np.random.choice(len(self.distractor_stage_list),len(self.distractor_stage_list),replace=False)
        
        # Define Variables - Probability Probe
        self.probability_high_list = list()
        high_distract_prob = 1 - self.probabilty_probe_high
        high_target_prob_single = self.probabilty_probe_high / len(self.correct_images)
        high_distract_prob_single = high_distract_prob / len(self.incorrect_images)
        for a in range(0, len(self.correct_images)):
            self.probability_high_list.append(high_target_prob_single)
        for a in range(0, len(self.incorrect_images)):
            self.probability_high_list.append(high_distract_prob_single)

        self.probability_mid_list = list()
        mid_distract_prob = 1 - self.probabilty_probe_mid
        mid_target_prob_single = self.probabilty_probe_mid / len(self.correct_images)
        mid_distract_prob_single = mid_distract_prob / len(self.incorrect_images)
        for a in range(0, len(self.correct_images)):
            self.probability_mid_list.append(mid_target_prob_single)
        for a in range(0, len(self.incorrect_images)):
            self.probability_mid_list.append(mid_distract_prob_single)

        self.probability_low_list = list()
        low_distract_prob = 1 - self.probabilty_probe_low
        low_target_prob_single = self.probabilty_probe_low / len(self.correct_images)
        low_distract_prob_single = low_distract_prob / len(self.incorrect_images)
        for a in range(0, len(self.correct_images)):
            self.probability_low_list.append(low_target_prob_single)
        for a in range(0, len(self.incorrect_images)):
            self.probability_low_list.append(low_distract_prob_single)


        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path


        self.center_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.center_stimulus = ImageButton(source=self.center_stimulus_image_path)
        self.center_stimulus.bind(on_press=self.center_pressed)

        self.left_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path)

        self.right_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path)

    def load_parameters(self, parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'iCPT2GStim1' + self.folder_mod + 'Configuration.ini'
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
        self.main_task_active = self.parameters_dict['main_task']
        if self.main_task_active == 'Enabled':
            self.main_task_active = True
        else:
            self.main_task_active = False
        self.stimulus_duration_probe_active = self.parameters_dict['stimulus_duration_probe']
        if self.stimulus_duration_probe_active == 'Enabled':
            self.stimulus_duration_probe_active = True
        else:
            self.stimulus_duration_probe_active = False
        self.stimulus_duration_list = self.parameters_dict['stimulus_durations_probe']
        self.stimulus_duration_list = self.stimulus_duration_list.split(',')
        self.stimulus_duration_list = [eval(i) for i in self.stimulus_duration_list]
        self.limited_hold_list = self.parameters_dict['limited_holds_probe']
        self.limited_hold_list = self.limited_hold_list.split(',')
        self.limited_hold_list = [eval(i) for i in self.limited_hold_list]
        self.flanker_probe_active = self.parameters_dict['flanker_probe']
        if self.flanker_probe_active == "Enabled":
            self.flanker_probe_active = True
        else:
            self.flanker_probe_active = False
        self.stimulus_duration_block_length = int(self.parameters_dict['stimulus_duration_probe_block_length'])
        self.stimulus_duration_block_count = int(self.parameters_dict['stimulus_duration_probe_block_count'])
        self.flanker_block_length = int(self.parameters_dict['flanker_probe_block_length'])
        self.flanker_block_count = int(self.parameters_dict['flanker_probe_block_count'])
        self.probability_probe_active = self.parameters_dict['probability_probe']
        if self.probability_probe_active == "Enabled":
            self.probability_probe_active = True
        else:
            self.probability_probe_active = False
        self.probabilty_probe_high = float(self.parameters_dict['probability_probe_high'])
        self.probabilty_probe_mid = float(self.parameters_dict['probability_probe_mid'])
        self.probabilty_probe_low = float(self.parameters_dict['probability_probe_low'])
        self.probabilty_probe_length = int(self.parameters_dict['probability_probe_length'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        # Define Language
        self.set_language(self.language)

        # Define Variables - List
        self.stage_list = ['Training', 'Main', 'Stimulus Duration Probe', 'Flanker Probe', 'Probability Probe']

        # Define Variables - Boolean
        self.current_correction = False

        # Define Variables - Count
        self.current_hits = 0
        self.trial_outcome = 1  # 1-Hit,2-Miss,3-Mistake,4-Correct Rejection,5-Premature

        # Define Variables - String
        self.center_image = self.training_image
        self.current_stage = self.stage_list[self.stage_index]
        self.protocol_floatlayout.add_event([0, 'Variable Change', 'Current Stage', 'Value', str(self.current_stage),
                                     '', '', '', ''])

        # Define Variables - Time
        self.start_stimulus = 0
        self.response_lat = 0

        # Define Variables - Trial Configurations
        distractor_prob = 1 - self.target_probability
        target_prob_single = self.target_probability / len(self.correct_images)
        distractor_prob_single = distractor_prob / len(self.incorrect_images)
        self.image_prob_list = list()
        for a in range(0, len(self.correct_images)):
            self.image_prob_list.append(target_prob_single)
        for a in range(0, len(self.incorrect_images)):
            self.image_prob_list.append(distractor_prob_single)
        
        # Define Variables - Stimulus Duration Probe
        self.stimulus_duration_list += self.stimulus_duration_list
        self.limited_hold_list += self.limited_hold_list
        self.stimulus_duration_index_list = np.random.choice(len(self.stimulus_duration_list),len(self.stimulus_duration_list),replace=False)
        self.stimulus_duration_pos = 0
        
        # Define Variables - Flanker Probe
        self.distractor_stage = 'No Distractor'
        self.distractor = ''
        self.distractor_stage_list = ['No Distractor','Congruent Distractor','Incongruent Distractor','No Distractor','Congruent Distractor','Incongruent Distractor']
        self.distractor_stage_pos = 0
        self.distractor_stage_index_list = np.random.choice(len(self.distractor_stage_list),len(self.distractor_stage_list),replace=False)

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path

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
        
        self.feedback_image_path = self.image_folder + 'Check.png'
        self.feedback_image = ImageButton(source=self.feedback_image_path)
        self.feedback_image.pos_hint = {"center_x": 0.5, "center_y": 0.7}

        self.present_instructions()

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

    def stimulus_presentation(self, *args):
        if not self.stimulus_on_screen:
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Stage Change', 'Display Stimulus', '', '',
                 '', '', '', ''])
            self.protocol_floatlayout.add_widget(self.center_stimulus)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Displayed', 'Center Stimulus', 'X Position', '1',
                 'Y Position', '1', 'Image Name', self.center_image])
            if self.stage_index == 3:
                self.protocol_floatlayout.add_widget(self.left_stimulus)
                self.left_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
                self.protocol_floatlayout.add_widget(self.right_stimulus)
                self.right_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
                self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Displayed', 'Left Stimulus', 'X Position', '0',
                 'Y Position', '1', 'Image Name', self.distractor])
                self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Displayed', 'Right Stimulus', 'X Position', '2',
                 'Y Position', '1', 'Image Name', self.distractor])
            self.center_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
            self.hold_button.bind(on_press=self.hold_returned_stim)
            self.hold_button.bind(on_release=self.hold_removed_stim)

            self.start_stimulus = time.time()

            self.stimulus_on_screen = True
            Clock.schedule_interval(self.stimulus_presentation, 0.1)

        else:
            if (time.time() - self.start_stimulus) > self.stimulus_duration:
                self.center_stimulus_image_path = self.image_folder + self.mask_image + '.png'
                self.center_stimulus.source = self.center_stimulus_image_path
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Image Displayed', 'Center Stimulus', 'X Position', '1',
                     'Y Position', '1', 'Image Name', self.mask_image])
                if self.stage_index == 3:
                    self.left_stimulus_image_path = self.image_folder + self.mask_image + '.png'
                    self.right_stimulus_image_path = self.image_folder + self.mask_image + '.png'
                    self.left_stimulus.source = self.left_stimulus_image_path
                    self.right_stimulus.source = self.right_stimulus_image_path
                    
                    self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Image Displayed', 'Left Stimulus', 'X Position', '0',
                    'Y Position', '1', 'Image Name', self.mask_image])
                    self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Image Displayed', 'Right Stimulus', 'X Position', '2',
                    'Y Position', '1', 'Image Name', self.mask_image])
            if (time.time() - self.start_stimulus) > self.limited_hold:
                Clock.unschedule(self.stimulus_presentation)
                self.protocol_floatlayout.remove_widget(self.center_stimulus)
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Image Removed', 'Center Stimulus', 'X Position', '1',
                     'Y Position', '1', 'Image Name', self.center_image])
                if self.stage_index == 3:
                    self.protocol_floatlayout.remove_widget(self.left_stimulus)
                    self.protocol_floatlayout.remove_widget(self.right_stimulus)
                    self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Image Removed', 'Left Stimulus', 'X Position', '0',
                    'Y Position', '1', 'Image Name', self.left_stimulus])
                    self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Image Removed', 'Right Stimulus', 'X Position', '2',
                    'Y Position', '1', 'Image Name', self.right_stimulus])
                self.stimulus_on_screen = False
                self.center_notpressed()

    def premature_response(self, *args):
        if self.stimulus_on_screen:
            return None

        Clock.unschedule(self.iti)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Premature Response', '', '',
             '', '', '', ''])
        self.feedback_string = self.feedback_dict['wait']
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
        self.write_trial(response, contingency)
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_string
        if not self.feedback_text_on_screen:
            self.protocol_floatlayout.add_widget(self.feedback_label)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
                 '', '', '', ''])
            self.feedback_text_on_screen = True
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)

    def return_hold(self):
        self.feedback_string = self.feedback_dict['return']
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
        if self.stage_index == 3:
            self.protocol_floatlayout.remove_widget(self.left_stimulus)
            self.protocol_floatlayout.remove_widget(self.right_stimulus)
            self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Left Stimulus', 'X Position', '0',
            'Y Position', '1', 'Image Name', self.left_stimulus])
            self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Right Stimulus', 'X Position', '2',
            'Y Position', '1', 'Image Name', self.right_stimulus])

        self.stimulus_on_screen = False
        self.response_lat = time.time() - self.start_stimulus
        self.response = '1'
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Response', 'Value', str(self.response),
             '', '', '', ''])
        if (self.center_image in self.correct_images) or (self.center_image == self.training_image):
            self.contingency = '1'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Contingency', 'Value', str(self.contingency),
                 '', '', '', ''])
            self.trial_outcome = '1'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Outcome', 'Value', str(self.trial_outcome),
                 '', '', '', ''])
            self.current_hits += 1
            self.feedback_image.size_hint = ((0.2 * self.width_adjust), (0.2 * self.height_adjust))
            self.protocol_floatlayout.add_widget(self.feedback_image)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
                 '', '', '', ''])
        else:
            self.trial_outcome = '3'
            self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Outcome', 'Value', str(self.trial_outcome),
             '', '', '', ''])
            self.contingency = '0'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Contingency', 'Value', str(self.contingency),
                 '', '', '', ''])
            self.current_mistakes += 1

        self.feedback_start_time = time.time()
        self.feedback_text_on_screen = True
        self.write_trial(self.response, self.contingency)
        self.trial_contingency()

        self.hold_button.unbind(on_press=self.hold_returned_stim)
        self.hold_button.unbind(on_release=self.hold_removed_stim)

        self.hold_button.bind(on_press=self.iti)

    def center_notpressed(self):
        self.response_lat = ''
        self.response = '0'
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Response', 'Value', str(self.response),
             '', '', '', ''])
        if (self.center_image in self.correct_images) or (self.center_image == self.training_image):
            self.feedback_string = ''
            self.contingency = '0'  #######
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Contingency', 'Value', str(self.contingency),
                 '', '', '', ''])
            self.trial_outcome = '2'  #####
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Outcome', 'Value', str(self.trial_outcome),
                 '', '', '', ''])
            self.current_misses += 1
        else:
            self.feedback_string = ''
            self.contingency = '1'  #####
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Contingency', 'Value', str(self.contingency),
                 '', '', '', ''])
            self.trial_outcome = '4'  ######
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Trial Outcome', 'Value', str(self.trial_outcome),
                 '', '', '', ''])
            self.current_correct_rejections += 1
        self.write_trial(self.response, self.contingency)
        self.trial_contingency()

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
    def write_trial(self, response, contingency):
        trial_data = [self.current_trial, self.current_stage, self.current_substage,self.current_block, self.center_image, int(self.current_correction),
        response, contingency, self.trial_outcome, self.response_lat]
        self.write_summary_file(trial_data)
        return

    # Trial Contingency Functions #

    def trial_contingency(self):
        self.current_trial += 1
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Current Trial', 'Value', str(self.current_trial),
             '', '', '', ''])

        if self.current_trial > self.session_trial_max:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()
            return

        if (self.current_hits >= 10) and (self.stage_index == 0):
            self.feedback_start = time.time()
            self.protocol_floatlayout.remove_widget(self.hold_button)
            Clock.schedule_interval(self.block_contingency, 0.1)
            return

        if self.current_hits >= self.block_max_length:
            self.feedback_start = time.time()
            self.protocol_floatlayout.remove_widget(self.hold_button)
            Clock.schedule_interval(self.block_contingency, 0.1)
            return

        if self.contingency == '0' and self.response == "1":
            self.current_correction = True
            self.center_stimulus_image_path = self.image_folder + self.center_image + '.png'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Center Image', 'Value', str(self.center_image),
                 '', '', '', ''])
            self.center_stimulus.source = self.center_stimulus_image_path
            return
        elif self.contingency == '2':
            self.center_stimulus_image_path = self.image_folder + self.center_image + '.png'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Center Image', 'Value', str(self.center_image),
                 '', '', '', ''])
            self.center_stimulus.source = self.center_stimulus_image_path
            return
        else:
            self.current_correction = False
            if self.stage_index == 0:
                self.center_image = self.training_image
            elif self.stage_index >= 1:
                self.center_image = np.random.choice(a=self.total_image_list, size=None, p=self.image_prob_list)
            self.center_stimulus_image_path = self.image_folder + self.center_image + '.png'
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Center Image', 'Value', str(self.center_image),
                 '', '', '', ''])
            self.center_stimulus.source = self.center_stimulus_image_path
            
        if self.stage_index == 2:
            self.stimulus_duration = self.stimulus_duration_list[self.stimulus_duration_index_list[self.stimulus_duration_pos]]
            self.current_substage = str(self.stimulus_duration)
            self.limited_hold = self.limited_hold_list[self.stimulus_duration_index_list[self.stim_duration_pos]]
            self.stimulus_duration_pos += 1
            if self.stimulus_duration_pos >= len(self.stimulus_duration_list):
                self.stimulus_duration_index_list = np.random.choice(len(self.stimulus_duration_list),4,replace=False)
                self.stimulus_duration_pos = 0
        
        if self.stage_index == 3:
            self.distractor_stage = self.distractor_stage_list[self.distractor_stage_index_list[self.distractor_stage_pos]]
            self.current_substage = self.distractor_stage
            if self.distractor_stage == 'No Distractor':
                self.left_stimulus_image_path = self.image_folder + 'black.png'
                self.right_stimulus_image_path = self.image_folder + 'black.png'
            elif self.distractor_stage == 'Congruent Distractor':
                self.left_stimulus_image_path = self.center_stimulus_image_path
                self.right_stimulus_image_path = self.center_stimulus_image_path
            elif self.distractor_stage == 'Incongruent Distractor':
                if self.center_image in self.correct_images:
                    self.distractor = np.random.choice(self.incorrect_images)
                else:
                    self.distractor = np.random.choice(self.correct_images)
                self.left_stimulus_image_path = self.image_folder + self.distractor + '.png'
                self.right_stimulus_image_path = self.image_folder + self.distractor + '.png'

            self.left_stimulus.source = self.left_stimulus_image_path
            self.right_stimulus.source = self.right_stimulus_image_path
            self.distractor_stage_pos += 1
            if self.distractor_stage_pos >= len(self.distractor_stage_list):
                self.distractor_stage_index_list = np.random.choice(len(self.distractor_stage_list),len(self.distractor_stage_list),replace=False)
                self.distractor_stage_pos = 0

    def block_contingency(self, *args):

        if self.feedback_text_on_screen == True:
            curr_time = time.time()
            if (curr_time - self.feedback_start) >= self.feedback_length:
                Clock.unschedule(self.block_contingency)
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_string = ''
                self.feedback_label.text = self.feedback_string
                self.feedback_text_on_screen = False
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
            self.current_substage = ''


            if self.stage_index == 1 and self.stimulus_duration_probe == False:
                self.stage_index += 1

            if self.stage_index == 2 and self.stimulus_duration_probe_active == False:
                self.stage_index += 1
            elif self.stage_index == 2 and self.stimulus_duration_probe_active == True:
                self.current_stage = self.stage_list[self.stage_index]
                self.block_max_count += self.stimulus_duration_block_count
                self.block_max_length = self.stimulus_duration_block_length
                
            if self.stage_index == 3 and self.flanker_probe_active == False:
                self.stage_index += 1
            elif self.stage_index == 3 and self.flanker_probe_active == True:
                self.current_stage = self.stage_list[self.stage_index]
                self.stimulus_duration = float(self.parameters_dict['stimulus_duration'])
                self.limited_hold = float(self.parameters_dict['limited_hold'])
                self.block_max_count += self.flanker_block_count
                self.block_max_length = self.flanker_block_length

            if self.stage_index == 4 and self.probability_probe_active == False:
                Clock.unschedule(self.clock_monitor)
                self.protocol_end()
                return
            elif self.stage_index == 4 and self.probability_probe_active == True:
                self.current_stage = self.stage_list[self.stage_index]
                self.probability_stage = self.probability_stage_list[self.probability_stage_index_list[self.probability_stage_pos]]
                self.probability_stage_pos += 1
                self.block_max_count += 3
                self.block_max_length = self.probabilty_probe_length
                if self.probability_stage == 'High Probability':
                    self.image_prob_list = self.probability_high_list
                elif self.probability_stage == 'Middle Probability':
                    self.image_prob_list = self.probability_mid_list
                elif self.probability_stage == 'Low Probability':
                    self.image_prob_list = self.probability_low_list
                self.current_substage = self.probability_stage

            if self.stage_index >= 5:
                Clock.unschedule(self.clock_monitor)
                self.protocol_end()
                return

        self.trial_contingency()
        self.block_screen()
        
        