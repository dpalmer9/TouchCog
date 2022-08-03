# Imports #
import sys
import os
import configparser
import time
import numpy as np
import random
import csv
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


class ProtocolScreen(Screen):
    def __init__(self, **kwargs):
        super(ProtocolScreen, self).__init__(**kwargs)
        self.protocol_floatlayout = FloatLayout()
        self.add_widget(self.protocol_floatlayout)
        width = self.protocol_floatlayout.width
        height = self.protocol_floatlayout.height

        self.screen_ratio = width / height

        if sys.platform == 'linux' or sys.platform == 'darwin':
            self.folder_mod = '/'
        elif sys.platform == 'win32':
            self.folder_mod = '\\'

        # Define Variables - Folder Path
        self.image_folder = 'Protocol' + self.folder_mod + 'TUNL' + self.folder_mod + 'Image' + self.folder_mod
        self.data_output_path = None

        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + 'TUNL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        self.parameters_dict = config_file['TaskParameters']
        self.participant_id = 'Default'
        self.session_max_length = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.stimulus_image = self.parameters_dict['stimulus_image']
        self.distractor_ignore_image = self.parameters_dict['distractor_ignore_image']
        self.distractor_target_image = self.parameters_dict['distractor_target_image']
        self.num_target_distractors = int(self.parameters_dict['num_target_distractors'])
        self.num_ignore_distractors = int(self.parameters_dict['num_ignore_distractors'])
        self.block_distractor_increase = int(self.parameters_dict['block_distractor_increase'])
        self.block_length = int(self.parameters_dict['block_length'])
        self.block_count = int(self.parameters_dict['block_count'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']
        self.block_threshold = self.block_length

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

        # Define Variables - Boolean
        self.stimulus_on_screen = False
        self.iti_active = False
        self.feedback_on_screen = False
        self.hold_active = True
        self.block_started = False
        self.correction_trial = True
        self.sample_completed = False
        self.block_started = False

        # Define Variables - Counter
        self.current_trial = 1
        self.current_correct = 0
        self.current_correction = 0
        self.current_block = 1
        self.baseline_pr_threshold = 4
        self.current_pr_threshold = 4
        self.current_pr_multiplier = 2
        self.current_pr_threshold_step_max = 4
        self.current_pr_step = 0
        self.current_response_count = 0
        self.distractor_press_count = 0
        self.stage_index = 0

        # Define Variables - String
        self.feedback_string = ''

        # Define Variables - Time
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0
        self.start_sample = 0
        self.elapsed_time = 0
        self.block_start = 0
        self.sample_touch_time = 0
        self.choice_touch_time = 0
        self.sample_lat = 0
        self.choice_start = 0
        self.delay_length = 0
        self.feedback_start = 0
        self.sample_press_to_choice = 0
        self.choice_lat = 0

        # Define Variables - Coordinates
        self.trial_coord = generate_sample_choice_pos()
        self.distractor_target_list, self.distractor_ignore_list = self.generate_distractor_pos(3, 3)

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path, allow_stretch=True)
        self.hold_button.size_hint = ((0.075 * self.screen_ratio), 0.075)
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
            cell.size_hint = ((.08 * self.screen_ratio), .08)
            if x_pos > 7:
                x_pos = 0
                y_pos = y_pos + 1
            cell.pos_hint = {"center_x": self.x_dim_hint[x_pos], "center_y": self.y_dim_hint[y_pos]}
            cell.source = self.mask_image_path
            x_pos = x_pos + 1

        self.sample_image_button = ImageButton(source=self.stimulus_image_path, allow_stretch=True)
        self.sample_image_button.size_hint = ((0.08 * self.screen_ratio), 0.08)
        self.sample_image_button.pos_hint = {"center_x": self.x_dim_hint[self.trial_coord['Sample'][0]],
                                             "center_y": self.y_dim_hint[self.trial_coord['Sample'][1]]}
        self.sample_image_button.bind(on_press=self.sample_pressed)

        self.novel_image_button = ImageButton(source=self.stimulus_image_path, allow_stretch=True)
        self.novel_image_button.size_hint = ((0.08 * self.screen_ratio), 0.08)
        self.novel_image_button.pos_hint = {"center_x": self.x_dim_hint[self.trial_coord['Choice'][0]],
                                            "center_y": self.y_dim_hint[self.trial_coord['Choice'][1]]}
        self.novel_image_button.bind(on_press=self.novel_pressed)

        self.distractor_target_button_list = list()
        self.distractor_target_image_path = self.image_folder + self.distractor_target_image + '.png'

        for coord in self.distractor_target_list:
            index = 0
            image = ImageButton(source=self.distractor_target_image_path, allow_stretch=True)
            image.size_hint = ((0.08 * self.screen_ratio), 0.08)
            image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
            image.bind(on_press=lambda instance: self.distractor_target_press(instance, index))
            self.distractor_target_button_list.append(image)

        self.distractor_ignore_button_list = list()
        self.distractor_ignore_image_path = self.image_folder + self.distractor_ignore_image + '.png'

        for coord in self.distractor_ignore_list:
            image = ImageButton(source=self.distractor_ignore_image_path, allow_stretch=True)
            image.size_hint = ((0.08 * self.screen_ratio), 0.08)
            image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
            self.distractor_ignore_button_list.append(image)

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
        self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.98}

        # Define Widgets - Button
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

    # Initialization Functions

    def load_parameters(self, parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'TUNL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        if len(self.parameters_dict) == 0:
            self.parameters_dict = config_file['TaskParameters']
        else:
            self.participant_id = self.parameters_dict['participant_id']

        self.session_max_length = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.stimulus_image = self.parameters_dict['stimulus_image']
        self.distractor_ignore_image = self.parameters_dict['distractor_ignore_image']
        self.distractor_target_image = self.parameters_dict['distractor_target_image']
        self.num_target_distractors = int(self.parameters_dict['num_target_distractors'])
        self.num_ignore_distractors = int(self.parameters_dict['num_ignore_distractors'])
        self.block_distractor_increase = int(self.parameters_dict['block_distractor_increase'])
        self.block_length = int(self.parameters_dict['block_length'])
        self.block_count = int(self.parameters_dict['block_count'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.block_threshold = self.block_length

        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        self.present_instructions()

    def generate_distractor_pos(self, n_target, n_distractor):
        target_list = list()
        distractor_list = list()
        for a in range(n_target):
            x = random.randint(0, 7)
            y = random.randint(0, 7)
            coord = [x, y]
            while (coord is self.trial_coord) or (coord in target_list):
                x = random.randint(0, 7)
                y = random.randint(0, 7)
                coord = [x, y]
            target_list.append(coord)

        for a in range(n_distractor):
            x = random.randint(0, 7)
            y = random.randint(0, 7)
            coord = [x, y]
            while coord in (self.trial_coord or target_list or distractor_list):
                x = random.randint(0, 7)
                y = random.randint(0, 7)
                coord = [x, y]
            distractor_list.append(coord)
        return target_list, distractor_list

    def generate_output_files(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        if os.path.exists(folder_path) is False:
            os.makedirs(folder_path)
        file_index = 1
        temp_filename = self.participant_id + '_TUNL_' + str(file_index) + '.csv'
        self.data_output_path = folder_path + self.folder_mod + temp_filename
        while os.path.isfile(self.file_path):
            file_index += 1
            temp_filename = self.participant_id + '_TUNL_' + str(file_index) + '.csv'
            self.data_output_path = folder_path + self.folder_mod + temp_filename
        data_cols = 'TrialNo,Current Block,Sample_X,Sample_Y,Novel_X,Novel_Y,Num_Distractors,Correction Trial,' \
                    'Correct,Sample Latency,Distractor Delay Latency,True Delay Length, Choice Latency'
        data_file = open(self.file_path, "w+")
        data_file.write(data_cols)
        data_file.close()

    def metadata_output_generation(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        metadata_rows = ['participant_id', 'stimulus_image', 'distractor_target_image',
                         'distractor_ignore_image', 'num_target_distractors',
                         'num_ignore_distractors', 'block_distractor_increase',
                         'block_length', 'block_count', 'iti_length', 'session_length_max',
                         'session_trial_max']

        meta_list = list()
        for meta_row in metadata_rows:
            row_list = list()
            row_list.append(meta_row)
            row_list.append(str(self.parameters_dict[meta_row]))
            meta_list.append(row_list)

        file_index = 1
        meta_output_filename = self.participant_id + '_TUNL_Metadata_' + str(file_index) + '.csv'
        meta_output_path = folder_path + self.folder_mod + meta_output_filename
        while os.path.isfile(meta_output_path):
            file_index += 1
            meta_output_filename = self.participant_id + '_TUNL_Metadata_' + str(file_index) + '.csv'
            meta_output_path = folder_path + self.folder_mod + meta_output_filename
        meta_colnames = ['Parameter', 'Value']

        with open(meta_output_path, 'w') as meta_output_file:
            csv_writer = csv.writer(meta_output_file, delimiter=',')
            csv_writer.writerow(meta_colnames)
            for meta_param in meta_list:
                csv_writer.writerow(meta_param)

    # Start Task - Put Instructions on Screen
    def present_instructions(self):
        self.generate_output_files()
        self.metadata_output_generation()
        self.protocol_floatlayout.add_widget(self.instruction_label)
        self.protocol_floatlayout.add_widget(self.start_button)

    # Present Block Screen
    def block_screen(self, *args):
        if self.block_started is False:
            self.protocol_floatlayout.add_widget(self.block_label)
            self.block_start = time.time()
            self.block_started = True
            Clock.schedule_interval(self.block_screen, 0.1)
        if (time.time() - self.block_start) > self.block_min_rest_duration:
            Clock.unschedule(self.block_screen)
            self.protocol_floatlayout.add_widget(self.continue_button)

    # Remove Block Screen and Resume Task
    def block_end(self, *args):
        self.block_started = False
        self.protocol_floatlayout.clear_widgets()
        self.trial_contingency()
        for image_wid in self.background_grid_list:
            self.protocol_floatlayout.add_widget(image_wid)
        self.protocol_floatlayout.add_widget(self.hold_button)

    # End Experiment
    def protocol_end(self):
        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_widget(self.end_label)
        self.protocol_floatlayout.add_widget(self.return_button)

    # Return to Main Screen
    def return_to_main(self, *args):
        self.manager.current = 'mainmenu'

    # Protocol Staging

    # Create Hold Button and add 8x8 Grid
    def start_protocol(self, *args):
        self.protocol_floatlayout.remove_widget(self.instruction_label)
        self.protocol_floatlayout.remove_widget(self.start_button)
        self.start_clock()

        self.protocol_floatlayout.add_widget(self.hold_button)
        for image_wid in self.background_grid_list:
            self.protocol_floatlayout.add_widget(image_wid)
        self.feedback_label.text = self.feedback_string
        self.hold_button.size_hint_y = 0.2
        self.hold_button.width = self.hold_button.height
        self.hold_button.pos_hint = {"center_x": 0.5, "center_y": 0.1}
        self.hold_button.bind(on_press=self.iti)

    # ITI period
    def iti(self, *args):
        if self.iti_active is False:
            self.hold_button.unbind(on_press=self.iti)
            self.hold_button.bind(on_release=self.premature_response)
            self.start_iti = time.time()
            self.iti_active = True

            if self.feedback_string == self.hold_feedback_wait_str:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_string = ''

            if self.feedback_on_screen is False:
                self.feedback_label.text = self.feedback_string
                self.protocol_floatlayout.add_widget(self.feedback_label)
                self.feedback_on_screen = True
            Clock.schedule_interval(self.iti, 0.1)
        if self.iti_active is True:
            if (time.time() - self.start_iti) > self.feedback_length:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_on_screen = False
            if (time.time() - self.start_iti) > self.iti_length:
                Clock.unschedule(self.iti)
                self.iti_active = False
                self.hold_button.unbind(on_release=self.premature_response)
                self.sample_presentation()

    # Display Sample Stimuli
    def sample_presentation(self, *args):
        self.protocol_floatlayout.add_widget(self.sample_image_button)
        self.start_sample = time.time()
        self.stimulus_on_screen = True

    # Display Distractor During Delay
    def delay_presentation(self):

        self.protocol_floatlayout.remove_widget(self.sample_image_button)

        for image in self.distractor_ignore_button_list:
            self.protocol_floatlayout.add_widget(image)

        for image in self.distractor_target_button_list:
            self.protocol_floatlayout.add_widget(image)

    # Display Sample and Novel Stimuli
    def choice_presentation(self, *args):
        for image in self.distractor_ignore_button_list:
            self.protocol_floatlayout.remove_widget(image)

        self.choice_start = time.time()
        self.delay_length = self.choice_start - self.sample_touch_time
        self.protocol_floatlayout.add_widget(self.sample_image_button)
        self.protocol_floatlayout.add_widget(self.novel_image_button)

    # Stimuli Pressed too early
    def premature_response(self, *args):
        # return
        if self.stimulus_on_screen is True:
            return None

        Clock.unschedule(self.iti)
        self.feedback_string = self.hold_feedback_wait_str
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_string
        if self.feedback_on_screen is False:
            self.protocol_floatlayout.add_widget(self.feedback_label)
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)

    # Sample Stimuli Pressed during Choice
    def sample_pressed(self, *args):
        if self.sample_completed is False:
            self.sample_completed = True
            self.sample_touch_time = time.time()
            self.sample_lat = self.sample_touch_time - self.start_sample
            self.delay_presentation()
            return
        elif self.sample_completed is True:
            self.choice_touch_time = time.time()
            self.sample_press_to_choice = self.choice_touch_time - self.sample_touch_time
            self.choice_lat = self.choice_touch_time - self.choice_start
            self.protocol_floatlayout.remove_widget(self.sample_image_button)
            self.protocol_floatlayout.remove_widget(self.novel_image_button)
            self.feedback_string = self.stim_feedback_incorrect_str
            self.feedback_label.text = self.feedback_string
            self.current_correct = 0
            self.write_summary_file()

            self.current_correction = 1
            self.protocol_floatlayout.add_widget(self.feedback_label)
            self.feedback_on_screen = True
            self.hold_button.bind(on_press=self.iti)
            self.sample_completed = False
            return

    # Novel Stimuli Pressed during Choice
    def novel_pressed(self, *args):
        self.choice_touch_time = time.time()
        self.sample_press_to_choice = self.choice_touch_time - self.sample_touch_time
        self.choice_lat = self.choice_touch_time - self.choice_start
        self.protocol_floatlayout.remove_widget(self.sample_image_button)
        self.protocol_floatlayout.remove_widget(self.novel_image_button)
        self.feedback_string = self.stim_feedback_correct_str
        self.feedback_label.text = self.feedback_string
        self.current_correct = 1
        self.write_summary_file()

        self.current_correction = 0
        self.trial_contingency()
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.feedback_on_screen = True
        self.hold_button.bind(on_press=self.iti)
        self.sample_completed = False
        return

    # Distractor pressed during Choice
    def distractor_target_press(self, instance, *args):
        self.protocol_floatlayout.remove_widget(instance)
        self.distractor_press_count += 1

        if self.distractor_press_count >= self.num_target_distractors:
            self.choice_presentation()
            self.distractor_press_count = 0
            return
        else:
            return

            # Data Saving Function

    def write_summary_file(self):
        data_file = open(self.file_path, "a")
        data_file.write("\n")
        data_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
            self.current_trial, self.current_block, (self.sample_xpos + 1), (self.sample_ypos + 1),
            (self.novel_xpos + 1),
            (self.novel_ypos + 1), self.num_target_distractors, self.current_correction, self.current_correct,
            self.sample_lat, self.delay_length, self.sample_press_to_choice, self.choice_lat))
        data_file.close()
        return

    # Trial Contingency Functions
    def trial_contingency(self):
        self.current_trial += 1

        # Define Variables - Coordinates
        self.trial_coord = generate_sample_choice_pos()
        self.distractor_target_list, self.distractor_ignore_list = self.generate_distractor_pos(3, 3)

        self.sample_image_button.pos_hint = {"center_x": self.x_dim_hint[self.trial_coord['Sample'][0]],
                                             "center_y": self.y_dim_hint[self.trial_coord['Sample'][1]]}
        self.novel_image_button.pos_hint = {"center_x": self.x_dim_hint[self.trial_coord['Choice'][0]],
                                            "center_y": self.y_dim_hint[self.trial_coord['Choice'][1]]}

        self.distractor_target_list = list()
        self.distractor_ignore_list = list()

        for a in range(0, self.num_target_distractors):
            x = random.randint(0, 7)
            y = random.randint(0, 7)
            coord = [x, y]

            if a == 0:
                while coord in self.main_pair:
                    x = random.randint(0, 7)
                    y = random.randint(0, 7)
                    coord = [x, y]
                self.distractor_target_list.append(coord)
            else:
                while (coord in self.main_pair) or (coord in self.distractor_target_list):
                    x = random.randint(0, 7)
                    y = random.randint(0, 7)
                    coord = [x, y]
                self.distractor_target_list.append(coord)

        for a in range(0, self.num_ignore_distractors):
            x = random.randint(0, 7)
            y = random.randint(0, 7)
            coord = [x, y]
            if a == 0:
                while (coord in self.main_pair) or (coord in self.distractor_target_list):
                    x = random.randint(0, 7)
                    y = random.randint(0, 7)
                    coord = [x, y]
                self.distractor_ignore_list.append(coord)
            else:
                while (coord in self.main_pair) or (coord in self.distractor_target_list) or (
                        coord in self.distractor_ignore_list):
                    x = random.randint(0, 7)
                    y = random.randint(0, 7)
                    coord = [x, y]
                self.distractor_ignore_list.append(coord)

        self.distractor_target_button_list = list()
        for coord in self.distractor_target_list:
            index = 0
            image = ImageButton(source=self.distractor_target_image_path, allow_stretch=True)
            image.size_hint = ((0.08 * self.screen_ratio), 0.08)
            image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
            image.bind(on_press=lambda instance: self.distractor_target_press(instance, index))
            self.distractor_target_button_list.append(image)

        self.distractor_ignore_button_list = list()
        for coord in self.distractor_ignore_list:
            image = ImageButton(source=self.distractor_ignore_image_path, allow_stretch=True)
            image.size_hint = ((0.08 * self.screen_ratio), 0.08)
            image.pos_hint = {"center_x": self.x_dim_hint[coord[0]], "center_y": self.y_dim_hint[coord[1]]}
            self.distractor_ignore_button_list.append(image)

        if self.current_trial > self.block_threshold:
            self.feedback_start = time.time()
            self.protocol_floatlayout.remove_widget(self.hold_button)
            self.block_threshold += self.block_length
            Clock.schedule_interval(self.block_contingency, 0.1)
            return

        if self.current_trial > self.session_trial_max:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()
            return

    # Block Contingency Function
    def block_contingency(self):
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

        if self.current_block > self.block_count:
            self.protocol_end()
            return

        self.num_target_distractors += self.block_distractor_increase
        self.num_ignore_distractors += self.block_distractor_increase

        self.generate_trial_contingency()

        self.current_block += 1

        self.block_screen()

    # Start Task Clock
    def start_clock(self, *args):
        self.start_time = time.time()
        Clock.schedule_interval(self.clock_monitor, 0.1)
        Clock.schedule_interval(self.display_monitor, 0.1)

    # Update Clock
    def clock_monitor(self, *args):
        self.current_time = time.time()
        self.elapsed_time = self.current_time - self.start_time

        if self.elapsed_time > self.session_max_length:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()

    # Get Display Information
    def display_monitor(self, *args):
        width = self.protocol_floatlayout.width
        height = self.protocol_floatlayout.height

        self.screen_ratio = width / height
