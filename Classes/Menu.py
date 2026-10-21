"""Base config-selector widgets and the shared menu screen that builds a task settings grid."""
# Import

import configparser
import importlib
import importlib.util
import sys

from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.effects.scroll import ScrollEffect
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line
from kivy.logger import Logger


class ImageSetItem(ButtonBehavior, BoxLayout):
	"""A single selectable dropdown row: label on the left, thumbnails on the right.

	This widget is intended to be added to a DropDown. When released it will call
	`dropdown.select(value)` so the parent dropdown receives the selection.

	Attributes
	----------
	dropdown : kivy.uix.dropdown.DropDown
		The parent dropdown that owns this row and receives the selection.
	value : str
		The value passed to ``dropdown.select`` on release; defaults to the label text.
	"""
	def __init__(self, label_text, image_paths, dropdown, value=None, thumb_size=dp(48), **kwargs):
		"""Build the label and thumbnail widgets for this row.

		Parameters
		----------
		label_text : str
			Text shown in the left-hand label.
		image_paths : list of str
			Paths of the thumbnail images shown on the right.
		dropdown : kivy.uix.dropdown.DropDown
			The parent dropdown that will receive the selection.
		value : str, optional
			Value passed to ``dropdown.select`` on release. Defaults to ``label_text``.
		thumb_size : float, optional
			Side length in pixels of each thumbnail. Defaults to ``dp(48)``.
		**kwargs : dict
			Additional keyword arguments passed to the BoxLayout.
		"""
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
				Logger.warning(f'TouchCog: could not load thumbnail {p}')
				# If image fails to load, add an empty label placeholder (white text on black bg)
				thumb_container.add_widget(Label(text='?', size_hint=(None, None), size=(thumb_size, thumb_size), color=(1,1,1,1)))

		self.add_widget(thumb_container)

	def on_release(self):
		"""Notify the parent dropdown of the selection when the row is released."""
		# When the row is clicked, notify the dropdown
		try:
			self.dropdown.select(self.value)
		except Exception:
			Logger.exception('TouchCog: dropdown select failed')


class StyledDropDown(DropDown):
	"""A DropDown with a visible border/background and which ensures it is
	on top of other widgets when opened.

	This draws a background rectangle and border in canvas.before and when
	opened re-adds itself to the parent window to move to the front.

	Attributes
	----------
	bg_color : tuple of 4 float
		RGBA background colour of the dropdown.
	border_color : tuple of 4 float
		RGBA colour of the border line.
	border_width : float
		Width in pixels of the border line.
	"""
	def __init__(self, bg_color=(0,0,0,1), border_color=(1,1,1,1), border_width=1, **kwargs):
		"""Initialise the dropdown and draw its background rectangle and border.

		Parameters
		----------
		bg_color : tuple of 4 float, optional
			RGBA background colour. Defaults to ``(0, 0, 0, 1)``.
		border_color : tuple of 4 float, optional
			RGBA colour of the border line. Defaults to ``(1, 1, 1, 1)``.
		border_width : float, optional
			Width in pixels of the border line. Defaults to 1.
		**kwargs : dict
			Additional keyword arguments passed to the DropDown.
		"""
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
		"""Sync the background and border shapes to the current position and size.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy property binding (pos/size change).
		"""
		try:
			self._bg_rect.pos = self.pos
			self._bg_rect.size = self.size
			self._border_line.rectangle = (self.x, self.y, self.width, self.height)
		except Exception:
			# graphics not ready yet
			pass

	def open(self, widget):
		"""Open the dropdown on the given widget and raise it to the front of the window.

		Parameters
		----------
		widget : kivy.uix.widget.Widget
			The widget the dropdown is opened relative to.
		"""
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
			Logger.warning('TouchCog: could not raise dropdown to front')


class ImageSetDropdown(BoxLayout):
	"""A labeled dropdown selector where each option shows a label and small images.

	Usage:
	options = [
		{'label': 'Image Set 1', 'images': ['Protocol/CPT/Image/set1_a.png', 'Protocol/CPT/Image/set1_b.png'], 'value': 'set1'},
		...
	]
	widget = ImageSetDropdown(options)

	Attributes
	----------
	options : list of dict
		Each dict provides ``label``, ``images`` and ``value`` keys for one option.
	selected_value : str or None
		The value most recently chosen, or None before any selection.
	left_label : kivy.uix.label.Label
		The static descriptive label on the left.
	button : kivy.uix.button.Button
		The button that opens the dropdown and shows the current selection.
	dropdown : StyledDropDown
		The dropdown holding the ImageSetItem rows.
	"""
	def __init__(self, options, left_label='Image Set', default_text='Select...', thumb_size=dp(48), **kwargs):
		"""Build the label, button and dropdown rows from the given options.

		Parameters
		----------
		options : list of dict
			Each dict provides ``label``, ``images`` and ``value`` keys for one option.
		left_label : str, optional
			Text of the static label on the left. Defaults to ``'Image Set'``.
		default_text : str, optional
			Initial text of the button before any selection. Defaults to ``'Select...'``.
		thumb_size : float, optional
			Side length in pixels of each thumbnail. Defaults to ``dp(48)``.
		**kwargs : dict
			Additional keyword arguments passed to the BoxLayout.
		"""
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
		"""Store the selected value and update the button text to its label.

		Parameters
		----------
		instance : kivy.uix.dropdown.DropDown
			The dropdown that emitted the selection.
		value : str
			The selected value; used to look up the matching option label.
		"""
		# update button text and store selected value
		self.selected_value = value
		# try to find the label text for nicer display
		for opt in self.options:
			if opt.get('value', opt.get('label')) == value:
				self.button.text = opt.get('label', str(value))
				break

	def get_selected(self):
		"""Return the currently selected value, or None if none is chosen.

		Returns
		-------
		str or None
			The selected option value, or None before any selection.
		"""
		return self.selected_value


def normalize_field_name(field_name):
	"""Normalize a field name for comparison with configuration keys.

	Parameters
	----------
	field_name : str
		The raw field name to normalize.

	Returns
	-------
	str
		The field name lowercased with every space replaced by an underscore.
	"""
	return field_name.lower().replace(' ', '_')


def load_protocol_module(app_root, protocol, mod_name):
	"""Load a protocol task module lazily under a unique top-level name.

	Parameters
	----------
	app_root : pathlib.Path
		The TouchCog application root directory.
	protocol : str
		Name of the protocol folder under ``Protocol/``.
	mod_name : str
		Name of the task module file (``.py``) to load.

	Returns
	-------
	module
		The imported module, registered in ``sys.modules`` under the unique name.
	"""
	working = app_root / 'Protocol' / protocol / 'Task' / f'{mod_name}.py'
	# Unique name so the top-level 'Protocol' package entry is not overwritten
	unique_mod_name = f'{protocol}.{mod_name}'
	mod_spec = importlib.util.spec_from_file_location(unique_mod_name, working)
	mod_loader = importlib.util.LazyLoader(mod_spec.loader)
	mod_spec.loader = mod_loader
	module = importlib.util.module_from_spec(mod_spec)
	sys.modules[unique_mod_name] = module
	mod_loader.exec_module(module)
	return module


def read_grid_parameters(grid):
	"""Read a settings grid as ``{normalized label: value}`` from its direct label/value pairs, in add order.

	Parameters
	----------
	grid : kivy.uix.gridlayout.GridLayout
		The grid whose children form label/value pairs.

	Returns
	-------
	dict
		Maps each normalized label to the value of the paired widget; a text input
		value, checkbox active state, ImageSetDropdown selection or button text.
	"""
	parameter_dict = {}
	key = ''
	for widget in reversed(grid.children):
		if isinstance(widget, Label) and not isinstance(widget, Button):
			key = normalize_field_name(widget.text)
		elif isinstance(widget, ImageSetDropdown):
			parameter_dict[key] = widget.get_selected()
		elif isinstance(widget, TextInput):
			parameter_dict[key] = widget.text
		elif isinstance(widget, CheckBox):
			parameter_dict[key] = widget.active
		elif isinstance(widget, Button):
			parameter_dict[key] = widget.text
	return parameter_dict


class MenuBase(Screen):
	"""Shared menu screen that builds a task settings grid and starts protocols.

	Reads the per-language ``menubase.ini`` text, lays out the settings
	scrollview, the participant ID entry and the back/start buttons, and
	launches protocols or advances a battery on start.

	Attributes
	----------
	name : str
		Screen name ``'menuscreen'``.
	app : kivy.app.App
		The running TouchCog app.
	language : str
		Language folder name used to locate ``menubase.ini``.
	menu_config : configparser.ConfigParser
		Parsed ``menubase.ini`` providing the button and label text.
	menu_path : pathlib.Path
		Path of the ``menubase.ini`` file.
	protocol_name : str
		Name of the protocol this menu is built for.
	parameters_config : dict
		The task parameters loaded from ``Configuration.ini``.
	is_battery_mode : bool
		Whether the menu runs within a battery sequence.
	battery_required_fields : list of str or None
		Named fields to display in battery mode; None shows all fields.
	"""


	def __init__(self, **kwargs):
		"""Initialise the menu screen and lay out its title, settings and buttons.

		Parameters
		----------
		**kwargs : dict
			Additional keyword arguments passed to :class:`kivy.uix.screenmanager.Screen`.
		"""

		super(MenuBase, self).__init__(**kwargs)
		
		self.name = 'menuscreen'
		self.main_layout = FloatLayout()

		self.app = App.get_running_app()

		self.language = self.app.language

		self.menu_config = configparser.ConfigParser()
		self.menu_path = self.app.app_root / 'Language' / self.language / 'menubase.ini'
		self.menu_config.read(self.menu_path)

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
		"""Update battery mode and optionally set the fields for filtering.

		Parameters
		----------
		is_battery : bool
			Whether the menu is in battery mode.
		required_fields : list of str or None, optional
			Field names to display; None shows all fields and restores the
			participant ID row. Defaults to None.
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
				self.id_grid.size_hint_y = 0.05
		else:
			self.is_battery_mode = False
			self.battery_required_fields = None
			self.start_button.text = self.menu_config['Text']['start_button_regular']
			# Show participant ID
			self.id_grid.size_hint_y = 0.05

	def _normalize_field_name(self, field_name):
		"""Normalize a field name via the module-level helper.

		Parameters
		----------
		field_name : str
			The raw field name to normalize.

		Returns
		-------
		str
			The normalized field name.
		"""
		return normalize_field_name(field_name)

	def _should_display_field(self, field_name):
		"""Determine whether a field should be displayed under required-fields filtering.

		Parameters
		----------
		field_name : str
			The raw field name to test.

		Returns
		-------
		bool
			True if no filtering is active or the normalized field is in the
			required fields; False otherwise.
		"""
		# If no filtering, show all fields
		if self.battery_required_fields is None:
			return True
		
		# If filtering, only show if field is in required_fields
		normalized_field = self._normalize_field_name(field_name)
		normalized_required = [self._normalize_field_name(f) for f in self.battery_required_fields]
		
		return normalized_field in normalized_required

	def apply_required_fields_filter(self):
		"""Remove label/value widget pairs from the grid layout based on required-fields filtering.

		This is called after menu_constructor to filter already-created widgets. It walks
		from the end to the start so widgets can be removed without index shifting.
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
		"""Start the chosen protocol or advance to the next battery config.

		Reads parameters from the settings grid, adds ``participant_id`` unless
		required-fields filtering is active in battery mode, then either loads and
		presents the protocol task screen or merges ``parameter_dict`` into the
		battery config and starts the next battery config.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (the pressed button).
		"""


		parameter_dict = read_grid_parameters(self.setting_gridlayout)
		
		
		# Only add participant_id if not using required_fields filtering in battery mode
		# (when using required fields, participant_id should have been collected upfront and stored elsewhere)
		if not (self.is_battery_mode and self.battery_required_fields is not None and len(self.battery_required_fields) > 0):
			parameter_dict['participant_id'] = self.id_entry.text
		# An ID entered in the battery popup (self.app.participant_id) wins over the id_entry default
		if self.is_battery_mode and getattr(self.app, 'participant_id', None):
			parameter_dict['participant_id'] = self.app.participant_id

		
		# Start or protocol or continue battery
		if not self.is_battery_mode:
			task_module = load_protocol_module(self.app.app_root, self.protocol, 'Protocol')
			protocol_task_screen = task_module.ProtocolScreen(screen_resolution=self.size)
		
			# Remove any stale screen with the same name before adding the new one
			self.app.replace_screen(protocol_task_screen)
		
			protocol_task_screen.load_parameters(parameter_dict)
		
			self.app.active_screen = protocol_task_screen.name
			self.app.present_task_screen(protocol_task_screen.name)
			self._remove_self_later()
		
		else:
			protocol_name = self.app.battery_protocols[self.app.battery_index]
			
			# If in battery mode with required fields filtering, update only the required field values
			# in the pre-loaded config (merge the filled-in values into the existing config)
			# Always merge so JSON-supplied overrides not shown in the menu are kept
			self.app.battery_configs.setdefault(protocol_name, {}).update(parameter_dict)
			
			self.app.battery_index += 1
			self.app.start_next_battery_config()
			self._remove_self_later()

	def _remove_self_later(self):
		"""Schedule removal of this screen once the manager has moved off it.

		Config screens are never reused, so this one is dropped after 0.5 seconds if
		the manager is no longer showing it (removing the current screen would switch).
		"""
		# Config screens are never reused; drop this one once the manager has moved off it
		# (Kivy's remove_widget on the current screen would switch screens)
		manager = self.manager
		def _remove(dt):
			"""Remove this screen from the manager if it is no longer the current one."""
			if manager is not None and self.parent is manager and manager.current != self.name:
				manager.remove_widget(self)
		Clock.schedule_once(_remove, 0.5)


	def update_parameters_external(self, new_params):
		"""Replace the parameters config and push its new values into the grid widgets.

		Sets ``parameters_config`` from ``new_params``, converting it to a
		``TaskParameters`` section if it is not already a SectionProxy, then updates the
		text of matching TextInput widgets and the active state of CheckBox widgets.
		Calls ``update_image_widget`` if such a method exists.

		Parameters
		----------
		new_params : dict or configparser.SectionProxy
			The new parameter name/value pairs to apply to the grid.
		"""
		# Replace self.parameters_config with new_params and rebuild the menu
		self.parameters_config = new_params
		# Convert dictionary to configparser format if needed
		if not isinstance(self.parameters_config, configparser.SectionProxy):
			config = configparser.ConfigParser()
			config['TaskParameters'] = self.parameters_config
			self.parameters_config = config['TaskParameters']
		# Push the new values into the already-built grid widgets
		new_values = {self._normalize_field_name(str(k)): v for k, v in self.parameters_config.items()}
		label_name = None
		for widget in reversed(self.setting_gridlayout.children):
			if isinstance(widget, Label) and not isinstance(widget, Button):
				label_name = self._normalize_field_name(widget.text)
			elif label_name in new_values:
				if isinstance(widget, TextInput):
					widget.text = str(new_values[label_name])
				elif isinstance(widget, CheckBox):
					widget.active = str(new_values[label_name]).lower() == 'true'
		# Check if method update_image_widget exists, if so, execute
		if hasattr(self, 'update_image_widget') and callable(getattr(self, 'update_image_widget')):
			self.update_image_widget()
	
	
	def return_menu(self, *args):
		"""Switch the screen manager back to the protocol menu.

		Parameters
		----------
		*args : tuple
			Ignored; supplied by Kivy event dispatch (the pressed button).
		"""
		
		
		self.manager.current = 'protocolmenu'
	
	
	
	def menu_constructor(self, protocol_name):
		"""Build the settings grid for the given protocol from its configuration file.

		Preserves the current scroll position, loads ``Configuration.ini`` for the
		protocol (using the ``DebugParameters`` section when debug mode is enabled,
		otherwise ``TaskParameters``), rebuilds the grid with a label and a CheckBox or
		TextInput per parameter, then restores the scroll position and applies
		required-fields filtering.

		Parameters
		----------
		protocol_name : str
			Name of the protocol whose configuration drives the grid.
		"""
		# Preserve scroll position
		prev_scroll_y = self.setting_scrollview.scroll_y if self.setting_scrollview.children else 1.0

		self.protocol_name = protocol_name
		self.protocol_path = self.app.app_root / 'Protocol' / self.protocol_name
		config_path = self.protocol_path / 'Configuration.ini'

		config_file = configparser.ConfigParser()
		config_file.read(config_path)

		if ('DebugParameters' in config_file) \
			and (config_file.getboolean('DebugParameters', 'debug_mode', fallback=False)):
			self.parameters_config = config_file['DebugParameters']
		else:
			self.parameters_config = config_file['TaskParameters']

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

