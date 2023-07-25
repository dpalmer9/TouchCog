##############################################################################
#                      Kivy Launcher Interface                               #
#                      by: Daniel Palmer PhD                                 #
#                      Version: 2.0                                          #
##############################################################################
# Setup#
from kivy.config import Config
import os
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

class Screen_Manager(ScreenManager):
    def __init__(self, **kwargs):
        super(Screen_Manager, self).__init__(**kwargs)


# Class Task Selection #
class Main_Menu(Screen):
    def __init__(self, **kwargs):
        super(Main_Menu, self).__init__(**kwargs)
        self.Menu_Layout = FloatLayout()
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
        self.protocol_window = Protocol_Menu()
        self.manager.add_widget(Protocol_Menu(name='protocolmenu'))
        self.manager.current = "protocolmenu"

    def exit_program(self, *args):
        App.get_running_app().stop()
        Window.close()


# Class Protocol Selection #
class Protocol_Menu(Screen):
    def __init__(self, **kwargs):
        super(Protocol_Menu, self).__init__(**kwargs)
        self.Protocol_Layout = FloatLayout()

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
        self.protocol_constructor(label)
        self.Protocol_Configure_Screen.size = Window.size
        self.manager.switch_to(self.Protocol_Configure_Screen)

    def cancel_protocol(self, *args):
        self.manager.current = "mainmenu"

    def search_protocols(self):
        cwd = os.getcwd()
        mod = os_folder_modifier()
        folder = cwd + mod + "Protocol"
        task_list = os.listdir(folder)
        return task_list

    def protocol_constructor(self, protocol):
        # cwd = os.getcwd()
        # mod = os_folder_modifier()
        # prot_path = cwd + mod + 'Protocol' + mod + protocol
        # sys.path.append(prot_path)
        from Classes.Menu import MenuBase
        self.Protocol_Configure_Screen = MenuBase()
        # sys.path.remove(prot_path)
        self.Protocol_Configure_Screen.menu_constructor(protocol)


# Class App Builder #
class MenuApp(App):
    def build(self):
        self.s_manager = Screen_Manager()
        self.s_manager.add_widget(Main_Menu(name="mainmenu"))

        return self.s_manager

    def add_screen(self, screen):
        self.s_manager.add_widget(screen)


if __name__ == '__main__':
    MenuApp().run()
