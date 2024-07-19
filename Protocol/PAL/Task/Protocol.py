# Imports #
import configparser
import time
from Classes.Protocol import ImageButton, ProtocolBase
import random


class ProtocolScreen(ProtocolBase):
    def __init__(self,**kwargs):
        super(ProtocolScreen,self).__init__(**kwargs)
        self.protocol_name = 'PAL'
        self.update_task()
        
        # Define Variables - Folder Path
        self.image_folder = 'Protocol' + self.folder_mod + 'PAL' + self.folder_mod + 'Image' + self.folder_mod
        self.data_output_path = None

        # Define Data Columns

        self.data_cols = ['TrialNo', 'Current Stage', 'Correct Image', 'Incorrect Image', 'Correct Location',
                                      'Incorrect Location', 'Correction Trial', 'Location Chosen',
                                      'Correct', 'Response Latency']
        self.metadata_cols = ['participant_id', 'training_image', 'test_images', 'iti_length', 'block_length',
                              'block_count', 'location_1_correct', 'location_2_correct', 'location_3_correct',
                              'session_length_max', 'session_trial_max', 'pal_type']

        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + 'PAL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        self.parameters_dict = config_file['TaskParameters']

        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.training_image = self.parameters_dict['training_image']
        self.training_image_incorrect = 'Grey'
        self.test_images = self.parameters_dict['test_images']
        self.test_images = self.test_images.split(',')
        self.l1_correct = self.parameters_dict['location_1_correct']
        self.l2_correct = self.parameters_dict['location_2_correct']
        self.l3_correct = self.parameters_dict['location_3_correct']
        total_images = [self.training_image,self.training_image_incorrect,'black'] + self.test_images
        self.load_images(total_images)
        self.block_length = int(self.parameters_dict['block_length'])
        self.block_count = int(self.parameters_dict['block_count'])
        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = float(self.parameters_dict['session_trial_max'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']
        self.paltype = 'dPAL'
        self.correction_trials_enabled = False

        # Define Language
        self.language = 'English'
        self.set_language(self.language)
        # Define Variables - List
        self.stage_list = ['Training', 'Test']

        # Define Variables - Boolean
        self.correction_trial = True

        # Define Variables - Counter
        self.current_correct = 0
        self.left_chosen = 0
        self.center_chosen = 0
        self.right_chosen = 0
        self.location_chosen = 0

        # Define Variables - String
        self.correct_image = self.training_image
        self.incorrect_image = self.training_image_incorrect
        self.current_stage = self.stage_list[self.stage_index]
        self.feedback_string = ''
        self.l1_image = ''
        self.l2_image = ''
        self.l3_image = ''

        # Define Variables - Time
        self.start_stimulus = 0
        self.response_lat = 0
        self.correct_location = 0
        self.incorrect_location = 0

        # Define Variables - Trial Configuration
        self.trial_configuration = random.randint(1, 6)
        self.generate_trial_contingency(training=True)

        self.block_threshold = 10 + self.block_length

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path

        self.left_stimulus_image_path = self.image_folder + self.l1_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path)

        self.center_stimulus_image_path = self.image_folder + self.l2_image + '.png'
        self.center_stimulus = ImageButton(source=self.left_stimulus_image_path)

        self.right_stimulus_image_path = self.image_folder + self.l3_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path)

    # Initialization Functions #
        
    def load_parameters(self,parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'PAL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        self.participant_id = self.parameters_dict['participant_id']
        self.language = self.parameters_dict['language']

        # Define Variables - Config
        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.training_image = self.parameters_dict['training_image']
        self.training_image_incorrect = 'Grey'
        self.test_images = self.parameters_dict['test_images']
        self.test_images = self.test_images.split(',')
        self.l1_correct = self.parameters_dict['location_1_correct']
        self.l2_correct = self.parameters_dict['location_2_correct']
        self.l3_correct = self.parameters_dict['location_3_correct']
        self.block_length = int(self.parameters_dict['block_length'])
        self.block_count = int(self.parameters_dict['block_count'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']
        self.paltype = self.parameters_dict['pal_type']
        self.correction_trials_enabled = self.parameters_dict['correction_trials']
        if self.correction_trials_enabled == 'Correction Trials Enabled':
            self.correction_trials_enabled = True
        else:
            self.correction_trials_enabled = False

        # Define Language
        self.set_language(self.language)

        # Define Variables - String
        self.correct_image = self.training_image
        self.incorrect_image = self.training_image_incorrect
        self.current_stage = self.stage_list[self.stage_index]
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Current Stage', 'Value', str(self.current_stage),
             '', '', '', ''])
        self.feedback_string = ''
        
        # Define Clock
        self.session_event = self.session_clock.create_trigger(self.clock_monitor, self.session_length_max, interval=False)

        # Define Variables - Trial Configuration
        self.trial_configuration = random.randint(1, 6)
        self.generate_trial_contingency(training=True)

        self.block_threshold = 10 + self.block_length

        # Define Widgets - Images
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button.source = self.hold_button_image_path

        self.left_stimulus_image_path = self.image_folder + self.l1_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path)
        self.left_stimulus.pos_hint = {"center_x": 0.2, "center_y": 0.6}
        self.left_stimulus.bind(on_press=self.left_stimulus_pressed)

        self.center_stimulus_image_path = self.image_folder + self.l2_image + '.png'
        self.center_stimulus = ImageButton(source=self.left_stimulus_image_path)
        self.center_stimulus.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.center_stimulus.bind(on_press=self.center_stimulus_pressed)

        self.right_stimulus_image_path = self.image_folder + self.l3_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path)
        self.right_stimulus.width = self.right_stimulus.height
        self.right_stimulus.pos_hint = {"center_x": 0.8, "center_y": 0.6}
        self.right_stimulus.bind(on_press=self.right_stimulus_pressed)

        self.present_instructions()

    def generate_trial_contingency(self,training=False):
        if not training and self.paltype == 'dPAL':
            if self.trial_configuration == 1:
                self.correct_location = 0
                self.incorrect_location = 1
                self.correct_image = self.l1_correct
                self.incorrect_image = self.l3_correct
                self.l1_image = self.correct_image
                self.l2_image = self.incorrect_image
                self.l3_image = self.mask_image
            elif self.trial_configuration == 2:
                self.correct_location = 0
                self.incorrect_location = 2
                self.correct_image = self.l1_correct
                self.incorrect_image = self.l2_correct
                self.l1_image = self.correct_image
                self.l3_image = self.incorrect_image
                self.l2_image = self.mask_image
            elif self.trial_configuration == 3:
                self.correct_location = 1
                self.incorrect_location = 0
                self.correct_image = self.l2_correct
                self.incorrect_image = self.l3_correct
                self.l2_image = self.correct_image
                self.l1_image = self.incorrect_image
                self.l3_image = self.mask_image
            elif self.trial_configuration == 4:
                self.correct_location = 1
                self.incorrect_location = 2
                self.correct_image = self.l2_correct
                self.incorrect_image = self.l1_correct
                self.l2_image = self.correct_image
                self.l3_image = self.incorrect_image
                self.l1_image = self.mask_image
            elif self.trial_configuration == 5:
                self.correct_location = 2
                self.incorrect_location = 0
                self.correct_image = self.l3_correct
                self.incorrect_image = self.l2_correct
                self.l3_image = self.correct_image
                self.l1_image = self.incorrect_image
                self.l2_image = self.mask_image
            elif self.trial_configuration == 6:
                self.correct_location = 2
                self.incorrect_location = 1
                self.correct_image = self.l3_correct
                self.incorrect_image = self.l1_correct
                self.l3_image = self.correct_image
                self.l2_image = self.incorrect_image
                self.l1_image = self.mask_image
        if not training and self.paltype == 'sPAL':
            if self.trial_configuration == 1:
                self.correct_location = 0
                self.incorrect_location = 1
                self.correct_image = self.l1_correct
                self.incorrect_image = self.l1_correct
                self.l1_image = self.correct_image
                self.l2_image = self.incorrect_image
                self.l3_image = self.mask_image
            elif self.trial_configuration == 2:
                self.correct_location = 0
                self.incorrect_location = 2
                self.correct_image = self.l1_correct
                self.incorrect_image = self.l1_correct
                self.l1_image = self.correct_image
                self.l3_image = self.incorrect_image
                self.l2_image = self.mask_image
            elif self.trial_configuration == 3:
                self.correct_location = 1
                self.incorrect_location = 0
                self.correct_image = self.l2_correct
                self.incorrect_image = self.l2_correct
                self.l2_image = self.correct_image
                self.l1_image = self.incorrect_image
                self.l3_image = self.mask_image
            elif self.trial_configuration == 4:
                self.correct_location = 1
                self.incorrect_location = 2
                self.correct_image = self.l2_correct
                self.incorrect_image = self.l2_correct
                self.l2_image = self.correct_image
                self.l3_image = self.incorrect_image
                self.l1_image = self.mask_image
            elif self.trial_configuration == 5:
                self.correct_location = 2
                self.incorrect_location = 0
                self.correct_image = self.l3_correct
                self.incorrect_image = self.l3_correct
                self.l3_image = self.correct_image
                self.l1_image = self.incorrect_image
                self.l2_image = self.mask_image
            elif self.trial_configuration == 6:
                self.correct_location = 2
                self.incorrect_location = 1
                self.correct_image = self.l3_correct
                self.incorrect_image = self.l3_correct
                self.l3_image = self.correct_image
                self.l2_image = self.incorrect_image
                self.l1_image = self.mask_image
        elif training:
            if self.trial_configuration == 1:
                self.correct_location = 0
                self.incorrect_location = 1
                self.correct_image = self.training_image
                self.incorrect_image = self.training_image_incorrect
                self.l1_image = self.correct_image
                self.l2_image = self.incorrect_image
                self.l3_image = self.mask_image
            elif self.trial_configuration == 2:
                self.correct_location = 0
                self.incorrect_location = 2
                self.correct_image = self.training_image
                self.incorrect_image = self.training_image_incorrect
                self.l1_image = self.correct_image
                self.l3_image = self.incorrect_image
                self.l2_image = self.mask_image
            elif self.trial_configuration == 3:
                self.correct_location = 1
                self.incorrect_location = 0
                self.correct_image = self.training_image
                self.incorrect_image = self.training_image_incorrect
                self.l2_image = self.correct_image
                self.l1_image = self.incorrect_image
                self.l3_image = self.mask_image
            elif self.trial_configuration == 4:
                self.correct_location = 1
                self.incorrect_location = 2
                self.correct_image = self.training_image
                self.incorrect_image = self.training_image_incorrect
                self.l2_image = self.correct_image
                self.l3_image = self.incorrect_image
                self.l1_image = self.mask_image
            elif self.trial_configuration == 5:
                self.correct_location = 2
                self.incorrect_location = 0
                self.correct_image = self.training_image
                self.incorrect_image = self.training_image_incorrect
                self.l3_image = self.correct_image
                self.l1_image = self.incorrect_image
                self.l2_image = self.mask_image
            elif self.trial_configuration == 6:
                self.correct_location = 2
                self.incorrect_location = 1
                self.correct_image = self.training_image
                self.incorrect_image = self.training_image_incorrect
                self.l3_image = self.correct_image
                self.l2_image = self.incorrect_image
                self.l1_image = self.mask_image
                
        #self.left_stimulus_image_path = self.image_folder + self.l1_image + '.png'
        #self.center_stimulus_image_path = self.image_folder + self.l2_image + '.png'
        #self.right_stimulus_image_path = self.image_folder + self.l3_image + '.png'
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Correct Image', 'Value', str(self.correct_image),
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Incorrect Image', 'Value', str(self.incorrect_image),
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Correct Location', 'Value', str(self.correct_location),
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [0, 'Variable Change', 'Incorrect Location', 'Value', str(self.incorrect_location),
             '', '', '', ''])

    # Protocol Staging #

    def stimulus_presentation(self,*args):
        #self.left_stimulus.source = self.left_stimulus_image_path
        #self.center_stimulus.source = self.center_stimulus_image_path
        #self.right_stimulus.source = self.right_stimulus_image_path
        self.left_stimulus.texture = self.image_dict[self.l1_image].image.texture
        self.center_stimulus.texture = self.image_dict[self.l2_image].image.texture
        self.right_stimulus.texture = self.image_dict[self.l3_image].image.texture
        
        self.protocol_floatlayout.add_widget(self.left_stimulus)
        self.protocol_floatlayout.add_widget(self.center_stimulus)
        self.protocol_floatlayout.add_widget(self.right_stimulus)
        self.left_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
        self.right_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
        self.center_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Displayed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.l1_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Displayed', 'Center Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.l2_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Displayed', 'Center Stimulus', 'X Position', '3',
             'Y Position', '1', 'Image Name', self.l3_image])
            
        self.start_stimulus = time.time()
        
        self.stimulus_on_screen = True

    def premature_response(self,*args):
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
        
    # Contingency Stages #
    def left_stimulus_pressed(self,*args):
        if self.l1_image == self.mask_image:
            return
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_stimulus)
        self.protocol_floatlayout.remove_widget(self.center_stimulus)
        self.protocol_floatlayout.remove_widget(self.right_stimulus)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.l1_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Center Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.l2_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Right Stimulus', 'X Position', '3',
             'Y Position', '1', 'Image Name', self.l3_image])
        
        self.left_chosen = 1
        self.center_chosen = 0
        self.right_chosen = 0
        self.location_chosen = 1
        
        if self.l1_image == self.correct_image and self.correct_location == 0:
            correct = '1'
            self.current_correct += 1
            self.feedback_string = self.feedback_dict['correct']
        else:
            correct = '0'
            self.feedback_string = self.feedback_dict['incorrect']

        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Trial Correct', 'Value', str(correct),
             '', '', '', ''])
        self.response_lat = time.time() - self.start_stimulus
        
        self.feedback_label.text = self.feedback_string
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_trial(correct)
        
        if correct == '0':
            self.correction_trial = True
            if not self.correction_trials_enabled:
                self.correction_trial = False
                self.trial_contingency()
        else:
            self.correction_trial = False
            self.trial_contingency()

        self.hold_button.bind(on_press=self.iti)
        
    def center_stimulus_pressed(self,*args):
        if self.l2_image == self.mask_image:
            return
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_stimulus)
        self.protocol_floatlayout.remove_widget(self.center_stimulus)
        self.protocol_floatlayout.remove_widget(self.right_stimulus)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.l1_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Center Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.l2_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Right Stimulus', 'X Position', '3',
             'Y Position', '1', 'Image Name', self.l3_image])
        
        self.left_chosen = 0
        self.center_chosen = 1
        self.right_chosen = 0
        self.location_chosen = 2
        
        if self.l2_image == self.correct_image and self.correct_location == 1:
            correct = '1'
            self.current_correct += 1
            self.feedback_string = self.feedback_dict['correct']
        else:
            correct = '0'
            self.feedback_string = self.feedback_dict['incorrect']

        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Trial Correct', 'Value', str(correct),
             '', '', '', ''])
        self.response_lat = time.time() - self.start_stimulus
        
        self.feedback_label.text = self.feedback_string
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_trial(correct)
        
        if correct == '0':
            self.correction_trial = True
            if not self.correction_trials_enabled:
                self.correction_trial = False
                self.trial_contingency()
        else:
            self.correction_trial = False
            self.trial_contingency()

        self.hold_button.bind(on_press=self.iti)
    
    def right_stimulus_pressed(self,*args):
        if self.l3_image == self.mask_image:
            return
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_stimulus)
        self.protocol_floatlayout.remove_widget(self.center_stimulus)
        self.protocol_floatlayout.remove_widget(self.right_stimulus)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.l1_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Center Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.l2_image])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Right Stimulus', 'X Position', '3',
             'Y Position', '1', 'Image Name', self.l3_image])
        
        self.left_chosen = 0
        self.center_chosen = 0
        self.right_chosen = 1
        self.location_chosen = 3
        
        if self.l3_image == self.correct_image and self.correct_location == 2:
            correct = '1'
            self.current_correct += 1
            self.feedback_string = self.feedback_dict['correct']
        else:
            correct = '0'
            self.feedback_string = self.feedback_dict['incorrect']
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Trial Correct', 'Value', str(correct),
             '', '', '', ''])
            
        self.response_lat = time.time() - self.start_stimulus
        
        self.feedback_label.text = self.feedback_string
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_trial(correct)
        
        if correct == '0':
            self.correction_trial = True
            if not self.correction_trials_enabled:
                self.correction_trial = False
                self.trial_contingency()
        else:
            self.correction_trial = False
            self.trial_contingency()

        self.hold_button.bind(on_press=self.iti)

    def write_trial(self, correct):
        if self.correction_trial:
            correction = 1
        else:
            correction = 0
        trial_data = [self.current_trial, self.current_stage, self.correct_image, self.incorrect_image,
                      self.correct_location, self.incorrect_location, correction, self.location_chosen, correct,
                      self.response_lat]
        self.write_summary_file(trial_data)
        return

    # Trial Contingency Functions #
    
    def trial_contingency(self):
        self.current_trial += 1
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Current Trial', 'Value', str(self.current_trial),
             '', '', '', ''])
        
        if self.current_trial > self.session_trial_max:
            self.session_event.cancel()
            self.protocol_end()
            return
        if self.stage_index == 0:
            if self.current_correct >= 10:
                self.block_contingency()
                return
            self.trial_configuration = random.randint(1,6)
            self.generate_trial_contingency(training=True)
        
        if self.stage_index == 1:
            if self.current_trial > self.block_threshold:
                self.block_contingency()
                self.block_threshold += self.block_length
                return
            self.trial_configuration = random.randint(1,6)
            self.generate_trial_contingency()
        
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
