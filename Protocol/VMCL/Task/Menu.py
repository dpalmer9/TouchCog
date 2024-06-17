# Imports
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from Classes.Menu import MenuBase

class ConfigureScreen(MenuBase):
    def __init__(self, **kwargs):
        super(ConfigureScreen,self).__init__(**kwargs)
        
        self.protocol = 'VMCL'
        
        self.menu_constructor(self.protocol)
        self.correction_dropdown = DropDown()
        self.correction_button = Button(text='Correction Trials Enabled')
        self.correction_list = ['Correction Trials Enabled', 'Correction Trials Disabled']
        for correction in self.correction_list:
            corrections_opt = Button(text=correction, size_hint_y=None, height=100)
            corrections_opt.bind(on_release=lambda corrections_opt: self.correction_dropdown.select(corrections_opt.text
                                                                                                    ))
            self.correction_dropdown.add_widget(corrections_opt)
        self.correction_button.bind(on_release=self.correction_dropdown.open)
        self.correction_dropdown.bind(on_select=lambda instance, x: setattr(self.correction_button, 'text', x))
        self.settings_widgets.append(Label(text='Correction Trials'))
        self.settings_widgets.append(self.correction_button)