##############################################################################
#                      Kivy Launcher Interface                               #
#                      by: Daniel Palmer PhD                                 #
#                      Version: 2.0                                          #
##############################################################################
# Setup#
from kivy.config import Config
import os
import importlib.util
import importlib
import cProfile
import configparser
main_path = os.getcwd()
config_path = main_path + '/Screen.ini'
config_file = configparser.ConfigParser()
config_file.read(config_path)
x_dim = config_file['Screen']['x']
y_dim = config_file['Screen']['y']
fullscreen = int(config_file['Screen']['fullscreen'])
virtual_keyboard = int(config_file['keyboard']['virtual_keyboard'])
use_mouse = int(config_file['mouse']['use_mouse'])
Config.set('graphics', 'allow_screensaver', 0)
Config.set('kivy', 'kivy_clock', 'interrupt')
Config.set('graphics', 'maxfps', 120)

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
    Config.set('graphics','show_cursor', 0)

# Imports #
import kivy
import zipimport
import sys
import os
import configparser
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
# from win32api import GetSystemMetrics
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.config import Config
from functools import partial
from Classes.Menu import MenuBase

# Window.borderless = True
Window.size = (int(x_dim), int(y_dim))
Window.borderless = '0'


# from Protocol_Configure import Protocol_Select

# General Functions #
def os_folder_modifier():
    os_platform = sys.platform
    if os_platform == "linux":
        mod = "/"
    elif os_platform == "darwin":
        mod = "/"
    elif os_platform == "win32":
        mod = "\\"
    else:
        mod = "/"
    return mod


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
        launch_button = Button(text="Start Session")
        launch_button.size_hint = (0.3, 0.2)
        launch_button.pos_hint = {"x": 0.35, "y": 0.6}
        launch_button.bind(on_press=self.load_protocol_menu)
        self.Menu_Layout.add_widget(launch_button)

        exit_button = Button(text="Close Program")
        exit_button.size_hint = (0.3, 0.2)
        exit_button.pos_hint = {"x": 0.35, "y": 0.2}
        exit_button.bind(on_press=self.exit_program)
        self.Menu_Layout.add_widget(exit_button)

    def load_protocol_menu(self, *args):
        if isinstance(self.protocol_window, ProtocolMenu):
            self.manager.current = "protocolmenu"
        else:
            self.protocol_window = ProtocolMenu()
            self.manager.add_widget(self.protocol_window)
            self.manager.current = "protocolmenu"

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
        self.Protocol_List.pos_hint = {"x": 0.1, "y": 0.3}
        self.Protocol_Layout.add_widget(self.Protocol_List)

        cancel_button = Button(text="Cancel")
        cancel_button.size_hint = (0.2, 0.1)
        cancel_button.pos_hint = {"x": 0.4, "y": 0.1}
        cancel_button.bind(on_press=self.cancel_protocol)
        self.Protocol_Layout.add_widget(cancel_button)

        self.add_widget(self.Protocol_Layout)

    def set_protocol(self, label, *args):
        if isinstance(self.Protocol_Configure_Screen,MenuBase):
            self.manager.remove_widget(self.Protocol_Configure_Screen)
        self.protocol_constructor(label)
        self.Protocol_Configure_Screen.size = Window.size
        self.manager.add_widget(self.Protocol_Configure_Screen)
        self.manager.current = 'menuscreen'

    def cancel_protocol(self, *args):
        self.manager.current = "mainmenu"

    def search_protocols(self):
        cwd = os.getcwd()
        mod = os_folder_modifier()
        folder = cwd + mod + "Protocol"
        task_list = os.listdir(folder)
        for task in task_list:
            if '.py' in task:
                task_list.remove(task)
        return task_list

    def protocol_constructor(self, protocol):
        #cwd = os.getcwd()
        #mod = os_folder_modifier()
        #prot_path = cwd + mod + 'Protocol' + mod + protocol
        #sys.path.append(prot_path)
        #from Task.Menu import ConfigureScreen
        #self.Protocol_Configure_Screen = ConfigureScreen()
        #sys.path.remove(prot_path)
        def lazy_import(protocol):
            cwd = os.getcwd()
            working = cwd + '\\Protocol\\' + protocol + '\\Task\\Menu.py'
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
        self.s_manager = ScreenManager()
        self.main_menu = MainMenu()
        self.s_manager.add_widget(self.main_menu)

        return self.s_manager

    def add_screen(self, screen):
        self.s_manager.add_widget(screen)

    def on_start(self):
        self.profile = cProfile.Profile()
        self.profile.enable()

    def on_stop(self):
        self.profile.disable()
        self.profile.dump_stats('touchcog.profile')


if __name__ == '__main__':
    MenuApp().run()
