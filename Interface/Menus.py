# Part of the TouchCog Kivy launcher interface (split out of KivyMenuInterface.py).

# Interface.Startup must be imported first: it configures Kivy before kivy.core.window loads.
import Interface.Startup

import os
import pathlib
import re
import json
import threading
import urllib.request
import zipfile
import configparser
from datetime import datetime
from functools import partial
from Classes.Menu import MenuBase
from Classes.Menu import load_protocol_module
from Classes.Survey import SurveyBase
from kivy.app import App
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.dropdown import DropDown
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from Interface.Startup import app_root
from Interface.Startup import config_file
from Interface.Startup import user_config_path
from Interface.Startup import search_protocols
from Interface.Battery import BatteryMenu

# Class Task Selection #

class LanguageMenu(Screen):
	
	def __init__(self, **kwargs):
		
		super(LanguageMenu, self).__init__(**kwargs)
		self.name = 'languagemenu'
		self.app = App.get_running_app()
		self.app.active_screen = self.name
		self.config = config_file
		self.Language_Layout = FloatLayout()
		self.add_widget(self.Language_Layout)

		self.manifest_path = 'https://touchscreencognition.org/uploads/manifest.json'

		self.language_list = list()
		self._manifest = None

		# Build the dropdown from the local Language/ directory now; the remote
		# manifest is fetched off the main thread and may add more languages later.
		with os.scandir(app_root / 'Language') as entries:
			for entry in entries:
				if entry.is_dir():
					self.language_list.append(entry.name)
		self.language_dropdown = DropDown()
		self.language_drop_button = Button(text='Select Language')
		# Position dropdown near top middle
		self.language_drop_button.size_hint = (0.4, 0.08)
		self.language_drop_button.pos_hint = {'x': 0.3, 'y': 0.5}
		for language in self.language_list:
			self._add_language_button(language)

		self.language_dropdown.bind(on_select=lambda instance, x: setattr(self.language_drop_button, 'text', x))
		self.language_drop_button.bind(on_release=self.language_dropdown.open)
		self.Language_Layout.add_widget(self.language_drop_button)

		self.start_button = Button(text='Start')
		# Position start button near bottom center
		self.start_button.size_hint = (0.3, 0.12)
		self.start_button.pos_hint = {'x': 0.35, 'y': 0.08}
		self.start_button.bind(on_press=self.start_touchcog)
		# Enabled once the manifest fetch has finished (success or failure)
		self.start_button.disabled = True

		self.Language_Layout.add_widget(self.start_button)

		threading.Thread(target=self._load_manifest_async, daemon=True).start()

	def _add_language_button(self, language):
		btn = Button(text=language, size_hint_y=None, height=44)
		btn.bind(on_release=lambda btn: self.language_dropdown.select(btn.text))
		self.language_dropdown.add_widget(btn)

	def _load_manifest_async(self):
		manifest = self._fetch_manifest()
		Clock.schedule_once(lambda dt: self._apply_manifest(manifest))

	def _apply_manifest(self, manifest):
		self._manifest = manifest
		# Manifest format: a list of dicts under 'languages', each mapping a language name to its entries
		if isinstance(manifest, dict):
			for lang_block in manifest.get('languages', []):
				if isinstance(lang_block, dict):
					for lang_name in lang_block.keys():
						if lang_name not in self.language_list:
							self.language_list.append(lang_name)
							self._add_language_button(lang_name)
		self.start_button.disabled = False

	def start_touchcog(self, *args):
		self.app.language = self.language_drop_button.text
		# If no language selected, just go to main menu
		if self.app.language == 'Select Language' or not self.app.language:
			self.app.language = self.config['language']['language']
			self.main_menu = MainMenu()
			self.app.replace_screen(self.main_menu)
			self.manager.current = 'mainmenu'
			return

		manifest = self._manifest
		if manifest is None:
			# Couldn't load manifest; proceed to main menu
			self.app.language = self.config['language']['language']
			self.main_menu = MainMenu()
			self.app.replace_screen(self.main_menu)
			self.manager.current = 'mainmenu'
			return

		# Write the user-local Config.ini in the user's home directory
		self.config['language']['language'] = self.app.language
		try:
			with open(str(user_config_path), 'w', encoding='utf-8') as f:
				self.config.write(f)
		except Exception as e:
			Logger.warning(f'TouchCog: could not write Config.ini: {e}')

		# Ensure bin folder exists
		self._ensure_destination(None)

		# Collect all potential downloads
		download_candidates = []

		# 1. Language file
		try:
			for lang_block in manifest.get('languages', []):
				if self.app.language in lang_block:
					# lang_block[self.app.language] is a list with one dict
					entry = lang_block[self.app.language][0]
					download_candidates.append(entry)
					break
		except Exception:
			Logger.exception('TouchCog: could not read language entry from manifest')

		# 2. Videos
		for entry in manifest.get('Videos', []):
			download_candidates.append(entry)

		# 3. Battery
		for entry in manifest.get('Battery', []):
			download_candidates.append(entry)

		# Filter for what actually needs downloading
		items_to_download = []
		bin_path = app_root / 'bin'
		
		for entry in download_candidates:
			filename = entry.get('filename')
			if not filename:
				continue
			
			local_file = bin_path / filename
			needs_download = False
			
			if not local_file.exists():
				needs_download = True
			else:
				# Check date
				manifest_date_str = entry.get('date')
				if manifest_date_str:
					try:
						manifest_date = datetime.strptime(manifest_date_str, '%Y-%m-%d')
						local_mtime = datetime.fromtimestamp(local_file.stat().st_mtime)
						# Compare dates (ignoring time for manifest date)
						# If local file is older than manifest date, update
						if local_mtime < manifest_date:
							needs_download = True
					except Exception as e:
						Logger.warning(f'TouchCog: date comparison failed for {filename}: {e}')
			
			if needs_download:
				items_to_download.append(entry)

		if not items_to_download:
			# Nothing to download
			self.main_menu = MainMenu()
			self.app.replace_screen(self.main_menu)
			self.manager.current = 'mainmenu'
			return

		# Prepare UI: popup with progress bar and filename label
		self._download_popup_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
		self._download_label = Label(text='Preparing downloads...')
		self._download_bar = ProgressBar(max=100, value=0)
		self._download_popup_content.add_widget(self._download_label)
		self._download_popup_content.add_widget(self._download_bar)
		self._download_popup = Popup(title='Downloading updates', content=self._download_popup_content, size_hint=(0.6, 0.3))
		self._download_popup.open()

		# Run downloads in background thread
		thread = threading.Thread(target=self._download_files_thread, args=(items_to_download,))
		thread.daemon = True
		thread.start()

		# When downloads complete, the thread will switch to main menu


	def _fetch_manifest(self):
		# Try to fetch JSON from manifest_path; fallback to local manifest.json
		try:
			with urllib.request.urlopen(self.manifest_path, timeout=10) as resp:
				data = resp.read().decode('utf-8')
				# First try strict JSON parsing, then try to sanitize common errors
				try:
					return json.loads(data)
				except json.JSONDecodeError:
					Logger.warning('TouchCog: remote manifest JSON failed strict parsing; attempting sanitize')
					sanitized = self._sanitize_json_text(data)
					try:
						return json.loads(sanitized)
					except Exception as e:
						Logger.warning(f'TouchCog: sanitized remote manifest JSON still failed parsing: {e}')
						raise
		except Exception:
			# Fallback to local file in project root
			local_path = app_root / 'manifest.json'
			try:
				with open(local_path, 'r', encoding='utf-8') as f:
					local_text = f.read()
					try:
						return json.loads(local_text)
					except json.JSONDecodeError:
						Logger.warning('TouchCog: local manifest JSON failed strict parsing; attempting sanitize')
						sanitized = self._sanitize_json_text(local_text)
						try:
							return json.loads(sanitized)
						except Exception as e:
							Logger.warning(f'TouchCog: sanitized local manifest JSON still failed parsing: {e}')
							return None
			except Exception:
				return None


	def _sanitize_json_text(self, text):
		"""Return a least-effort sanitized JSON string.

		This attempts to fix common formatting mistakes in manually-edited
		JSON files such as trailing commas before closing array/object tokens
		(e.g. [1,2,] or {"a": 1,}). This is carefully scoped: it does not try
		to implement a full tolerant parser, but it helps with the manifest's
		most-common issue (trailing commas).
		"""
		if not isinstance(text, str):
			return text

		# Remove byte order mark if present
		if text.startswith('\ufeff'):
			text = text.lstrip('\ufeff')

		# Remove trailing commas before a closing bracket or curly brace
		# e.g. { "a": 1, } -> { "a": 1 }
		sanitized = re.sub(r',\s*(?=[}\]])', '', text)
		return sanitized


	def _ensure_destination(self, destination_path):
		# Ensure bin folder exists
		bin_path = app_root / 'bin'
		if not bin_path.exists():
			bin_path.mkdir(parents=True, exist_ok=True)
		return bin_path


	def _download_files_thread(self, file_list):
		total = len(file_list)
		completed = 0
		bin_path = app_root / 'bin'

		for entry in file_list:
			name = entry.get('filename')
			server_path = entry.get('server_path', '')
			
			# Update label to current file
			Clock.schedule_once(lambda dt, n=name: setattr(self._download_label, 'text', f'Downloading: {n}'))

			local_file = bin_path / name

			# Attempt download with progress
			try:
				if server_path:
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
					
					# Extract
					Clock.schedule_once(lambda dt, n=name: setattr(self._download_label, 'text', f'Extracting: {n}'))
					try:
						with zipfile.ZipFile(local_file, 'r') as zip_ref:
							root = pathlib.Path(app_root).resolve()
							if all((root / m).resolve().is_relative_to(root) for m in zip_ref.namelist()):
								zip_ref.extractall(app_root)
							else:
								Logger.warning(f'TouchCog: skipping {name}: archive contains paths outside the app directory')
					except Exception:
						Logger.exception(f'TouchCog: failed to extract {name}')

			except Exception:
				Logger.exception(f'TouchCog: failed to download {name}')
				# On failure, ensure file doesn't exist
				try:
					if local_file.exists():
						local_file.unlink()
				except Exception:
					# partial file cleanup
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
		self.app.replace_screen(self.main_menu)
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
		self.menu_config.read(app_root / 'Language' / self.language / 'mainmenu.ini')
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
			self.app.replace_screen(self.protocol_window)
			self.manager.current = 'protocolmenu'
	
	def load_battery_menu(self, *args):
		
		if isinstance(self.protocol_window, BatteryMenu):
			self.manager.current = 'batterymenu'
		
		else:
			self.protocol_window = BatteryMenu()
			self.app.replace_screen(self.protocol_window)
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
		self.menu_config.read(app_root / 'Language' / self.language / 'protocolmenu.ini')
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

		if (app_root / 'Protocol' / label / 'Task' / 'Menu.py').is_file():
			task_module = load_protocol_module(app_root, label, 'Menu')
			self.Protocol_Configure_Screen = task_module.ConfigureScreen()
		else:
			task_module = load_protocol_module(app_root, label, 'Protocol')
			self.Protocol_Configure_Screen = task_module.SurveyProtocol()

		self.Protocol_Configure_Screen.size = Window.size
		self.app.replace_screen(self.Protocol_Configure_Screen)
		if isinstance(self.Protocol_Configure_Screen, SurveyBase):
			self.app.present_task_screen(self.Protocol_Configure_Screen.name)
		else:
			self.app.active_screen = self.Protocol_Configure_Screen.name
			self.manager.current = self.Protocol_Configure_Screen.name

	
	
	
	def cancel_protocol(self, *args):
		
		self.manager.current = 'mainmenu'
