# Imports #
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from Classes.Menu import MenuBase


class ConfigureScreen(MenuBase):
    def __init__(self,**kwargs):
        super(ConfigureScreen,self).__init__(**kwargs)
        self.protocol = 'TUNL'
        self.menu_constructor(self.protocol)
            
        
        
