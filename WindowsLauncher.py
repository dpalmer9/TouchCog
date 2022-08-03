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
    def __init__(self):
        self.launcher_window = tk.Tk()
        
        self.launcher_title = tk.Label(self.launcher_window,text="TouchCog Windows Launcher v2")
        self.launcher_title.grid(row=0,column=0)
        
        self.launcher_settings_button = tk.Button(self.launcher_window,text="Settings",command=self.settings_menu)
        self.launcher_settings_button.grid(row=1,column=0)
        
        self.launcher_start_button = tk.Button(self.launcher_window,text="Launch",command=self.launch_app)
        self.launcher_start_button.grid(row=2,column=0)
        
        self.launcher_window.mainloop()
    
    def settings_menu(self):
        main_path = os.getcwd()
        self.config_path = main_path + '/Screen.ini'
        self.config_file = configparser.ConfigParser()
        self.config_file.read(self.config_path)
        self.x_dim = int(self.config_file['Screen']['x'])
        self.y_dim = int(self.config_file['Screen']['y'])
        self.fullscreen_var = tk.IntVar()
        fullscreen_val = int(self.config_file['Screen']['fullscreen'])
        self.fullscreen_var.set(fullscreen_val)
        
        
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

        
        self.accept_button = tk.Button(self.configuration_menu_top,text='Accept',command=self.close_configuration)
        self.accept_button.grid(row=4,column=1)
        
    def close_configuration(self):
        self.config_file['Screen']['x'] = str(self.x_res_field.get())
        self.config_file['Screen']['y'] = str(self.y_res_field.get())
        self.config_file['Screen']['fullscreen'] = str(self.fullscreen_var.get())
        
        with open(self.config_path,'w') as configfile:
            self.config_file.write(configfile)
        
        self.configuration_menu_top.destroy()
    
    def launch_app(self):
        self.launcher_window.destroy()
        from KivyMenuInterface import MenuApp
        app = MenuApp()
        app.run()
        return
    
    
    

main_launcher = Windows_Launcher()