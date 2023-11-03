# Imports #

import configparser
import time
import numpy as np
import random
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from TouchCog.Classes.Protocol import ImageButton, ProtocolBase


class ProtocolScreen(ProtocolBase):
    def __init__(self, screen_resolution, **kwargs):
        super(ProtocolScreen,self).__init__(**kwargs)
        self.protocol_name = 'PRHuman'
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

        # Define Variables - Folder Path
        self.image_folder = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Image' + self.folder_mod
        self.data_output_path = None
        self.data_cols = ['TrialNo', 'Current Reward', 'Current Threshold', 'X_Position', 'Y_Position', 'Latency',
                          'Time of Press']

        self.metadata_cols = ['participant_id', 'stimulus_image', 'pr_ratio_multiplier', 'baseline_pr', 'pr_step_max',
                              'block_count', 'reward_type', 'iti_length', 'session_length_max', 'session_trial_max']

        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        self.parameters_dict = config_file['TaskParameters']
        self.participant_id = 'Default'

        self.session_length_max = float(self.parameters_dict['session_length_max'])
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

        # Define Widgets - Buttons
        self.quit_button = Button()
        self.quit_button.size_hint = (0.1, 0.1)
        self.quit_button.pos_hint = {'center_x': 0.1, 'center_y': 0.7}
        self.quit_button.bind(on_press=self.protocol_end)

        # Define Language
        self.language = 'English'
        self.feedback_dict = {}
        self.set_language(self.language)
        self.feedback_label.size_hint = (0.7, 0.4)
        self.feedback_label.pos_hint = {'center_x': 0.8, 'center_y': 0.7}

        # Define Variables - List
        self.stage_list = ['Reward x20', 'Reward x10', 'Reward x5', 'Reward x2', 'Reward x1']
        self.reward_value_score = [200, 100, 50, 20, 10]
        self.reward_value_curr = [2.00, 1.00, 0.50, 0.25, 0.10]

        # Define Variables - Boolean
        self.correction_trial = True

        # Define Variables - Count
        self.current_pr_threshold = self.baseline_pr_threshold
        self.current_pr_step = 0
        self.current_response_count = 0
        self.block_threshold = 10 + self.block_length

        # Define Variables - String
        self.current_stage = self.stage_list[self.stage_index]

        # Define Variables - Time
        self.start_stimulus = 0
        self.response_lat = 0

        # Define Variables - Trial Configuration
        self.trial_configuration = 0
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

        self.stimulus_image_button = ImageButton(source=self.stimulus_image_path)
        self.stimulus_image_button.bind(on_press=self.stimulus_pressed)


    # Initialization Functions #
        
    def load_parameters(self,parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        self.participant_id = self.parameters_dict['participant_id']

        self.session_length_max = float(self.parameters_dict['session_length_max'])
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
        self.set_language(self.language)

        # Define Variables - List
        self.stage_list = ['Reward x20', 'Reward x10', 'Reward x5', 'Reward x2', 'Reward x1']
        self.reward_value_score = [200, 100, 50, 20, 10]
        self.reward_value_curr = [2.00, 1.00, 0.50, 0.25, 0.10]

        # Define Variables - Count
        self.current_pr_threshold = self.baseline_pr_threshold
        self.block_threshold = 10 + self.block_length

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
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Current Reward', 'Value', str(self.current_reward_value),
             '', '', '', ''])
        self.x_pos_mod = random.randint(0, 7)
        self.y_pos_mod = random.randint(0, 7)

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path
        self.hold_button.pos_hint = {"center_x": 0.5, "center_y": 0.001}

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

        self.present_instructions()

    def set_language(self, language):
        self.language = language
        lang_folder_path = 'Protocol' + self.folder_mod + self.protocol_name + self.folder_mod + 'Language' + \
                           self.folder_mod + self.language + self.folder_mod
        start_path = lang_folder_path + 'Start.txt'
        start_open = open(start_path, 'r', encoding="utf-8")
        start_label_str = start_open.read()
        start_open.close()
        self.instruction_label.text = start_label_str

        break_path = lang_folder_path + 'Break.txt'
        break_open = open(break_path, 'r', encoding="utf-8")
        break_label_str = break_open.read()
        break_open.close()
        self.block_label.text = break_label_str

        end_path = lang_folder_path + 'End.txt'
        end_open = open(end_path, 'r', encoding="utf-8")
        end_label_str = end_open.read()
        end_open.close()
        self.end_label.text = end_label_str

        button_lang_path = lang_folder_path + 'Button.ini'
        button_lang_config = configparser.ConfigParser()
        button_lang_config.read(button_lang_path, encoding="utf-8")

        start_button_label_str = button_lang_config['Button']['start']
        self.start_button.text = start_button_label_str
        continue_button_label_str = button_lang_config['Button']['continue']
        self.continue_button.text = continue_button_label_str
        return_button_label_str = button_lang_config['Button']['return']
        self.return_button.text = return_button_label_str
        stop_button_label_str = button_lang_config['Button']['stop']
        self.quit_button.text = stop_button_label_str

        feedback_lang_path = lang_folder_path + 'Feedback.ini'
        feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
        feedback_lang_config.read(feedback_lang_path, encoding="utf-8")

        self.feedback_dict = {}
        stim_feedback_correct_str = feedback_lang_config['Stimulus']['correct']
        stim_feedback_correct_color = feedback_lang_config['Stimulus']['correct_colour']
        if stim_feedback_correct_color != '':
            color_text = '[color=%s]' % stim_feedback_correct_color
            stim_feedback_correct_str = color_text + stim_feedback_correct_str + '[/color]'
        self.feedback_dict['correct'] = stim_feedback_correct_str


        stim_feedback_incorrect_str = feedback_lang_config['Stimulus']['incorrect']
        stim_feedback_incorrect_color = feedback_lang_config['Stimulus']['incorrect_colour']
        if stim_feedback_incorrect_color != '':
            color_text = '[color=%s]' % stim_feedback_incorrect_color
            stim_feedback_incorrect_str = color_text + stim_feedback_incorrect_str + '[/color]'
        self.feedback_dict['incorrect'] = stim_feedback_incorrect_str

        hold_feedback_wait_str = feedback_lang_config['Hold']['wait']
        hold_feedback_wait_color = feedback_lang_config['Hold']['wait_colour']
        if hold_feedback_wait_color != '':
            color_text = '[color=%s]' % hold_feedback_wait_color
            hold_feedback_wait_str = color_text + hold_feedback_wait_str + '[/color]'
        self.feedback_dict['wait'] = hold_feedback_wait_str

        hold_feedback_return_str = feedback_lang_config['Hold']['return']
        hold_feedback_return_color = feedback_lang_config['Hold']['return_colour']
        if hold_feedback_return_color != '':
            color_text = '[color=%s]' % hold_feedback_return_color
            hold_feedback_return_str = color_text + hold_feedback_return_str + '[/color]'
        self.feedback_dict['return'] = hold_feedback_return_str

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
        
    # Block Staging
            
    def block_end(self, *args):
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
        
    def return_to_main(self, *args):
        self.manager.current = 'mainmenu'
    
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
        self.response_lat = 0
        self.iti_active = False
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)

    def iti(self, *args):
        if not self.iti_active:
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
            Clock.schedule_interval(self.iti, 0.1)
        if self.iti_active:
            if (time.time() - self.start_iti) > self.iti_length:
                Clock.unschedule(self.iti)
                self.iti_active = False
                self.stimulus_presentation()

    # Contingency Stages
    def stimulus_pressed(self, *args):
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
        self.write_trial()
        self.trial_contingency()
        self.hold_button.bind(on_press=self.iti)
        
    # Data Saving Functions #

    def write_trial(self):
        trial_data = [self.current_trial, self.current_stage, self.current_pr_threshold, str(self.x_pos_mod + 1),
                      str(self.y_pos_mod + 1), self.response_lat, self.response_time]
        self.write_summary_file(trial_data)
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
                self.feedback_string = 'Reward: \n %d Points' % self.current_reward_value
            elif self.reward_type == 'currency':
                self.current_reward_value = 0.00
                self.feedback_string = 'Reward: \n $%.2f' % self.current_reward_value
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
