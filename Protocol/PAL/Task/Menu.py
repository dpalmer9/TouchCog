# Imports #
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from Classes.Menu import MenuBase


class ConfigureScreen(MenuBase):
    def __init__(self,**kwargs):
        super(ConfigureScreen,self).__init__(**kwargs)
        self.protocol = 'PAL'
        self.paltype_dropdown = DropDown()
        self.paltype_button = Button(text='dPAL')
        self.paltype_list = ['dPAL', 'sPAL']
        for paltype in self.paltype_list:
            paltype_opt = Button(text=paltype, size_hint_y=None, height=100, size_hint_x=0.3)
            paltype_opt.bind(on_release=lambda paltype_opt: self.paltype_dropdown.select(paltype_opt.text
                                                                                         ))
            self.paltype_dropdown.add_widget(paltype_opt)
        self.paltype_button.bind(on_release=self.paltype_dropdown.open)
        self.paltype_dropdown.bind(on_select=lambda instance, x: setattr(self.paltype_button, 'text', x))
        self.settings_widgets.append(Label(text='PAL Type'))
        self.settings_widgets.append(self.paltype_button)

        self.menu_constructor(self.protocol)
