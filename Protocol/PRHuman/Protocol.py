# Imports #
import sys
import os
import configparser
import time
import pandas as pd
import numpy as np
import csv
import random
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

class ImageButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(ImageButton, self).__init__(**kwargs)
        self.coord = None
        self.fit_mode = 'fill'
        self.press_x = 0
        self.press_y = 0
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
        super(Protocol_Screen,self).__init__(**kwargs)
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
        self.image_folder = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Image' + self.folder_mod
        self.data_output_path = None

        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        self.parameters_dict = config_file['TaskParameters']
        self.participant_id = 'Default'

        self.session_max_length = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])

        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])

        self.stimulus_image = self.parameters_dict['stimulus_image']

        self.current_pr_multiplier = int(self.parameters_dict['pr_ratio_multiplier'])
        self.baseline_pr_threshold = int(self.parameters_dict['baseline_pr'])
        self.current_pr_threshold_step_max = int(self.parameters_dict['pr_step_max'])

        self.reward_type = str(self.parameters_dict['reward_type'])

        self.block_length = int(self.parameters_dict['block_length'])
        self.block_count = int(self.parameters_dict['block_count'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])

        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        # Define Language
        self.language = 'English'
        lang_folder_path = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Language' + \
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
        self.stop_button_label_str = button_lang_config['Button']['stop']

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
        self.stage_list = ['Reward x20', 'Reward x10', 'Reward x5', 'Reward x2', 'Reward x1']
        self.reward_value_score = [200, 100, 50, 20, 10]
        self.reward_value_curr = [2.00, 1.00, 0.50, 0.25, 0.10]

        # Define Variables - Boolean
        self.stimulus_on_screen = False
        self.iti_active = False
        self.feedback_on_screen = False
        self.hold_active = True
        self.block_started = False
        self.correction_trial = True

        # Define Variables - Count
        self.current_trial = 1
        self.current_block = 0
        self.current_pr_threshold = self.baseline_pr_threshold
        self.current_pr_step = 0
        self.current_response_count = 0
        self.block_threshold = 10 + self.block_length
        self.stage_index = 0

        # Define Variables - String
        self.current_stage = self.stage_list[self.stage_index]

        # Define Variables - Time
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0
        self.elapsed_time = 0

        # Define Variables - Trial Configuration
        if self.reward_type == 'point':
            self.reward_list = self.reward_value_score
            self.current_reward_value = 0
            self.feedback_string = 'Reward:\n %d Points' % self.current_reward_value
        elif self.reward_type == 'currency':
            self.reward_list = self.reward_value_curr
            self.current_reward_value = 0.00
            self.feedback_string = 'Reward:\n $%.2f' % self.current_reward_value

        self.current_reward = self.reward_list[self.stage_index]
        self.x_pos_mod = random.randint(0, 7)
        self.y_pos_mod = random.randint(0, 7)

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path)

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

        self.stimulus_image_button = ImageButton(source=self.stimulus_image_path)
        self.stimulus_image_button.bind(on_press=self.stimulus_pressed)

        # Define Widgets - Text
        self.instruction_label = Label(text= self.start_label_str, font_size='35sp')
        self.instruction_label.size_hint = (0.6, 0.4)
        self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.block_label = Label(text=self.break_label_str, font_size='50sp')
        self.block_label.size_hint = (0.5, 0.3)
        self.block_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.end_label = Label(text=self.end_label_str)
        self.end_label.size_hint = (0.6, 0.4)
        self.end_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.feedback_string = ''
        self.feedback_label = Label(text=self.feedback_string, font_size='40sp', markup=True)
        self.feedback_label.size_hint = (0.7, 0.4)
        self.feedback_label.pos_hint = {'center_x': 0.8, 'center_y': 0.7}
        self.feedback_label.halign = 'center'

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

        self.quit_button = Button(text=self.stop_button_label_str)
        self.quit_button.size_hint = (0.1, 0.1)
        self.quit_button.pos_hint = {'center_x': 0.1, 'center_y': 0.7}
        self.quit_button.bind(on_press=self.protocol_end)

        
    # Initialization Functions #
        
    def load_parameters(self,parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        self.participant_id = self.parameters_dict['participant_id']

        self.session_max_length = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])

        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])

        self.stimulus_image = self.parameters_dict['stimulus_image']

        self.current_pr_multiplier = int(self.parameters_dict['pr_ratio_multiplier'])
        self.baseline_pr_threshold = int(self.parameters_dict['baseline_pr'])
        self.current_pr_threshold_step_max = int(self.parameters_dict['pr_step_max'])

        self.reward_type = str(self.parameters_dict['reward_type'])

        self.block_length = int(self.parameters_dict['block_length'])
        self.block_count = int(self.parameters_dict['block_count'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])

        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        # Define Language
        self.language = self.parameters_dict['language']
        lang_folder_path = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Language' + \
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
        self.stop_button_label_str = button_lang_config['Button']['stop']

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
        self.stage_list = ['Reward x20', 'Reward x10', 'Reward x5', 'Reward x2', 'Reward x1']
        self.reward_value_score = [200, 100, 50, 20, 10]
        self.reward_value_curr = [2.00, 1.00, 0.50, 0.25, 0.10]

        # Define Variables - Boolean
        self.stimulus_on_screen = False
        self.iti_active = False
        self.feedback_on_screen = False
        self.hold_active = True
        self.block_started = False
        self.correction_trial = True

        # Define Variables - Count
        self.current_trial = 1
        self.current_block = 0
        self.current_pr_threshold = self.baseline_pr_threshold
        self.current_pr_step = 0
        self.current_response_count = 0
        self.block_threshold = 10 + self.block_length
        self.stage_index = 0

        # Define Variables - String
        self.current_stage = self.stage_list[self.stage_index]
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Current Stage', 'Value', str(self.current_stage),
             '', '', '', ''])

        # Define Variables - Time
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0

        # Define Variables - Trial Configuration
        if self.reward_type == 'point':
            self.reward_list = self.reward_value_score
            self.current_reward_value = 0
            self.feedback_string = 'Reward:\n %d Points' % (self.current_reward_value)
        elif self.reward_type == 'currency':
            self.reward_list = self.reward_value_curr
            self.current_reward_value = 0.00
            self.feedback_string = 'Reward:\n $%.2f' % (self.current_reward_value)


        self.current_reward = self.reward_list[self.stage_index]
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Current Reward', 'Value', str(self.current_reward_value),
             '', '', '', ''])
        self.x_pos_mod = random.randint(0, 7)
        self.y_pos_mod = random.randint(0, 7)

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path, allow_stretch=True)
        self.hold_button.pos_hint = {"center_x": 0.5, "center_y": 0.001}

        # self.x_dim_hint = []
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

        self.stimulus_image_button = ImageButton(source=self.stimulus_image_path, allow_stretch=True)
        self.stimulus_image_button.pos_hint = {"center_x": self.x_dim_hint[self.x_pos_mod],
                                               "center_y": self.y_dim_hint[self.y_pos_mod]}
        self.stimulus_image_button.bind(on_press=self.stimulus_pressed)

        # Define Widgets - Text
        self.instruction_label = Label(text=self.start_label_str, font_size='35sp')
        self.instruction_label.size_hint = (0.6, 0.4)
        self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.block_label = Label(text=self.break_label_str, font_size='50sp')
        self.block_label.size_hint = (0.5, 0.3)
        self.block_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.end_label = Label(text=self.end_label_str)
        self.end_label.size_hint = (0.6, 0.4)
        self.end_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.feedback_string = ''
        self.feedback_label = Label(text=self.feedback_string, font_size='40sp', markup=True)
        self.feedback_label.size_hint = (0.7, 0.4)
        self.feedback_label.pos_hint = {'center_x': 0.8, 'center_y': 0.7}
        self.feedback_label.halign = 'center'

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

        self.quit_button = Button(text=self.stop_button_label_str)
        self.quit_button.size_hint = (0.1, 0.1)
        self.quit_button.pos_hint = {'center_x': 0.1, 'center_y': 0.7}
        self.quit_button.bind(on_press=self.protocol_end)

        self.present_instructions()

        
    def generate_output_files(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        if os.path.exists(folder_path) == False:
            os.makedirs(folder_path)
        folder_list = os.listdir(folder_path)
        file_index = 1
        temp_filename = self.participant_id + '_PRHuman_' + str(file_index) + '.csv'
        self.file_path = folder_path + self.folder_mod + temp_filename
        while os.path.isfile(self.file_path):
            file_index += 1
            temp_filename = self.participant_id + '_PRHuman_' + str(file_index) + '.csv'
            self.file_path = folder_path + self.folder_mod + temp_filename
        data_cols = 'TrialNo,Current Reward,Current Threshold,X_Position,Y_Position,Latency,Time of Press'
        self.data_file = open(self.file_path, "w+")
        self.data_file.write(data_cols)
        self.data_file.close()

        event_path = folder_path + self.folder_mod + self.participant_id + '_TUNLProbe_' + str(
            file_index) + '_Event_Data.csv'
        self.protocol_floatlayout.update_path(event_path)
        
    def metadata_output_generation(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        metadata_rows = ['participant_id','stimulus_image','pr_ratio_multiplier',
                         'baseline_pr','pr_step_max','block_count','reward_type',
                         'iti_length','session_length_max','session_trial_max']
    
        
        meta_list = list()
        for meta_row in metadata_rows:
            row_list = list()
            row_list.append(meta_row)
            row_list.append(str(self.parameters_dict[meta_row]))
            meta_list.append(row_list)
            #meta_array[row_index,0] = meta_row
            #meta_array[row_index,1] = self.parameters_dict[meta_row]
        
        file_index = 1
        meta_output_filename = self.participant_id + '_PRHuman_Metadata_' + str(file_index) + '.csv'
        meta_output_path = folder_path + self.folder_mod + meta_output_filename
        while os.path.isfile(meta_output_path):
            file_index += 1
            meta_output_filename = self.participant_id + '_PRHuman_Metadata_' + str(file_index) + '.csv'
            meta_output_path = folder_path + self.folder_mod + meta_output_filename
        
        meta_colnames = ['Parameter','Value']
        
        with open(meta_output_path,'w') as meta_output_file:
            csv_writer = csv.writer(meta_output_file,delimiter=',')
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
    def block_screen(self,*args):
        if self.block_started == False:
            self.protocol_floatlayout.add_widget(self.block_label)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Text Displayed', 'Block Instruction', '', '',
                 '', '', '', ''])
            self.block_start = time.time()
            self.block_started = True
            Clock.schedule_interval(self.block_screen,0.1)
        if (time.time() - self.block_start) > self.block_min_rest_duration:
            Clock.unschedule(self.block_screen)
            self.protocol_floatlayout.add_widget(self.continue_button)
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Button Displayed', 'Continue Button', '', '',
                 '', '', '', ''])
            
    def block_end(self,*args):
        self.block_started = False
        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Removed', 'Block Instruction', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Button Removed', 'Continue Button', '', '',
             '', '', '', ''])
        self.trial_contingency()
        self.protocol_floatlayout.add_widget(self.hold_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Button Displayed', 'Hold Button', '', '',
             '', '', '', ''])
        self.score_label.text = 'Your Points:\n%s' % (self.current_score)
        self.protocol_floatlayout.add_widget(self.score_label)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Displayed', 'Score', '', '',
             '', '', '', ''])
    
    # End Staging #
    def protocol_end(self, *args):
        Clock.unschedule(self.clock_monitor)
        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_widget(self.end_label)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Displayed', 'End Instruction', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_widget(self.return_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Button Displayed', 'Return Button', '', '',
             '', '', '', ''])
        
    def return_to_main(self,*args):
        self.manager.current='mainmenu'
    
    # Protocol Staging #
    
    def start_protocol(self,*args):
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
        self.protocol_floatlayout.add_widget(self.quit_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Button Displayed', 'Quit Button', '', '',
             '', '', '', ''])
        self.feedback_label.text = self.feedback_string
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Displayed', 'Score', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.hold_button.pos_hint = {"center_x":0.5,"center_y":0.1}
        self.hold_button.bind(on_press=self.iti)
    
        
    def iti(self,*args):
        if self.iti_active == False:
            self.hold_button.unbind(on_press=self.iti)
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
            Clock.schedule_interval(self.iti,0.1)
        if self.iti_active == True:
            if (time.time() - self.start_iti) > self.iti_length:
                Clock.unschedule(self.iti)
                self.iti_active = False
                self.stimulus_presentation()
                
    def stimulus_presentation(self,*args):
        self.protocol_floatlayout.add_widget(self.stimulus_image_button)
        self.stimulus_image_button.size_hint = ((0.08 * self.width_adjust), (0.08 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Displayed', 'Sample Image', 'X Position', self.x_dim_hint[self.x_pos_mod],
             'Y Position', self.y_dim_hint[self.y_pos_mod], 'Image Name', self.stimulus_image])


            
        self.start_stimulus = time.time()
        
        self.stimulus_on_screen = True
            
                
    def premature_response(self,*args):
        if self.stimulus_on_screen:
            return None
        
        Clock.unschedule(self.iti)
        self.feedback_string = 'WAIT FOR IMAGE \n PLEASE TRY AGAIN'
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_string
        if not self.feedback_on_screen:
            self.protocol_floatlayout.add_widget(self.feedback_label)
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)
        
        
            
        
    # Contingency Stages #

    def stimulus_pressed(self,*args):
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.stimulus_image_button)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Sample Image', 'X Position', self.x_dim_hint[self.x_pos_mod],
             'Y Position', self.y_dim_hint[self.y_pos_mod], 'Image Name', self.stimulus_image])
        
        self.current_response_count += 1
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Current Responses', 'Value', str(self.current_response_count),
             '', '', '', ''])
        
            
        self.response_lat = time.time() - self.start_stimulus
        self.response_time = time.time() - self.start_time
        self.write_summary_file()
        
        self.trial_contingency()
        
        
        self.hold_button.bind(on_press=self.iti)
        
        
    
        
    # Data Saving Functions #
    def write_summary_file(self):
        if self.correction_trial == True:
            correction = 1
        else:
            correction = 0
        data_file = open(self.file_path, "a")
        data_file.write("\n")
        data_file.write("%s,%s,%s,%s,%s,%s,%s" % (self.current_trial,self.current_stage,self.current_pr_threshold,str(self.x_pos_mod + 1),str(self.y_pos_mod + 1),self.response_lat,self.response_time))
        data_file.close()
        return
    
    # Trial Contingency Functions #
    
    def trial_contingency(self):
        self.current_trial += 1
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Current Trial', 'Value', str(self.current_trial),
             '', '', '', ''])
        
        self.x_pos_mod = random.randint(0,7)
        self.y_pos_mod = random.randint(0,7)
        self.stimulus_image_button.pos_hint = {"center_x":self.x_dim_hint[self.x_pos_mod],"center_y":self.y_dim_hint[self.y_pos_mod]}
        
        
        if self.current_response_count >= self.current_pr_threshold:
            self.current_pr_threshold *= self.current_pr_multiplier
            self.protocol_floatlayout.add_event(
                [0, 'Variable Change', 'Current Threshold', 'Value', str(self.current_pr_threshold),
                 '', '', '', ''])
            self.current_pr_step += 1
            self.current_reward_value += self.current_reward
            self.protocol_floatlayout.add_event(
                [0, 'Variable Change', 'Current Reward', 'Value', str(self.current_reward_value),
                 '', '', '', ''])
            self.current_response_count = 0
            if self.reward_type == 'point':
                self.feedback_string = 'Reward: \n %d Points' % (self.current_reward_value)
            elif self.reward_type == 'currency':
                self.current_reward_value = 0.00
                self.feedback_string = 'Reward: \n $%.2f' % (self.current_reward_value)
            self.feedback_label.text = self.feedback_string
            
        if self.current_pr_step > self.current_pr_threshold_step_max:
            self.stage_index += 1
            self.current_stage = self.stage_list[self.stage_index]
            self.protocol_floatlayout.add_event(
                [0, 'Variable Change', 'Current Stage', 'Value', str(self.current_stage),
                 '', '', '', ''])
            self.current_pr_step = 0
            self.current_reward = self.reward_list[self.stage_index]
            self.current_pr_threshold = self.baseline_pr_threshold
            
        
        if self.current_trial > self.session_trial_max:
            self.protocol_end()
            return
        
        if self.stage_index > len(self.stage_list):
            self.protocol_end()
            return
        
        
    def block_contingency(self):
        self.protocol_floatlayout.clear_widgets()
        
        if self.stage_index == 0:
            self.stage_index = 1
            self.current_block = 1
            self.trial_configuration = random.randint(1,6)
            self.generate_trial_contingency()
            self.current_stage = self.stage_list[self.stage_index]
        elif self.stage_index == 1:
            self.current_block += 1
            if self.current_block > self.block_count:
                self.protocol_end()
                return
            
            self.trial_configuration = random.randint(1,6)
            self.generate_trial_contingency()

        
        self.block_screen()
            
    
    # Time Monitor Functions #
    def start_clock(self,*args):
        self.start_time = time.time()
        Clock.schedule_interval(self.clock_monitor,0.1)
    
    def clock_monitor(self,*args):
        self.current_time = time.time()
        self.elapsed_time = self.current_time - self.start_time
        self.protocol_floatlayout.elapsed_time = self.elapsed_time
        
        if self.elapsed_time > self.session_max_length:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()

            
        
        
        