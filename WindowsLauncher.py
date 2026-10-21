"""Tkinter launcher that edits Config.ini display settings and starts TouchCog."""
###############################################################
#####              Touchscreen Windows Launcher         #######
#####                   by: Daniel Palmer, PhD          #######
###############################################################                  


#Imports#
from tkinter import N
from tkinter import S
from tkinter import W
from tkinter import E
from tkinter import END
from tkinter import BROWSE
from tkinter import VERTICAL
from tkinter import ttk
import tkinter as tk
import os
import configparser


## Class Function (Tkinter Launcher) ##

class Windows_Launcher():
    """Tkinter launcher window with Settings and Launch buttons.

    Creating an instance builds the window and runs the Tk main loop until it
    is closed or the Kivy app is launched.

    Attributes
    ----------
    launcher_window : tkinter.Tk
        The main launcher window.
    config_path : str
        Path of the Config.ini being edited (set by :meth:`settings_menu`).
    config_file : configparser.ConfigParser
        Parsed Config.ini (set by :meth:`settings_menu`).
    fullscreen_var, keyboard_var, mouse_var : tkinter.IntVar
        Checkbox states for ``Screen/fullscreen``, ``keyboard/virtual_keyboard`` and
        ``mouse/use_mouse``.
    x_res_field, y_res_field : tkinter.Entry
        Entry fields for the ``Screen/x`` and ``Screen/y`` resolution values.
    configuration_menu_top : tkinter.Toplevel
        The settings window.
    """
    def __init__(self):
        """Build the launcher window and enter the Tk main loop."""
        self.launcher_window = tk.Tk()
        
        self.launcher_title = tk.Label(self.launcher_window,text="TouchCog Windows Launcher v2")
        self.launcher_title.grid(row=0,column=0)
        
        self.launcher_settings_button = tk.Button(self.launcher_window,text="Settings",command=self.settings_menu)
        self.launcher_settings_button.grid(row=1,column=0)
        
        self.launcher_start_button = tk.Button(self.launcher_window,text="Launch",command=self.launch_app)
        self.launcher_start_button.grid(row=2,column=0)
        
        self.launcher_window.mainloop()
    
    def settings_menu(self):
        """Open the settings window populated from Config.ini.

        Reads the per-user ``~/Documents/TouchCog/Config.ini``, falling back to the
        Config.ini next to this file when it does not exist. Loads the ``Screen``
        ``x``, ``y`` and ``fullscreen``, ``keyboard`` ``virtual_keyboard`` and
        ``mouse`` ``use_mouse`` values into entry fields and checkboxes, with an
        Accept button bound to :meth:`close_configuration`.
        """
        # Same per-user Config.ini that KivyMenuInterface reads; fall back to the packaged copy
        self.config_path = os.path.join(os.path.expanduser('~'), 'Documents', 'TouchCog', 'Config.ini')
        if not os.path.exists(self.config_path):
            self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Config.ini')
        self.config_file = configparser.ConfigParser()
        self.config_file.read(self.config_path)
        self.x_dim = int(self.config_file['Screen']['x'])
        self.y_dim = int(self.config_file['Screen']['y'])
        self.fullscreen_var = tk.IntVar()
        self.keyboard_var = tk.IntVar()
        self.mouse_var = tk.IntVar()

        fullscreen_val = int(self.config_file['Screen']['fullscreen'])
        self.fullscreen_var.set(fullscreen_val)
        keyboard_val = int(self.config_file['keyboard']['virtual_keyboard'])
        self.keyboard_var.set(keyboard_val)
        mouse_val = int(self.config_file['mouse']['use_mouse'])
        self.mouse_var.set(mouse_val)
        
        
        self.configuration_menu_top = tk.Toplevel() 
        
        self.configuration_title = tk.Label(self.configuration_menu_top,text='Configuration')
        self.configuration_title.grid(row=0,column=1)
        
        self.x_res_label = tk.Label(self.configuration_menu_top,text='X Resolution:')
        self.x_res_label.grid(row=1,column=0)
        
        self.x_res_field = tk.Entry(self.configuration_menu_top)
        self.x_res_field.grid(row=1,column=2)
        self.x_res_field.insert(tk.END,str(self.x_dim))
        
        self.y_res_label = tk.Label(self.configuration_menu_top,text='Y Resolution:')
        self.y_res_label.grid(row=2,column=0)
        
        self.y_res_field = tk.Entry(self.configuration_menu_top)
        self.y_res_field.grid(row=2,column=2)
        self.y_res_field.insert(tk.END,str(self.y_dim))
        
        self.fullscreen_checkbox = tk.Checkbutton(self.configuration_menu_top,text='Fullscreen',
                                                  variable=self.fullscreen_var)
        self.fullscreen_checkbox.grid(row=3,column=1)

        self.keyboard_checkbox = tk.Checkbutton(self.configuration_menu_top, text='Virtual Keyboard',
                                                variable=self.keyboard_var)
        self.keyboard_checkbox.grid(row=4, column=1)

        self.mouse_checkbox = tk.Checkbutton(self.configuration_menu_top, text='Use Mouse',
                                             variable=self.mouse_var)
        self.mouse_checkbox.grid(row=5, column=1)

        
        self.accept_button = tk.Button(self.configuration_menu_top,text='Accept',command=self.close_configuration)
        self.accept_button.grid(row=6,column=1)
        
    def close_configuration(self):
        """Write the settings window values to Config.ini and close the window.

        Sets ``Screen`` ``x``, ``y`` and ``fullscreen``, ``keyboard``
        ``virtual_keyboard`` and ``mouse`` ``use_mouse`` from the widgets, writes the
        whole configuration to ``self.config_path`` and destroys the settings window.
        """
        self.config_file['Screen']['x'] = str(self.x_res_field.get())
        self.config_file['Screen']['y'] = str(self.y_res_field.get())
        self.config_file['Screen']['fullscreen'] = str(self.fullscreen_var.get())
        self.config_file['keyboard']['virtual_keyboard'] = str(self.keyboard_var.get())
        self.config_file['mouse']['use_mouse'] = str(self.mouse_var.get())
        
        with open(self.config_path,'w') as configfile:
            self.config_file.write(configfile)
        
        self.configuration_menu_top.destroy()
    
    def launch_app(self):
        """Close the launcher window and run the Kivy ``MenuApp``."""
        self.launcher_window.destroy()
        from KivyMenuInterface import MenuApp
        app = MenuApp()
        app.run()
        return
    
    
    

main_launcher = Windows_Launcher()