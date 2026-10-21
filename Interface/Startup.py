"""Startup configuration and window setup for the TouchCog Kivy launcher."""
# Interface.Startup: startup configuration and window setup for the Kivy launcher.
# Importing this module (before kivy.core.window is imported anywhere else) applies DPI
# awareness, environment variables and Kivy Config, then sets up the window.

# Import - General #

import os
import sys

# Per-monitor DPI awareness (must run before any kivy import) so input matches the drawn UI
if sys.platform == 'win32':
	import ctypes
	_user32 = ctypes.windll.user32
	for _set_dpi in (
		lambda: _user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)),  # PER_MONITOR_AWARE_V2
		lambda: ctypes.windll.shcore.SetProcessDpiAwareness(2),
		lambda: _user32.SetProcessDPIAware(),
	):
		try:
			if _set_dpi():
				break
		except Exception:
			pass

# Kivy/SDL on Windows size the window in DPI-scaled points, not physical pixels
dpi_scale = 1.0
if sys.platform == 'win32':
	try:
		dpi_scale = _user32.GetDpiForSystem() / 96
	except Exception:
		pass

os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'

import configparser
import shutil
import pathlib
import subprocess
import re

TOUCHCOG_VERSION = "2.0.1"

os.environ['KIVY_VIDEO'] = 'ffpyplayer'
os.environ['KIVY_AUDIO'] = 'ffpyplayer'

def get_base_path():
	"""Return the base path for locating app resources.

	In a PyInstaller bundle, ``sys._MEIPASS`` is used when present
	(onefile builds), otherwise the parent directory of the executable
	(onedir builds). In development, the repo root (the parent of the
	``Interface`` package) is returned.

	Returns
	-------
	pathlib.Path
		The resolved base path.
	"""
	if getattr(sys, 'frozen', False):
		# When running as a PyInstaller executable, PyInstaller extracts
		# bundled data to a temporary folder accessible via sys._MEIPASS.
		# Prefer that location for resource access (onefile builds). If
		# sys._MEIPASS is not present (e.g. onedir builds), fall back to
		# the parent dir of the executable.
		meipass = getattr(sys, '_MEIPASS', None)
		if meipass:
			return pathlib.Path(meipass).resolve()
		return pathlib.Path(sys.executable).resolve().parent
	else:
		# Running in development: use the repo root (the parent of the Interface package)
		return pathlib.Path(__file__).parent.parent.resolve()

from kivy.config import Config
# Change current working directory to location of this file

def get_refresh_rate():
	"""Return the current display refresh rate in hertz.

	On Windows the rate is read from the current display mode
	(``EnumDisplaySettingsW``), falling back to 60 Hz if the call fails.
	On Linux it is parsed from ``xrandr --verbose`` (the ``*``-marked
	current mode, else a "current ... Hz" line); on macOS from
	``system_profiler SPDisplaysDataType``. Unrecognized platforms, and
	Linux or macOS detection failures, return None.

	Returns
	-------
	int or None
		The refresh rate in Hz, or None when it could not be detected.
	"""
	if sys.platform.startswith('win'):
		import ctypes
		user32 = ctypes.windll.user32
		class DEVMODE(ctypes.Structure):
			"""ctypes Structure mirroring the Windows DEVMODE display-mode fields."""
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

# Ensure a per-user Config.ini exists in the user's home directory. If not, copy
# the default packaged Config.ini from app_root into the user's home.
user_config_path = pathlib.Path.home() / 'Documents' / 'TouchCog' / 'Config.ini'
if not user_config_path.exists():
	try:
		# If running as a PyInstaller onefile executable, resources are extracted
		# to sys._MEIPASS; prefer that path for the packaged config file.
		packaged_root = pathlib.Path(getattr(sys, '_MEIPASS', app_root))
		packaged_config = packaged_root / 'Config.ini'
		# Ensure the parent folder exists for user_config_path
		try:
			user_config_path.parent.mkdir(parents=True, exist_ok=True)
		except Exception:
			pass
		if packaged_config.exists():
			shutil.copy2(str(packaged_config), str(user_config_path))
			print("Copied Config.ini from packaged root to user home:", user_config_path)
		else:
			print("WARNING: default Config.ini not found in packaged root:", packaged_config)
	except Exception as e:
		print("WARNING: Could not copy Config.ini to user home:", e)

# Use the user-local config path for all subsequent reads/writes
config_path = user_config_path

config_file = configparser.ConfigParser()
read_files = config_file.read(str(config_path), encoding='utf-8')
print("Read Config files:", read_files)

default_config_file = configparser.ConfigParser()
default_config_file.read(str(app_root / 'Config.ini'), encoding='utf-8')

fullscreen = int(config_file['Screen']['fullscreen'])

# Config.ini holds physical pixels; convert so mouse/touch input maps onto the drawn UI at any scaling
x_px, y_px = int(config_file['Screen']['x']), int(config_file['Screen']['y'])
if fullscreen == 1 and sys.platform == 'win32':
	# Fullscreen always covers the primary monitor, whatever Config.ini says
	x_px, y_px = _user32.GetSystemMetrics(0), _user32.GetSystemMetrics(1)
x_dim = round(x_px / dpi_scale)
y_dim = round(y_px / dpi_scale)
virtual_keyboard = int(config_file['keyboard']['virtual_keyboard'])
use_mouse = int(config_file['mouse']['use_mouse'])
skip_video = config_file.getboolean(
	'Video',
	'skip_video',
	fallback=default_config_file.getboolean('Video', 'skip_video', fallback=False)
)
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
	# 'auto' = borderless fullscreen at desktop resolution; True switches the display mode and breaks input mapping on scaled displays
	Config.set('graphics', 'fullscreen', 'auto')


if virtual_keyboard == 0:
	Config.set('kivy', 'keyboard_mode', 'system')

elif virtual_keyboard == 1:
	Config.set('kivy', 'keyboard_mode', 'multi')
	Config.set('kivy', 'keyboard_layout', 'qwerty')


if use_mouse == 0:
	Config.set('graphics', 'show_cursor', 0)




# Kivy window setup, once config is done #

from kivy.core.window import Window
from kivy.uix.vkeyboard import VKeyboard

class LargeVKeyboard(VKeyboard):
	"""Virtual keyboard that keeps its width at 66% of the window.

	Overrides the default Kivy sizing so the keyboard spans 66% of the
	``Window`` width, sits anchored at the bottom with a larger font, and
	reasserts the target width if Kivy's layout changes it.

	Attributes
	----------
	width : int
		Keyboard width, forced to 66% of ``Window.width``.
	y : int
		Vertical position, kept at 0 (bottom of the window).
	font_size : str
		Key font size ``'40sp'``.
	"""
	def __init__(self, **kwargs):
		"""Initialise the keyboard at 66% of the window width, anchored at the bottom.

		Disables the vertical size hint, sets the width to 66% of
		``Window.width``, positions the keyboard at ``y = 0`` and sets the
		font size to ``'40sp'``.

		Parameters
		----------
		**kwargs : dict
			Additional keyword arguments passed to :class:`kivy.uix.vkeyboard.VKeyboard`.
		"""
		super().__init__(**kwargs)
		# Disable the default size hint so Kivy doesn't shrink it
		self.size_hint_y = None 
		# Force the width to 66% of the Window
		self.width = Window.width * 0.66

		# Ensure it sits at the bottom
		self.y = 0
		# Change default font size
		self.font_size = '40sp'

	def on_width(self, instance, value):
		"""Reassert the 66%-of-window keyboard width and recompute its height.

		If the new width differs from 66% of ``Window.width`` by more than
		5 pixels, the width is reset to that target. The height is then set
		to the width divided by 3, the standard keyboard ratio.

		Parameters
		----------
		instance : kivy.uix.vkeyboard.VKeyboard
			The widget the event is bound to (this keyboard).
		value : float
			The new width value in pixels.
		"""
		# Prevent Kivy's internal layout from resetting the width later
		target = Window.width * 0.66
		if abs(value - target) > 5:
			self.width = target
		# Maintain 16:9/standard keyboard ratio dynamically
		standard_keyboard_ratio = 3.0
		self.height = self.width / standard_keyboard_ratio





# Window.borderless = True

Window.size = (int(x_dim), int(y_dim))
Window.borderless = False
Window.set_vkeyboard_class(LargeVKeyboard)

def search_protocols():
		"""Return the names of the protocol folders shipped with the app.

		Scans the ``Protocol`` folder under the base path and collects the
		stem (name without extension) of every subdirectory, skipping files.

		Returns
		-------
		list of str
			The protocol folder names.
		"""
		task_path = app_root / 'Protocol'
		task_list = list(task_path.glob('*'))
		output_list = list()
		
		for task in task_list:
		
			if not task.is_dir():
				continue
			
			output_list.append(task.stem)
		
		return output_list
