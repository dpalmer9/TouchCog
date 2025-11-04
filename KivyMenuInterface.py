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

config_path = app_root / 'Config.ini'

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
import json
import threading
import urllib.request

from Classes.Menu import MenuBase
from Classes.Survey import SurveyBase

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
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Line
from kivy.uix.dropdown import DropDown
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup




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

class LanguageMenu(Screen):
	
	def __init__(self, **kwargs):
		
		super(LanguageMenu, self).__init__(**kwargs)
		self.name = 'languagemenu'
		self.app = App.get_running_app()
		self.app.active_screen = self.name
		self.config = configparser.ConfigParser()
		self.config.read('Config.ini')
		self.Language_Layout = FloatLayout()
		self.add_widget(self.Language_Layout)

		self.manifest_path = 'http://nyx.canspace.ca/uploads/Touchscreen%20Tasks/manifest.json'

		self.language_list = list()
		with os.scandir(pathlib.Path('Language')) as entries:
			for entry in entries:
				if entry.is_dir():
					self.language_list.append(entry.name)
		self.language_dropdown = DropDown()
		self.language_drop_button = Button(text='Select Language')
		# Position dropdown near top middle
		self.language_drop_button.size_hint = (0.4, 0.08)
		self.language_drop_button.pos_hint = {'x': 0.3, 'y': 0.5}
		for language in self.language_list:
			btn = Button(text=language, size_hint_y=None, height=44)
			btn.bind(on_release=lambda btn: self.language_dropdown.select(btn.text))
			self.language_dropdown.add_widget(btn)

		self.language_dropdown.bind(on_select=lambda instance, x: setattr(self.language_drop_button, 'text', x))
		self.language_drop_button.bind(on_release=self.language_dropdown.open)
		self.Language_Layout.add_widget(self.language_drop_button)

		self.start_button = Button(text='Start')
		# Position start button near bottom center
		self.start_button.size_hint = (0.3, 0.12)
		self.start_button.pos_hint = {'x': 0.35, 'y': 0.08}
		self.start_button.bind(on_press=self.start_touchcog)

		self.Language_Layout.add_widget(self.start_button)
	
	def start_touchcog(self, *args):
		self.app.language = self.language_drop_button.text
		# If no language selected, just go to main menu
		if self.app.language == 'Select Language' or not self.app.language:
			self.app.language = self.config['language']['language']
			self.main_menu = MainMenu()
			self.manager.add_widget(self.main_menu)
			self.manager.current = 'mainmenu'
			return

		# Fetch manifest (from web then fallback to local file)
		manifest = self._fetch_manifest()
		if manifest is None:
			# Couldn't load manifest; proceed to main menu
			self.app.language = self.config['language']['language']
			self.main_menu = MainMenu()
			self.manager.add_widget(self.main_menu)
			self.manager.current = 'mainmenu'
			return

		# Extract language entries
		self.config['language']['language'] = self.app.language
		self.config.write(open('Config.ini', 'w'))
		language_entries = None
		try:
			for lang_block in manifest.get('languages', []):
				if self.app.language in lang_block:
					# lang_block[self.app.language] is a list with one dict
					language_entries = lang_block[self.app.language][0]
					break
		except Exception:
			language_entries = None

		if not language_entries:
			# Nothing to download for this language
			self.main_menu = MainMenu(self.app.language)
			self.manager.add_widget(self.main_menu)
			self.manager.current = 'mainmenu'
			return

		# Collect files from Videos and Text keys
		file_list = []
		for key in ('Videos', 'Text'):
			items = language_entries.get(key, [])
			for item in items:
				file_list.append(item)

		# Prepare UI: popup with progress bar and filename label
		self._download_popup_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
		self._download_label = Label(text='Preparing downloads...')
		self._download_bar = ProgressBar(max=100, value=0)
		self._download_popup_content.add_widget(self._download_label)
		self._download_popup_content.add_widget(self._download_bar)
		self._download_popup = Popup(title='Downloading language files', content=self._download_popup_content, size_hint=(0.6, 0.3))
		self._download_popup.open()

		# Run downloads in background thread
		thread = threading.Thread(target=self._download_files_thread, args=(file_list,))
		thread.daemon = True
		thread.start()

		# When downloads complete, the thread will switch to main menu


	def _fetch_manifest(self):
		# Try to fetch JSON from manifest_path; fallback to local manifest.json
		try:
			with urllib.request.urlopen(self.manifest_path, timeout=10) as resp:
				data = resp.read().decode('utf-8')
				return json.loads(data)
		except Exception:
			# Fallback to local file in project root
			local_path = app_root / 'manifest.json'
			try:
				with open(local_path, 'r', encoding='utf-8') as f:
					return json.load(f)
			except Exception:
				return None


	def _ensure_destination(self, destination_path):
		# destination_path is like '/Protocol/CPT/Language/English/' in manifest
		# Convert to local path under app_root
		# Strip leading slash if present
		rel = destination_path.lstrip('/').replace('/', os.sep)
		full = app_root / rel
		if not full.exists():
			full.mkdir(parents=True, exist_ok=True)
		return full


	def _download_files_thread(self, file_list):
		total = len(file_list)
		completed = 0
		for entry in file_list:
			name = entry.get('name')
			server_path = entry.get('server_path', '')
			destination_path = entry.get('destination_path', '')

			# Update label to current file
			Clock.schedule_once(lambda dt, n=name: setattr(self._download_label, 'text', f'Downloading: {n}'))

			# Determine local destination
			local_dest_dir = self._ensure_destination(destination_path)
			local_file = local_dest_dir / name

			# If file exists, skip
			if local_file.exists():
				completed += 1
				pct = int((completed / total) * 100)
				Clock.schedule_once(lambda dt, v=pct: setattr(self._download_bar, 'value', v))
				continue

			# If no server_path provided, skip
			if not server_path:
				completed += 1
				pct = int((completed / total) * 100)
				Clock.schedule_once(lambda dt, v=pct: setattr(self._download_bar, 'value', v))
				continue

			# Attempt download with progress
			try:
				with urllib.request.urlopen(server_path, timeout=30) as resp:
					length = resp.getheader('Content-Length')
					if length:
						total_size = int(length)
						bytes_so_far = 0
						with open(local_file, 'wb') as out:
							while True:
								chunk = resp.read(8192)
								if not chunk:
									break
								out.write(chunk)
								bytes_so_far += len(chunk)
								pct = int(((completed + bytes_so_far / total_size) / total) * 100)
								Clock.schedule_once(lambda dt, v=pct: setattr(self._download_bar, 'value', v))
					else:
						# Unknown total size: stream to file without progress
						with open(local_file, 'wb') as out:
							out.write(resp.read())
			except Exception:
				# On failure, ensure file doesn't exist
				try:
					if local_file.exists():
						local_file.unlink()
				except Exception:
					pass
			# Mark completed
			completed += 1
			pct = int((completed / total) * 100)
			Clock.schedule_once(lambda dt, v=pct: setattr(self._download_bar, 'value', v))

		# Close popup and proceed to main menu
		Clock.schedule_once(lambda dt: self._download_popup.dismiss())
		Clock.schedule_once(lambda dt: self._open_main_menu())


	def _open_main_menu(self, *args):
		self.app.language = self.config['language']['language']
		self.main_menu = MainMenu()
		self.manager.add_widget(self.main_menu)
		self.manager.current = 'mainmenu'


class MainMenu(Screen):
	
	def __init__(self, **kwargs):
		
		super(MainMenu, self).__init__(**kwargs)
		self.name = 'mainmenu'
		self.app = App.get_running_app()
		self.app.active_screen = self.name
		self.Menu_Layout = FloatLayout()
		self.protocol_window = ''
		self.language = self.app.language
		self.add_widget(self.Menu_Layout)
		self.menu_config = configparser.ConfigParser()
		self.menu_config.read(pathlib.Path('Language', self.language, 'mainmenu.ini'))
		launch_button = Button(text=self.menu_config['Text']['launch_button'])
		launch_button.size_hint = (0.3, 0.2)
		launch_button.pos_hint = {'x': 0.35, 'y': 0.6}
		launch_button.bind(on_press=self.load_protocol_menu)
		self.Menu_Layout.add_widget(launch_button)
		battery_button = Button(text=self.menu_config['Text']['battery_button'])
		battery_button.size_hint = (0.3, 0.2)
		battery_button.pos_hint = {'x': 0.35, 'y': 0.4}
		battery_button.bind(on_press=self.load_battery_menu)
		self.Menu_Layout.add_widget(battery_button)
		exit_button = Button(text=self.menu_config['Text']['exit_button'])
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
		
		if isinstance(self.protocol_window, BatteryMenu):
			self.manager.current = 'batterymenu'
		
		else:
			self.protocol_window = BatteryMenu()
			self.manager.add_widget(self.protocol_window)
			self.manager.current = 'batterymenu'
	
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
		self.app = App.get_running_app()
		self.app.active_screen = self.name
		self.language = self.app.language

		self.menu_config = configparser.ConfigParser()
		self.menu_config.read(pathlib.Path('Language', self.language, 'protocolmenu.ini'))
		self.Protocol_Configure_Screen = None
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

		cancel_button = Button(text=self.menu_config['Text']['cancel_button'])
		cancel_button.size_hint = (0.2, 0.1)
		cancel_button.pos_hint = {'x': 0.4, 'y': 0.1}
		cancel_button.bind(on_press=self.cancel_protocol)
		self.Protocol_Layout.add_widget(cancel_button)
		
		self.add_widget(self.Protocol_Layout)
	
	
	
	def set_protocol(self, label, *args):
		
		if isinstance(self.Protocol_Configure_Screen, MenuBase):
			self.manager.remove_widget(self.Protocol_Configure_Screen)
		elif isinstance(self.Protocol_Configure_Screen, SurveyBase):
			self.manager.remove_widget(self.Protocol_Configure_Screen)

		if pathlib.Path('Protocol', label, 'Task', 'Menu.py').is_file():
			task_module = protocol_constructor(label, 'Menu')
			self.Protocol_Configure_Screen = task_module.ConfigureScreen()
		else:
			task_module = protocol_constructor(label, 'Protocol')
			self.Protocol_Configure_Screen = task_module.SurveyProtocol()

		self.Protocol_Configure_Screen.size = Window.size
		self.manager.add_widget(self.Protocol_Configure_Screen)
		self.app.active_screen = self.Protocol_Configure_Screen.name
		self.manager.current = self.Protocol_Configure_Screen.name
	
	
	
	def cancel_protocol(self, *args):
		
		self.manager.current = 'mainmenu'

class BatteryMenu(Screen):
	def __init__(self, **kwargs):
		super(BatteryMenu, self).__init__(**kwargs)
		self.name = 'batterymenu'
		self.app = App.get_running_app()
		self.app.active_screen = self.name
		self.language = self.app.language
		
		# Load language config
		self.menu_config = configparser.ConfigParser()
		self.menu_config.read(pathlib.Path('Language', self.language, 'batterymenu.ini'))
		
		self.Battery_Layout = FloatLayout()
		
		# Load available batteries from Battery/ directory
		self.batteries = self._load_batteries()
		self.selected_battery = None
		self.battery_buttons = {}
		
		# Title
		title = Label(text='Select Battery', size_hint=(1, 0.1), pos_hint={'x': 0, 'y': 0.9}, font_size='24sp', bold=True)
		self.Battery_Layout.add_widget(title)
		
		# Create bordered container for battery list
		battery_container = FloatLayout(size_hint=(0.6, 0.6), pos_hint={'x': 0.2, 'y': 0.25})
		with battery_container.canvas.before:
			Color(1, 1, 1, 1)  # White border
			self.battery_border = Line(rectangle=(0, 0, 1, 1), width=3)
		battery_container.bind(pos=self.update_battery_border, size=self.update_battery_border)
		
		# ScrollView for battery list
		battery_scroll = ScrollView(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
		self.battery_grid = GridLayout(cols=1, spacing=5, padding=[10, 10, 10, 10], size_hint_y=None)
		self.battery_grid.bind(minimum_height=self.battery_grid.setter('height'))
		battery_scroll.add_widget(self.battery_grid)
		battery_container.add_widget(battery_scroll)
		self.Battery_Layout.add_widget(battery_container)
		
		# Populate battery list
		self.refresh_battery_list()
		
		# Start button
		start_button = Button(text='Start Selected Battery', size_hint=(0.25, 0.1), pos_hint={'x': 0.1, 'y': 0.05})
		start_button.bind(on_press=self.start_battery)
		self.Battery_Layout.add_widget(start_button)
		
		# Manual battery button
		manual_button = Button(text='Manual Battery', size_hint=(0.25, 0.1), pos_hint={'x': 0.4, 'y': 0.05})
		manual_button.bind(on_press=self.load_protocol_battery)
		self.Battery_Layout.add_widget(manual_button)
		
		# Cancel button
		cancel_button = Button(text=self.menu_config['Text']['cancel_button'], size_hint=(0.25, 0.1), pos_hint={'x': 0.65, 'y': 0.05})
		cancel_button.bind(on_press=self.cancel_battery)
		self.Battery_Layout.add_widget(cancel_button)
		
		self.add_widget(self.Battery_Layout)
	
	def update_battery_border(self, instance, value):
		"""Update the border when the container is resized or moved"""
		self.battery_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
	
	def _load_batteries(self):
		"""Load all battery JSON files from Battery/ directory"""
		batteries = []
		battery_path = pathlib.Path('Battery')
		
		if not battery_path.exists():
			return batteries
		
		try:
			for json_file in battery_path.glob('*.json'):
				try:
					with open(json_file, 'r', encoding='utf-8') as f:
						battery_data = json.load(f)
						batteries.append({
							'name': battery_data.get('name', json_file.stem),
							'path': json_file,
							'data': battery_data
						})
				except Exception as e:
					print(f"Error loading battery file {json_file}: {e}")
		except Exception as e:
			print(f"Error accessing Battery directory: {e}")
		
		return batteries
	
	def refresh_battery_list(self):
		"""Refresh the battery list display"""
		self.battery_grid.clear_widgets()
		self.battery_buttons.clear()
		
		if not self.batteries:
			no_label = Label(text='No batteries found', size_hint_y=None, height=50)
			self.battery_grid.add_widget(no_label)
			return
		
		for battery in self.batteries:
			btn = Button(text=battery['name'], size_hint_y=None, height=60, font_size='16sp')
			btn.bind(on_press=partial(self.select_battery, battery['name']))
			self.battery_buttons[battery['name']] = btn
			self.battery_grid.add_widget(btn)
	
	def select_battery(self, battery_name, *args):
		"""Toggle selection of a battery from the list"""
		# If clicking the same battery, deselect it
		if self.selected_battery == battery_name:
			self.battery_buttons[battery_name].background_color = (1, 1, 1, 1)
			self.selected_battery = None
		else:
			# Deselect previous selection
			if self.selected_battery and self.selected_battery in self.battery_buttons:
				self.battery_buttons[self.selected_battery].background_color = (1, 1, 1, 1)
			
			# Select new battery
			self.selected_battery = battery_name
			if battery_name in self.battery_buttons:
				self.battery_buttons[battery_name].background_color = (0.3, 0.6, 0.9, 1)  # Blue highlight
	
	def start_battery(self, *args):
		"""Start the selected battery"""
		if not self.selected_battery:
			print("No battery selected")
			return
		
		# Find the selected battery data
		battery_data = None
		for battery in self.batteries:
			if battery['name'] == self.selected_battery:
				battery_data = battery['data']
				break
		
		if not battery_data:
			return
		
		# Prompt for participant ID first, then build configurations and start tasks
		content = FloatLayout()
		input_box = TextInput(hint_text='Participant ID', size_hint=(0.8, 0.2), pos_hint={'x':0.1, 'y':0.45}, multiline=False)
		content.add_widget(input_box)
		msg_label = Label(text='Enter Participant ID to start battery', size_hint=(0.8, 0.2), pos_hint={'x':0.1,'y':0.7})
		content.add_widget(msg_label)

		def on_confirm(instance):
			participant_id = input_box.text.strip()
			if participant_id == '':
				# keep popup open if empty
				return

			# store participant id at app level
			self.app.participant_id = participant_id

			# Build protocol list and fully-populated configuration dicts
			protocols = [task.get('task') for task in battery_data.get('tasks', [])]
			self.app.battery_protocols = protocols
			self.app.battery_active = len(protocols) > 0
			self.app.battery_index = 0
			battery_configs = {}
			# track types (task vs survey) so we know whether to pass configs
			self.app.battery_task_types = {}

			for task in battery_data.get('tasks', []):
				pname = task.get('task')
				ttype = task.get('type', 'task')
				self.app.battery_task_types[pname] = ttype
				# Only build a configuration dict for actual 'task' types; surveys get no config
				if ttype == 'task':
					overrides = task.get('overrides', {}) or {}
					# Build a flat parameter dict (like MenuBase.start_protocol produces)
					parameter_dict = {}
					conf_path = pathlib.Path('Protocol', pname, 'Configuration.ini')
					if conf_path.is_file():
						cfg = configparser.ConfigParser()
						cfg.read(conf_path, encoding='utf-8')
						# choose which section to use for UI parameters
						use_section = 'TaskParameters'
						if 'DebugParameters' in cfg and cfg.getboolean('DebugParameters', 'debug_mode', fallback=False):
							use_section = 'DebugParameters'
						if use_section in cfg:
							for opt in cfg[use_section]:
								val = cfg.get(use_section, opt)
								# try to coerce numeric/bool types
								try:
									if isinstance(val, str) and val.lower() in ('true', 'false'):
										parsed = cfg.getboolean(use_section, opt)
									else:
										try:
											parsed = cfg.getint(use_section, opt)
										except Exception:
											try:
												parsed = cfg.getfloat(use_section, opt)
											except Exception:
												parsed = val
								except Exception:
									parsed = val
								# normalize key the same way MenuBase.start_protocol does
								key_norm = opt.lower().replace(' ', '_')
								parameter_dict[key_norm] = parsed
					else:
						# no config file: start with empty dict and allow overrides + participant id
						parameter_dict = {}

					# Apply overrides: support 'section.option' or match to normalized parameter names
					for k, v in overrides.items():
						if isinstance(k, str) and '.' in k:
							sec, opt = k.split('.', 1)
							# try to map section.option to parameter name if possible
							if conf_path.is_file():
								cfg_try = configparser.ConfigParser()
								cfg_try.read(conf_path, encoding='utf-8')
								if sec in cfg_try and opt in cfg_try[sec]:
									key_norm = opt.lower().replace(' ', '_')
									parameter_dict[key_norm] = v
								else:
									# fallback: store under normalized combined key
									parameter_dict[k.lower().replace(' ', '_')] = v
						else:
							# try to match plain override key to existing normalized keys
							norm = k.lower().replace(' ', '_')
							if norm in parameter_dict:
								parameter_dict[norm] = v
							else:
								# fallback: store override as-is (normalized)
								parameter_dict[norm] = v

					# Ensure participant id is included (same key as MenuBase.start_protocol)
					parameter_dict['participant_id'] = participant_id

					battery_configs[pname] = parameter_dict
				else:
					# survey: do not build/present a configuration to the survey task
					battery_configs.pop(pname, None)

			self.app.battery_configs = battery_configs
			popup.dismiss()

			# Start running battery tasks
			if self.app.battery_active:
				self.app.start_battery_tasks()

		def on_cancel(instance):
			popup.dismiss()

		confirm_button = Button(text='Confirm', size_hint=(0.4, 0.15), pos_hint={'x':0.05,'y':0.05})
		confirm_button.bind(on_press=on_confirm)
		content.add_widget(confirm_button)
		cancel_button = Button(text='Cancel', size_hint=(0.4, 0.15), pos_hint={'x':0.55,'y':0.05})
		cancel_button.bind(on_press=on_cancel)
		content.add_widget(cancel_button)

		popup = Popup(title='Participant ID', content=content, size_hint=(0.6, 0.4))
		popup.open()
	
	def load_protocol_battery(self, *args):
		"""Load the manual ProtocolBattery screen"""
		self.manager.current = 'protocolbattery'
	
	def cancel_battery(self, *args):
		"""Cancel and return to main menu"""
		self.manager.current = 'mainmenu'

class ProtocolBattery(Screen):

	def __init__(self, **kwargs):
		super(ProtocolBattery, self).__init__(**kwargs)

		self.app = App.get_running_app()

		self.protocol_battery_layout = FloatLayout()
		self.protocol_configure_screen = MenuBase()
		self.name = 'protocolbattery'
		self.app.active_screen = self.name
		
		self.language = self.app.language

		self.menu_config = configparser.ConfigParser()
		self.menu_config.read(pathlib.Path('Language', self.language, 'batterymenu.ini'))

		self.protocol_list = search_protocols()
		self.available_protocols = self.protocol_list.copy()
		self.selected_protocols = []

		if len(self.protocol_list) == 0:
			no_label = Label(text=self.menu_config['Text']['no_label'], size_hint=(0.8, 0.1), pos_hint={'x':0.1,'y':0.45})
			self.protocol_battery_layout.add_widget(no_label)
		else:
			# Title labels
			available_title = Label(text=self.menu_config['Text']['available_title'], size_hint=(0.35, 0.05), pos_hint={'x':0.05, 'y':0.85}, font_size='20sp', bold=True)
			self.protocol_battery_layout.add_widget(available_title)

			selected_title = Label(text=self.menu_config['Text']['selected_title'], size_hint=(0.35, 0.05), pos_hint={'x':0.6, 'y':0.85}, font_size='20sp', bold=True)
			self.protocol_battery_layout.add_widget(selected_title)

			# Create bordered containers for the lists
			# Left box container with border
			available_container = FloatLayout(size_hint=(0.35, 0.6), pos_hint={'x':0.05, 'y':0.2})
			with available_container.canvas.before:
				Color(0.5, 0.5, 0.5, 1)  # Gray border
				self.available_border = Line(rectangle=(0, 0, 1, 1), width=2)
			available_container.bind(pos=self.update_available_border, size=self.update_available_border)
			
			# ScrollView for available protocols
			available_scroll = ScrollView(size_hint=(1, 1), pos_hint={'x':0, 'y':0})
			self.available_grid = GridLayout(cols=1, spacing=5, padding=[5,5,5,5], size_hint_y=None)
			self.available_grid.bind(minimum_height=self.available_grid.setter('height'))
			available_scroll.add_widget(self.available_grid)
			available_container.add_widget(available_scroll)
			self.protocol_battery_layout.add_widget(available_container)
			
			# Right box container with border
			selected_container = FloatLayout(size_hint=(0.35, 0.6), pos_hint={'x':0.6, 'y':0.2})
			with selected_container.canvas.before:
				Color(0.5, 0.5, 0.5, 1)  # Gray border
				self.selected_border = Line(rectangle=(0, 0, 1, 1), width=2)
			selected_container.bind(pos=self.update_selected_border, size=self.update_selected_border)
			
			# ScrollView for selected protocols
			selected_scroll = ScrollView(size_hint=(1, 1), pos_hint={'x':0, 'y':0})
			self.selected_grid = GridLayout(cols=1, spacing=5, padding=[5,5,5,5], size_hint_y=None)
			self.selected_grid.bind(minimum_height=self.selected_grid.setter('height'))
			selected_scroll.add_widget(self.selected_grid)
			selected_container.add_widget(selected_scroll)
			self.protocol_battery_layout.add_widget(selected_container)

			# Control buttons in the middle
			move_right_button = Button(text=self.menu_config['Text']['move_right_button'], size_hint=(0.15, 0.08), pos_hint={'x':0.425, 'y':0.6}, font_size='18sp')
			move_right_button.bind(on_press=self.move_to_selected)
			self.protocol_battery_layout.add_widget(move_right_button)

			move_left_button = Button(text=self.menu_config['Text']['move_left_button'], size_hint=(0.15, 0.08), pos_hint={'x':0.425, 'y':0.5}, font_size='18sp')
			move_left_button.bind(on_press=self.move_to_available)
			self.protocol_battery_layout.add_widget(move_left_button)

			move_up_button = Button(text=self.menu_config['Text']['move_up_button'], size_hint=(0.15, 0.08), pos_hint={'x':0.425, 'y':0.4}, font_size='18sp')
			move_up_button.bind(on_press=self.move_up)
			self.protocol_battery_layout.add_widget(move_up_button)

			move_down_button = Button(text=self.menu_config['Text']['move_down_button'], size_hint=(0.15, 0.08), pos_hint={'x':0.425, 'y':0.3}, font_size='18sp')
			move_down_button.bind(on_press=self.move_down)
			self.protocol_battery_layout.add_widget(move_down_button)

			# Bottom buttons
			battery_start_button = Button(text=self.menu_config['Text']['battery_start_button'])
			battery_start_button.size_hint = (0.2, 0.1)
			battery_start_button.pos_hint = {'x': 0.25, 'y': 0.05}
			battery_start_button.bind(on_press=self.start_battery)
			self.protocol_battery_layout.add_widget(battery_start_button)

			cancel_button = Button(text=self.menu_config['Text']['cancel_button'])
			cancel_button.size_hint = (0.2, 0.1)
			cancel_button.pos_hint = {'x': 0.55, 'y': 0.05}
			cancel_button.bind(on_press=self.cancel_battery)
			self.protocol_battery_layout.add_widget(cancel_button)

			# Track selected items (now using sets for multi-select)
			self.selected_available_items = set()
			self.selected_selected_items = set()
		
			# Keep track of button widgets for color management
			self.available_buttons = {}
			self.selected_buttons = {}

			# Populate available protocols
			self.refresh_lists()

		self.add_widget(self.protocol_battery_layout)

	def update_available_border(self, instance, value):
		"""Update the border when the container is resized or moved"""
		self.available_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
	
	def update_selected_border(self, instance, value):
		"""Update the border when the container is resized or moved"""
		self.selected_border.rectangle = (instance.x, instance.y, instance.width, instance.height)

	def refresh_lists(self):
		"""Refresh both protocol lists"""
		self.available_grid.clear_widgets()
		self.selected_grid.clear_widgets()
		self.available_buttons.clear()
		self.selected_buttons.clear()
		
		# Populate available protocols list
		for protocol in self.available_protocols:
			btn = Button(text=protocol, size_hint_y=None, height=50, font_size='18sp')
			btn.bind(on_press=partial(self.toggle_available_item, protocol))
			self.available_buttons[protocol] = btn
			
			# Restore highlighting if previously selected
			if protocol in self.selected_available_items:
				btn.background_color = (0.3, 0.6, 0.9, 1)  # Blue highlight
			
			self.available_grid.add_widget(btn)
		
		# Populate selected protocols list
		for protocol in self.selected_protocols:
			btn = Button(text=protocol, size_hint_y=None, height=50, font_size='18sp')
			btn.bind(on_press=partial(self.toggle_selected_item, protocol))
			self.selected_buttons[protocol] = btn
			
			# Restore highlighting if previously selected
			if protocol in self.selected_selected_items:
				btn.background_color = (0.3, 0.6, 0.9, 1)  # Blue highlight
			
			self.selected_grid.add_widget(btn)

	def toggle_available_item(self, protocol, *args):
		"""Toggle selection of an item in the available list"""
		if protocol in self.selected_available_items:
			self.selected_available_items.remove(protocol)
			if protocol in self.available_buttons:
				self.available_buttons[protocol].background_color = (1, 1, 1, 1)  # Default color
		else:
			self.selected_available_items.add(protocol)
			if protocol in self.available_buttons:
				self.available_buttons[protocol].background_color = (0.3, 0.6, 0.9, 1)  # Blue highlight
		
		# Clear selections in the other list
		self.selected_selected_items.clear()
		for btn in self.selected_buttons.values():
			btn.background_color = (1, 1, 1, 1)

	def toggle_selected_item(self, protocol, *args):
		"""Toggle selection of an item in the selected list"""
		if protocol in self.selected_selected_items:
			self.selected_selected_items.remove(protocol)
			if protocol in self.selected_buttons:
				self.selected_buttons[protocol].background_color = (1, 1, 1, 1)  # Default color
		else:
			self.selected_selected_items.add(protocol)
			if protocol in self.selected_buttons:
				self.selected_buttons[protocol].background_color = (0.3, 0.6, 0.9, 1)  # Blue highlight
		
		# Clear selections in the other list
		self.selected_available_items.clear()
		for btn in self.available_buttons.values():
			btn.background_color = (1, 1, 1, 1)

	def move_to_selected(self, *args):
		"""Move selected protocols from available to selected list"""
		if self.selected_available_items:
			# Convert to list and sort to maintain consistent order
			items_to_move = sorted(list(self.selected_available_items))
			for protocol in items_to_move:
				if protocol in self.available_protocols:
					self.available_protocols.remove(protocol)
					self.selected_protocols.append(protocol)
			
			self.selected_available_items.clear()
			self.refresh_lists()

	def move_to_available(self, *args):
		"""Move selected protocols from selected to available list"""
		if self.selected_selected_items:
			# Convert to list to process
			items_to_move = list(self.selected_selected_items)
			for protocol in items_to_move:
				if protocol in self.selected_protocols:
					self.selected_protocols.remove(protocol)
					self.available_protocols.append(protocol)
			
			self.selected_selected_items.clear()
			self.refresh_lists()

	def move_up(self, *args):
		"""Move selected protocols up in the selected list"""
		if not self.selected_selected_items:
			return
		
		# Get indices of selected items, sorted
		indices = sorted([self.selected_protocols.index(p) for p in self.selected_selected_items if p in self.selected_protocols])
		
		# Move each selected item up, starting from the top
		for idx in indices:
			if idx > 0 and self.selected_protocols[idx-1] not in self.selected_selected_items:
				# Swap with the item above
				self.selected_protocols[idx], self.selected_protocols[idx-1] = \
					self.selected_protocols[idx-1], self.selected_protocols[idx]
		
		self.refresh_lists()

	def move_down(self, *args):
		"""Move selected protocols down in the selected list"""
		if not self.selected_selected_items:
			return
		
		# Get indices of selected items, sorted in reverse
		indices = sorted([self.selected_protocols.index(p) for p in self.selected_selected_items if p in self.selected_protocols], reverse=True)
		
		# Move each selected item down, starting from the bottom
		for idx in indices:
			if idx < len(self.selected_protocols) - 1 and self.selected_protocols[idx+1] not in self.selected_selected_items:
				# Swap with the item below
				self.selected_protocols[idx], self.selected_protocols[idx+1] = \
					self.selected_protocols[idx+1], self.selected_protocols[idx]
		
		self.refresh_lists()

	def cancel_battery(self, *args):
		self.manager.current = 'mainmenu'

	def start_battery(self, *args):
		"""Start battery with protocols in the order they appear in selected list"""
		# Use the selected_protocols list which maintains order
		self.app.battery_protocols = self.selected_protocols.copy()
		self.app.battery_active = len(self.selected_protocols) > 0

		if self.app.battery_active:
			# Start the configuration process for the first protocol
			self.app.start_next_battery_config()
		else:
			# No protocols selected, return to main menu
			self.manager.current = 'mainmenu'

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
		self.active_screen = ''
		self.config = configparser.ConfigParser()
		self.config.read('Config.ini')
		self.language = self.config.get('language', 'language', fallback='English')
		self.language_menu = LanguageMenu()
		self.s_manager.add_widget(self.language_menu)
		self.active_screen = self.language_menu.name
		
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
		# Start the task at the current battery_index (do not reset here)
		if not self.battery_protocols:
			self.s_manager.current = 'mainmenu'
			self.battery_active = False
			return

		if self.battery_index < len(self.battery_protocols):
			protocol_name = self.battery_protocols[self.battery_index]
			parameter_dict = self.battery_configs[protocol_name] if protocol_name in self.battery_configs else {}
			if pathlib.Path('Protocol', protocol_name, 'Task', 'Menu.py').is_file():
				task_module = protocol_constructor(protocol_name, 'Protocol')
				protocol_task_screen = task_module.ProtocolScreen(screen_resolution=Window.size)
			else:
				task_module = protocol_constructor(protocol_name, 'Protocol')
				protocol_task_screen = task_module.SurveyProtocol()
			# Provide parameters to the task only for 'task' types (not surveys)
			try:
				task_type = self.battery_task_types.get(protocol_name, 'task') if hasattr(self, 'battery_task_types') else 'task'
				if task_type == 'task' and hasattr(protocol_task_screen, 'load_parameters'):
					protocol_task_screen.load_parameters(parameter_dict)
			except Exception:
				# Some protocols may expect different parameter shapes; still continue
				pass
			self.s_manager.add_widget(protocol_task_screen)
			self.s_manager.current = protocol_task_screen.name
		else:
			# No more tasks in battery
			self.battery_active = False
			self.s_manager.current = 'mainmenu'

	def battery_task_finished(self):
		"""Called by a protocol when it returns to the main menu during a battery run.
		This advances the battery index and starts the next task if available.
		"""
		# Only advance if a battery run is active
		if not getattr(self, 'battery_active', False):
			return

		self.battery_index = int(self.battery_index) + 1
		if self.battery_index < len(self.battery_protocols):
			# Start the next battery task
			self.start_battery_tasks()
		else:
			# Finished all battery tasks
			self.battery_active = False
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

