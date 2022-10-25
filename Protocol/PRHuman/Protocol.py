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
        config_path = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Configuration.ini'
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
    
    def initialize_parameters(self):
        #ListVariables#
        self.stage_index = 0
        self.stage_list = ['Reward x3','Reward x2','Reward x1']
        self.reward_value_score = [200,100,50]
        self.reward_value_curr = [2.00,1.00,0.50]
        print(self.reward_type)
        if self.reward_type == 'point':
            self.reward_list = self.reward_value_score
            self.current_reward_value = 0
            self.feedback_string = 'Reward: %d Points' % (self.current_reward_value)
        elif self.reward_type == 'currency':
            self.reward_list = self.reward_value_curr
            self.current_reward_value = 0.00
            self.feedback_string = 'Reward: $%.2f' % (self.current_reward_value)
            
        self.current_reward = self.reward_list[self.stage_index]
        
        
        
        #Boolean#
        self.stimulus_on_screen = False
        self.iti_active = False
        self.feedback_on_screen = False
        self.hold_active = True
        self.block_started = False
        self.correction_trial = True
        
        #ActiveVariables - Count#
        
        self.current_trial = 1
        
        self.current_block = 0
        self.current_pr_threshold = self.baseline_pr_threshold
        self.current_pr_step = 0
        self.current_response_count = 0
        
        
        #ActiveVariables - String#
        self.current_stage = self.stage_list[self.stage_index]
    
        
        #TimeVariables#
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0
        
        #FolderPath#
        self.image_folder = 'Protocol' + self.folder_mod + 'PRHuman' + self.folder_mod + 'Image' + self.folder_mod
        
        #Random#
        self.x_pos_mod = random.randint(0,7)
        self.y_pos_mod = random.randint(0,7)
        
        self.block_threshold = 10 + self.block_length
        
        
    
    def initialize_image_widgets(self):
        
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path,allow_stretch=True)
        #self.hold_button.size_hint_y = 0.2
        #self.hold_button.width = self.hold_button.height
        self.hold_button.size_hint = ((0.075* self.screen_ratio),0.075)
        self.hold_button.pos_hint = {"center_x":0.5,"center_y":0.001}
        
        #self.x_dim_hint = []
        self.x_dim_hint = np.linspace(0.3,0.7,8)
        self.x_dim_hint = self.x_dim_hint.tolist()
        self.y_dim_hint = [0.925,0.825,0.725,0.625,0.525,0.425,0.325,0.225]
        self.stimulus_image_path = self.image_folder + self.stimulus_image + '.png'
        self.mask_image_path = self.image_folder + self.mask_image + '.png'
        self.background_grid_list = [Image() for i in range(64)]
        x_pos = 0
        y_pos = 0
        for cell in self.background_grid_list:
            cell.size_hint = ((.08 * self.screen_ratio),.08)
            if x_pos > 7:
                x_pos = 0
                y_pos = y_pos + 1
            cell.pos_hint = {"center_x":self.x_dim_hint[x_pos],"center_y":self.y_dim_hint[y_pos]}
            cell.source = self.mask_image_path
            x_pos = x_pos + 1
            
        self.stimulus_image_button = ImageButton(source=self.stimulus_image_path,allow_stretch=True)
        self.stimulus_image_button.size_hint = ((0.08 * self.screen_ratio),0.08)
        self.stimulus_image_button.pos_hint = {"center_x":self.x_dim_hint[self.x_pos_mod],"center_y":self.y_dim_hint[self.y_pos_mod]}
        self.stimulus_image_button.bind(on_press=self.stimulus_pressed)
        
        
    def initialize_text_widgets(self):
        self.instruction_label = Label(text= 'During the experiment, hold your finger on the white square before responding .\nTo make a response, press on one of the images on the centre of the screen.\nYou will receive feedback following touching an image.'
                                       , font_size = '35sp')
        self.instruction_label.size_hint = (0.6,0.4)
        self.instruction_label.pos_hint = {'center_x':0.5,'center_y':0.3}
        
        self.block_label = Label(text='PRESS BUTTON TO CONTINUE WHEN READY',font_size='50sp')
        self.block_label.size_hint = (0.5,0.3)
        self.block_label.pos_hint = {'center_x':0.5,'center_y':0.3}
        
        self.end_label = Label(text= 'Thank you for your participation. Please press Return to end experiment.')
        self.end_label.size_hint = (0.6,0.4)
        self.end_label.pos_hint = {'center_x':0.5,'center_y':0.3}
        
        self.feedback_string = ''
        self.feedback_label = Label(text=self.feedback_string,font_size='40sp', markup=True)
        self.feedback_label.size_hint = (0.7,0.4)
        self.feedback_label.pos_hint = {'center_x':0.5,'center_y':0.98}
        
        
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

        self.quit_button = Button(text='Stop')
        self.quit_button.size_hint = (0.1, 0.1)
        self.quit_button.pos_hint = {'center_x': 0.1, 'center_y': 0.7}
        self.quit_button.bind(on_press=self.protocol_end)
        
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
        for image_wid in self.background_grid_list:
            self.protocol_floatlayout.add_widget(image_wid)
        self.protocol_floatlayout.add_widget(self.quit_button)
        self.protocol_floatlayout.add_widget(self.hold_button)
    
    # End Staging #
    def protocol_end(self, *args):
        Clock.unschedule(self.clock_monitor)
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
        for image_wid in self.background_grid_list:
            self.protocol_floatlayout.add_widget(image_wid)
        self.protocol_floatlayout.add_widget(self.quit_button)
        self.feedback_label.text = self.feedback_string
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.feedback_on_screen = True
        self.hold_button.size_hint_y = 0.2
        self.hold_button.width = self.hold_button.height
        self.hold_button.pos_hint = {"center_x":0.5,"center_y":0.1}
        self.hold_button.bind(on_press=self.iti)
    
        
    def iti(self,*args):
        if self.iti_active == False:
            self.hold_button.unbind(on_press=self.iti)
            #self.hold_button.bind(on_release=self.premature_response)
            self.start_iti = time.time()
            self.iti_active = True
            
            if self.feedback_string == 'WAIT FOR IMAGE - PLEASE TRY AGAIN':
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_string = ''
            Clock.schedule_interval(self.iti,0.1)
        if self.iti_active == True:
            if (time.time() - self.start_iti) > self.iti_length:
                Clock.unschedule(self.iti)
                self.iti_active = False
                #self.hold_button.unbind(on_release=self.premature_response)
                self.stimulus_presentation()
                
    def stimulus_presentation(self,*args):
        self.protocol_floatlayout.add_widget(self.stimulus_image_button)


            
        self.start_stimulus = time.time()
        
        self.stimulus_on_screen = True
            
                
    def premature_response(self,*args):
        return
        if self.stimulus_on_screen == True:
            return None
        
        Clock.unschedule(self.iti)
        self.feedback_string = 'WAIT FOR IMAGE - PLEASE TRY AGAIN'
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_string
        if self.feedback_on_screen == False:
            self.protocol_floatlayout.add_widget(self.feedback_label)
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)
        
        
            
        
    # Contingency Stages #

    def stimulus_pressed(self,*args):
        self.stimulus_on_screen = False
        self.protocol_floatlayout.remove_widget(self.stimulus_image_button)
        
        self.current_response_count += 1
        
            
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
        
        self.x_pos_mod = random.randint(0,7)
        self.y_pos_mod = random.randint(0,7)
        self.stimulus_image_button.pos_hint = {"center_x":self.x_dim_hint[self.x_pos_mod],"center_y":self.y_dim_hint[self.y_pos_mod]}
        
        
        if self.current_response_count >= self.current_pr_threshold:
            self.current_pr_threshold *= self.current_pr_multiplier
            self.current_pr_step += 1
            self.current_reward_value += self.current_reward
            self.current_response_count = 0
            if self.reward_type == 'point':
                self.feedback_string = 'Reward: %d Points' % (self.current_reward_value)
            elif self.reward_type == 'currency':
                self.current_reward_value = 0.00
                self.feedback_string = 'Reward: $%.2f' % (self.current_reward_value)
            self.feedback_label.text = self.feedback_string
            
        if self.current_pr_step > self.current_pr_threshold_step_max:
            self.stage_index += 1
            self.current_stage = self.stage_list[self.stage_index]
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
            
        
        
        