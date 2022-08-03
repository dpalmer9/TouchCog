# Imports #
import kivy
import zipimport
import sys
import os
import configparser
import time
import numpy as np
import random
import csv
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import AsyncImage
#from win32api import GetSystemMetrics
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.screenmanager import ScreenManager, Screen
from functools import partial

class ImageButton(ButtonBehavior,Image):
    def __init__(self,**kwargs):
        super(ImageButton,self).__init__(**kwargs)

class Protocol_Screen(Screen):
    def __init__(self,**kwargs):
        super(Protocol_Screen,self).__init__(**kwargs)
        self.protocol_floatlayout = FloatLayout()
        self.add_widget(self.protocol_floatlayout)
        width  = self.protocol_floatlayout.width
        height = self.protocol_floatlayout.height
       
        self.screen_ratio = width/height
        
        if sys.platform == 'linux' or sys.platform == 'darwin':
            self.folder_mod = '/'
        elif sys.platform == 'win32':
            self.folder_mod = '\\'
    
        self.initialize_text_widgets()
        self.initialize_button_widgets()
        
        self.present_instructions()
        
    # Initialization Functions #
        
    def import_configuration(self,parameter_dict):
        self.parameters_dict = parameter_dict
        self.load_configuration_file()
        self.initialize_parameters()
        self.initialize_image_widgets()
        
        self.generate_output_files()
        self.metadata_output_generation()
        
    def load_configuration_file(self):
        config_path = 'Protocol' + self.folder_mod + 'vPRL' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        
        if len(self.parameters_dict) == 0:
            self.parameters_dict = config_file['TaskParameters']
            self.participant_id = 'Default'
        else:
            self.participant_id = self.parameters_dict['participant_id']
        
        self.session_max_length = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = int(self.parameters_dict['session_trial_max'])
        
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        
        self.training_image = self.parameters_dict['training_image']
        self.training_images = ['grey',self.training_image]
        self.test_images = self.parameters_dict['test_images']
        self.test_images = self.test_images.split(',')
        
        self.image_probability = float(self.parameters_dict['image_probability'])
        self.decimal_values = len(str(self.image_probability - int(self.image_probability))[2:])
        self.reward_distribution_list_size = 10**(self.decimal_values)
        self.reward_distribution_count = int(self.reward_distribution_list_size * self.image_probability)
        self.reward_distribution = ([0] * (self.reward_distribution_list_size - self.reward_distribution_count)) + ([1] * (self.reward_distribution_count))
        random.shuffle(self.reward_distribution)
        self.reward_index = 0
        self.reward_contingency = 1
        
        self.reversal_threshold = int(self.parameters_dict['reversal_threshold'])
        self.maximum_reversals = int(self.parameters_dict['maximum_reversals'])
        
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        
            
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']
    
    def initialize_parameters(self):
        #ListVariables#
        self.stage_list = ['Training','Test']
        
        #Boolean#
        self.stimulus_on_screen = False
        self.iti_active = False
        self.feedback_on_screen = False
        self.hold_active = True
        self.block_started = False
        
        #ActiveVariables - Count#
        
        self.current_trial = 1
        self.current_correct = 0
        self.current_reversal = 0
        self.stage_index = 0
        self.current_score = 0
        
        #ActiveVariables - String#
        self.correct_image = 'snowflake'
        self.incorrect_image = 'grey'
        self.current_stage = self.stage_list[self.stage_index]
        self.feedback_string = ''
    
        
        #TimeVariables#
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0
        
        #FolderPath#
        self.image_folder = 'Protocol' + self.folder_mod + 'vPRL' + self.folder_mod + 'Image' + self.folder_mod
        
        #Random#
        self.left_stimulus_index = random.randint(0,1)
        if self.left_stimulus_index == 0:
            self.right_stimulus_index = 1
        else:
            self.right_stimulus_index = 0
        self.left_stimulus_image = self.training_images[self.left_stimulus_index]
        self.right_stimulus_image = self.training_images[self.right_stimulus_index]
        self.left_chosen = 0
        self.right_chosen = 1
        
        
        
        
    def initialize_image_widgets(self):
        
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path,allow_stretch=True)
        #self.hold_button.size_hint_y = 0.2
        #self.hold_button.width = self.hold_button.height
        self.hold_button.size_hint = ((0.2* self.screen_ratio),0.2)
        self.hold_button.pos_hint = {"center_x":0.5,"center_y":0.1}
        
        
        self.left_stimulus_image_path = self.image_folder + self.left_stimulus_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path,allow_stretch=True)
        self.left_stimulus.size_hint = ((0.4* self.screen_ratio),0.4)
        #self.left_stimulus.size_hint_y = 0.3
        #self.left_stimulus.width = self.left_stimulus.height
        self.left_stimulus.pos_hint = {"center_x":0.3,"center_y":0.6}
        self.left_stimulus.border = [0,0,0,0]
        self.left_stimulus.bind(on_press = self.left_stimulus_pressed)
        
        self.right_stimulus_image_path = self.image_folder + self.right_stimulus_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path,allow_stretch=True)
        self.right_stimulus.size_hint = ((0.4* self.screen_ratio),0.4)
        self.right_stimulus.width = self.right_stimulus.height
        self.right_stimulus.pos_hint = {"center_x":0.7,"center_y":0.6}
        self.right_stimulus.border = [0,0,0,0]
        self.right_stimulus.bind(on_press = self.right_stimulus_pressed)
        
    def initialize_text_widgets(self):
        self.instruction_label = Label(text= 'During the experiment, hold your finger on the white square before responding .\nTo make a response, press on one of the images on the centre of the screen.\nYou will receive feedback following touching an image.'
                                       , font_size = '35sp')
        self.instruction_label.size_hint = (0.6,0.4)
        self.instruction_label.pos_hint = {'center_x':0.5,'center_y':0.3}
        
        self.block_label = Label(text='PRESS BUTTON TO CONTINUE WHEN READY',font_size='50sp')
        self.block_label.size_hint = (0.5,0.3)
        self.block_label.pos_hint = {'center_x':0.5,'center_y':0.3}
        
        self.end_label = Label(text= 'Thank you for your participation. Please press Return to end experiment.', font_size='50sp')
        self.end_label.size_hint = (0.6,0.4)
        self.end_label.pos_hint = {'center_x':0.5,'center_y':0.3}
        
        self.feedback_string = ''
        self.feedback_label = Label(text=self.feedback_string,font_size='50sp', markup=True)
        self.feedback_label.size_hint = (0.7,0.4)
        self.feedback_label.pos_hint = {'center_x':0.5,'center_y':0.5}
        
        self.score_string = 'Your Points:\n%s' % (0)
        self.score_label = Label(text=self.score_string,font_size='50sp',markup=True,halign='center')
        self.score_label.size_hint = (0.8,0.2)
        self.score_label.pos_hint = {'center_x':0.5,'center_y':0.9}
        
    def initialize_button_widgets(self):
        self.start_button = Button(text='Start')
        self.start_button.size_hint = (0.1,0.1)
        self.start_button.pos_hint = {'center_x':0.5,'center_y':0.7}
        self.start_button.bind(on_press=self.start_protocol)
        
        self.continue_button = Button(text='Continue')
        self.continue_button.size_hint = (0.1,0.1)
        self.continue_button.pos_hint = {'center_x':0.5,'center_y':0.7}
        self.continue_button.bind(on_press=self.block_end)
        
        self.return_button = Button(text='Return')
        self.return_button.size_hint = (0.1,0.1)
        self.return_button.pos_hint = {'center_x':0.5,'center_y':0.7}
        self.return_button.bind(on_press=self.return_to_main)
        
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
            #meta_array[row_index,0] = meta_row
            #meta_array[row_index,1] = self.parameters_dict[meta_row]
        
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
        self.protocol_floatlayout.add_widget(self.instruction_label)
        self.protocol_floatlayout.add_widget(self.start_button)
        
    # Block Staging #
    def block_screen(self,*args):
        if self.block_started == False:
            self.protocol_floatlayout.add_widget(self.block_label)
            self.block_start = time.time()
            self.block_started = True
            Clock.schedule_interval(self.block_screen,0.1)
        if (time.time() - self.block_start) > self.block_min_rest_duration:
            Clock.unschedule(self.block_screen)
            self.protocol_floatlayout.add_widget(self.continue_button)
            
    def block_end(self,*args):
        self.block_started = False
        self.protocol_floatlayout.clear_widgets()
        self.trial_contingency()
        self.protocol_floatlayout.add_widget(self.hold_button)
        self.score_label.text = 'Your Points:\n%s' % (self.current_score)
        self.protocol_floatlayout.add_widget(self.score_label)
    
    # End Staging #
    def protocol_end(self):
        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_widget(self.end_label)
        self.protocol_floatlayout.add_widget(self.return_button)
        
    def return_to_main(self,*args):
        self.manager.current='mainmenu'
    
    # Protocol Staging #
    
    def start_protocol(self,*args):
        self.protocol_floatlayout.remove_widget(self.instruction_label)
        self.protocol_floatlayout.remove_widget(self.start_button)
        self.start_clock()
        
        self.protocol_floatlayout.add_widget(self.hold_button)
        self.hold_button.size_hint_y = 0.2
        self.hold_button.width = self.hold_button.height
        self.hold_button.pos_hint = {"center_x":0.5,"center_y":0.1}
        self.hold_button.bind(on_press=self.iti)
        self.protocol_floatlayout.add_widget(self.score_label)
    
        
    def iti(self,*args):
        if self.iti_active == False:
            self.hold_button.unbind(on_press=self.iti)
            self.hold_button.bind(on_release=self.premature_response)
            self.start_iti = time.time()
            self.iti_active = True
            
            if self.feedback_string == 'WAIT FOR IMAGE - PLEASE TRY AGAIN':
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_string = ''
            
            if self.feedback_on_screen == False:
                self.feedback_label.text = self.feedback_string
                self.protocol_floatlayout.add_widget(self.feedback_label)
                self.feedback_on_screen = True
            Clock.schedule_interval(self.iti,0.1)
        if self.iti_active == True:
            if (time.time() - self.start_iti) > self.feedback_length:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_on_screen = False
            if (time.time() - self.start_iti) > self.iti_length:
                Clock.unschedule(self.iti)
                self.iti_active = False
                self.hold_button.unbind(on_release=self.premature_response)
                self.stimulus_presentation()
                
    def stimulus_presentation(self,*args):
        self.protocol_floatlayout.add_widget(self.left_stimulus)
       # self.left_stimulus.size_hint_y = 0.4
        #self.left_stimulus.width = self.left_stimulus.height
        #self.left_stimulus.pos_hint = {"center_x":0.3,"center_y":0.6}
        #self.left_stimulus.size = (50,50)
        #self.left_stimulus.pos = (200,200)
        self.protocol_floatlayout.add_widget(self.right_stimulus)
        #self.right_stimulus.size_hint_y = 0.4
        #self.right_stimulus.width = self.right_stimulus.height
        #self.right_stimulus.pos_hint = {"center_x":0.7,"center_y":0.6}
        #self.right_stimulus.size = (50,50)
        #self.right_stimulus.pos = (600,200)

            
        self.start_stimulus = time.time()
        
        self.stimulus_on_screen = True
            
                
    def premature_response(self,*args):
        if self.stimulus_on_screen == True:
            return None
        
        Clock.unschedule(self.iti)
        self.feedback_string = 'WAIT FOR IMAGE - PLEASE TRY AGAIN'
        contingency = '2'
        response = '1'
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_string
        if self.feedback_on_screen == False:
            self.protocol_floatlayout.add_widget(self.feedback_label)
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)
        
        
            
        
    # Contingency Stages #
    def left_stimulus_pressed(self,*args):
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_stimulus)
        self.protocol_floatlayout.remove_widget(self.right_stimulus)
        
        self.left_chosen = 1
        self.right_chosen = 0
        
        if self.left_stimulus_image == self.correct_image:
            response = '1'
            self.current_correct += 1
            if self.reward_contingency == 1:
                self.feedback_string = '[color=008000]YOU WIN 50 POINTS[/color]'
                self.current_score += 50
                contingency = '1'
            else:
                self.feedback_string = '[color=FF0000]NO POINTS[/color]'
                contingency = '0'
        else:
            response = '0'
            self.current_correct = 0
            if self.reward_contingency == 1:
                self.feedback_string = '[color=FF0000]NO POINTS[/color]'
                contingency = '0'
            else:
                self.feedback_string = '[color=008000]YOU WIN 50 POINTS[/color]'
                self.current_score += 50
                contingency = '1'
                
            
        
        self.response_lat = time.time() - self.start_stimulus

            
        self.feedback_label.text = self.feedback_string
        self.score_label.text = 'Your Points:\n%s' % (self.current_score)
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.feedback_on_screen = True
        self.write_summary_file(response,contingency)
        self.trial_contingency()
        
        self.hold_button.bind(on_press=self.iti)
    
    def right_stimulus_pressed(self,*args):
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.left_stimulus)
        self.protocol_floatlayout.remove_widget(self.right_stimulus)
        
        self.left_chosen = 0
        self.right_chosen = 1
        
        
        if self.right_stimulus_image == self.correct_image:
            response = '1'
            self.current_correct += 1
            if self.reward_contingency == 1:
                self.feedback_string = '[color=008000]YOU WIN 50 POINTS[/color]'
                self.current_score += 50
                contingency = '1'
            else:
                self.feedback_string = '[color=FF0000]NO POINTS[/color]'
                contingency = '0'
        else:
            response = '0'
            self.current_correct = 0
            if self.reward_contingency == 1:
                self.feedback_string = '[color=FF0000]NO POINTS[/color]'
                contingency = '0'
            else:
                self.feedback_string = '[color=008000]YOU WIN 50 POINTS[/color]'
                self.current_score += 50
                contingency = '1'
                
            
        
        self.response_lat = time.time() - self.start_stimulus

            
        self.feedback_label.text = self.feedback_string
        self.score_label.text = 'Your Points:\n%s' % (self.current_score)
        self.protocol_floatlayout.add_widget(self.feedback_label)
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
                
            if self.reward_index >= len(self.reward_distribution):
                self.reward_index = 0
                random.shuffle(self.reward_distribution)
            self.reward_contingency = self.reward_distribution[self.reward_index]
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
        Clock.schedule_interval(self.display_monitor,0.1)
    
    def clock_monitor(self,*args):
        self.current_time = time.time()
        self.elapsed_time = self.current_time - self.start_time
        
        if self.elapsed_time > self.session_max_length:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()
            
    def display_monitor(self,*args):
       width  = self.protocol_floatlayout.width
       height = self.protocol_floatlayout.height
       
       self.screen_ratio = width/height
            
        
        
        