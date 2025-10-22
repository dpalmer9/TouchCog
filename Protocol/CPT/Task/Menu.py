from Classes.Menu import MenuBase, ImageSetDropdown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown

class ConfigureScreen(MenuBase):
    def __init__(self, **kwargs):
        super(ConfigureScreen, self).__init__(**kwargs)

        self.protocol = 'CPT'
        self.protocol_name = 'Continuous Performance Task'
        self.protocol_title_label.text = self.protocol_name
        self.name = self.protocol + '_configscreen'

        self.image_select_label = Label(text='Image Set:')
        self.image_selector = ImageSetDropdown([
            {'label': 'Image Set 1',
            'images': ['Protocol/CPT/Image/Fribbles/Fb/Fb2_1111.png', 'Protocol/CPT/Image/Fribbles/Fb/Fb2_1112.png'],
            'value': 'set1'}
            ])
        self.menu_constructor(self.protocol)
        self.setting_gridlayout.rows += 1
        self.setting_gridlayout.add_widget(self.image_select_label)
        self.setting_gridlayout.add_widget(self.image_selector)
