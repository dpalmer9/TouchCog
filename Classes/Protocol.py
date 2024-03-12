# Import
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import ButtonBehavior, Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
import pandas as pd
import configparser
import sys
import os
import time


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
        self.touch_pos = [0, 0]
        self.held_name = ''
        self.event_columns = ['Time', 'Event_Type', 'Event_Name', 'Arg1_Name', 'Arg1_Value',
                              'Arg2_Name', 'Arg2_Value', 'Arg3_Name', 'Arg3_Value']
        self.event_dataframe = pd.DataFrame(columns=self.event_columns)
        self.event_index = 0
        self.save_path = ''
        self.elapsed_time = 0
        self.touch_time = 0
        self.start_time = 0

    def filter_children(self,string):
        return
    def on_touch_down(self, touch):
        self.touch_pos = touch.pos
        self.touch_time = time.time() - self.start_time
        if self.disabled and self.collide_point(*touch.pos):
            return True
        for child in self.children:
            if child.dispatch('on_touch_down', touch):
                if isinstance(child, ImageButton):
                    self.held_name = child.name
                else:
                    self.held_name = ''
                self.add_event([self.touch_time, 'Screen', 'Touch Press', 'X Position', self.touch_pos[0],
                                'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])
                return True
        self.held_name = ''
        self.add_event([self.touch_time, 'Screen', 'Touch Press', 'X Position',
                        self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])

    def on_touch_move(self, touch):
        self.touch_pos = touch.pos
        self.touch_time = time.time() - self.start_time
        if self.disabled:
            return
        for child in self.children:
            if child.dispatch('on_touch_move', touch):
                if isinstance(child, ImageButton):
                    self.held_name = child.name
                else:
                    self.held_name = ''
                self.add_event([self.touch_time, 'Screen', 'Touch Move', 'X Position',
                                self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])
                return True
        self.held_name = ''
        self.add_event([self.touch_time, 'Screen', 'Touch Press', 'X Position',
                        self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])

    def on_touch_up(self, touch):
        self.touch_pos = touch.pos
        self.touch_time = time.time() - self.start_time
        if self.disabled:
            return
        for child in self.children:
            if child.dispatch('on_touch_up', touch):
                if isinstance(child, ImageButton):
                    self.held_name = child.name
                else:
                    self.held_name = ''
                self.add_event([self.touch_time, 'Screen', 'Touch Release', 'X Position',
                                self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])
                return True
        self.add_event([self.touch_time, 'Screen', 'Touch Release', 'X Position',
                        self.touch_pos[0], 'Y Position', self.touch_pos[1], 'Stimulus Name', self.held_name])
        if self.held_name != '':
            self.held_name = ''

    def add_event(self, row):
        self.event_dataframe.loc[self.event_index] = row
        self.event_index += 1
        if self.save_path != '':
            self.event_dataframe.to_csv(self.save_path, index=False)

    def update_path(self, path):
        self.save_path = path


class ProtocolBase(Screen):
    def __init__(self, **kwargs):
        super(ProtocolBase, self).__init__(**kwargs)
        self.name = 'protocolscreen'

        if sys.platform == 'linux' or sys.platform == 'darwin':
            self.folder_mod = '/'
        elif sys.platform == 'win32':
            self.folder_mod = '\\'

        self.protocol_floatlayout = FloatLayoutLog()
        self.add_widget(self.protocol_floatlayout)

        # Define Folders
        self.protocol_name = ''
        self.image_folder = ''
        self.config_path = ''
        self.file_path = ''

        # Define Datafile
        self.meta_data = pd.DataFrame()
        self.session_data = pd.DataFrame()
        self.data_cols = []
        self.metadata_cols = []

        # Define General Parameters
        self.participant_id = 'Default'
        self.block_max_length = 0
        self.block_max_count = 0
        self.block_min_rest_duration = 0.00
        self.session_length_max = 0.00
        self.session_trial_max = 0
        self.iti_length = 0.00
        self.feedback_length = -1.00
        self.hold_image = ''
        self.mask_image = ''

        # Define Language
        self.language = 'English'
        self.start_label_str = ''
        self.break_label_str = ''
        self.end_label_str = ''
        self.start_button_label_str = ''
        self.continue_button_label_str = ''
        self.return_button_label_str = ''
        self.stim_feedback_correct_str = ''
        self.stim_feedback_incorrect_str = ''
        self.hold_feedback_wait_str = ''
        self.hold_feedback_return_str = ''

        # Define Variables - Boolean
        self.stimulus_on_screen = False
        self.iti_active = False
        self.block_started = False
        self.feedback_on_screen = False
        self.hold_active = True

        # Define Variables - Counter
        self.current_block = 1
        self.current_trial = 1
        self.stage_index = 0

        # Define Variables - Time
        self.start_iti = 0
        self.start_time = 0
        self.block_start = 0
        self.elapsed_time = 0
        self.feedback_start_time = 0

        # Define Class - Clock
        self.iti_clock = Clock
        self.session_clock = Clock
        self.block_clock = Clock

        # Define Dictionaries
        self.parameters_dict = {}
        self.feedback_dict = {}

        # Define Widgets - Images
        self.hold_button = ImageButton()
        self.hold_button.pos_hint = {"center_x": 0.5, "center_y": 0.1}
        self.hold_button.name = 'Hold Button'

        # Define Widgets - Text
        self.instruction_label = Label(font_size='35sp')
        self.instruction_label.size_hint = (0.6, 0.4)
        self.instruction_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.block_label = Label(font_size='50sp')
        self.block_label.size_hint = (0.5, 0.3)
        self.block_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.end_label = Label(font_size='50sp')
        self.end_label.size_hint = (0.6, 0.4)
        self.end_label.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        self.feedback_string = ''
        self.feedback_label = Label(text=self.feedback_string, font_size='50sp', markup=True)
        self.feedback_label.size_hint = (0.7, 0.4)
        self.feedback_label.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # Define Widgets - Buttons
        self.start_button = Button()
        self.start_button.size_hint = (0.1, 0.1)
        self.start_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.start_button.bind(on_press=self.start_protocol)

        self.continue_button = Button()
        self.continue_button.size_hint = (0.1, 0.1)
        self.continue_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.continue_button.bind(on_press=self.block_end)

        self.return_button = Button()
        self.return_button.size_hint = (0.1, 0.1)
        self.return_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        self.return_button.bind(on_press=self.return_to_main)

    def update_task(self):
        self.image_folder = 'Protocol' + self.folder_mod + self.protocol_name + self.folder_mod + 'Image' + \
                            self.folder_mod

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

    def generate_output_files(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_index = 1
        temp_filename = self.participant_id + self.protocol_name + str(file_index) + '.csv'
        self.file_path = folder_path + self.folder_mod + temp_filename
        while os.path.isfile(self.file_path):
            file_index += 1
            temp_filename = self.participant_id + self.protocol_name + str(file_index) + '.csv'
            self.file_path = folder_path + self.folder_mod + temp_filename

        self.session_data = pd.DataFrame(columns=self.data_cols)
        self.session_data.to_csv(path_or_buf=self.file_path, sep=',', index=False)

        event_path = folder_path + self.folder_mod + self.participant_id + self.protocol_name + str(
            file_index) + '_Event_Data.csv'
        self.protocol_floatlayout.update_path(event_path)

    def metadata_output_generation(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id

        meta_list = list()
        for meta_row in self.metadata_cols:
            row_list = list()
            row_list.append(meta_row)
            row_list.append(str(self.parameters_dict[meta_row]))
            meta_list.append(row_list)

        file_index = 1
        meta_output_filename = self.participant_id + '_' + self.protocol_name + '_Metadata_' + str(file_index) + '.csv'
        meta_output_path = folder_path + self.folder_mod + meta_output_filename
        while os.path.isfile(meta_output_path):
            file_index += 1
            meta_output_filename = self.participant_id + '_' + self.protocol_name + '_Metadata_' + str(file_index) + \
                                   '.csv'
            meta_output_path = folder_path + self.folder_mod + meta_output_filename

        self.meta_data = pd.DataFrame(meta_list, columns=['Parameter', 'Value'])
        self.meta_data.to_csv(path_or_buf=meta_output_path, sep=',', index=False)

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
                [(time.time() - self.start_time), 'Text Displayed', 'Block Instruction', '', '',
                 '', '', '', ''])
            self.block_start = time.time()
            self.block_started = True
            Clock.schedule_interval(self.block_screen, 0.01)
        if (time.time() - self.block_start) > self.block_min_rest_duration:
            Clock.unschedule(self.block_screen)
            self.protocol_floatlayout.add_widget(self.continue_button)
            self.protocol_floatlayout.add_event(
                [(time.time() - self.start_time), 'Button Displayed', 'Continue Button', '', '',
                 '', '', '', ''])

    def block_end(self, *args):
        self.block_started = False
        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_event(
            [(time.time() - self.start_time), 'Text Removed', 'Block Instruction', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [(time.time() - self.start_time), 'Button Removed', 'Continue Button', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_widget(self.hold_button)
        self.protocol_floatlayout.add_event(
            [(time.time() - self.start_time), 'Button Displayed', 'Hold Button', '', '',
             '', '', '', ''])

    # End Staging #
    def protocol_end(self, *args):
        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_widget(self.end_label)
        self.protocol_floatlayout.add_event(
            [(time.time() - self.start_time), 'Text Displayed', 'End Instruction', '', '',
             '', '', '', ''])
        self.protocol_floatlayout.add_widget(self.return_button)
        self.protocol_floatlayout.add_event(
            [(time.time() - self.start_time), 'Button Displayed', 'Return Button', '', '',
             '', '', '', ''])

    def return_to_main(self, *args):
        self.manager.current = 'mainmenu'

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
            [(time.time() - self.start_time), 'Button Displayed', 'Hold Button', '', '',
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
                [(time.time() - self.start_time), 'Stage Change', 'ITI Start', '', '',
                 '', '', '', ''])

            if self.feedback_string == self.feedback_dict['wait']:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.protocol_floatlayout.add_event(
                    [(time.time() - self.start_time), 'Text Removed', 'Feedback', '', '',
                     '', '', '', ''])
                self.feedback_string = ''

            if not self.feedback_on_screen:
                self.feedback_label.text = self.feedback_string
                self.protocol_floatlayout.add_widget(self.feedback_label)
                self.protocol_floatlayout.add_event(
                    [(time.time() - self.start_time), 'Text Displayed', 'Feedback', '', '',
                     '', '', '', ''])
                self.feedback_start_time = time.time()
                self.feedback_on_screen = True
            if ((time.time() - self.feedback_start_time) > self.feedback_length) and self.feedback_on_screen and \
                    self.feedback_length > 0:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.protocol_floatlayout.add_event(
                    [(time.time() - self.start_time), 'Text Removed', 'Feedback', '', '',
                     '', '', '', ''])
                self.feedback_on_screen = False
            Clock.schedule_interval(self.iti, 0.01)
        if self.iti_active:
            if (((time.time() - self.start_iti) > self.feedback_length) or (
                    (time.time() - self.feedback_start_time) > self.feedback_length)) and self.feedback_on_screen:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.protocol_floatlayout.add_event(
                    [(time.time() - self.start_time), 'Text Removed', 'Feedback', '', '',
                     '', '', '', ''])
                self.feedback_on_screen = False
            if (time.time() - self.start_iti) > self.iti_length:
                Clock.unschedule(self.iti)
                self.iti_active = False
                self.protocol_floatlayout.add_event(
                    [(time.time() - self.start_time), 'Stage Change', 'ITI End', '', '',
                     '', '', '', ''])
                self.hold_button.unbind(on_release=self.premature_response)
                self.hold_active = True
                self.stimulus_presentation()

    def write_summary_file(self, data_row):
        data_row = pd.Series(data_row, index=self.data_cols)
        self.session_data = pd.concat([self.session_data, data_row.to_frame().T], axis=0, ignore_index=True)
        self.session_data.to_csv(path_or_buf=self.file_path, sep=',', index=False)
        return

    def start_clock(self, *args):
        self.start_time = time.time()
        self.session_clock.schedule_once(self.clock_monitor, self.session_length_max)
        self.protocol_floatlayout.start_time = self.start_time
        return

    def clock_monitor(self, *args):
        Clock.unschedule(self.session_clock)
        self.protocol_end()
        return