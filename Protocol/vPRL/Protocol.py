# Imports #
import sys
import os
import configparser
import time
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
    def __init__(self,screen_resolution,**kwargs):
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
        self.image_folder = 'Protocol' + self.folder_mod + 'vPRL' + self.folder_mod + 'Image' + self.folder_mod
        self.data_output_path = None

        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + 'vPRL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        self.parameters_dict = config_file['TaskParameters']
        self.participant_id = 'Default'
        self.session_max_length = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.training_image = self.parameters_dict['training_image']
        self.training_images = ['grey', self.training_image]
        self.test_images = self.parameters_dict['test_images']
        self.test_images = self.test_images.split(',')
        self.image_probability = float(self.parameters_dict['image_probability'])
        self.decimal_values = len(str(self.image_probability - int(self.image_probability))[2:])
        self.reward_distribution_list_size = 10 ** self.decimal_values
        self.reward_distribution_count = int(self.reward_distribution_list_size * self.image_probability)
        self.reward_distribution = ([0] * (self.reward_distribution_list_size - self.reward_distribution_count)) + (
                    [1] * self.reward_distribution_count)
        random.shuffle(self.reward_distribution)
        self.reward_index = 0
        self.reward_contingency = 1
        self.reversal_threshold = int(self.parameters_dict['reversal_threshold'])
        self.maximum_reversals = int(self.parameters_dict['maximum_reversals'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        # Define Language
        self.language = 'English'
        lang_folder_path = 'Protocol' + self.folder_mod + 'PAL' + self.folder_mod + 'Language' + \
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
        self.stage_list = ['Training', 'Test']

        # Define Variables - Boolean
        self.stimulus_on_screen = False
        self.iti_active = False
        self.feedback_on_screen = False
        self.hold_active = True
        self.block_started = False

        # Define Variables - Count
        self.current_trial = 1
        self.current_correct = 0
        self.current_reversal = 0
        self.stage_index = 0
        self.current_score = 0

        # Define Variables - String
        self.correct_image = 'snowflake'
        self.incorrect_image = 'grey'
        self.current_stage = self.stage_list[self.stage_index]
        self.feedback_string = ''

        # Define Variables - Time
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0

        # Define Variables - Trial Configuration
        self.left_stimulus_index = random.randint(0, 1)
        if self.left_stimulus_index == 0:
            self.right_stimulus_index = 1
        else:
            self.right_stimulus_index = 0
        self.left_stimulus_image = self.training_images[self.left_stimulus_index]
        self.right_stimulus_image = self.training_images[self.right_stimulus_index]
        self.left_chosen = 0
        self.right_chosen = 1

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path)
        self.hold_button.pos_hint = {"center_x": 0.5, "center_y": 0.1}

        self.left_stimulus_image_path = self.image_folder + self.left_stimulus_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path)
        self.left_stimulus.pos_hint = {"center_x": 0.3, "center_y": 0.6}
        self.left_stimulus.bind(on_press=self.left_stimulus_pressed)

        self.right_stimulus_image_path = self.image_folder + self.right_stimulus_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path)
        self.right_stimulus.pos_hint = {"center_x": 0.7, "center_y": 0.6}
        self.right_stimulus.bind(on_press=self.right_stimulus_pressed)

        # Define Widgets - Text
        self.instruction_label = Label(
            text= self.start_label_str, font_size='35sp')
        self.instruction_label.size_hint = (0.6, 0.4)
        self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.block_label = Label(text= self.break_label_str, font_size='50sp')
        self.block_label.size_hint = (0.5, 0.3)
        self.block_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.end_label = Label(text= self.end_label_str, font_size='50sp')
        self.end_label.size_hint = (0.6, 0.4)
        self.end_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.feedback_string = ''
        self.feedback_label = Label(text=self.feedback_string, font_size='50sp', markup=True)
        self.feedback_label.size_hint = (0.7, 0.4)
        self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        self.score_string = 'Your Points:\n%s' % (0)
        self.score_label = Label(text=self.score_string, font_size='50sp', markup=True, halign='center')
        self.score_label.size_hint = (0.8, 0.2)
        self.score_label.pos_hint = {'center_x': 0.5, 'center_y': 0.9}

        # Define Widgets - Buttons
        self.start_button = Button(text= self.start_button_label_str)
        self.start_button.size_hint = (0.1, 0.1)
        self.start_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.start_button.bind(on_press=self.start_protocol)

        self.continue_button = Button(text= self.continue_button_label_str)
        self.continue_button.size_hint = (0.1, 0.1)
        self.continue_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.continue_button.bind(on_press=self.block_end)

        self.return_button = Button(text= self.return_button_label_str)
        self.return_button.size_hint = (0.1, 0.1)
        self.return_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.return_button.bind(on_press=self.return_to_main)
        
    # Initialization Functions #
        
    def load_parameters(self,parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'PAL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        if len(self.parameters_dict) == 0:
            self.parameters_dict = config_file['TaskParameters']
        else:
            self.participant_id = self.parameters_dict['participant_id']

        # Define Variables - Config
        self.session_max_length = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.training_image = self.parameters_dict['training_image']
        self.training_images = ['grey', self.training_image]
        self.test_images = self.parameters_dict['test_images']
        self.test_images = self.test_images.split(',')
        self.image_probability = float(self.parameters_dict['image_probability'])
        self.decimal_values = len(str(self.image_probability - int(self.image_probability))[2:])
        self.reward_distribution_list_size = 10 ** self.decimal_values
        self.reward_distribution_count = int(self.reward_distribution_list_size * self.image_probability)
        self.reward_distribution = ([0] * (self.reward_distribution_list_size - self.reward_distribution_count)) + (
                [1] * self.reward_distribution_count)
        random.shuffle(self.reward_distribution)
        self.reward_index = 0
        self.reward_contingency = 1
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Current Reward Contingency', 'Value', str(self.reward_contingency),
             '', '', '', ''])
        self.reversal_threshold = int(self.parameters_dict['reversal_threshold'])
        self.maximum_reversals = int(self.parameters_dict['maximum_reversals'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        # Define Language
        self.language = self.parameters_dict['language']
        lang_folder_path = 'Protocol' + self.folder_mod + 'PAL' + self.folder_mod + 'Language' + \
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
        self.stage_list = ['Training', 'Test']

        # Define Variables - Boolean
        self.stimulus_on_screen = False
        self.iti_active = False
        self.feedback_on_screen = False
        self.hold_active = True
        self.block_started = False

        # Define Variables - Count
        self.current_trial = 1
        self.current_correct = 0
        self.current_reversal = 0
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Current Reversal', 'Value', str(self.current_reversal),
             '', '', '', ''])
        self.stage_index = 0
        self.current_score = 0

        # Define Variables - String
        self.correct_image = 'snowflake'
        self.incorrect_image = 'grey'
        self.current_stage = self.stage_list[self.stage_index]
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Current Stage', 'Value', str(self.current_stage),
             '', '', '', ''])
        self.feedback_string = ''

        # Define Variables - Time
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0

        # Define Variables - Trial Configuration
        self.left_stimulus_index = random.randint(0, 1)
        if self.left_stimulus_index == 0:
            self.right_stimulus_index = 1
        else:
            self.right_stimulus_index = 0
        self.left_stimulus_image = self.training_images[self.left_stimulus_index]
        self.right_stimulus_image = self.training_images[self.right_stimulus_index]
        self.left_chosen = 0
        self.right_chosen = 1

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path)
        self.hold_button.pos_hint = {"center_x": 0.5, "center_y": 0.1}

        self.left_stimulus_image_path = self.image_folder + self.left_stimulus_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path)
        self.left_stimulus.pos_hint = {"center_x": 0.3, "center_y": 0.6}
        self.left_stimulus.bind(on_press=self.left_stimulus_pressed)

        self.right_stimulus_image_path = self.image_folder + self.right_stimulus_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path)
        self.right_stimulus.pos_hint = {"center_x": 0.7, "center_y": 0.6}
        self.right_stimulus.bind(on_press=self.right_stimulus_pressed)

        # Define Widgets - Text
        self.instruction_label = Label(
            text=self.start_label_str, font_size='35sp')
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

        self.score_string = 'Your Points:\n%s' % (0)
        self.score_label = Label(text=self.score_string, font_size='50sp', markup=True, halign='center')
        self.score_label.size_hint = (0.8, 0.2)
        self.score_label.pos_hint = {'center_x': 0.5, 'center_y': 0.9}

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
        temp_filename = self.participant_id + '_vPRL_' + str(file_index) + '.csv'
        self.file_path = folder_path + self.folder_mod + temp_filename
        while os.path.isfile(self.file_path):
            file_index += 1
            temp_filename = self.participant_id + '_vPRL_' + str(file_index) + '.csv'
            self.file_path = folder_path + self.folder_mod + temp_filename
        data_cols = 'TrialNo,Current Stage,Reversal #,S+ Image,S- Image,Left Image,Right Image,S+ Rewarded,S- Rewarded,Left Chosen, Right Chosen,Correct Response,Reward Given,Response Latency'
        self.data_file = open(self.file_path, "w+")
        self.data_file.write(data_cols)
        self.data_file.close()

        event_path = folder_path + self.folder_mod + self.participant_id + '_TUNLProbe_' + str(
            file_index) + '_Event_Data.csv'
        self.protocol_floatlayout.update_path(event_path)
        
    def metadata_output_generation(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        metadata_rows = ['participant_id','training_image','test_images',
                         'image_probability','iti_length','session_length_max',
                         'reversal_threshold','maximum_reversals',
                         'session_trial_max']
    
        
        meta_list = list()
        for meta_row in metadata_rows:
            row_list = list()
            row_list.append(meta_row)
            row_list.append(str(self.parameters_dict[meta_row]))
            meta_list.append(row_list)
        
        file_index = 1
        meta_output_filename = self.participant_id + '_vPRL_Metadata_' + str(file_index) + '.csv'
        meta_output_path = folder_path + self.folder_mod + meta_output_filename
        while os.path.isfile(meta_output_path):
            file_index += 1
            meta_output_filename = self.participant_id + '_vPRL_Metadata_' + str(file_index) + '.csv'
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
        self.hold_button.size_hint = ((0.2 * self.width_adjust), (0.2 * self.height_adjust))
        self.hold_button.size_hint_y = 0.2
        self.hold_button.width = self.hold_button.height
        self.hold_button.pos_hint = {"center_x":0.5,"center_y":0.1}
        self.hold_button.bind(on_press=self.iti)
        self.protocol_floatlayout.add_widget(self.score_label)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Displayed', 'Score', '', '',
             '', '', '', ''])
    
        
    def iti(self,*args):
        if self.iti_active == False:
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
                self.feedback_on_screen = True
            Clock.schedule_interval(self.iti,0.1)
        if self.iti_active == True:
            if (time.time() - self.start_iti) > self.feedback_length:
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
                self.stimulus_presentation()
                
    def stimulus_presentation(self,*args):
        self.protocol_floatlayout.add_widget(self.left_stimulus)
        self.left_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Displayed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.left_stimulus_image])
        self.protocol_floatlayout.add_widget(self.right_stimulus)
        self.right_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Displayed', 'Right Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.right_stimulus_image])
            
        self.start_stimulus = time.time()
        
        self.stimulus_on_screen = True
            
                
    def premature_response(self,*args):
        if self.stimulus_on_screen == True:
            return None
        
        Clock.unschedule(self.iti)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Stage Change', 'Premature Response', '', '',
             '', '', '', ''])
        self.feedback_string = self.hold_feedback_wait_str
        contingency = '2'
        response = '1'
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
        
        
            
        
    # Contingency Stages #
    def left_stimulus_pressed(self,*args):
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_stimulus)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.left_stimulus_image])
        self.protocol_floatlayout.remove_widget(self.right_stimulus)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Right Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.right_stimulus_image])
        
        self.left_chosen = 1
        self.right_chosen = 0
        
        if self.left_stimulus_image == self.correct_image:
            response = '1'
            self.current_correct += 1
            if self.reward_contingency == 1:
                self.feedback_string = self.stim_feedback_correct_str
                self.current_score += 50
                contingency = '1'
            else:
                self.feedback_string = self.stim_feedback_incorrect_str
                contingency = '0'
        else:
            response = '0'
            self.current_correct = 0
            if self.reward_contingency == 1:
                self.feedback_string = self.stim_feedback_incorrect_str
                contingency = '0'
            else:
                self.feedback_string = self.stim_feedback_correct_str
                self.current_score += 50
                contingency = '1'
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Correct', 'Value', str(response),
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Total Correct', 'Value', str(self.current_correct),
             '', '', '', ''])
                
            
        
        self.response_lat = time.time() - self.start_stimulus

            
        self.feedback_label.text = self.feedback_string
        self.score_label.text = 'Your Points:\n%s' % (self.current_score)
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_summary_file(response,contingency)
        self.trial_contingency()
        
        self.hold_button.bind(on_press=self.iti)
    
    def right_stimulus_pressed(self,*args):
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_stimulus)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.left_stimulus_image])
        self.protocol_floatlayout.remove_widget(self.right_stimulus)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Image Removed', 'Right Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.right_stimulus_image])
        
        self.left_chosen = 0
        self.right_chosen = 1
        
        
        if self.right_stimulus_image == self.correct_image:
            response = '1'
            self.current_correct += 1
            if self.reward_contingency == 1:
                self.feedback_string = self.stim_feedback_correct_str
                self.current_score += 50
                contingency = '1'
            else:
                self.feedback_string = self.stim_feedback_incorrect_str
                contingency = '0'
        else:
            response = '0'
            self.current_correct = 0
            if self.reward_contingency == 1:
                self.feedback_string = self.stim_feedback_incorrect_str
                contingency = '0'
            else:
                self.feedback_string = self.stim_feedback_correct_str
                self.current_score += 50
                contingency = '1'
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Trial Correct', 'Value', str(response),
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Variable Change', 'Total Correct', 'Value', str(self.current_correct),
             '', '', '', ''])
                
            
        
        self.response_lat = time.time() - self.start_stimulus

            
        self.feedback_label.text = self.feedback_string
        self.score_label.text = 'Your Points:\n%s' % (self.current_score)
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [self.elapsed_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_summary_file(response,contingency)
        self.trial_contingency()
        
        self.hold_button.bind(on_press=self.iti)
        
        
    # Data Saving Functions #
    def write_summary_file(self,response,contingency):
        if self.reward_contingency == 1:
            s_min_cont = '0'
        else:
            s_min_cont = '1'
        data_file = open(self.file_path, "a")
        data_file.write("\n")
        #'TrialNo,Current Stage,Reversal #,S+ Image,S- Image,Left Image,Right Image,S+ Rewarded,,Response Latency'
        data_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (self.current_trial,self.current_stage,self.current_reversal,self.correct_image,self.incorrect_image,self.left_stimulus_image,self.right_stimulus_image,self.reward_contingency,s_min_cont,self.left_chosen,self.right_chosen,response,contingency,self.response_lat))
        data_file.close()
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
        if self.stage_index == 0:
            if (self.current_correct >= 10):
                self.block_contingency()
                return
            self.left_stimulus_index = random.randint(0,1)
            if self.left_stimulus_index == 0:
                self.right_stimulus_index = 1
            else:
                self.right_stimulus_index = 0
            self.left_stimulus_image = self.training_images[self.left_stimulus_index]
            self.right_stimulus_image = self.training_images[self.right_stimulus_index]
            self.left_stimulus.source = self.image_folder + self.left_stimulus_image + '.png'
            self.right_stimulus.source = self.image_folder + self.right_stimulus_image + '.png'
            self.reward_contingency = 1
            
        

        
        if self.stage_index == 1:
            self.left_stimulus_index = random.randint(0,1)
            if self.left_stimulus_index == 0:
                self.right_stimulus_index = 1
            else:
                self.right_stimulus_index = 0
            self.left_stimulus_image = self.test_images[self.left_stimulus_index]
            self.right_stimulus_image = self.test_images[self.right_stimulus_index]
            self.left_stimulus.source = self.image_folder + self.left_stimulus_image + '.png'
            self.right_stimulus.source = self.image_folder + self.right_stimulus_image + '.png'
            
            if self.current_correct >= self.reversal_threshold:
                if self.correct_image == self.test_images[0]:
                    self.correct_image = self.test_images[1]
                    self.incorrect_image = self.test_images[0]
                else:
                    self.correct_image = self.test_images[0]
                    self.incorrect_image = self.test_images[1]
                self.current_correct = 0
                self.current_reversal += 1
                self.protocol_floatlayout.add_event(
                    [self.elapsed_time, 'Variable Change', 'Current Reversal', 'Value', str(self.current_reversal),
                     '', '', '', ''])
                
            if self.reward_index >= len(self.reward_distribution):
                self.reward_index = 0
                random.shuffle(self.reward_distribution)
            self.reward_contingency = self.reward_distribution[self.reward_index]
            self.protocol_floatlayout.add_event(
                [self.elapsed_time, 'Variable Change', 'Current Reward Contingency', 'Value', str(self.reward_contingency),
                 '', '', '', ''])
            self.reward_index += 1
            if self.current_reversal >= self.maximum_reversals:
                self.protocol_end()
                return
        
    def block_contingency(self):
        self.protocol_floatlayout.clear_widgets()
        
        self.stage_index += 1
        self.current_stage = self.stage_list[self.stage_index]
        
        randindex = random.randint(0,1)
        
        self.correct_image = self.test_images[randindex]
        if randindex == 0:
            self.incorrect_image = self.test_images[1]
        else:
            self.incorrect_image = self.test_images[0]
        self.current_correct = 0
        self.current_score = 0
        
        self.block_screen()
            
    
    # Time Monitor Functions #
    def start_clock(self,*args):
        self.start_time = time.time()
        Clock.schedule_interval(self.clock_monitor,0.1)
    
    def clock_monitor(self,*args):
        self.current_time = time.time()
        self.elapsed_time = self.current_time - self.start_time
        
        if self.elapsed_time > self.session_max_length:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()
            
        
        
        