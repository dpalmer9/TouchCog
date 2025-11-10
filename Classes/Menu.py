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
from kivy.uix.screenmanager import Screen, ScreenManagerException
from kivy.uix.scrollview import ScrollView
from kivy.effects.scroll import ScrollEffect
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line


class ImageSetItem(ButtonBehavior, BoxLayout):
	"""A single selectable dropdown row: label on the left, thumbnails on the right.

	This widget is intended to be added to a DropDown. When released it will call
	`dropdown.select(value)` so the parent dropdown receives the selection.
	"""
	def __init__(self, label_text, image_paths, dropdown, value=None, thumb_size=dp(48), **kwargs):
		super(ImageSetItem, self).__init__(orientation='horizontal', spacing=8, padding=(8,6), **kwargs)
		self.dropdown = dropdown
		self.value = value if value is not None else label_text

		# Left: label
		self.label = Label(text=label_text, valign='middle', halign='left', size_hint_x=0.6, color=(1,1,1,1))
		self.label.bind(size=lambda instance, val: setattr(instance, 'text_size', (instance.width, instance.height)))
		self.add_widget(self.label)

		# Right: small thumbnails (can be one or several)
		thumb_container = BoxLayout(orientation='horizontal', spacing=4, size_hint_x=0.4)
		for p in image_paths:
			try:
				src = str(p)
				img = Image(source=src, size_hint=(None, None), size=(thumb_size, thumb_size), allow_stretch=True, keep_ratio=True)
				thumb_container.add_widget(img)
			except Exception:
				# If image fails to load, add an empty label placeholder (white text on black bg)
				thumb_container.add_widget(Label(text='?', size_hint=(None, None), size=(thumb_size, thumb_size), color=(1,1,1,1)))

		self.add_widget(thumb_container)

	def on_release(self):
		# When the row is clicked, notify the dropdown
		try:
			self.dropdown.select(self.value)
		except Exception:
			pass


class StyledDropDown(DropDown):
	"""A DropDown with a visible border/background and which ensures it is
	on top of other widgets when opened.

	This draws a background rectangle and border in canvas.before and when
	opened re-adds itself to the parent window to move to the front.
	"""
	def __init__(self, bg_color=(0,0,0,1), border_color=(1,1,1,1), border_width=1, **kwargs):
		super(StyledDropDown, self).__init__(**kwargs)
		self.bg_color = bg_color
		self.border_color = border_color
		self.border_width = border_width

		with self.canvas.before:
			self._bg_color_instr = Color(rgba=self.bg_color)
			self._bg_rect = Rectangle(pos=self.pos, size=self.size)
			self._border_color_instr = Color(rgba=self.border_color)
			self._border_line = Line(rectangle=(self.x, self.y, self.width, self.height), width=self.border_width)

		# Update shapes when size/pos change
		self.bind(pos=self._update_graphics, size=self._update_graphics)

	def _update_graphics(self, *args):
		try:
			self._bg_rect.pos = self.pos
			self._bg_rect.size = self.size
			self._border_line.rectangle = (self.x, self.y, self.width, self.height)
		except Exception:
			pass

	def open(self, widget):
		# Use parent open behavior
		super(StyledDropDown, self).open(widget)
		# Ensure we're on top by re-adding to the window if possible
		try:
			win = self.get_parent_window() or Window
			# remove/add to move to top if it's already been added
			if self in win.children:
				win.remove_widget(self)
			win.add_widget(self)
		except Exception:
			# Fallback: do nothing if window manipulation fails
			pass


class ImageSetDropdown(BoxLayout):
	"""A labeled dropdown selector where each option shows a label and small images.

	Usage:
	options = [
		{'label': 'Image Set 1', 'images': ['Protocol/CPT/Image/set1_a.png', 'Protocol/CPT/Image/set1_b.png'], 'value': 'set1'},
		...
	]
	widget = ImageSetDropdown(options)
	"""
	def __init__(self, options, left_label='Image Set', default_text='Select...', thumb_size=dp(48), **kwargs):
		super(ImageSetDropdown, self).__init__(orientation='horizontal', spacing=8, size_hint_y=None, height=thumb_size + dp(16), **kwargs)
		self.options = options
		self.selected_value = None
		self.thumb_size = thumb_size

		# Static label on the left (descriptive)
		self.left_label = Label(text=left_label, size_hint_x=None, width=dp(160), valign='middle', halign='left')
		self.left_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
		self.add_widget(self.left_label)

		# Main button that opens the dropdown
		self.button = Button(text=default_text)
		self.add_widget(self.button)

		# The dropdown that will hold ImageSetItem rows (styled with border/background)
		# Use black background + white border for dropdown
		self.dropdown = StyledDropDown(bg_color=(0,0,0,1), border_color=(1,1,1,1), border_width=1)

		# Populate dropdown
		for opt in self.options:
			label = opt.get('label', '')
			images = opt.get('images', [])
			value = opt.get('value', label)
			item = ImageSetItem(label_text=label, image_paths=images, dropdown=self.dropdown, value=value, thumb_size=self.thumb_size, size_hint_y=None, height=self.thumb_size + dp(12))
			self.dropdown.add_widget(item)

		# Hook selection
		self.dropdown.bind(on_select=self._on_select)
		self.button.bind(on_release=lambda btn: self.dropdown.open(btn))

	def _on_select(self, instance, value):
		# update button text and store selected value
		self.selected_value = value
		# try to find the label text for nicer display
		for opt in self.options:
			if opt.get('value', opt.get('label')) == value:
				self.button.text = opt.get('label', str(value))
				break

	def get_selected(self):
		return self.selected_value

	def set_selected_by_value(self, value):
		# programmatically set selection (will update button text if found)
		for opt in self.options:
			if opt.get('value', opt.get('label')) == value:
				self.selected_value = value
				self.button.text = opt.get('label', str(value))
				return True
		return False


class MenuBase(Screen):
	


	def __init__(self, **kwargs):


		super(MenuBase, self).__init__(**kwargs)
		
		self.name = 'menuscreen'
		self.main_layout = FloatLayout()

		self.app = App.get_running_app()

		self.language = self.app.language

		self.menu_config = configparser.ConfigParser()
		self.menu_config.read(pathlib.Path('Language', self.language, 'menubase.ini'))

		self.is_battery_mode = False
		self.battery_required_fields = None  # None means no filtering; list means only show these fields
		
		self.protocol_name = ''
		self.protocol_path = ''
		self.protocol_title_label = Label(text=self.protocol_name, font_size=32)
		self.protocol_title_label.size_hint = (0.6, 0.1)
		self.protocol_title_label.pos_hint = {'x': 0.2, 'y': 0.9}
		self.main_layout.add_widget(self.protocol_title_label)
		self.parameters_config = dict()
		self.setting_scrollview = ScrollView(effect_cls=ScrollEffect)
		self.setting_gridlayout = GridLayout()
		self.setting_gridlayout.size_hint_y = None
		self.setting_gridlayout.size_hint_x = 1
		self.setting_gridlayout.bind(minimum_height=self.setting_gridlayout.setter('height'))
		self.setting_scrollview.add_widget(self.setting_gridlayout)

		self.id_grid = GridLayout(cols=2, rows=1)
		self.id_label = Label(text=self.menu_config['Text']['id_label'])
		self.id_entry = TextInput(text=self.menu_config['Text']['id_entry'])
		self.id_grid.add_widget(self.id_label)
		self.id_grid.add_widget(self.id_entry)
		self.id_grid.size_hint = (0.85, 0.05)
		self.id_grid.pos_hint = {'x': 0.1, 'y': 0.3}

		self.back_button = Button(text=self.menu_config['Text']['back_button'])
		self.back_button.size_hint = (0.1, 0.1)
		self.back_button.pos_hint = {'x': 0.4, 'y': 0.1}
		self.back_button.bind(on_press=self.return_menu)

		if self.is_battery_mode:
			button_string = self.menu_config['Text']['start_button_battery']
		else:
			button_string = self.menu_config['Text']['start_button_regular']
		self.start_button = Button(text=button_string)
		self.start_button.size_hint = (0.1, 0.1)
		self.start_button.pos_hint = {'x': 0.6, 'y': 0.1}
		self.start_button.bind(on_press=self.start_protocol)

		# Add scrollview and other widgets to main_layout only once
		self.setting_scrollview.pos_hint = {'x': 0.1, 'y': 0.4}
		self.setting_scrollview.size_hint = (0.85, 0.5)
		self.main_layout.add_widget(self.setting_scrollview)
		self.main_layout.add_widget(self.id_grid)
		self.main_layout.add_widget(self.back_button)
		self.main_layout.add_widget(self.start_button)
		self.add_widget(self.main_layout)
	
	
	def update_battery_mode(self, is_battery, required_fields=None):
		"""
		Update battery mode and optionally set required fields for filtering.
		
		Args:
			is_battery: Boolean indicating battery mode
			required_fields: None (show all fields) or list of field names to display
		"""
		if is_battery:
			self.is_battery_mode = True
			self.battery_required_fields = required_fields  # None or list of field names
			self.start_button.text = self.menu_config['Text']['start_button_battery']
			# Hide participant ID if required fields exist
			if required_fields is not None and len(required_fields) > 0:
				self.id_grid.height = 0
				self.id_grid.size_hint_y = 0
				self.apply_required_fields_filter()
			else:
				self.id_grid.height = None
				self.id_grid.size_hint_y = 0.05
		else:
			self.is_battery_mode = False
			self.battery_required_fields = None
			self.start_button.text = self.menu_config['Text']['start_button_regular']
			# Show participant ID
			self.id_grid.height = None
			self.id_grid.size_hint_y = 0.05

	def _normalize_field_name(self, field_name):
		"""
		Normalize a field name for comparison with configuration keys.
		Converts to lowercase and replaces spaces with underscores.
		"""
		return field_name.lower().replace(' ', '_')

	def _should_display_field(self, field_name):
		"""
		Determine if a field should be displayed given required_fields filtering.
		Returns True if field should be shown, False otherwise.
		"""
		# If no filtering, show all fields
		if self.battery_required_fields is None:
			return True
		
		# If filtering, only show if field is in required_fields
		normalized_field = self._normalize_field_name(field_name)
		normalized_required = [self._normalize_field_name(f) for f in self.battery_required_fields]
		
		return normalized_field in normalized_required

	def apply_required_fields_filter(self):
		"""
		Hide/remove widgets from the grid layout based on required_fields filtering.
		This is called AFTER menu_constructor to filter already-created widgets.
		Walks from the end to the start to safely remove widgets without index shifting.
		"""
		# If no filtering needed, leave all widgets visible
		if self.battery_required_fields is None or len(self.battery_required_fields) == 0:
			return
		
		# Walk through grid layout from end to start (newest child is first in list)
		# This avoids index shifting issues when removing widgets
		i = len(self.setting_gridlayout.children) - 1
		while i >= 0:
			widget = self.setting_gridlayout.children[i]
			
			# Labels are those that aren't Buttons (pairs: label, value)
			if isinstance(widget, Label) and not isinstance(widget, Button):
				field_name = widget.text
				# Check if this field should be displayed
				if not self._should_display_field(field_name):
					# Remove the value widget first (next in pair, since we're walking backwards)
					if i - 1 < len(self.setting_gridlayout.children):
						self.setting_gridlayout.remove_widget(self.setting_gridlayout.children[i - 1])
					# Then remove the label
					self.setting_gridlayout.remove_widget(widget)
			
			i -= 2
		
		# Update grid row count
		self.setting_gridlayout.rows = len(self.setting_gridlayout.children) // 2

	def start_protocol(self, *args):
		
		
		def lazy_import(protocol):
			working = pathlib.Path('Protocol', protocol, 'Task', 'Protocol.py')
			mod_name = 'Protocol'
			mod_spec = importlib.util.spec_from_file_location(mod_name, working)
			mod_loader = importlib.util.LazyLoader(mod_spec.loader)
			mod_spec.loader = mod_loader
			module = importlib.util.module_from_spec(mod_spec)
			sys.modules[mod_name] = module
			mod_loader.exec_module(module)
			
			return module
		
		key = ''
		value = ''
		parameter_dict = {}
		
		for widget in self.setting_gridlayout.walk():
			
			
			if isinstance(widget, Label) and not isinstance(widget, Button):
				
				
				key = widget.text
				key = key.lower()
				key = key.replace(' ', '_')
			
			
			elif isinstance(widget, TextInput):
				value = widget.text
				parameter_dict[key] = value
			
			
			elif isinstance(widget, Button):
				# Ignore buttons that belong to an ImageSetDropdown; the
				# ImageSetDropdown itself is handled separately (it provides
				# the selected value via get_selected()). This prevents the
				# internal dropdown button from overwriting the parameter.
				parent = getattr(widget, 'parent', None)
				if isinstance(parent, ImageSetDropdown):
					# skip the internal button
					continue
				value = widget.text
				parameter_dict[key] = value
			
			elif isinstance(widget, ImageSetDropdown):
				value = widget.get_selected()
				parameter_dict[key] = value

			elif isinstance(widget, CheckBox):
				value = widget.active
				parameter_dict[key] = value
		
		
		# Only add participant_id if not using required_fields filtering in battery mode
		# (when using required fields, participant_id should have been collected upfront and stored elsewhere)
		if not (self.is_battery_mode and self.battery_required_fields is not None and len(self.battery_required_fields) > 0):
			parameter_dict['participant_id'] = self.id_entry.text
		else:
			# In required-fields battery mode, use the app-level participant_id
			if hasattr(self.app, 'participant_id') and self.app.participant_id:
				parameter_dict['participant_id'] = self.app.participant_id

		
		# Start or protocol or continue battery
		if not self.is_battery_mode:
			task_module = lazy_import(self.protocol)
			protocol_task_screen = task_module.ProtocolScreen(screen_resolution=self.size)
		
			try:
			
			
				self.manager.remove_widget(self.manager.get_screen(protocol_task_screen.name))
				self.manager.add_widget(protocol_task_screen)
		
		
			except ScreenManagerException:
			
			
				self.manager.add_widget(protocol_task_screen)
		
			protocol_task_screen.load_parameters(parameter_dict)
		
			self.app.active_screen = protocol_task_screen.name
			self.manager.current = protocol_task_screen.name
		
		else:
			protocol_name = self.app.battery_protocols[self.app.battery_index]
			
			# If in battery mode with required fields filtering, update only the required field values
			# in the pre-loaded config (merge the filled-in values into the existing config)
			if self.battery_required_fields is not None and len(self.battery_required_fields) > 0:
				# Merge new values into existing config for this protocol
				if protocol_name in self.app.battery_configs:
					self.app.battery_configs[protocol_name].update(parameter_dict)
				else:
					self.app.battery_configs[protocol_name] = parameter_dict
			else:
				# No required fields: replace entire config (normal battery mode)
				self.app.battery_configs[protocol_name] = parameter_dict
			
			self.app.battery_index += 1
			self.app.start_next_battery_config()


	
	
	
	def return_menu(self, *args):
		
		
		self.manager.current = 'protocolmenu'
	
	
	
	def menu_constructor(self, protocol_name):
		# Preserve scroll position
		prev_scroll_y = self.setting_scrollview.scroll_y if self.setting_scrollview.children else 1.0

		self.protocol_name = protocol_name
		self.protocol_path = pathlib.Path('Protocol', self.protocol_name)
		config_path = self.protocol_path / 'Configuration.ini'

		config_file = configparser.ConfigParser()
		config_file.read(config_path)

		if ('DebugParameters' in config_file) \
			and (config_file.getboolean('DebugParameters', 'debug_mode', fallback=False)):
			self.parameters_config = config_file['DebugParameters']
			self.debug_mode = True
		else:
			self.parameters_config = config_file['TaskParameters']
			self.debug_mode = False

		num_parameters = len(self.parameters_config)

		self.setting_gridlayout.clear_widgets()
		self.setting_gridlayout.rows = (num_parameters)
		self.setting_gridlayout.cols = 2

		# Build ALL widgets (we'll filter after in apply_required_fields_filter)
		for parameter in self.parameters_config:
			label = Label(text=parameter, size_hint_y=None, height=50)
			if self.parameters_config[parameter].lower() in ['true', 'false']:
				checkbox = CheckBox(active=self.parameters_config[parameter].lower() == 'true', size_hint_x=None, width=50)
				self.setting_gridlayout.add_widget(label)
				self.setting_gridlayout.add_widget(checkbox)
			else:
				text_input = TextInput(text=self.parameters_config[parameter], size_hint_y=None, height=50)
				self.setting_gridlayout.add_widget(label)
				self.setting_gridlayout.add_widget(text_input)

	# Height is now automatically bound to minimum_height

		# Restore scroll position
		self.setting_scrollview.scroll_y = prev_scroll_y
		
		# Apply required fields filtering AFTER widgets are created
		self.apply_required_fields_filter()

