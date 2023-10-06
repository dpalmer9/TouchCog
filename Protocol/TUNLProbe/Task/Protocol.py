# Imports #
import sys
import os
import configparser
import time
import numpy as np
import pandas as pd
import csv
import random
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from Classes.Protocol import ImageButton, ProtocolBase


def generate_sample_choice_pos():
    sample_xpos = random.randint(0, 7)
    sample_ypos = random.randint(0, 7)

    novel_xpos = random.randint(0, 7)
    novel_ypos = random.randint(0, 7)

    sample_pair = [sample_xpos, sample_ypos]
    novel_pair = [novel_xpos, novel_ypos]

    while sample_pair == novel_pair:
        novel_xpos = random.randint(0, 7)
        novel_ypos = random.randint(0, 7)
        novel_pair = [novel_xpos, novel_ypos]

    trial_coord = {'Sample': sample_pair, 'Choice': novel_pair}
    return trial_coord


def generate_trial_pos_sep(sep_level):
    base_move = 1
    main_move = base_move + sep_level
    sample_xpos = random.randint(0, 7)
    sample_ypos = random.randint(0, 7)
    sample_coord = [sample_xpos,sample_ypos]

    horz_move = [[(sample_xpos-main_move), sample_ypos],
                 [(sample_xpos+main_move), sample_ypos]]
    vert_move = [[sample_xpos, (sample_ypos - main_move)],
                 [sample_xpos, (sample_ypos + main_move)]]

    move_list = horz_move + vert_move
    final_list = list()
    while len(final_list) <= 0:
        for move in horz_move:
            for i in range(1, (main_move+1)):
                new_moves = [[move[0], move[1] - i], [move[0], move[1] + i]]
                move_list = move_list + new_moves
        for move in vert_move:
            for i in range(1, (main_move+1)):
                new_moves = [[move[0] - i, move[1]], [move[0] + i, move[1]]]
                move_list = move_list + new_moves
        for move in move_list:
            if (move[0] < 0) or (move[0] > 7) or (move[1] < 0) or (move[1] > 7):
                continue
            else:
                final_list.append(move)

        if len(final_list) <= 0:
            sample_xpos = random.randint(0, 7)
            sample_ypos = random.randint(0, 7)
            sample_coord = [sample_xpos, sample_ypos]

            horz_move = [[(sample_xpos - main_move), sample_ypos],
                         [(sample_xpos + main_move), sample_ypos]]
            vert_move = [[sample_xpos, (sample_ypos - main_move)],
                         [sample_xpos, (sample_ypos + main_move)]]

    novel_index = random.randint(0,(len(final_list) - 1))
    novel_coord = final_list[novel_index]

    trial_coord = {'Sample': sample_coord, 'Choice': novel_coord}

    return trial_coord


class ProtocolScreen(ProtocolBase):
    def __init__(self,screen_resolution,**kwargs):
        super(ProtocolScreen, self).__init__(**kwargs)
        self.protocol_name = 'TUNLProbe'
        self.update_task()
        width = screen_resolution[0]
        height = screen_resolution[1]
        self.size = screen_resolution
        self.protocol_floatlayout.size = screen_resolution
        self.screen_ratio = 1

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
        self.image_folder = 'Protocol' + self.folder_mod + 'TUNLProbe' + self.folder_mod + 'Image' + self.folder_mod
        self.data_output_path = None

        self.data_cols = ['TrialNo,Current Block','Probe Type,Separation','Delay','Sample_X','Sample_Y','Novel_X',
                          'Novel_Y','Num_Distractors','Correction Trial','Correct,Sample Latency','Choice Latency']

        self.metadata_cols = ['participant_id', 'stimulus_image', 'distractor_target_image',
                         'distractor_ignore_image', 'iti_length', 'session_length_max',
                         'session_trial_max', 'space_probe_block_length', 'space_probe_easy_sep',
                         'space_probe_med_sep', 'space_probe_hard_sep', 'space_probe_distract_target_count',
                         'space_probe_distract_distractor_count', 'space_probe_delay_length', 'delay_probe_block_length',
                         'delay_probe_target_count', 'delay_probe_distractor_count', 'delay_probe_easy_delay_length',
                         'delay_probe_med_delay_length', 'delay_probe_hard_delay_length', 'delay_probe_sep']

        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + 'TUNLProbe' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        self.parameters_dict = config_file['TaskParameters']

        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.stimulus_image = self.parameters_dict['stimulus_image']
        self.distractor_ignore_image = self.parameters_dict['distractor_ignore_image']
        self.distractor_target_image = self.parameters_dict['distractor_target_image']
        self.space_probe_block_length = int(self.parameters_dict['space_probe_block_length'])
        self.space_probe_easy_sep = int(self.parameters_dict['space_probe_easy_sep'])
        self.space_probe_med_sep = int(self.parameters_dict['space_probe_med_sep'])
        self.space_probe_hard_sep = int(self.parameters_dict['space_probe_hard_sep'])
        self.space_probe_distract_target_count = int(self.parameters_dict['space_probe_distract_target_count'])
        self.space_probe_distract_distractor_count = int(self.parameters_dict['space_probe_distract_distractor_count'])
        self.space_probe_delay_length = float(self.parameters_dict['space_probe_delay_length'])
        cond_count = int(self.space_probe_block_length / 3)
        self.space_probe_trial_list = list()
        self.space_probe_trial_list += cond_count * [self.space_probe_easy_sep]
        self.space_probe_trial_list += cond_count * [self.space_probe_med_sep]
        self.space_probe_trial_list += cond_count * [self.space_probe_hard_sep]
        random.shuffle(self.space_probe_trial_list)
        self.current_space_trial_index = 0
        self.current_sep = self.space_probe_trial_list[self.current_space_trial_index]
        self.current_delay = self.space_probe_delay_length
        self.current_space_trial_index += 1

        self.delay_probe_block_length = int(self.parameters_dict['delay_probe_block_length'])
        self.delay_probe_target_count = int(self.parameters_dict['delay_probe_target_count'])
        self.delay_probe_distractor_count = int(self.parameters_dict['delay_probe_distractor_count'])
        self.delay_probe_easy_delay_length = float(self.parameters_dict['delay_probe_easy_delay_length'])
        self.delay_probe_med_delay_length = float(self.parameters_dict['delay_probe_med_delay_length'])
        self.delay_probe_hard_delay_length = float(self.parameters_dict['delay_probe_hard_delay_length'])
        self.delay_probe_sep = int(self.parameters_dict['delay_probe_sep'])
        cond_count = int(self.delay_probe_block_length / 3)
        self.delay_probe_trial_list = list()
        self.delay_probe_trial_list += cond_count * [self.delay_probe_easy_delay_length]
        self.delay_probe_trial_list += cond_count * [self.delay_probe_med_delay_length]
        self.delay_probe_trial_list += cond_count * [self.delay_probe_hard_delay_length]
        random.shuffle(self.delay_probe_trial_list)
        self.current_delay_trial_index = 0

        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.block_trial_break = float(self.parameters_dict['block_trial_break'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']
        self.block_threshold = self.block_min_rest_duration

        # Define Boolean
        self.sample_completed = False

        # Define Numeric
        self.distractor_press_count = 0
        self.current_correction = 0

        # Define Language
        self.language = 'English'
        self.set_language(self.language)

        # Define Variables - Coordinates
        self.trial_coord = generate_trial_pos_sep(self.current_sep)
        self.distractor_target_list, self.distractor_ignore_list = \
            self.generate_distractor_pos(self.space_probe_distract_target_count,
                                         self.space_probe_distract_distractor_count)

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source =self.hold_button_image_path

        self.x_dim_hint = np.linspace(0.3, 0.7, 8)
        self.x_dim_hint = self.x_dim_hint.tolist()
        self.y_dim_hint = np.linspace(0.915,0.215,8)
        self.stimulus_image_path = self.image_folder + self.stimulus_image + '.png'
        self.mask_image_path = self.image_folder + self.mask_image + '.png'
        self.background_grid_list = [Image() for _ in range(64)]
        x_pos = 0
        y_pos = 0
        for cell in self.background_grid_list:
            cell.fit_mode = 'fill'
            cell.size_hint = ((.08 * self.width_adjust), (.08 * self.height_adjust))
            if x_pos > 7:
                x_pos = 0
                y_pos = y_pos + 1
            cell.pos_hint = {"center_x": self.x_dim_hint[x_pos], "center_y": self.y_dim_hint[y_pos]}
            cell.source = self.mask_image_path
            x_pos = x_pos + 1

        self.sample_image_button = ImageButton(source=self.stimulus_image_path)
        self.sample_image_button.bind(on_press=self.sample_pressed)

        self.novel_image_button = ImageButton(source=self.stimulus_image_path)
        self.novel_image_button.bind(on_press=self.novel_pressed)

        self.distractor_target_button_list = list()
        self.distractor_target_image_path = self.image_folder + self.distractor_target_image + '.png'

        for coord in self.distractor_target_list:
            index = 0
            image = ImageButton(source=self.distractor_target_image_path)
            image.coord = coord
            image.bind(on_press=lambda instance: self.distractor_target_press(instance, index))
            self.distractor_target_button_list.append(image)

        self.distractor_ignore_button_list = list()
        self.distractor_ignore_image_path = self.image_folder + self.distractor_ignore_image + '.png'

        for coord in self.distractor_ignore_list:
            image = ImageButton(source=self.distractor_ignore_image_path)
            image.coord = coord
            self.distractor_ignore_button_list.append(image)


    # Initialization Functions

    def load_parameters(self, parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'TUNLProbe' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        self.participant_id = self.parameters_dict['participant_id']
        self.language = self.parameters_dict['language']

        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.stimulus_image = self.parameters_dict['stimulus_image']
        self.distractor_ignore_image = self.parameters_dict['distractor_ignore_image']
        self.distractor_target_image = self.parameters_dict['distractor_target_image']
        self.space_probe_block_length = int(self.parameters_dict['space_probe_block_length'])
        self.space_probe_easy_sep = int(self.parameters_dict['space_probe_easy_sep'])
        self.space_probe_med_sep = int(self.parameters_dict['space_probe_med_sep'])
        self.space_probe_hard_sep = int(self.parameters_dict['space_probe_hard_sep'])
        self.space_probe_distract_target_count = int(self.parameters_dict['space_probe_distract_target_count'])
        self.space_probe_distract_distractor_count = int(self.parameters_dict['space_probe_distract_distractor_count'])
        self.space_probe_delay_length = float(self.parameters_dict['space_probe_delay_length'])
        cond_count = int(self.space_probe_block_length / 3)
        self.space_probe_trial_list = list()
        self.space_probe_trial_list += cond_count * [self.space_probe_easy_sep]
        self.space_probe_trial_list += cond_count * [self.space_probe_med_sep]
        self.space_probe_trial_list += cond_count * [self.space_probe_hard_sep]
        random.shuffle(self.space_probe_trial_list)
        self.current_space_trial_index = 0
        self.current_sep = self.space_probe_trial_list[self.current_space_trial_index]
        self.protocol_floatlayout.add_event([0, 'Variable Change', 'Current Separation', 'Value', str(self.current_sep),
                                     '', '', '', ''])
        self.current_delay = self.space_probe_delay_length
        self.protocol_floatlayout.add_event([0, 'Variable Change', 'Current Delay', 'Value', str(self.current_delay),
                                     '', '', '', ''])
        self.current_space_trial_index += 1

        self.delay_probe_block_length = int(self.parameters_dict['delay_probe_block_length'])
        self.delay_probe_target_count = int(self.parameters_dict['delay_probe_target_count'])
        self.delay_probe_distractor_count = int(self.parameters_dict['delay_probe_distractor_count'])
        self.delay_probe_easy_delay_length = float(self.parameters_dict['delay_probe_easy_delay_length'])
        self.delay_probe_med_delay_length = float(self.parameters_dict['delay_probe_med_delay_length'])
        self.delay_probe_hard_delay_length = float(self.parameters_dict['delay_probe_hard_delay_length'])
        self.delay_probe_sep = int(self.parameters_dict['delay_probe_sep'])
        cond_count = int(self.delay_probe_block_length / 3)
        self.delay_probe_trial_list = list()
        self.delay_probe_trial_list += cond_count * [self.delay_probe_easy_delay_length]
        self.delay_probe_trial_list += cond_count * [self.delay_probe_med_delay_length]
        self.delay_probe_trial_list += cond_count * [self.delay_probe_hard_delay_length]
        random.shuffle(self.delay_probe_trial_list)

        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.block_trial_break = float(self.parameters_dict['block_trial_break'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']
        self.block_threshold = self.block_trial_break

        self.correction_trial_enabled_str = str(self.parameters_dict['correction_trials'])
        if self.correction_trial_enabled_str == 'Correction Trials Enabled':
            self.correction_trial_enabled = True
        else:
            self.correction_trial_enabled = False

        # Define Language
        self.set_language(self.language)

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path

        self.x_dim_hint = np.linspace(0.3, 0.7, 8)
        self.x_dim_hint = self.x_dim_hint.tolist()
        self.y_dim_hint = [0.915, 0.815, 0.715, 0.615, 0.515, 0.415, 0.315, 0.215]
        self.stimulus_image_path = self.image_folder + self.stimulus_image + '.png'
        self.mask_image_path = self.image_folder + self.mask_image + '.png'
        self.background_grid_list = [Image() for _ in range(64)]
        x_pos = 0
        y_pos = 0
        for cell in self.background_grid_list:
            cell.fit_mode = 'fill'
            cell.size_hint = ((.08 * self.width_adjust), (.08 * self.height_adjust))
            if x_pos > 7:
                x_pos = 0
                y_pos = y_pos + 1
            cell.pos_hint = {"center_x": self.x_dim_hint[x_pos], "center_y": self.y_dim_hint[y_pos]}
            cell.source = self.mask_image_path
            x_pos = x_pos + 1

        self.sample_image_button = ImageButton(source=self.stimulus_image_path)
        self.sample_image_button.pos_hint = {"center_x": self.x_dim_hint[self.trial_coord['Sample'][0]],
                                             "center_y": self.y_dim_hint[self.trial_coord['Sample'][1]]}
        self.sample_image_button.bind(on_press=self.sample_pressed)
        self.sample_image_button.size_hint = (None, None)
        self.sample_image_button.name = 'Sample Image'

        self.novel_image_button = ImageButton(source=self.stimulus_image_path)
        self.novel_image_button.pos_hint = {"center_x": self.x_dim_hint[self.trial_coord['Choice'][0]],
                                            "center_y": self.y_dim_hint[self.trial_coord['Choice'][1]]}
        self.novel_image_button.bind(on_press=self.novel_pressed)
        self.novel_image_button.size_hint = (None, None)
        self.novel_image_button.name = 'Novel Image'

        self.distractor_target_button_list = list()
        self.distractor_target_image_path = self.image_folder + self.distractor_target_image + '.png'

        for coord in self.distractor_target_list:
            index = 0
            image = ImageButton(source=self.distractor_target_image_path)
            image.coord = coord
            image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
            image.bind(on_press=lambda instance: self.distractor_target_press(instance, index))
            image.size_hint = (None, None)
            image.name = 'Distractor Target'
            self.distractor_target_button_list.append(image)

        self.distractor_ignore_button_list = list()
        self.distractor_ignore_image_path = self.image_folder + self.distractor_ignore_image + '.png'

        for coord in self.distractor_ignore_list:
            image = ImageButton(source=self.distractor_ignore_image_path)
            image.coord = coord
            image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
            image.size_hint = (None, None)
            image.name = 'Distractor Ignore'
            self.distractor_ignore_button_list.append(image)

        self.present_instructions()

    def generate_distractor_pos(self, n_target, n_distractor):
        target_list = list()
        distractor_list = list()
        for a in range(n_target):
            x = random.randint(0, 7)
            y = random.randint(0, 7)
            coord = [x, y]
            while (coord in self.trial_coord.values()) or (coord in target_list):
                x = random.randint(0, 7)
                y = random.randint(0, 7)
                coord = [x, y]
            target_list.append(coord)

        for a in range(n_distractor):
            x = random.randint(0, 7)
            y = random.randint(0, 7)
            coord = [x, y]
            while (coord in self.trial_coord.values()) or (coord in target_list) or (coord in distractor_list):
                x = random.randint(0, 7)
                y = random.randint(0, 7)
                coord = [x, y]
            distractor_list.append(coord)
        return target_list, distractor_list


    # Protocol Staging
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
        self.hold_button.size_hint = ((0.1 * self.width_adjust), (0.1 * self.height_adjust))
        for image_wid in self.background_grid_list:
            self.protocol_floatlayout.add_widget(image_wid)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Displayed', 'Grid Array', '', '',
             '', '', '', ''])
        self.feedback_label.text = self.feedback_string
        self.hold_button.pos_hint = {"center_x": 0.5, "center_y": 0.1}
        self.hold_button.bind(on_press=self.iti)


    # Delay Period
    def delay_period(self,*args):
        delay_length = time.time() - self.sample_touch_time
        if delay_length > self.current_delay:
            Clock.unschedule(self.delay_period)
            self.choice_presentation()

    # Display Sample Stimuli
    def stimulus_presentation(self, *args):
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Display Sample', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_widget(self.sample_image_button)
        self.sample_image_button.size_hint = ((0.08 * self.width_adjust), (0.08 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Displayed', 'Sample Image', 'X Position', self.trial_coord['Sample'][0],
             'Y Position', self.trial_coord['Sample'][1], 'Image Name', self.stimulus_image])
        self.start_sample = time.time()
        self.stimulus_on_screen = True

    # Display Distractor During Delay
    def delay_presentation(self):
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Delay Start', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.remove_widget(self.sample_image_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Sample Image', 'X Position', self.trial_coord['Sample'][0],
             'Y Position', self.trial_coord['Sample'][1], 'Image Name', self.stimulus_image])

        for image in self.distractor_ignore_button_list:
            self.protocol_floatlayout.add_widget(image)
            image.size_hint = ((0.08 * self.width_adjust), (0.08 * self.height_adjust))
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Displayed', 'Distractor Ignore Image', 'X Position', image.coord[0],
                 'Y Position', image.coord[1], 'Image Name', self.distractor_ignore_image])

        for image in self.distractor_target_button_list:
            self.protocol_floatlayout.add_widget(image)
            image.size_hint = ((0.08 * self.width_adjust), (0.08 * self.height_adjust))
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Displayed', 'Distractor Target Image', 'X Position', image.coord[0],
                 'Y Position', image.coord[1], 'Image Name', self.distractor_target_image])

        Clock.schedule_interval(self.delay_period,0.01)

    # Display Sample and Novel Stimuli
    def choice_presentation(self, *args):
        for image in self.distractor_ignore_button_list:
            self.protocol_floatlayout.remove_widget(image)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Removed', 'Distractor Ignore Image', 'X Position', image.coord[0],
                 'Y Position', image.coord[1], 'Image Name', self.distractor_ignore_image])
        for image in self.distractor_target_button_list:
            self.protocol_floatlayout.remove_widget(image)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Removed', 'Distractor Target Image', 'X Position', image.coord[0],
                 'Y Position', image.coord[1], 'Image Name', self.distractor_target_image])

        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Display Choice', '', '',
             '', '', '', ''])
        self.choice_start = time.time()
        self.delay_length = self.choice_start - self.sample_touch_time
        self.protocol_floatlayout.add_widget(self.sample_image_button)
        self.protocol_floatlayout.add_widget(self.novel_image_button)
        self.sample_image_button.size_hint = ((0.08 * self.width_adjust), (0.08 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Displayed', 'Sample Image', 'X Position', self.trial_coord['Sample'][0],
             'Y Position', self.trial_coord['Sample'][1], 'Image Name', self.stimulus_image])
        self.novel_image_button.size_hint = ((0.08 * self.width_adjust), (0.08 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Displayed', 'Novel Image', 'X Position', self.trial_coord['Choice'][0],
             'Y Position', self.trial_coord['Choice'][1], 'Image Name', self.stimulus_image])

    # Stimuli Pressed too early
    def premature_response(self, *args):
        # return
        if self.stimulus_on_screen is True:
            return None

        Clock.unschedule(self.iti)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Premature Response', '', '',
             '', '', '', ''])
        self.feedback_string = self.feedback_dict['wait']
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_string
        if self.feedback_on_screen is False:
            self.protocol_floatlayout.add_widget(self.feedback_label)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
                 '', '', '', ''])
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)

    # Sample Stimuli Pressed during Choice
    def sample_pressed(self, *args):
        if self.sample_completed is False:
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Stage Change', 'Sample Pressed', '', '',
                 '', '', '', ''])
            self.sample_completed = True
            self.sample_touch_time = time.time()
            self.sample_lat = self.sample_touch_time - self.start_sample
            self.delay_presentation()
            return
        elif self.sample_completed is True:
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Stage Change', 'Incorrect Response', '', '',
                 '', '', '', ''])
            self.choice_touch_time = time.time()
            self.sample_press_to_choice = self.choice_touch_time - self.sample_touch_time
            self.choice_lat = self.choice_touch_time - self.choice_start
            self.protocol_floatlayout.remove_widget(self.sample_image_button)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Removed', 'Sample Image', 'X Position', self.trial_coord['Sample'][0],
                 'Y Position', self.trial_coord['Sample'][1], 'Image Name', self.stimulus_image])
            self.protocol_floatlayout.remove_widget(self.novel_image_button)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Image Removed', 'Novel Image', 'X Position', self.trial_coord['Choice'][0],
                 'Y Position', self.trial_coord['Choice'][1], 'Image Name', self.stimulus_image])
            self.feedback_string = self.feedback_dict['incorrect']
            self.feedback_label.text = self.feedback_string
            self.current_correct = 0
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Current Correct', 'Value', str(self.current_correction),
                 '', '', '', ''])
            self.write_summary_file()

            self.protocol_floatlayout.add_widget(self.feedback_label)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
                 '', '', '', ''])
            self.feedback_on_screen = True
            self.hold_button.bind(on_press=self.iti)
            self.sample_completed = False

            if self.correction_trial_enabled:
                self.current_correction = 1
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Variable Change', 'Current Correction', 'Value', str(self.current_correction),
                     '', '', '', ''])
                if self.current_probe == 'Spatial':
                    self.distractor_target_list, self.distractor_ignore_list = \
                        self.generate_distractor_pos(self.space_probe_distract_target_count,
                                                     self.space_probe_distract_distractor_count)
                elif self.current_probe == 'Delay':
                    self.distractor_target_list, self.distractor_ignore_list = \
                        self.generate_distractor_pos(self.delay_probe_target_count,
                                                     self.delay_probe_distractor_count)
                self.distractor_target_button_list = list()
                for coord in self.distractor_target_list:
                    index = 0
                    image = ImageButton(source=self.distractor_target_image_path)
                    image.coord = coord
                    image.size_hint = ((0.08 * self.screen_ratio), 0.08)
                    image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
                    image.bind(on_press=lambda instance: self.distractor_target_press(instance, index))
                    image.size_hint = (None, None)
                    self.distractor_target_button_list.append(image)

                self.distractor_ignore_button_list = list()
                for coord in self.distractor_ignore_list:
                    image = ImageButton(source=self.distractor_ignore_image_path, allow_stretch=True)
                    image.coord = coord
                    image.size_hint = ((0.08 * self.screen_ratio), 0.08)
                    image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
                    image.size_hint = (None, None)
                    self.distractor_ignore_button_list.append(image)
            else:
                self.current_correction = 0
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Variable Change', 'Current Correction', 'Value', str(self.current_correction),
                     '', '', '', ''])
                self.trial_contingency()


            return

    # Novel Stimuli Pressed during Choice
    def novel_pressed(self, *args):
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Correct Response', '', '',
             '', '', '', ''])
        self.choice_touch_time = time.time()
        self.sample_press_to_choice = self.choice_touch_time - self.sample_touch_time
        self.choice_lat = self.choice_touch_time - self.choice_start
        self.protocol_floatlayout.remove_widget(self.sample_image_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Sample Image', 'X Position', self.trial_coord['Sample'][0],
             'Y Position', self.trial_coord['Sample'][1], 'Image Name', self.stimulus_image])
        self.protocol_floatlayout.remove_widget(self.novel_image_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Novel Image', 'X Position', self.trial_coord['Choice'][0],
             'Y Position', self.trial_coord['Choice'][1], 'Image Name', self.stimulus_image])
        self.feedback_string = self.feedback_dict['correct']
        self.feedback_label.text = self.feedback_string
        self.current_correct = 1
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Current Correct', 'Value', str(self.current_correction),
             '', '', '', ''])
        self.write_summary_file()
        self.current_correction = 0
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Current Correction', 'Value', str(self.current_correction),
             '', '', '', ''])
        self.trial_contingency()
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.hold_button.bind(on_press=self.iti)
        self.sample_completed = False
        return

    # Distractor pressed during Choice
    def distractor_target_press(self, instance, *args):
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Distractor Target Pressed', '', '',
             '', '', '', ''])
        touch_coord = instance.coord
        distract_index = random.randint(0, (len(self.distractor_ignore_list) - 1))
        old_coord = [touch_coord,self.distractor_ignore_list[distract_index]]

        self.protocol_floatlayout.remove_widget(instance)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Distractor Target', 'X Position', touch_coord[0],
             'Y Position', touch_coord[1], 'Image Name', self.distractor_target_image])
        self.protocol_floatlayout.remove_widget(self.distractor_ignore_button_list[distract_index])
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Distractor Ignore', 'X Position',
             self.distractor_ignore_button_list[distract_index].coord[0],
             'Y Position', self.distractor_ignore_button_list[distract_index].coord[1], 'Image Name',
             self.distractor_ignore_image])
        del self.distractor_target_button_list[self.distractor_target_list.index(touch_coord)]
        del self.distractor_ignore_button_list[distract_index]
        self.distractor_target_list.remove(touch_coord)
        del self.distractor_ignore_list[distract_index]

        new_target_x = random.randint(0, 7)
        new_target_y = random.randint(0, 7)
        new_distract_x = random.randint(0, 7)
        new_distract_y = random.randint(0, 7)
        new_target = [new_target_x, new_target_y]
        new_distract = [new_distract_x, new_distract_y]
        target_new = False
        distract_new = False

        while target_new is False:
            if (new_target in self.trial_coord.values()) or (new_target in self.distractor_target_list) or \
                    (new_target in self.distractor_ignore_list) or (new_target in old_coord):
                new_target_x = random.randint(0, 7)
                new_target_y = random.randint(0, 7)
                new_target = [new_target_x, new_target_y]
            else:
                target_new = True

        self.distractor_target_list.append(new_target)

        while distract_new is False:
            if (new_distract in self.trial_coord.values()) or (new_distract in self.distractor_target_list) or \
                    (new_distract in self.distractor_ignore_list) or (new_target in old_coord):
                new_distract_x = random.randint(0, 7)
                new_distract_y = random.randint(0, 7)
                new_distract = [new_distract_x, new_distract_y]
            else:
                distract_new = True
        self.distractor_ignore_list.append(new_distract)

        index = 0
        image = ImageButton(source=self.distractor_target_image_path, allow_stretch=True)
        image.coord = new_target
        image.size_hint = ((0.08 * self.screen_ratio), 0.08)
        image.pos_hint = {"center_x": self.x_dim_hint[new_target[0]], "center_y": self.y_dim_hint[new_target[1]]}
        image.size_hint = (None, None)
        image.bind(on_press=lambda instance: self.distractor_target_press(instance,index))
        image.name = 'Distractor Target'
        self.distractor_target_button_list.append(image)
        self.protocol_floatlayout.add_widget(self.distractor_target_button_list[len(self.distractor_target_button_list) - 1])
        self.distractor_target_button_list[len(self.distractor_target_button_list) - 1].size_hint = ((0.08 * self.width_adjust), (0.08 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Displayed', 'Distractor Target', 'X Position', new_target[0],
             'Y Position', new_target[0], 'Image Name', self.distractor_target_image])

        image = ImageButton(source=self.distractor_ignore_image_path, allow_stretch=True)
        image.coord = new_distract
        image.size_hint = ((0.08 * self.screen_ratio), 0.08)
        image.pos_hint = {"center_x": self.x_dim_hint[new_distract[0]], "center_y": self.y_dim_hint[new_distract[1]]}
        image.size_hint = (None, None)
        image.name = 'Distractor Ignore'
        self.distractor_ignore_button_list.append(image)
        self.protocol_floatlayout.add_widget(
            self.distractor_ignore_button_list[len(self.distractor_ignore_button_list) - 1])

        self.distractor_ignore_button_list[len(self.distractor_target_button_list) - 1].size_hint = (
        (0.08 * self.width_adjust), (0.08 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Displayed', 'Distractor Ignore', 'X Position', new_distract[0],
             'Y Position', new_distract[0], 'Image Name', self.distractor_ignore_image])
        self.distractor_press_count += 1

    # Data Saving Function

    # Trial Contingency Functions
    def trial_contingency(self):
        self.current_trial += 1
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Current Trial', 'Value', str(self.current_trial),
             '', '', '', ''])

        if self.current_trial > self.block_threshold:
            self.current_trial -= 1
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Current Trial', 'Value', str(self.current_trial),
                 '', '', '', ''])
            self.feedback_start = time.time()
            self.protocol_floatlayout.remove_widget(self.hold_button)
            self.block_threshold += self.block_trial_break
            Clock.schedule_interval(self.block_contingency, 0.1)
            return

        if self.current_trial > self.session_trial_max:
            Clock.unschedule(self.clock_monitor)
            print('trial max')
            return
        # Define Variables - Coordinates

        if self.current_probe == 'Spatial':
            self.current_sep = self.space_probe_trial_list[self.current_space_trial_index]
            self.trial_coord = generate_trial_pos_sep(self.current_sep)
            self.current_delay = self.space_probe_delay_length
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Current Separation', 'Value', str(self.current_sep),
                 '', '', '', ''])
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Sample Position', 'X Position',
                 str(self.trial_coord['Sample'][0]),
                 'Y Position', str(self.trial_coord['Sample'][1]), '', ''])
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Choice Position', 'X Position',
                 str(self.trial_coord['Choice'][0]),
                 'Y Position', str(self.trial_coord['Choice'][1]), '', ''])
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Current Delay', 'Value', str(self.current_delay),
                 '', '', '', ''])
            self.distractor_target_list, self.distractor_ignore_list = \
                self.generate_distractor_pos(self.space_probe_distract_target_count,
                                             self.space_probe_distract_distractor_count)
            self.current_space_trial_index += 1
        elif self.current_probe == 'Delay':
            self.current_sep = self.delay_probe_sep
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Current Separation', 'Value', str(self.current_sep),
                 '', '', '', ''])
            self.trial_coord = generate_trial_pos_sep(self.current_sep)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Sample Position', 'X Position',
                 str(self.trial_coord['Sample'][0]),
                 'Y Position', str(self.trial_coord['Sample'][1]), '', ''])
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Choice Position', 'X Position',
                 str(self.trial_coord['Choice'][0]),
                 'Y Position', str(self.trial_coord['Choice'][1]), '', ''])
            self.current_delay = self.delay_probe_trial_list[self.current_delay_trial_index]
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Current Delay', 'Value', str(self.current_delay),
                 '', '', '', ''])
            self.distractor_target_list, self.distractor_ignore_list = \
                self.generate_distractor_pos(self.delay_probe_target_count,
                                             self.delay_probe_distractor_count)
            self.current_delay_trial_index += 1

        self.sample_image_button.pos_hint = {"center_x": self.x_dim_hint[self.trial_coord['Sample'][0]],
                                             "center_y": self.y_dim_hint[self.trial_coord['Sample'][1]]}
        self.novel_image_button.pos_hint = {"center_x": self.x_dim_hint[self.trial_coord['Choice'][0]],
                                            "center_y": self.y_dim_hint[self.trial_coord['Choice'][1]]}

        self.distractor_target_button_list = list()
        for coord in self.distractor_target_list:
            index = 0
            image = ImageButton(source=self.distractor_target_image_path, allow_stretch=True)
            image.coord = coord
            image.size_hint = ((0.08 * self.screen_ratio), 0.08)
            image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
            image.bind(on_press=lambda instance: self.distractor_target_press(instance, index))
            image.size_hint = (None, None)
            image.name = 'Distractor Target'
            self.distractor_target_button_list.append(image)

        self.distractor_ignore_button_list = list()
        for coord in self.distractor_ignore_list:
            image = ImageButton(source=self.distractor_ignore_image_path, allow_stretch=True)
            image.coord = coord
            image.size_hint = ((0.08 * self.screen_ratio), 0.08)
            image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
            image.size_hint = (None, None)
            image.name = 'Distractor Ignore'
            self.distractor_ignore_button_list.append(image)

    # Block Contingency Function
    def block_contingency(self,*args):
        if self.feedback_on_screen is True:
            curr_time = time.time()
            if (curr_time - self.feedback_start) >= self.feedback_length:
                Clock.unschedule(self.block_contingency)
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_on_screen = False
            else:
                return
        else:
            Clock.unschedule(self.block_contingency)

        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Grid Array', '', '',
             '', '', '', ''])
        self.feedback_string = ''
        self.feedback_label.text = self.feedback_string

        if (self.current_trial >= self.space_probe_block_length) and (self.current_probe == 'Spatial'):
            self.delay_probe_block_length = self.delay_probe_block_length + self.space_probe_block_length
            self.current_probe = 'Delay'

        if (self.current_trial >= self.delay_probe_block_length) and (self.current_probe == 'Delay'):
            self.protocol_end()
            return

        self.current_block += 1

        self.block_screen()