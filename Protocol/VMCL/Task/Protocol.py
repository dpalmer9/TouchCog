import configparser
import time
from Classes.Protocol import ImageButton, ProtocolBase


class ProtocolScreen(ProtocolBase):
    def __init__(self, **kwargs):
        super(ProtocolScreen,self).__init__(**kwargs)
        self.protocol_name = 'VMCL'
        self.update_task()

        # Define Variables - Folder Path
        self.image_folder = 'Protocol' + self.folder_mod + 'PAL' + self.folder_mod + 'Image' + self.folder_mod
        self.data_output_path = None

        # Define Data Columns

        self.data_cols = ['TrialNo', 'Current Stage', 'Sample Image', 'Correct Location', 'Incorrect Location',
                          'Correction Trial', 'Location Chosen', 'Correct', 'Omission', 'Response Latency']

        self.metadata_cols = ['participant_id', 'training_image', 'left_resp_image', 'right_resp_image',
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

        # Define Variables - Counter


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

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path

        self.left_image_path = self.image_folder + self.response_image + '.png'
        self.left_image = ImageButton(source=self.left_image_path)

        self.right_image_path = self.image_folder + self.response_image + '.png'
        self.right_image = ImageButton(source=self.right_image_path)

        self.sample_image_path = self.image_folder + self.trial_list[self.trial_index] + '.png'
        self.sample_image = ImageButton(source=self.sample_image_path)

    def load_parameters(self, parameter_dict)
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

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path

        self.left_image_path = self.image_folder + self.response_image + '.png'
        self.left_image = ImageButton(source=self.left_image_path)
        self.left_image.pos_hint = {"center_x": 0.2, "center_y": 0.6}

        self.right_image_path = self.image_folder + self.response_image + '.png'
        self.right_image = ImageButton(source=self.right_image_path)
        self.right_image.pos_hint = {"center_x": 0.8, "center_y": 0.6}

        self.sample_image_path = self.image_folder + self.trial_list[self.trial_index] + '.png'
        self.sample_image = ImageButton(source=self.sample_image_path)
        self.center_stimulus.pos_hint = {"center_x": 0.5, "center_y": 0.6}

        self.present_instructions()

        # Protocol Staging

    def present_sample(self, *args):
        self.sample_image.texture = self.image_dict[self.trial_list[self.trial_index]].image.texture

        self.protocol_floatlayout.add_widget(self.sample_image)
        self.sample_image.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))

        self.start_sample = time.time()
        self.sample_on_screen = True

    def sample_pressed(self, *args):
        self.protocol_floatlayout.remove_widget(self.sample_image)

        self.protocol_floatlayout.add_widget(self.left_image)
        self.protocol_floatlayout.add_widget(self.right_image)

        self.left_image.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
        self.right_image.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))

    def left_choice_press(self, *args):
        if self.trial_list[self.trial_index] == self.left_resp_image:
            return
        else:
            return

    def right_choice_press(self, *args):
        if self.trial_list[self.trial_index] == self.right_resp_image:
            return
        else:
            return



        

