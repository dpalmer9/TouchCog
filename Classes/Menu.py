# Import

import configparser
import importlib
import importlib.util
import os
import pathlib
import sys

from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen ,ScreenManagerException
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput




class MenuBase(Screen):
	
	
	
	def __init__(self ,**kwargs):
		
		
		super(MenuBase ,self).__init__(**kwargs)
		
		self.name = 'menuscreen'
		self.main_layout = FloatLayout()
		
		if sys.platform == 'linux' or sys.platform == 'darwin':
			
			
			self.folder_mod = '/'
		
		
		elif sys.platform == 'win32':
			
			
			self.folder_mod = '\\'
		
		
		self.protocol_name = ''
		self.protocol_path = ''
		self.parameters_config = dict()
		self.setting_scrollview = ScrollView()
		self.setting_gridlayout = GridLayout()
		
		self.language_dropdown = DropDown()
		self.dropdown_main = Button(text='Select Language')
		self.language_list = ['English' ,'French']
		
		for language in self.language_list:
			
			
			lang_button = Button(text=language ,size_hint_y=None ,height=100)
			lang_button.bind(on_release=lambda lang_button: self.language_dropdown.select(lang_button.text))
			self.language_dropdown.add_widget(lang_button)
		
		
		self.dropdown_main.bind(on_release=self.language_dropdown.open)
		self.language_dropdown.bind(on_select=lambda instance ,x: setattr(self.dropdown_main ,'text' ,x))
		
		self.id_grid = GridLayout(cols=2 ,rows=1)
		self.id_label = Label(text='Participant ID')
		self.id_entry = TextInput(text='')
		self.id_grid.add_widget(self.id_label)
		self.id_grid.add_widget(self.id_entry)
		self.id_grid.size_hint = (0.85 ,0.05)
		self.id_grid.pos_hint = {'x': 0.1 ,'y': 0.3}
		
		self.back_button = Button(text='Back')
		self.back_button.size_hint = (0.1 ,0.1)
		self.back_button.pos_hint = {'x': 0.4 ,'y': 0.1}
		self.back_button.bind(on_press=self.return_menu)
		
		self.start_button = Button(text='Start Task')
		self.start_button.size_hint = (0.1 ,0.1)
		self.start_button.pos_hint = {'x': 0.6 ,'y': 0.1}
		self.start_button.bind(on_press=self.start_protocol)
		
		self.settings_widgets = [Label(text='Language') ,self.dropdown_main]
	
	
	
	def start_protocol(self ,*args):
		
		
		def lazy_import(protocol):
			
			
			working = pathlib.Path('Protocol' ,protocol ,'Task' ,'Protocol.py')
			
# 			cwd = os.getcwd()
# 			working = cwd + '\\Protocol\\' + protocol + '\\Task\\Protocol.py'
			
			mod_name = 'Protocol'
			mod_spec = importlib.util.spec_from_file_location(mod_name ,working)
			mod_loader = importlib.util.LazyLoader(mod_spec.loader)
			mod_spec.loader = mod_loader
			module = importlib.util.module_from_spec(mod_spec)
			sys.modules[mod_name] = module
			mod_loader.exec_module(module)
			
			return module
		
		
		task_module = lazy_import(self.protocol)
		protocol_task_screen = task_module.ProtocolScreen(screen_resolution=self.size)
		
		try:
			
			
			self.manager.remove_widget(self.manager.get_screen('protocolscreen'))
			self.manager.add_widget(protocol_task_screen)
		
		
		except ScreenManagerException:
			
			
			self.manager.add_widget(protocol_task_screen)
		
		
		key = ''
		value = ''
		parameter_dict = {}
		
		for widget in self.setting_gridlayout.walk():
			
			
			if isinstance(widget ,Label) and not isinstance(widget ,Button):
				
				
				key = widget.text
				key = key.lower()
				key = key.replace(' ' ,'_')
			
			
			elif isinstance(widget ,TextInput):
				
				
				value = widget.text
				parameter_dict[key] = value
			
			
			elif isinstance(widget ,Button):
				
				
				value = widget.text
				parameter_dict[key] = value
		
		
		parameter_dict['participant_id'] = self.id_entry.text
		
		if self.dropdown_main.text == 'Select Language':
			
			
			parameter_dict['language'] = 'English'
		
		
		else:
			
			
			parameter_dict['language'] = self.dropdown_main.text
		
		
		protocol_task_screen.load_parameters(parameter_dict)
		
		self.manager.current = 'protocolscreen'
	
	
	
	def return_menu(self ,*args):
		
		
		self.manager.current = 'protocolmenu'
	
	
	
	def menu_constructor(self ,protocol_name):
		
		
		self.protocol_name = protocol_name
		
		self.protocol_path = pathlib.Path('Protocol' ,self.protocol_name)
		config_path = self.protocol_path / 'Configuration.ini'
		
# 		self.protocol_path = os.getcwd() + self.folder_mod + 'Protocol' + self.folder_mod + self.protocol_name
# 		config_path = self.protocol_path + self.folder_mod + 'Configuration.ini'
		
		
		config_file = configparser.ConfigParser()
		config_file.read(config_path)
		self.parameters_config = config_file['TaskParameters']
		num_parameters = len(self.parameters_config)
		self.setting_gridlayout.rows = (num_parameters + int(len(self.settings_widgets) / 2))
		self.setting_gridlayout.cols = 2
		self.setting_scrollview.size_hint = (0.85 ,0.6)
		self.setting_scrollview.pos_hint = {'x': 0.1 ,'y': 0.4}
		
		for parameter in self.parameters_config:
			
			
			self.setting_gridlayout.add_widget(Label(text=parameter))
			self.setting_gridlayout.add_widget(TextInput(text=self.parameters_config[parameter]))
		
		
		for wid in self.settings_widgets:
			
			
			self.setting_gridlayout.add_widget(wid)
		
		
		self.setting_scrollview.add_widget(self.setting_gridlayout)
		self.main_layout.add_widget(self.setting_scrollview)
		self.main_layout.add_widget(self.id_grid)
		self.main_layout.add_widget(self.back_button)
		self.main_layout.add_widget(self.start_button)
		self.add_widget(self.main_layout)

