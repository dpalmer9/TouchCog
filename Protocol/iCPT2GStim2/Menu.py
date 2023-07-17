# Imports #
import kivy
import zipimport
import sys
import os
import configparser
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
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
## TextInput(text="Test",id="Test1")

class Configure_Screen(Screen):
    def __init__(self,**kwargs):
        super(Configure_Screen,self).__init__(**kwargs)
        self.main_layout = FloatLayout()
        
        if sys.platform == 'linux' or sys.platform == 'darwin':
            self.folder_mod = '/'
        elif sys.platform == 'win32':
            self.folder_mod = '\\'
        
        config_path = 'Protocol' + self.folder_mod + 'iCPT2GStim2' + self.folder_mod + 'Configuration.ini'
        self.config_file = configparser.ConfigParser()
        self.config_file.read(config_path)
        self.parameters_config = self.config_file['TaskParameters']
        print(self.parameters_config)
        num_parameters = len(self.parameters_config)
        
        self.setting_scrollview = ScrollView()
        self.setting_gridlayout = GridLayout(cols=2,rows=(num_parameters + 1))
        self.setting_scrollview.add_widget(self.setting_gridlayout)
        
        self.menu_constructor()
        
        self.setting_gridlayout.add_widget(Label(text='Language'))
        self.language_dropdown = DropDown()
        self.dropdown_main = Button(text='Select Language')
        self.language_list = ['English','French']
        for language in self.language_list:
            lang_button = Button(text=language, size_hint_y=None, height=100)
            lang_button.bind(on_release = lambda lang_button: self.language_dropdown.select(lang_button.text))
            self.language_dropdown.add_widget(lang_button)
        self.dropdown_main.bind(on_release=self.language_dropdown.open)
        self.language_dropdown.bind(on_select=lambda instance, x: setattr(self.dropdown_main,'text',x))
        self.setting_gridlayout.add_widget(self.dropdown_main)
        
        self.setting_scrollview.size_hint = (0.85,0.6)
        self.setting_scrollview.pos_hint = {"x": 0.1 ,"y":0.4}
        
        self.main_layout.add_widget(self.setting_scrollview)
        
        self.id_grid = GridLayout(cols=2,rows=1)
        self.id_label = Label(text='Participant ID')
        self.id_entry = TextInput(text='')
        self.id_grid.add_widget(self.id_label)
        self.id_grid.add_widget(self.id_entry)
        self.id_grid.size_hint = (0.85,0.05)
        self.id_grid.pos_hint = {'x':0.1,'y':0.3}
        self.main_layout.add_widget(self.id_grid)
        
        self.start_button = Button(text="Start Task")
        self.start_button.size_hint = (0.1,0.1)
        self.start_button.pos_hint = {"x":0.45,"y":0.1}
        self.start_button.bind(on_press=self.start_protocol)
        self.main_layout.add_widget(self.start_button)
        
        self.add_widget(self.main_layout)
        
    def start_protocol(self,*args):
        from Protocol.iCPT2GStim2.Protocol import ProtocolScreen
        protocol_task_screen = ProtocolScreen(screen_resolution=self.size)
        
        key = ''
        value = ''
        parameter_dict = {}
        for widget in self.setting_gridlayout.walk():
            if isinstance(widget,Label):
                key = widget.text
            elif isinstance(widget,TextInput):
                value = widget.text
                parameter_dict[key] = value
        parameter_dict['participant_id'] = self.id_entry.text
        if self.dropdown_main.text == 'Select Language':
            parameter_dict['language'] = 'English'
        else:
            parameter_dict['language'] = self.dropdown_main.text
        
        protocol_task_screen.load_parameters(parameter_dict)
        
        self.manager.switch_to(protocol_task_screen)
        
    def menu_constructor(self):
        for parameter in self.parameters_config:
            #label_widget_list.append(Label(text=parameter))
            #text_entry_list.append(TextInput(text=parameters_config[parameter]))
            self.setting_gridlayout.add_widget(Label(text=parameter))
            self.setting_gridlayout.add_widget(TextInput(text=self.parameters_config[parameter]))
            
        
        
