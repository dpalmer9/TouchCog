# Imports #
import configparser
import time
import random
from kivy.uix.label import Label
from kivy.clock import Clock
from Classes.Protocol import ImageButton, ProtocolBase


class ProtocolScreen(ProtocolBase):
    def __init__(self,**kwargs):
        super(ProtocolScreen,self).__init__(**kwargs)
        self.protocol_name = 'vPRL'
        self.update_task()
        
        # Define Data Columns
        self.data_cols = ['TrialNo', 'Current Stage', 'Reversal #', 'S+ Image', 'S- Image', 'Left Image', 'Right Image',
                          'S+ Rewarded', 'S- Rewarded', 'Left Chosen', 'Right Chosen', 'Correct Response',
                          'Reward Given', 'Response Latency']

        self.metadata_cols = ['participant_id','training_image','test_images',
                         'image_probability','iti_length','session_length_max',
                         'reversal_threshold','maximum_reversals',
                         'session_trial_max']

        # Define Variables - Config
        config_path = 'Protocol' + self.folder_mod + 'vPRL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        self.parameters_dict = config_file['TaskParameters']

        self.participant_id = 'Default'
        self.session_length_max = float(self.parameters_dict['session_length_max'])
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
        self.set_language(self.language)

        # Define Variables - List
        self.stage_list = ['Training', 'Test']

        # Define Variables - Count
        self.current_correct = 0
        self.current_reversal = 0
        self.current_score = 0

        # Define Variables - String
        self.correct_image = 'snowflake'
        self.incorrect_image = 'grey'
        self.current_stage = self.stage_list[self.stage_index]
        self.feedback_string = ''

        # Define Variables - Time
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
        self.hold_button.source = self.hold_button_image_path

        self.left_stimulus_image_path = self.image_folder + self.left_stimulus_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path)
        self.left_stimulus.bind(on_press=self.left_stimulus_pressed)

        self.right_stimulus_image_path = self.image_folder + self.right_stimulus_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path)
        self.right_stimulus.bind(on_press=self.right_stimulus_pressed)

        # Define Widgets - Text
        self.score_string = 'Your Points:\n%s' % (0)
        self.score_label = Label(text=self.score_string, font_size='50sp', markup=True, halign='center')
        self.score_label.size_hint = (0.8, 0.2)
        self.score_label.pos_hint = {'center_x': 0.5, 'center_y': 0.9}
    # Initialization Functions #
        
    def load_parameters(self,parameter_dict):
        self.parameters_dict = parameter_dict
        config_path = 'Protocol' + self.folder_mod + 'PAL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)

        self.participant_id = self.parameters_dict['participant_id']

        # Define Variables - Config
        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.training_image = self.parameters_dict['training_image']
        self.training_images = ['grey', self.training_image]
        self.test_images = self.parameters_dict['test_images']
        self.test_images = self.test_images.split(',')
        total_images = self.test_images + self.training_images
        self.load_images(total_images)
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
            [time.time() - self.start_time, 'Variable Change', 'Current Reward Contingency', 'Value', str(self.reward_contingency),
             '', '', '', ''])
        self.reversal_threshold = int(self.parameters_dict['reversal_threshold'])
        self.maximum_reversals = int(self.parameters_dict['maximum_reversals'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']

        # Define Language
        self.language = self.parameters_dict['language']
        self.set_language(self.language)

        # Define Variables - List
        self.stage_list = ['Training', 'Test']

        # Define Variables - Count
        self.current_correct = 0
        self.current_reversal = 0
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Current Reversal', 'Value', str(self.current_reversal),
             '', '', '', ''])
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
        self.start_stimulus = 0
        self.response_lat = 0
        
        # Define Clock
        self.session_event = self.session_clock.create_trigger(self.clock_monitor, self.session_length_max, interval=False)

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
        self.hold_button.source = self.hold_button_image_path

        self.left_stimulus_image_path = self.image_folder + self.left_stimulus_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path)
        self.left_stimulus.pos_hint = {"center_x": 0.3, "center_y": 0.6}
        self.left_stimulus.bind(on_press=self.left_stimulus_pressed)

        self.right_stimulus_image_path = self.image_folder + self.right_stimulus_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path)
        self.right_stimulus.pos_hint = {"center_x": 0.7, "center_y": 0.6}
        self.right_stimulus.bind(on_press=self.right_stimulus_pressed)

        # Define Widgets - Text
        self.score_string = 'Your Points:\n%s' % (0)
        self.score_label = Label(text=self.score_string, font_size='50sp', markup=True, halign='center')
        self.score_label.size_hint = (0.8, 0.2)
        self.score_label.pos_hint = {'center_x': 0.5, 'center_y': 0.9}

        self.present_instructions()

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
            [time.time() - self.start_time, 'Button Displayed', 'Hold Button', '', '',
             '', '', '', ''])
        self.hold_button.size_hint = ((0.2 * self.width_adjust), (0.2 * self.height_adjust))
        self.hold_button.size_hint_y = 0.2
        self.hold_button.width = self.hold_button.height
        self.hold_button.pos_hint = {"center_x":0.5,"center_y":0.1}
        self.hold_button.bind(on_press=self.iti)
        self.protocol_floatlayout.add_widget(self.score_label)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Text Displayed', 'Score', '', '',
             '', '', '', ''])
                
    def stimulus_presentation(self,*args):
        self.protocol_floatlayout.add_widget(self.left_stimulus)
        self.left_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Displayed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.left_stimulus_image])
        self.protocol_floatlayout.add_widget(self.right_stimulus)
        self.right_stimulus.size_hint = ((0.4 * self.width_adjust), (0.4 * self.height_adjust))
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Displayed', 'Right Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.right_stimulus_image])
            
        self.start_stimulus = time.time()
        
        self.stimulus_on_screen = True
            
                
    def premature_response(self,*args):
        if self.stimulus_on_screen == True:
            return None
        
        self.iti_event.cancel()
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Stage Change', 'Premature Response', '', '',
             '', '', '', ''])
        self.feedback_string = self.feedback_dict['wait']
        contingency = '2'
        response = '1'
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_string
        if self.feedback_on_screen == False:
            self.protocol_floatlayout.add_widget(self.feedback_label)
            self.protocol_floatlayout.add_event(
                [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
                 '', '', '', ''])
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)
        
        
            
        
    # Contingency Stages #
    def left_stimulus_pressed(self,*args):
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_stimulus)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.left_stimulus_image])
        self.protocol_floatlayout.remove_widget(self.right_stimulus)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Right Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.right_stimulus_image])
        
        self.left_chosen = 1
        self.right_chosen = 0
        
        if self.left_stimulus_image == self.correct_image:
            response = '1'
            self.current_correct += 1
            if self.reward_contingency == 1:
                self.feedback_string = self.feedback_dict['correct']
                self.current_score += 50
                contingency = '1'
            else:
                self.feedback_string = self.feedback_dict['incorrect']
                contingency = '0'
        else:
            response = '0'
            self.current_correct = 0
            if self.reward_contingency == 1:
                self.feedback_string = self.feedback_dict['incorrect']
                contingency = '0'
            else:
                self.feedback_string = self.feedback_dict['correct']
                self.current_score += 50
                contingency = '1'
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Trial Correct', 'Value', str(response),
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Total Correct', 'Value', str(self.current_correct),
             '', '', '', ''])

        self.response_lat = time.time() - self.start_stimulus

        self.feedback_label.text = self.feedback_string
        self.score_label.text = 'Your Points:\n%s' % (self.current_score)
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_trial(response, contingency)
        self.trial_contingency()
        
        self.hold_button.bind(on_press=self.iti)
    
    def right_stimulus_pressed(self,*args):
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_stimulus)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Left Stimulus', 'X Position', '1',
             'Y Position', '1', 'Image Name', self.left_stimulus_image])
        self.protocol_floatlayout.remove_widget(self.right_stimulus)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Image Removed', 'Right Stimulus', 'X Position', '2',
             'Y Position', '1', 'Image Name', self.right_stimulus_image])
        
        self.left_chosen = 0
        self.right_chosen = 1
        
        if self.right_stimulus_image == self.correct_image:
            response = '1'
            self.current_correct += 1
            if self.reward_contingency == 1:
                self.feedback_string = self.feedback_dict['correct']
                self.current_score += 50
                contingency = '1'
            else:
                self.feedback_string = self.feedback_dict['incorrect']
                contingency = '0'
        else:
            response = '0'
            self.current_correct = 0
            if self.reward_contingency == 1:
                self.feedback_string = self.feedback_dict['incorrect']
                contingency = '0'
            else:
                self.feedback_string = self.feedback_dict['correct']
                self.current_score += 50
                contingency = '1'
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Trial Correct', 'Value', str(response),
             '', '', '', ''])
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Variable Change', 'Total Correct', 'Value', str(self.current_correct),
             '', '', '', ''])
                

        self.response_lat = time.time() - self.start_stimulus

        self.feedback_label.text = self.feedback_string
        self.score_label.text = 'Your Points:\n%s' % (self.current_score)
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.protocol_floatlayout.add_event(
            [time.time() - self.start_time, 'Text Displayed', 'Feedback', '', '',
             '', '', '', ''])
        self.feedback_on_screen = True
        self.write_trial(response, contingency)
        self.trial_contingency()
        
        self.hold_button.bind(on_press=self.iti)

    # Data Saving Functions #
    def write_trial(self, response, contingency):
        if self.reward_contingency == 1:
            s_min_cont = '0'
        else:
            s_min_cont = '1'
        trial_data = [self.current_trial, self.current_stage, self.current_reversal, self.correct_image,
                      self.incorrect_image, self.left_stimulus_image, self.right_stimulus_image,
                      self.reward_contingency, s_min_cont, self.left_chosen, self.right_chosen, response, contingency,
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
            self.left_stimulus_index = random.randint(0,1)
            if self.left_stimulus_index == 0:
                self.right_stimulus_index = 1
            else:
                self.right_stimulus_index = 0
            self.left_stimulus_image = self.training_images[self.left_stimulus_index]
            self.right_stimulus_image = self.training_images[self.right_stimulus_index]
            self.left_stimulus.texture = self.image_dict[self.left_stimulus_image].image.texture
            self.right_stimulus.texture = self.image_dict[self.right_stimulus_image].image.texture
            self.reward_contingency = 1

        if self.stage_index == 1:
            self.left_stimulus_index = random.randint(0,1)
            if self.left_stimulus_index == 0:
                self.right_stimulus_index = 1
            else:
                self.right_stimulus_index = 0
            self.left_stimulus_image = self.test_images[self.left_stimulus_index]
            self.right_stimulus_image = self.test_images[self.right_stimulus_index]
            self.left_stimulus.texture = self.image_dict[self.left_stimulus_image].image.texture
            self.right_stimulus.texture = self.image_dict[self.right_stimulus_image].image.texture
            
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
                    [time.time() - self.start_time, 'Variable Change', 'Current Reversal', 'Value', str(self.current_reversal),
                     '', '', '', ''])
                
            if self.reward_index >= len(self.reward_distribution):
                self.reward_index = 0
                random.shuffle(self.reward_distribution)
            self.reward_contingency = self.reward_distribution[self.reward_index]
            self.protocol_floatlayout.add_event(
                [time.time() - self.start_time, 'Variable Change', 'Current Reward Contingency', 'Value',
                 str(self.reward_contingency), '', '', '', ''])
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
        self.trial_contingency()
        self.block_screen()
