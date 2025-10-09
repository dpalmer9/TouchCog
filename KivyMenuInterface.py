##############################################################################
#                      Kivy Launcher Interface                               #
#                      by: Daniel Palmer PhD                                 #
#                      revisions: Filip Kosel PhD                            #
#                      Version: 2.1                                          #
##############################################################################

# Setup #

import configparser
import cProfile
import importlib
import importlib.util
import os
import pathlib
import subprocess
import re
import sys
import queue

os.environ['KIVY_VIDEO'] = 'ffpyplayer'
os.environ['KIVY_AUDIO'] = 'ffpyplayer'

def get_base_path():
	"""
	Determines the correct base path for the executable, whether running
	in a PyInstaller bundle or in development mode.
	"""
	if getattr(sys, 'frozen', False):
		# Running as a PyInstaller executable: use the path of the exe itself
		return pathlib.Path(sys.executable).resolve().parent
	else:
		# Running in development: use the script's current directory
		return pathlib.Path(__file__).parent.resolve()

from kivy.config import Config
# Change current working directory to location of this file

def get_refresh_rate():
	"""
	Returns the current display refresh rate as an integer (Hz).
	Falls back to sensible defaults or None when detection is not possible.
	"""
	if sys.platform.startswith('win'):
		import ctypes
		user32 = ctypes.windll.user32
		class DEVMODE(ctypes.Structure):
			_fields_ = [
				("dmDeviceName", ctypes.c_wchar * 32),
				("dmSpecVersion", ctypes.c_ushort),
				("dmDriverVersion", ctypes.c_ushort),
				("dmSize", ctypes.c_ushort),
				("dmDriverExtra", ctypes.c_ushort),
				("dmFields", ctypes.c_ulong),
				("dmOrientation", ctypes.c_short),
				("dmPaperSize", ctypes.c_short),
				("dmPaperLength", ctypes.c_short),
				("dmPaperWidth", ctypes.c_short),
				("dmScale", ctypes.c_short),
				("dmCopies", ctypes.c_short),
				("dmDefaultSource", ctypes.c_short),
				("dmPrintQuality", ctypes.c_short),
				("dmColor", ctypes.c_short),
				("dmDuplex", ctypes.c_short),
				("dmYResolution", ctypes.c_short),
				("dmTTOption", ctypes.c_short),
				("dmCollate", ctypes.c_short),
				("dmFormName", ctypes.c_wchar * 32),
				("dmLogPixels", ctypes.c_ushort),
				("dmBitsPerPel", ctypes.c_ulong),
				("dmPelsWidth", ctypes.c_ulong),
				("dmPelsHeight", ctypes.c_ulong),
				("dmDisplayFlags", ctypes.c_ulong),
				("dmDisplayFrequency", ctypes.c_ulong)
			]
		devmode = DEVMODE()
		devmode.dmSize = ctypes.sizeof(DEVMODE)
		if user32.EnumDisplaySettingsW(None, -1, ctypes.byref(devmode)):
			return int(devmode.dmDisplayFrequency)
		return 60  # fallback
	elif sys.platform.startswith('linux'):
		# Try to use xrandr (X11). For Wayland or systems without xrandr this will fail and return None
		try:
			out = subprocess.check_output(['xrandr', '--verbose'], stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
			# First try to find the frequency value that has a '*' (current mode), e.g. "60.00*"
			m = re.search(r"(\d+(?:\.\d+)?)\s*\*", out)
			if m:
				rate = float(m.group(1))
				return int(round(rate))
			# Fallback: search for 'current' lines that mention Hz
			m = re.search(r"[Cc]urrent[^\n\r]*?(\d+(?:\.\d+)?)\s*Hz", out)
			if m:
				rate = float(m.group(1))
				return int(round(rate))
		except Exception:
			pass
		# Could not detect
		return None
	elif sys.platform.startswith('darwin'):
		try:
			out = subprocess.check_output(['system_profiler', 'SPDisplaysDataType'], stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
			m = re.search(r'Refresh Rate:\s*(\d+(?:\.\d+)?)\s*Hz', out)
			if m:
				return int(round(float(m.group(1))))
		except Exception:
			pass
		# Could not detect
		return None
	else:
		return None




# Change current working directory to location of this file

app_root = get_base_path()

config_path = app_root / 'Screen.ini'

config_file = configparser.ConfigParser()
config_file.read(config_path)

x_dim = config_file['Screen']['x']
y_dim = config_file['Screen']['y']

fullscreen = int(config_file['Screen']['fullscreen'])
virtual_keyboard = int(config_file['keyboard']['virtual_keyboard'])
use_mouse = int(config_file['mouse']['use_mouse'])
Config.set('graphics', 'allow_screensaver', 0)
Config.set('kivy', 'kivy_clock', 'interrupt')
maxfps = get_refresh_rate()
if maxfps is not None:
	Config.set('graphics', 'maxfps', str(maxfps))
else:
	Config.set('graphics', 'maxfps', 0)

if fullscreen == 0:
	Config.set('graphics', 'width', str(x_dim))
	Config.set('graphics', 'height', str(y_dim))
	Config.set('graphics', 'fullscreen', '0')
	Config.set('graphics', 'position', 'custom')
	Config.set('graphics', 'top', 0)
	Config.set('graphics', 'left', 0)

elif fullscreen == 1:
	Config.set('graphics', 'width', str(x_dim))
	Config.set('graphics', 'height', str(y_dim))
	Config.set('graphics', 'position', 'custom')
	Config.set('graphics', 'top', 0)
	Config.set('graphics', 'left', 0)
	Config.set('graphics', 'fullscreen', True)


if virtual_keyboard == 0:
	Config.set('kivy', 'keyboard_mode', 'system')

elif virtual_keyboard == 1:
	Config.set('kivy', 'keyboard_mode', 'systemanddock')


if use_mouse == 0:
	Config.set('graphics', 'show_cursor', 0)




# Imports #

import configparser
import kivy
import os
import pandas as pd
import sys
import zipimport

from Classes.Menu import MenuBase

from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox




# Window.borderless = True

Window.size = (int(x_dim), int(y_dim))
Window.borderless = '0'

def search_protocols():
		
		task_list = list(pathlib.Path().glob('Protocol/*'))
		output_list = list()
		
		for task in task_list:
		
			if not task.is_dir():
				continue
			
			output_list.append(task.stem)
		
		return output_list

def protocol_constructor(protocol, mod_name):
		
		def lazy_import(protocol, mod_name):
			working = pathlib.Path('Protocol', protocol, 'Task', f'{mod_name}.py')
			mod_spec = importlib.util.spec_from_file_location(mod_name, working)
			mod_loader = importlib.util.LazyLoader(mod_spec.loader)
			mod_spec.loader = mod_loader
			module = importlib.util.module_from_spec(mod_spec)
			sys.modules[mod_name] = module
			mod_loader.exec_module(module)
			
			return module
		
		task_module = lazy_import(protocol, mod_name)

		return task_module


# Class Objects #

class ImageButton(ButtonBehavior, Image):
	
	def __init__(self, **kwargs):
		
		super(ImageButton, self).__init__(**kwargs)




# Class Screen Manager #

class ScreenManager(ScreenManager):
	
	def __init__(self, **kwargs):
		
		super(ScreenManager, self).__init__(**kwargs)




# Class Task Selection #

class MainMenu(Screen):
	
	def __init__(self, **kwargs):
		
		super(MainMenu, self).__init__(**kwargs)
		self.name = 'mainmenu'
		self.Menu_Layout = FloatLayout()
		self.protocol_window = ''
		self.add_widget(self.Menu_Layout)
		launch_button = Button(text='Start Session')
		launch_button.size_hint = (0.3, 0.2)
		launch_button.pos_hint = {'x': 0.35, 'y': 0.6}
		launch_button.bind(on_press=self.load_protocol_menu)
		self.Menu_Layout.add_widget(launch_button)
		battery_button = Button(text='Protocol Battery')
		battery_button.size_hint = (0.3, 0.2)
		battery_button.pos_hint = {'x': 0.35, 'y': 0.4}
		battery_button.bind(on_press=self.load_battery_menu)
		self.Menu_Layout.add_widget(battery_button)
		
		exit_button = Button(text='Close Program')
		exit_button.size_hint = (0.3, 0.2)
		exit_button.pos_hint = {'x': 0.35, 'y': 0.2}
		exit_button.bind(on_press=self.exit_program)
		self.Menu_Layout.add_widget(exit_button)
	
	

	def load_protocol_menu(self, *args):
		
		if isinstance(self.protocol_window, ProtocolMenu):
			self.manager.current = 'protocolmenu'
		
		else:
			self.protocol_window = ProtocolMenu()
			self.manager.add_widget(self.protocol_window)
			self.manager.current = 'protocolmenu'
	
	def load_battery_menu(self, *args):
		
		if isinstance(self.protocol_window, ProtocolBattery):
			self.manager.current = 'protocolbattery'
		
		else:
			self.protocol_window = ProtocolBattery()
			self.manager.add_widget(self.protocol_window)
			self.manager.current = 'protocolbattery'
	
	def exit_program(self, *args):
		
		App.get_running_app().stop()
		Window.close()




# Class Protocol Selection #

class ProtocolMenu(Screen):
	
	def __init__(self, **kwargs):
		
		super(ProtocolMenu, self).__init__(**kwargs)
		
		self.Protocol_Layout = FloatLayout()
		self.Protocol_Configure_Screen = ''
		self.name = 'protocolmenu'
		
		self.Protocol_Configure_Screen = MenuBase()
		
		protocol_list = search_protocols()
		self.Protocol_List = GridLayout(rows=len(protocol_list), cols=1)
		protocol_index = 0
		
		for protocol in protocol_list:
			button_func = partial(self.set_protocol, protocol)
			self.Protocol_List.add_widget(Button(text=protocol, on_press=button_func))
			protocol_index += 1
		
		
		self.Protocol_List.size_hint = (0.8, 0.7)
		self.Protocol_List.pos_hint = {'x': 0.1, 'y': 0.3}
		self.Protocol_Layout.add_widget(self.Protocol_List)
		
		cancel_button = Button(text='Cancel')
		cancel_button.size_hint = (0.2, 0.1)
		cancel_button.pos_hint = {'x': 0.4, 'y': 0.1}
		cancel_button.bind(on_press=self.cancel_protocol)
		self.Protocol_Layout.add_widget(cancel_button)
		
		self.add_widget(self.Protocol_Layout)
	
	
	
	def set_protocol(self, label, *args):
		
		if isinstance(self.Protocol_Configure_Screen, MenuBase):
			self.manager.remove_widget(self.Protocol_Configure_Screen)
		
		task_module = protocol_constructor(label, 'Menu')
		self.Protocol_Configure_Screen = task_module.ConfigureScreen()
		self.Protocol_Configure_Screen.size = Window.size
		self.manager.add_widget(self.Protocol_Configure_Screen)
		self.manager.current = self.Protocol_Configure_Screen.name
	
	
	
	def cancel_protocol(self, *args):
		
		self.manager.current = 'mainmenu'

class ProtocolBattery(Screen):

	def __init__(self, **kwargs):
		super(ProtocolBattery, self).__init__(**kwargs)

		self.app = App.get_running_app()

		self.protocol_battery_layout = FloatLayout()
		self.protocol_configure_screen = MenuBase()
		self.name = 'protocolbattery'

		self.protocol_list = search_protocols()

		# Build tight horizontal rows: each row is a BoxLayout with checkbox directly to the left of the label
		if len(self.protocol_list) == 0:
			no_label = Label(text='No protocols found', size_hint=(0.8, 0.1), pos_hint={'x':0.1,'y':0.45})
			self.protocol_battery_layout.add_widget(no_label)
		else:
			# single column grid where each child is a horizontal row (BoxLayout)
			# center the grid and make it occupy ~50% of vertical space
			self._protocol_grid = GridLayout(cols=1, spacing=10, padding=[10,10,10,10], size_hint=(0.8, 0.5), pos_hint={'x':0.1, 'y':0.25})
			self.protocol_checkboxes = {}

			for protocol in self.protocol_list:
				# each row is tighter horizontally but taller to accommodate larger checkbox and font
				row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=64)
				cb = CheckBox(size_hint=(None, None), size=(48, 48))
				# larger label font and vertically centered
				lbl = Label(text=protocol, valign='middle', halign='left', size_hint_x=1, font_size='28sp')
				# ensure label text is constrained to the widget bounds for proper alignment
				lbl.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, instance.height)))
				self.protocol_checkboxes[protocol] = cb
				row.add_widget(cb)
				row.add_widget(lbl)
				self._protocol_grid.add_widget(row)

			self.protocol_battery_layout.add_widget(self._protocol_grid)

		self.add_widget(self.protocol_battery_layout)

		
		battery_start_button = Button(text='Start Battery')
		battery_start_button.size_hint = (0.2, 0.1)
		battery_start_button.pos_hint = {'x': 0.25, 'y': 0.1}
		battery_start_button.bind(on_press=self.start_battery)
		self.protocol_battery_layout.add_widget(battery_start_button)
		cancel_button = Button(text='Cancel')
		cancel_button.size_hint = (0.2, 0.1)
		cancel_button.pos_hint = {'x': 0.5, 'y': 0.1}
		cancel_button.bind(on_press=self.cancel_battery)
		self.protocol_battery_layout.add_widget(cancel_button)

	def cancel_battery(self, *args):

		self.manager.current = 'mainmenu'

	def start_battery(self, *args):
		# gather selected protocols from the checkbox widgets
		selected = []
		if hasattr(self, 'protocol_checkboxes') and isinstance(self.protocol_checkboxes, dict):
			for name, cb in self.protocol_checkboxes.items():
				# Kivy CheckBox uses the 'active' attribute
				try:
					if getattr(cb, 'active', False):
						selected.append(name)
				except Exception:
					# ignore widgets that don't expose active
					continue

		# store on the running app instance
		self.app.battery_protocols = selected
		# set battery_active True if any were selected, otherwise False
		self.app.battery_active = len(selected) > 0

		for battery in self.app.battery_protocols:
			self.app.start_next_battery_config()

		# Optional: you may want to proceed to main menu or start the selected protocols here
		return
	
	def start_battery_task(self, *args):
		return



# Class App Builder #

class MenuApp(App):
	
	def build(self):
		self.session_event_data = pd.DataFrame()
		self.session_event_path = ''
		self.summary_event_data = pd.DataFrame()
		self.summary_event_path = ''
		self.event_queue = queue.Queue()
		self.event_list = list()
		self.event_columns = list()

		self.battery_active = False
		self.battery_protocols = list()
		self.battery_index = 0
		self.battery_configs = {}

		self.s_manager = ScreenManager()
		self.main_menu = MainMenu()
		self.s_manager.add_widget(self.main_menu)
		
		return self.s_manager
	
	def start_next_battery_config(self):
		if self.battery_index < len(self.battery_protocols):
			protocol_name = self.battery_protocols[self.battery_index]
			protocol_module = protocol_constructor(protocol_name, 'Menu')
			config_screen = protocol_module.ConfigureScreen()
			config_screen.update_battery_mode(True)
			config_screen.size = Window.size
			self.s_manager.add_widget(config_screen)
			self.s_manager.current = config_screen.name
		else:
			self.start_battery_tasks()
	
	def start_battery_tasks(self):
		self.battery_index = 0
		if self.battery_index < len(self.battery_protocols):
			protocol_name = self.battery_protocols[self.battery_index]
			parameter_dict = self.battery_configs[protocol_name]
			task_module = protocol_constructor(protocol_name, 'Protocol')
			protocol_task_screen = task_module.ProtocolScreen(screen_resolution=Window.size)
			protocol_task_screen.load_parameters(parameter_dict)
			self.s_manager.add_widget(protocol_task_screen)
			self.s_manager.current = protocol_task_screen.name
		else:
			self.s_manager.current = 'mainmenu'
	
	def add_screen(self, screen):
		
		self.s_manager.add_widget(screen)
	
	
	
	def on_stop(self):
		self.event_queue.put(None)
		if len(self.event_list) > 0:
			self.session_event_data = pd.DataFrame(self.event_list)
			self.session_event_data = self.session_event_data.sort_values(by=['Time'])
			try:
				self.session_event_data.to_csv(self.session_event_path, index=False)
			except FileNotFoundError:
				pass
			try:
				self.summary_event_data.to_csv(self.summary_event_path, index=False)
			except FileNotFoundError:
				pass



if __name__ == '__main__':
	MenuApp().run()

