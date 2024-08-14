import configparser
import time
import random
from Classes.Protocol import ImageButton, ProtocolBase


class ProtocolScreen(ProtocolBase):
    def __init__(self, **kwargs):
        super(ProtocolScreen,self).__init__(**kwargs)
        self.protocol_name = 'VMCL'
        self.update_task()

        # Define Variables - Folder Path
        self.image_folder = 'Protocol' + self.folder_mod + 'VMCL' + self.folder_mod + 'Image' + self.folder_mod
        self.data_output_path = None

        # Define Data Columns

        self.data_cols = ['TrialNo', 'Current Stage', 'Sample Image', 'Correct Location', 'Incorrect Location',
                          'Correction Trial', 'Location Chosen', 'Correct', 'Omission', 'Correction Trial','Response Latency']

        self.metadata_cols = ['participant_id', 'left_resp_image', 'right_resp_image',
                              'response_image', 'iti_length', 'stimulus_duration', 'limited_hold', 'block_length',
                              'block_count', 'session_length_max','session_trial_max']

        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + 'VMCL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        self.parameters_dict = config_file['TaskParameters']

        self.iti_length = float(self.parameters_dict['iti_length'])
        self.stimulus_duration = float(self.parameters_dict['stimulus_duration'])
        self.limited_hold = float(self.parameters_dict['limited_hold'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.left_resp_image = self.parameters_dict['left_resp_image']
        self.right_resp_image = self.parameters_dict['right_resp_image']
        self.response_image = self.parameters_dict['response_image']
        total_images = [self.left_resp_image, self.right_resp_image, self.response_image]
        self.load_images(total_images)
        self.block_length = int(self.parameters_dict['block_length'])
        self.block_count = int(self.parameters_dict['block_count'])
        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = float(self.parameters_dict['session_trial_max'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']
        self.correction_trials_enabled = False

        # Define Language
        self.language = 'English'
        self.set_language(self.language)

        # Define Variables - List

        # Define Variables - Boolean
        self.correction_trial = False
        self.sample_on_screen = False
        self.limited_hold_started = False

        # Define Variables - Numeric
        self.correct_location = 1
        self.incorrect_location = 3
        self.correction = 0

        # Define Variables - String
        self.current_stage = 'Main'
        self.feedback_string = ''

        # Define Variables - Time
        self.start_sample = 0
        self.start_choice = 0
        self.response_lat = 0

        # Define Variables - Trial Configuration
        total_trials = self.block_length * self.block_count
        if (total_trials % 2) != 0:
            total_trials += 1
        cont_count = total_trials/2
        self.trial_list = []
        self.trial_list.extend([self.left_resp_image for i in range(int(cont_count))])
        self.trial_list.extend([self.right_resp_image for i in range(int(cont_count))])
        random.shuffle(self.trial_list)
        self.trial_index = 0

        self.block_threshold = self.block_length

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path

        self.left_image_path = self.image_folder + self.response_image + '.png'
        self.left_image = ImageButton(source=self.left_image_path)

        self.right_image_path = self.image_folder + self.response_image + '.png'
        self.right_image = ImageButton(source=self.right_image_path)

        self.sample_image_path = self.image_folder + self.trial_list[self.trial_index] + '.png'
        self.sample_image = ImageButton(source=self.sample_image_path)

    def load_parameters(self, parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'VMCL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        self.participant_id = self.parameters_dict['participant_id']
        self.language = self.parameters_dict['language']

        # Define Variables - Config
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.stimulus_duration = float(self.parameters_dict['stimulus_duration'])
        self.limited_hold = float(self.parameters_dict['limited_hold'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.left_resp_image = self.parameters_dict['left_resp_image']
        self.right_resp_image = self.parameters_dict['right_resp_image']
        self.response_image = self.parameters_dict['response_image']
        total_images = [self.left_resp_image, self.right_resp_image, self.response_image]
        self.load_images(total_images)
        self.block_length = int(self.parameters_dict['block_length'])
        self.block_count = int(self.parameters_dict['block_count'])
        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = float(self.parameters_dict['session_trial_max'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']
        self.correction_trials_enabled = self.parameters_dict['correction_trials']
        if self.correction_trials_enabled == 'Correction Trials Enabled':
            self.correction_trials_enabled = True
        else:
            self.correction_trials_enabled = False

        # Define Language
        self.set_language(self.language)

        # Define Clock
        self.session_event = self.session_clock.create_trigger(self.clock_monitor, self.session_length_max,
                                                               interval=False)
        self.remove_choice_event = self.session_clock.create_trigger(self.sample_pressed, 0, interval=True)

        # Define Variables - Trial Configuration
        total_trials = self.block_length * self.block_count
        if (total_trials % 2) != 0:
            total_trials += 1
        cont_count = total_trials / 2
        self.trial_list = []
        self.trial_list.extend([self.left_resp_image for i in range(int(cont_count))])
        self.trial_list.extend([self.right_resp_image for i in range(int(cont_count))])
        random.shuffle(self.trial_list)
        self.trial_index = 0
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Stimulus Image', 'Value', str(self.trial_list[self.trial_index]),
             '', '', '', ''])

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path

        self.left_image_path = self.image_folder + self.response_image + '.png'
        self.left_image = ImageButton(source=self.left_image_path)
        self.left_image.pos_hint = {"center_x": 0.2, "center_y": 0.6}
        self.left_image.bind(on_press=self.left_choice_press)

        self.right_image_path = self.image_folder + self.response_image + '.png'
        self.right_image = ImageButton(source=self.right_image_path)
        self.right_image.pos_hint = {"center_x": 0.8, "center_y": 0.6}
        self.right_image.bind(on_press=self.right_choice_press)

        self.sample_image_path = self.image_folder + self.trial_list[self.trial_index] + '.png'
        self.sample_image = ImageButton(source=self.sample_image_path)
        self.sample_image.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.sample_image.bind(on_press=self.sample_pressed)

        self.present_instructions()

        # Protocol Staging

    def stimulus_presentation(self, *args):
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Stage Change', 'Display Sample', '', '',
             '', '', '', ''])
        self.sample_image.texture = self.image_dict[self.trial_list[self.trial_index]].image.texture
        self.left_image.source = self.image_folder + self.response_image + '.png'
        self.right_image.source = self.image_folder + self.response_image + '.png'

        self.protocol_floatlayout.add_widget(self.sample_image)
        self.sample_image.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))

        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Displayed', 'Sample Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.trial_list[self.trial_index]])

        self.start_sample = time.time()
        self.sample_on_screen = True

    def sample_pressed(self, *args):
        if not self.stimulus_on_screen:
            self.protocol_floatlayout.remove_widget(self.sample_image)
            self.protocol_floatlayout.add_event(
                [time.time() - self.start_time, 'Image Removed', 'Sample Stimulus', 'X Position', '3',
                 'Y Position', '1', 'Image Name', self.trial_list[self.trial_index]])

            self.protocol_floatlayout.add_event(
                [time.time() - self.start_time, 'Stage Change', 'Display Choice', '', '',
                 '', '', '', ''])
            self.protocol_floatlayout.add_widget(self.left_image)
            self.protocol_floatlayout.add_widget(self.right_image)

            self.left_image.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
            self.right_image.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
            self.protocol_floatlayout.add_event(
                [time.time() - self.start_time, 'Image Displayed', 'Left Response Stimulus', 'X Position', '2',
                 'Y Position', '1', 'Image Name', self.response_image])
            self.protocol_floatlayout.add_event(
                [time.time() - self.start_time, 'Image Displayed', 'Right Response Stimulus', 'X Position', '2',
                 'Y Position', '1', 'Image Name', self.response_image])
            self.start_stimulus = time.time()
            self.stimulus_on_screen = True
            self.remove_choice_event()
            return
        else:
            if ((time.time() - self.start_stimulus) > self.stimulus_duration) and not self.limited_hold_started:
                self.left_image.source = self.image_folder + 'black.png'
                self.right_image.source = self.image_folder + 'black.png'
                self.protocol_floatlayout.add_event(
                    [time.time() - self.start_time, 'Stage Change', 'Remove Choice Windows', '', '',
                     '', '', '', ''])
                self.protocol_floatlayout.add_event(
                    [time.time() - self.start_time, 'Image Removed', 'Left Response Stimulus', 'X Position', '2',
                     'Y Position', '1', 'Image Name', self.response_image])
                self.protocol_floatlayout.add_event(
                    [time.time() - self.start_time, 'Image Removed', 'Right Response Stimulus', 'X Position', '2',
                     'Y Position', '1', 'Image Name', self.response_image])
                self.limited_hold_started = True
                return

            if (time.time() - self.start_stimulus) > self.limited_hold:
                self.protocol_floatlayout.add_event(
                    [time.time() - self.start_time, 'Stage Change', 'Limited Hold End', '', '',
                     '', '', '', ''])
                self.remove_choice_event.cancel()
                self.limited_hold_end()




    def premature_response(self, *args):
        if self.stimulus_on_screen:
            return None

        self.iti_event.cancel()
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Stage Change', 'Premature Response', '', '',
             '', '', '', ''])
        self.feedback_string = self.feedback_dict['wait']
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_dict['wait']
        if self.feedback_on_screen == False:
            self.protocol_floatlayout.add_widget(self.feedback_label)
            self.protocol_floatlayout.add_event(
                [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
                 '', '', '', ''])
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)

    def left_choice_press(self, *args):
        print('left')
        self.remove_choice_event.cancel()
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_image)
        self.protocol_floatlayout.remove_widget(self.right_image)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Left Response Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.response_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Right Response Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.response_image])
        self.left_chosen = 1
        self.right_chosen = 0
        self.location_chosen = 'left'
        self.omission = 0
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Omission', 'Value', str(self.omission),
             '', '', '', ''])
        if self.trial_list[self.trial_index] == self.left_resp_image:
            correct = 1
            self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Correct', 'Value', str(correct),
             '', '', '', ''])
            self.correct_location = 'left'
            self.incorrect_location = 'right'
            self.feedback_string = self.feedback_dict['correct']
        else:
            correct = 0
            self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Correct', 'Value', str(correct),
             '', '', '', ''])
            self.correct_location = 'right'
            self.incorrect_location = 'left'
            self.feedback_string = self.feedback_dict['incorrect']
        self.feedback_label.text = self.feedback_string
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_trial(correct)
        if self.correction_trials_enabled:
            if correct == 0:
                self.correction_trial = True
                self.correction = 1
                self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Correction', 'Value', str(self.correction),
             '', '', '', ''])
            else:
                self.correction_trial = False
                self.trial_contingency()
                self.correction = 0
                self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Correction', 'Value', str(self.correction),
             '', '', '', ''])
        else:
            self.correction_trial = False
            self.trial_contingency()

        self.hold_button.bind(on_press= self.iti)

    def right_choice_press(self, *args):
        print('right')
        self.remove_choice_event.cancel()
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_image)
        self.protocol_floatlayout.remove_widget(self.right_image)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Left Response Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.response_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Right Response Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.response_image])
        self.left_chosen = 0
        self.right_chosen = 1
        self.location_chosen = 'right'
        self.omission = 0
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Omission', 'Value', str(self.omission),
             '', '', '', ''])
        if self.trial_list[self.trial_index] == self.right_resp_image:
            correct = 1
            self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Correct', 'Value', str(correct),
             '', '', '', ''])
            self.correct_location = 'right'
            self.incorrect_location = 'left'
            self.feedback_string = self.feedback_dict['correct']
        else:
            correct = 0
            self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Correct', 'Value', str(correct),
             '', '', '', ''])
            self.correct_location = 'left'
            self.incorrect_location = 'right'
            self.feedback_string = self.feedback_dict['incorrect']
        self.feedback_label.text = self.feedback_string
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_trial(correct)
        if self.correction_trials_enabled:
            if correct == 0:
                self.correction_trial = True
                self.correction = 1
                self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Correction', 'Value', str(self.correction),
             '', '', '', ''])
            else:
                self.correction_trial = False
                self.trial_contingency()
                self.correction = 0
                self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Correction', 'Value', str(self.correction),
             '', '', '', ''])
        else:
            self.correction_trial = False
            self.trial_contingency()

        self.hold_button.bind(on_press=self.iti)

    def limited_hold_end(self, *args):
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_image)
        self.protocol_floatlayout.remove_widget(self.right_image)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Left Response Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.response_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Right Response Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.response_image])
        self.left_chosen = 0
        self.right_chosen = 0
        self.omission = 1
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Trial Omission', 'Value', str(self.omission),
             '', '', '', ''])
        self.location_chosen = 'None'
        correct = 0
        if self.trial_list[self.trial_index] == self.right_resp_image:
            self.correct_location = 'right'
            self.incorrect_location = 'left'
        else:
            self.correct_location = 'left'
            self.incorrect_location = 'right'
        self.feedback_string = self.feedback_dict['incorrect']
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_trial(correct)
        self.trial_contingency()
        self.hold_button.bind(on_press=self.iti)

    def write_trial(self, correct):
        if self.correction_trial:
            correction = 1
        else:
            correction = 0
        trial_data = [self.current_trial, self.current_stage, self.trial_list[self.trial_index], self.correct_location,
                      self.incorrect_location, self.location_chosen, correct, self.omission, self.correction,
                      self.response_lat]
        self.write_summary_file(trial_data)
        return

    def trial_contingency(self):
        self.current_trial += 1
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Current Trial', 'Value', str(self.current_trial),
             '', '', '', ''])

        if self.current_trial > self.session_trial_max:
            self.session_event.cancel()
            self.protocol_end()
            return

        if self.current_trial > self.block_threshold:
            self.block_contingency()
            self.block_threshold += self.block_length
            return


        self.trial_index += 1
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Stimulus Image', 'Value', str(self.trial_list[self.trial_index]),
             '', '', '', ''])

    def block_contingency(self):
        self.protocol_floatlayout.clear_widgets()
        if self.current_block > self.block_count:
            self.protocol_end()
            return
        self.trial_index += 1
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Stimulus Image', 'Value', str(self.trial_list[self.trial_index]),
             '', '', '', ''])
        self.block_screen()



        

