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
from Quartz import CGDisplayCopyDisplayMode, CGMainDisplayID
from AppKit import NSScreen

os.environ['KIVY_VIDEO'] = 'ffpyplayer'
os.environ['KIVY_AUDIO'] = 'ffpyplayer'

from kivy.config import Config
# Change current working directory to location of this file

def get_refresh_rate():
	"""
	Returns the current display refresh rate as an integer (Hz).
	Uses ctypes for Windows, xrandr for Linux, and Quartz/AppKit or system_profiler for macOS.
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
		# macOS: try Quartz (pyobjc), then AppKit, then system_profiler as a last resort
		try:
			# Try Quartz APIs (requires pyobjc-framework-Quartz)
			mode = CGDisplayCopyDisplayMode(CGMainDisplayID())
			if mode is not None:
				# mode may expose a 'refreshRate' attribute or method
				try:
					rate = mode.refreshRate()
				except Exception:
					rate = getattr(mode, 'refreshRate', None)
				if rate:
					return int(round(rate))
		except Exception:
			pass
		# Fallback: parse system_profiler output
		import subprocess
		import re
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

os.chdir(pathlib.Path(__file__).parent.resolve())

config_path = pathlib.Path('Screen.ini')

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
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.widget import Widget




# Window.borderless = True

Window.size = (int(x_dim), int(y_dim))
Window.borderless = '0'




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
		
		protocol_list = self.search_protocols()
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
		
		self.protocol_constructor(label)
		self.Protocol_Configure_Screen.size = Window.size
		self.manager.add_widget(self.Protocol_Configure_Screen)
		self.manager.current = 'menuscreen'
	
	
	
	def cancel_protocol(self, *args):
		
		self.manager.current = 'mainmenu'
	
	
	
	def search_protocols(self):
		
		task_list = list(pathlib.Path().glob('Protocol/*'))
		output_list = list()
		
		for task in task_list:
		
			if not task.is_dir():
				continue
			
			output_list.append(task.stem)
		
		return output_list
	
	
	
	def protocol_constructor(self, protocol):
		
		def lazy_import(protocol):
			
			working = pathlib.Path('Protocol', protocol, 'Task', 'Menu.py')
			mod_name = 'Menu'
			mod_spec = importlib.util.spec_from_file_location(mod_name, working)
			mod_loader = importlib.util.LazyLoader(mod_spec.loader)
			mod_spec.loader = mod_loader
			module = importlib.util.module_from_spec(mod_spec)
			sys.modules[mod_name] = module
			mod_loader.exec_module(module)
			
			return module
		
		task_module = lazy_import(protocol)
		
		self.Protocol_Configure_Screen = task_module.ConfigureScreen()




# Class App Builder #

class MenuApp(App):
	
	def build(self):
		
		self.session_event_data = pd.DataFrame()
		self.session_event_path = ''
		self.summary_event_data = pd.DataFrame()
		self.summary_event_path = ''
		self.s_manager = ScreenManager()
		self.main_menu = MainMenu()
		self.s_manager.add_widget(self.main_menu)
		
		return self.s_manager
	
	
	
	def add_screen(self, screen):
		
		self.s_manager.add_widget(screen)
	
	
	
	def on_stop(self):
		
		self.session_event_data = self.session_event_data.sort_values(by=['Time'])
		self.session_event_data.to_csv(self.session_event_path, index=False)
		self.summary_event_data.to_csv(self.summary_event_path, index=False)



if __name__ == '__main__':
	
	MenuApp().run()

