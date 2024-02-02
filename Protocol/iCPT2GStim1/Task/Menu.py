from Classes.Menu import MenuBase
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown

class ConfigureScreen(MenuBase):
    def __init__(self, **kwargs):
        super(ConfigureScreen, self).__init__(**kwargs)

        self.protocol = 'iCPT2GStim1'

        self.main_task_dropdown = DropDown()
        self.main_task_button = Button(text='Enabled')
        self.main_task_list = ['Enabled', 'Disabled']
        for option in self.main_task_list:
            main_task_opt = Button(text=option, size_hint_y=None, height=100)
            main_task_opt.bind(
                on_release=lambda main_task_opt: self.main_task_dropdown.select(stim_duration_opt.text))
            self.main_task_dropdown.add_widget(main_task_opt)
        self.main_task_button.bind(on_release=self.main_task_dropdown.open)
        self.main_task_dropdown.bind(
            on_select=lambda instance, x: setattr(self.main_task_button, 'text', x))
        self.settings_widgets.append(Label(text='Main Task'))
        self.settings_widgets.append(self.main_task_button)
        
        
        self.stim_duration_probe_dropdown = DropDown()
        self.stim_duration_probe_button = Button(text='Disabled')
        self.stim_duration_probe_list = ['Enabled','Disabled']
        for option in self.stim_duration_probe_list:
            stim_duration_opt = Button(text=option, size_hint_y=None,height=100)
            stim_duration_opt.bind(on_release=lambda stim_duration_opt: self.stim_duration_probe_dropdown.select(stim_duration_opt.text))
            self.stim_duration_probe_dropdown.add_widget(stim_duration_opt)
        self.stim_duration_probe_button.bind(on_release=self.stim_duration_probe_dropdown.open)
        self.stim_duration_probe_dropdown.bind(on_select=lambda instance, x: setattr(self.stim_duration_probe_button, 'text', x))
        self.settings_widgets.append(Label(text='Stimulus Duration Probe'))
        self.settings_widgets.append(self.stim_duration_probe_button)
        
        self.flanker_probe_dropdown = DropDown()
        self.flanker_probe_button = Button(text='Disabled')
        self.flanker_probe_list = ['Enabled','Disabled']
        for option in self.flanker_probe_list:
            flanker_opt = Button(text=option, size_hint_y=None,height=100)
            flanker_opt.bind(on_release=lambda flanker_opt: self.flanker_probe_dropdown.select(flanker_opt.text))
            self.flanker_probe_dropdown.add_widget(flanker_opt)
        self.flanker_probe_button.bind(on_release=self.flanker_probe_dropdown.open)
        self.flanker_probe_dropdown.bind(on_select=lambda instance, x: setattr(self.flanker_probe_button, 'text', x))
        self.settings_widgets.append(Label(text='Flanker Probe'))
        self.settings_widgets.append(self.flanker_probe_button)

        self.menu_constructor(self.protocol)
