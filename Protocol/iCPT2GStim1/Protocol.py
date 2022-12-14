# Imports #
import kivy
import zipimport
import sys
import os
import configparser
import time
import numpy as np
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
            
        
    
    def display_instructions(self):
        self.present_instructions()
        
    # Initialization Functions #
        
    def import_configuration(self,parameter_dict):
        self.parameters_dict = parameter_dict
        self.load_configuration_file()
        self.initialize_language_localization()
        self.initialize_parameters()
        self.initialize_image_widgets()
        self.initialize_text_widgets()
        self.initialize_button_widgets()
        self.image_list_generator()
        
        self.generate_output_files()
        self.metadata_output_generation()
        #self.EventListener = EventListener(self.participant_id,self.protocol_name,'csv')
        
    def load_configuration_file(self):
        config_path = 'Protocol' + self.folder_mod + 'iCPT2GStim1' + self.folder_mod + 'Configuration.ini'
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        
        if len(self.parameters_dict) == 0:
            self.parameters_dict = config_file['TaskParameters']
            self.participant_id = 'Default'
        else:
            self.participant_id = self.parameters_dict['participant_id']
        
        self.language = self.parameters_dict['language']
        
        self.stimulus_duration = float(self.parameters_dict['stimulus_duration'])
        self.limited_hold = float(self.parameters_dict['limited_hold'])
        self.target_probability = float(self.parameters_dict['target_probability'])
        self.iti_length = float(self.parameters_dict['iti_length'])
        self.feedback_length = float(self.parameters_dict['feedback_length'])
        self.training_image = self.parameters_dict['training_image']
        self.correct_images = self.parameters_dict['correct_images']
        self.correct_images = self.correct_images.split(',')
        self.incorrect_images = self.parameters_dict['incorrect_images']
        self.incorrect_images = self.incorrect_images.split(',')
        self.total_image_list = self.correct_images + self.incorrect_images
        self.block_max_length = int(self.parameters_dict['block_max_length'])
        self.block_max_count = int(self.parameters_dict['block_max_count'])
        self.block_min_rest_duration = float(self.parameters_dict['block_min_rest_duration'])
        self.session_length_max = float(self.parameters_dict['session_length_max'])
        self.session_trial_max = float(self.parameters_dict['session_trial_max'])
        self.stimulus_duration_probe_active = self.parameters_dict['stimulus_duration_probe_active']
        if self.stimulus_duration_probe_active == 'True':
            self.stimulus_duration_probe_active = True
        else:
            self.stimulus_duration_probe_active = False
        self.flanker_probe_active = self.parameters_dict['flanker_probe_active']
        if self.flanker_probe_active == "True":
            self.flanker_probe_active = True
        else:
            self.flanker_probe_active = False
            
        self.hold_image = config_file['Hold']['hold_image']
        self.mask_image = config_file['Mask']['mask_image']
    
    def initialize_language_localization(self):
        lang_folder_path = 'Protocol' + self.folder_mod + 'iCPT2GStim1' + self.folder_mod + 'Language' + self.folder_mod + self.language + self.folder_mod
        
        # Labels #
        start_path = lang_folder_path + 'Start.txt'
        start_open = open(start_path,'r',encoding= "utf-8")
        self.start_label = start_open.read()
        start_open.close()
        
        break_path = lang_folder_path + 'Break.txt'
        break_open = open(break_path,'r',encoding= "utf-8")
        self.break_label = break_open.read()
        break_open.close()
        
        end_path = lang_folder_path + 'End.txt'
        end_open = open(end_path,'r',encoding= "utf-8")
        self.end_label = end_open.read()
        end_open.close()
        
        # Buttons #
        button_lang_path = lang_folder_path + 'Button.ini'
        button_lang_config = configparser.ConfigParser()
        button_lang_config.read(button_lang_path,encoding= "utf-8")
        
        self.start_button_label = button_lang_config['Button']['start']
        self.continue_button_label = button_lang_config['Button']['continue']
        self.return_button_label = button_lang_config['Button']['return']
        
        # Feedback #
        feedback_lang_path = lang_folder_path + 'Feedback.ini'
        feedback_lang_config = configparser.ConfigParser(allow_no_value=True)
        feedback_lang_config.read(feedback_lang_path,encoding="utf-8")
        
        self.stim_feedback_correct = feedback_lang_config['Stimulus']['correct']
        stim_feedback_correct_color = feedback_lang_config['Stimulus']['correct_colour']
        if stim_feedback_correct_color != '':
            color_text = '[color=%s]' % (stim_feedback_correct_color)
            self.stim_feedback_correct = color_text + self.stim_feedback_correct + '[/color]'
            
        self.stim_feedback_incorrect = feedback_lang_config['Stimulus']['incorrect']
        stim_feedback_incorrect_color = feedback_lang_config['Stimulus']['incorrect_colour']
        if stim_feedback_incorrect_color != '':
            color_text = '[color=%s]' % (stim_feedback_incorrect_color)
            self.stim_feedback_incorrect = color_text + self.stim_feedback_incorrect + '[/color]'
            
        self.hold_feedback_wait = feedback_lang_config['Hold']['wait']
        hold_feedback_wait_color = feedback_lang_config['Hold']['wait_colour']
        if hold_feedback_wait_color != '':
            color_text = '[color=%s]' % (hold_feedback_wait_color)
            self.hold_feedback_wait = color_text + self.hold_feedback_wait + '[/color]'
            
        self.hold_feedback_return = feedback_lang_config['Hold']['return']
        hold_feedback_return_color = feedback_lang_config['Hold']['return_colour']
        if hold_feedback_return_color != '':
            color_text = '[color=%s]' % (hold_feedback_return_color)
            self.hold_feedback_return = color_text + self.hold_feedback_return + '[/color]'
    
    def initialize_parameters(self):
        ## Strings
        self.protocol_name = 'iCPT2GStim1'
        
        #ListVariables#
        self.stage_list = ['Training','Main','Stimulus Duration Probe','Flanker Probe']
        
        #Boolean#
        self.stimulus_on_screen = False
        self.iti_active = False
        self.current_correction = False
        self.block_started = False
        self.feedback_on_screen = False
        self.hold_active = True
        
        #ActiveVariables - Count#
        
        self.current_block = 1
        self.current_trial = 1
        self.current_hits = 0
        self.stage_index = 0
        self.trial_outcome = 1 #1-Hit,2-Miss,3-Mistake,4-Correct Rejection,5-Premature
        
        #ActiveVariables - String#
        self.center_image = self.training_image
        self.current_stage = self.stage_list[self.stage_index]
    
        
        #TimeVariables#
        self.start_iti = 0
        self.start_time = 0
        self.current_time = 0
        self.start_stimulus = 0
        self.response_lat = 0
        self.block_start = 0
        
        #FolderPath#
        self.image_folder = 'Protocol' + self.folder_mod + 'iCPT2GStim1' + self.folder_mod + 'Image' + self.folder_mod
        
        
    def initialize_image_widgets(self):
        
        self.hold_button_image_path = self.image_folder + self.hold_image + '.png'
        self.hold_button = ImageButton(source=self.hold_button_image_path,allow_stretch=True)
        self.hold_button.size_hint = ((0.2* self.screen_ratio),0.2)
        self.hold_button.pos_hint = {"center_x":0.5,"center_y":0.1}
        
        self.center_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.center_stimulus = ImageButton(source=self.center_stimulus_image_path,allow_stretch=True)
        self.center_stimulus.size_hint = ((0.4* self.screen_ratio),0.4)
        self.center_stimulus.pos_hint = {"center_x":0.5,"center_y":0.6}
        self.center_stimulus.bind(on_press = self.center_pressed)
        
        self.left_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.left_stimulus = ImageButton(source=self.left_stimulus_image_path,allow_stretch=True)
        self.left_stimulus.size_hint = ((0.4* self.screen_ratio),0.4)
        self.left_stimulus.pos_hint = {"center_x":0.2,"center_y":0.6}
        
        self.right_stimulus_image_path = self.image_folder + self.training_image + '.png'
        self.right_stimulus = ImageButton(source=self.right_stimulus_image_path,allow_stretch=True)
        self.right_stimulus.size_hint = ((0.4* self.screen_ratio),0.4)
        self.right_stimulus.pos_hint = {"center_x":0.8,"center_y":0.6}
        
    def initialize_text_widgets(self):
        self.instruction_label = Label(text= self.start_label
                                       , font_size = '35sp')
        self.instruction_label.size_hint = (0.6,0.4)
        self.instruction_label.pos_hint = {'center_x':0.5,'center_y':0.3}
        
        self.block_label = Label(text= self.break_label,font_size='50sp')
        self.block_label.size_hint = (0.5,0.3)
        self.block_label.pos_hint = {'center_x':0.5,'center_y':0.3}
        
        self.end_label = Label(text= self.end_label, font_size='50sp')
        self.end_label.size_hint = (0.6,0.4)
        self.end_label.pos_hint = {'center_x':0.5,'center_y':0.3}
        
        self.feedback_string = ''
        self.feedback_label = Label(text=self.feedback_string,font_size='50sp', markup=True)
        self.feedback_label.size_hint = (0.7,0.4)
        self.feedback_label.pos_hint = {'center_x':0.5,'center_y':0.5}
        
    def initialize_button_widgets(self):
        self.start_button = Button(text=self.start_button_label)
        self.start_button.size_hint = (0.1,0.1)
        self.start_button.pos_hint = {'center_x':0.5,'center_y':0.7}
        self.start_button.bind(on_press=self.start_protocol)
        
        self.continue_button = Button(text=self.continue_button_label)
        self.continue_button.size_hint = (0.1,0.1)
        self.continue_button.pos_hint = {'center_x':0.5,'center_y':0.7}
        self.continue_button.bind(on_press=self.block_end)
        
        self.return_button = Button(text=self.return_button_label)
        self.return_button.size_hint = (0.1,0.1)
        self.return_button.pos_hint = {'center_x':0.5,'center_y':0.7}
        self.return_button.bind(on_press=self.return_to_main)
        
    def generate_output_files(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        if os.path.exists(folder_path) == False:
            os.makedirs(folder_path)
        folder_list = os.listdir(folder_path)
        file_index = 1
        temp_filename = self.participant_id + '_iCPT2G_' + str(file_index) + '.csv'
        self.file_path = folder_path + self.folder_mod + temp_filename
        while os.path.isfile(self.file_path):
            file_index += 1
            temp_filename = self.participant_id + '_iCPT2G_' + str(file_index) + '.csv'
            self.file_path = folder_path + self.folder_mod + temp_filename
        data_cols = 'TrialNo,Stage,Block #,Trial Type,Correction Trial,Response,Contingency,Outcome,Response Latency'
        self.data_file = open(self.file_path, "w+")
        self.data_file.write(data_cols)
        self.data_file.close()
    
    def image_list_generator(self):
        distractor_prob = 1 - self.target_probability
        target_prob_single = self.target_probability / len(self.correct_images)
        distractor_prob_single = distractor_prob / len(self.incorrect_images)
        self.image_prob_list = list()
        for a in range(0,len(self.correct_images)):
            self.image_prob_list.append(target_prob_single)
        for a in range(0,len(self.incorrect_images)):
            self.image_prob_list.append(distractor_prob_single)
            
    def metadata_output_generation(self):
        folder_path = 'Data' + self.folder_mod + self.participant_id
        metadata_rows = ['participant_id','training_image','correct_images',
                         'incorrect_images','stimulus_duration','limited_hold',
                         'target_probability','iti_length','feedback_length',
                         'block_max_length','block_max_count','block_min_rest_duration',
                         'session_length_max','session_trial_max']
    
        
        meta_list = list()
        for meta_row in metadata_rows:
            row_list = list()
            row_list.append(meta_row)
            row_list.append(str(self.parameters_dict[meta_row]))
            meta_list.append(row_list)
            #meta_array[row_index,0] = meta_row
            #meta_array[row_index,1] = self.parameters_dict[meta_row]
        
        file_index = 1
        meta_output_filename = self.participant_id + '_iCPT2G_Metadata_' + str(file_index) + '.csv'
        meta_output_path = folder_path + self.folder_mod + meta_output_filename
        while os.path.isfile(meta_output_path):
            file_index += 1
            meta_output_filename = self.participant_id + '_iCPT2G_Metadata_' + str(file_index) + '.csv'
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
        self.trial_contingency(1,1)
        self.protocol_floatlayout.clear_widgets()
        self.trial_contingency(1,1)
        self.protocol_floatlayout.add_widget(self.hold_button)
    
    # End Staging #
    def protocol_end(self):
        self.protocol_floatlayout.clear_widgets()
        self.protocol_floatlayout.add_widget(self.end_label)
        self.protocol_floatlayout.add_widget(self.return_button)
        
    def return_to_main(self):
        self.manager.current = 'mainmenu'
    
    # Protocol Staging #
    
    def start_protocol(self,*args):
        self.protocol_floatlayout.remove_widget(self.instruction_label)
        self.protocol_floatlayout.remove_widget(self.start_button)
        self.start_clock()
        
        self.protocol_floatlayout.add_widget(self.hold_button)
        self.hold_button.bind(on_press=self.iti)
    
        
    def iti(self,*args):
        if self.iti_active == False:
            self.hold_button.unbind(on_press=self.iti)
            self.hold_button.bind(on_release=self.premature_response)
            self.start_iti = time.time()
            self.iti_active = True
            
            if self.feedback_string == self.hold_feedback_wait:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_string = ''
            
            if self.feedback_on_screen == False:
                self.feedback_label.text = self.feedback_string
                self.protocol_floatlayout.add_widget(self.feedback_label)
                self.feedback_start_time = time.time()
                self.feedback_on_screen = True
            if ((time.time() - self.feedback_start_time) > self.feedback_length) and self.feedback_on_screen == True:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_on_screen = False
            Clock.schedule_interval(self.iti,0.1)
        if self.iti_active == True:
            if (((time.time() - self.start_iti) > self.feedback_length) or ((time.time() - self.feedback_start_time) > self.feedback_length)) and self.feedback_on_screen == True:
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_on_screen = False
            if (time.time() - self.start_iti) > self.iti_length:
                Clock.unschedule(self.iti)
                self.iti_active = False
                self.hold_button.unbind(on_release=self.premature_response)
                self.hold_active = True
                self.stimulus_presentation()
                
    def stimulus_presentation(self,*args):
        if self.stimulus_on_screen == False:
            self.protocol_floatlayout.add_widget(self.center_stimulus)
            self.hold_button.bind(on_press = self.hold_returned_stim)
            self.hold_button.bind(on_release=self.hold_removed_stim)
            
            self.start_stimulus = time.time()
        
            self.stimulus_on_screen = True
            Clock.schedule_interval(self.stimulus_presentation,0.1)
            
        elif self.stimulus_on_screen == True:
            if (time.time() - self.start_stimulus) > self.stimulus_duration:
                self.center_stimulus_image_path = self.image_folder + self.mask_image + '.png'
                self.center_stimulus.source = self.center_stimulus_image_path
            if (time.time() - self.start_stimulus) > self.limited_hold:
                Clock.unschedule(self.stimulus_presentation)
                self.protocol_floatlayout.remove_widget(self.center_stimulus)
                self.stimulus_on_screen = False
                self.center_notpressed()
                
    def premature_response(self,*args):
        if self.stimulus_on_screen == True:
            return None
        
        Clock.unschedule(self.iti)
        self.feedback_string = self.hold_feedback_wait
        contingency = '2'
        response = '1'
        self.trial_outcome='5'
        self.write_summary_file(response, contingency)
        self.response_lat = 0
        self.iti_active = False
        self.feedback_label.text = self.feedback_string
        if self.feedback_on_screen == False:
            self.protocol_floatlayout.add_widget(self.feedback_label)
        self.hold_button.unbind(on_release=self.premature_response)
        self.hold_button.bind(on_press=self.iti)
        
    def return_hold(self):
        self.feedback_string = self.hold_feedback_return
        self.hold_button.bind(on_press=self.iti)
        
            
        
    # Contingency Stages #
    def center_pressed(self,*args):
        Clock.unschedule(self.stimulus_presentation)
        self.protocol_floatlayout.remove_widget(self.center_stimulus)
        self.stimulus_on_screen = False
        self.response_lat = time.time() - self.start_stimulus
        response = '1'
        if (self.center_image in self.correct_images) or (self.center_image == self.training_image):
            self.feedback_string = self.stim_feedback_correct
            contingency = '1'
            self.trial_outcome = '1'
            self.current_hits += 1
        else:
            self.feedback_string = self.stim_feedback_incorrect
            self.trial_outcome = '3'
            contingency = '0'
            
        self.feedback_label.text = self.feedback_string
        self.protocol_floatlayout.add_widget(self.feedback_label)
        self.feedback_start_time = time.time()
        self.feedback_on_screen = True
        self.write_summary_file(response,contingency)
        self.trial_contingency(response, contingency)
        
        self.hold_button.unbind(on_press=self.hold_returned_stim)
        self.hold_button.unbind(on_release=self.hold_removed_stim)
        
        self.hold_button.bind(on_press=self.iti)
    
    def center_notpressed(self):
        self.response_lat = ''
        response = '0'
        if (self.center_image in self.correct_images) or (self.center_image==self.training_image):
            self.feedback_string = ''
            contingency = '0' #######
            self.trial_outcome = '2' #####
        else:
            self.feedback_string = ''
            contingency = '1' #####
            self.trial_outcome = '4' ######
        self.write_summary_file(response,contingency)
        self.trial_contingency(response, contingency)
        
        self.hold_button.unbind(on_press=self.hold_returned_stim)
        self.hold_button.unbind(on_release=self.hold_removed_stim)
        
        if self.hold_active == True:
            self.iti()
        else:
            self.return_hold()
        
    def hold_removed_stim(self,*args):
        self.hold_active = False
        return
    
    def hold_returned_stim(self,*args):
        self.hold_active = True
        return
        
        
    # Data Saving Functions #
    def write_summary_file(self,response,contingency):
        data_file = open(self.file_path, "a")
        data_file.write("\n")
        data_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s" % (self.current_trial,self.current_stage,self.current_block,self.center_image,int(self.current_correction),response,contingency,self.trial_outcome,self.response_lat))
        data_file.close()
        return
    
    # Trial Contingency Functions #
    
    def trial_contingency(self,response,contingency):
        self.current_trial += 1
        
        if self.current_trial > self.session_trial_max:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()
            return
        
        if (self.current_hits > 10) and (self.stage_index == 0):
            self.feedback_start = time.time()
            self.protocol_floatlayout.remove_widget(self.hold_button)
            #self.block_contingency()
            Clock.schedule_interval(self.block_contingency,0.1)
            return
        
        if self.current_hits >= self.block_max_length:
            self.feedback_start = time.time()
            self.protocol_floatlayout.remove_widget(self.hold_button)
            #self.block_contingency()
            Clock.schedule_interval(self.block_contingency,0.1)
            return
        
        if contingency == '0' and response == "1":
            self.current_correction = True
            self.center_stimulus_image_path = self.image_folder + self.center_image + '.png'
            return
        elif contingency == '2':
            self.center_stimulus_image_path = self.image_folder + self.center_image + '.png'
            return
        else:
            self.current_correction = False
            if self.stage_index == 0:
                self.center_image = self.training_image
            elif self.stage_index == 1:
                self.center_image = np.random.choice(a=self.total_image_list,size=None,p=self.image_prob_list)
                print('random')
            self.center_stimulus_image_path = self.image_folder + self.center_image + '.png'
            self.center_stimulus.source = self.center_stimulus_image_path
        
    def block_contingency(self,*args):
        
        if self.feedback_on_screen == True:
            curr_time = time.time()
            if (curr_time - self.feedback_start) >= self.feedback_length:
                Clock.unschedule(self.block_contingency)
                self.protocol_floatlayout.remove_widget(self.feedback_label)
                self.feedback_string = ''
                self.feedback_label.text = self.feedback_string
                self.feedback_on_screen = False
            else:
                return
        else:
            Clock.unschedule(self.block_contingency)
        
        self.protocol_floatlayout.clear_widgets()
        
        
        self.current_block += 1
        self.current_hits = 0
        
        if (self.current_block > self.block_max_count) or self.stage_index == 0:
            self.stage_index += 1
            self.current_block = 1
            self.current_stage = self.stage_list[self.stage_index]
            if self.stage_index == 2 and self.stimulus_duration_probe_active == False:
                self.stage_index += 1
            if self.stage_index == 3 and self.flanker_probe_active == False:
                Clock.unschedule(self.clock_monitor)
                self.protocol_end()
                return
        
        self.block_screen()
            
    
    # Time Monitor Functions #
    def start_clock(self,*args):
        self.start_time = time.time()
        Clock.schedule_interval(self.clock_monitor,0.1)
        Clock.schedule_interval(self.display_monitor,0.1)
    
    def clock_monitor(self,*args):
        self.current_time = time.time()
        self.elapsed_time = self.current_time - self.start_time
        
        if self.elapsed_time > self.session_length_max:
            Clock.unschedule(self.clock_monitor)
            self.protocol_end()
            
    def display_monitor(self,*args):
       width  = self.protocol_floatlayout.width
       height = self.protocol_floatlayout.height
       
       self.screen_ratio = width/height
            
        
        
        