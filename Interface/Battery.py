# Part of the TouchCog Kivy launcher interface (split out of KivyMenuInterface.py).

# Interface.Startup must be imported first: it configures Kivy before kivy.core.window loads.
import Interface.Startup

import json
import configparser
from functools import partial
from Classes.Menu import normalize_field_name
from kivy.app import App
from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.uix.popup import Popup
from Interface.Startup import app_root
from Interface.Startup import search_protocols

class BatteryMenu(Screen):
	def __init__(self, **kwargs):
		super(BatteryMenu, self).__init__(**kwargs)
		self.name = 'batterymenu'
		self.app = App.get_running_app()
		self.app.active_screen = self.name
		self.language = self.app.language
		
		# Load language config
		self.menu_config = configparser.ConfigParser()
		self.menu_config.read(app_root / 'Language' / self.language / 'batterymenu.ini')
		
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
		battery_path = app_root / 'Battery'
		
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
					Logger.warning(f'TouchCog: error loading battery file {json_file}: {e}')
		except Exception as e:
			Logger.warning(f'TouchCog: error accessing Battery directory: {e}')
		
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
			Logger.warning('TouchCog: no battery selected')
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
				pname, ttype, required_fields, parameter_dict = self._build_battery_config(task, participant_id)
				if not pname:
					Logger.warning(f"TouchCog: skipping battery entry with missing 'task' field: {task}")
					continue
				self.app.battery_task_types[pname] = ttype
				self.app.battery_required_fields[pname] = required_fields
				if parameter_dict is None:
					# survey: do not build/present a configuration to the survey task
					battery_configs.pop(pname, None)
				else:
					battery_configs[pname] = parameter_dict

			self.app.battery_configs = battery_configs
			popup.dismiss()

			# Start configuration for first protocol (handles required fields)
			if self.app.battery_active:
				self.app.start_next_battery_config()

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
	
	def _build_battery_config(self, task, participant_id):
		"""Return (task name, type, required field names, parameter dict) for one battery entry.

		required field names is None (show all fields), [] (skip the configure screen) or a list of
		names to show; the parameter dict is None for surveys, which get no configuration.
		"""
		pname = task.get('task')
		if not pname:
			return None, None, None, None
		ttype = task.get('type', 'task')

		# 'required' is a dict like {'image_set': 'Image Set', ...}; its keys are the parameters to show.
		# An empty dict means a preloaded battery with nothing to ask for.
		required = task.get('required')
		required_fields = list(required.keys()) if isinstance(required, dict) else None
		if ttype != 'task':
			return pname, ttype, required_fields, None

		# Build a flat parameter dict (like MenuBase.start_protocol produces)
		parameter_dict = {}
		cfg = configparser.ConfigParser()
		conf_path = app_root / 'Protocol' / pname / 'Configuration.ini'
		has_conf = conf_path.is_file()
		if has_conf:
			cfg.read(conf_path, encoding='utf-8')
			# choose which section to use for UI parameters
			use_section = 'TaskParameters'
			if 'DebugParameters' in cfg and cfg.getboolean('DebugParameters', 'debug_mode', fallback=False):
				use_section = 'DebugParameters'
			if use_section in cfg:
				for opt in cfg[use_section]:
					val = cfg.get(use_section, opt)
					# coerce booleans
					parsed = cfg.getboolean(use_section, opt) if val.lower() in ('true', 'false') else val
					parameter_dict[normalize_field_name(opt)] = parsed

		# Apply overrides: support 'section.option' or plain parameter names
		for k, v in (task.get('overrides') or {}).items():
			if isinstance(v, str) and v.lower() in ('true', 'false'):
				v = v.lower() == 'true'
			if '.' in k:
				sec, opt = k.split('.', 1)
				# try to map section.option to parameter name if possible
				if has_conf:
					if sec in cfg and opt in cfg[sec]:
						parameter_dict[normalize_field_name(opt)] = v
					else:
						# fallback: store under normalized combined key
						parameter_dict[normalize_field_name(k)] = v
			else:
				parameter_dict[normalize_field_name(k)] = v

		# Only add participant_id if this task doesn't have required_fields filtering
		# (when required_fields are present, participant_id should be collected separately)
		if not required_fields:
			parameter_dict['participant_id'] = participant_id
		return pname, ttype, required_fields, parameter_dict

	def load_protocol_battery(self, *args):
		"""Load the manual ProtocolBattery screen"""
		self.protocol_battery_screen = ProtocolBattery()
		self.app.replace_screen(self.protocol_battery_screen)
		self.manager.current = 'protocolbattery'
	
	def cancel_battery(self, *args):
		"""Cancel and return to main menu"""
		self.manager.current = 'mainmenu'

class ProtocolBattery(Screen):

	def __init__(self, **kwargs):
		super(ProtocolBattery, self).__init__(**kwargs)

		self.app = App.get_running_app()

		self.protocol_battery_layout = FloatLayout()
		self.name = 'protocolbattery'
		self.app.active_screen = self.name
		
		self.language = self.app.language

		self.menu_config = configparser.ConfigParser()
		self.menu_path = app_root / 'Language' / self.language / 'batterymenu.ini'
		self.menu_config.read(self.menu_path)

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
		self.app.battery_index = 0
		self.app.battery_configs = {}
		self.app.battery_task_types = {}
		self.app.battery_required_fields = {}
		# Manual batteries have no upfront participant ID; clear any from a previous preset battery
		self.app.participant_id = None

		if self.app.battery_active:
			# For manual batteries we must detect whether each selected protocol is
			# a 'task' (has a Menu.py configure screen) or a 'survey' (no Menu.py).
			# Presence of Protocol/<name>/Task/Menu.py indicates a task.
			for protocol in self.app.battery_protocols:
				menu_path = app_root / 'Protocol' / protocol / 'Task' / 'Menu.py'
				if menu_path.is_file():
					# task: will present configure screen
					self.app.battery_task_types[protocol] = 'task'
					self.app.battery_required_fields[protocol] = None
				else:
					# survey: no configure screen and no parameter dict
					self.app.battery_task_types[protocol] = 'survey'
					self.app.battery_required_fields[protocol] = None
			
			# Start the configuration process for the first protocol
			self.app.start_next_battery_config()
		else:
			# No protocols selected, return to main menu
			self.manager.current = 'mainmenu'
