# Imports #
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from Classes.Menu import MenuBase, ImageSetDropdown, ImageSetItem


class ConfigureScreen(MenuBase):
    def __init__(self,**kwargs):
        super(ConfigureScreen,self).__init__(**kwargs)
        self.protocol = 'PAL'
        self.protocol_name = 'Paired Associates Learning'
        self.protocol_title_label.text = self.protocol_name
        self.name = self.protocol + '_configscreen'

        self.image_set_dspal = [{'label': 'Image Set 1',
                                 'images': ['Protocol/PAL/Image/PAL-Targets/blocks.png','Protocol/PAL/Image/PAL-Targets/cookie.png','Protocol/PAL/Image/PAL-Targets/nineties.png'],
                                 'value': 'set1'},
                                {'label': 'Image Set 2',
                                 'images': ['Protocol/PAL/Image/PAL-Targets/camera.png','Protocol/PAL/Image/PAL-Targets/ghost.png','Protocol/PAL/Image/PAL-Targets/ovals.png'],
                                 'value': 'set2'},
                                 {'label': 'Image Set 3',
                                  'images': ['Protocol/PAL/Image/PAL-Targets/lines.png','Protocol/PAL/Image/PAL-Targets/shapes.png','Protocol/PAL/Image/PAL-Targets/zigzags.png'],
                                  'value': 'set3'},
                                  {'label': 'Random',
                                   'images': [],
                                   'value': 'rand'}]

        self.image_set_recall = [{'label': 'Image Set 1',
                                 'images': ['Protocol/PAL/Image/PA-Targets/1.png','Protocol/PAL/Image/PA-Targets/2.png',
                                            'Protocol/PAL/Image/PA-Targets/4.png','Protocol/PAL/Image/PA-Targets/5.png',
                                            'Protocol/PAL/Image/PA-Targets/6.png'],
                                 'value': 'set1'},
                                {'label': 'Image Set 2',
                                 'images': ['Protocol/PAL/Image/PA-Targets/3.png','Protocol/PAL/Image/PA-Targets/7.png',
                                            'Protocol/PAL/Image/PA-Targets/9.png','Protocol/PAL/Image/PA-Targets/10.png',
                                            'Protocol/PAL/Image/PA-Targets/12.png'],
                                 'value': 'set2'},
                                 {'label': 'Image Set 3',
                                  'images': ['Protocol/PAL/Image/PA-Targets/8.png','Protocol/PAL/Image/PA-Targets/14.png',
                                            'Protocol/PAL/Image/PA-Targets/15.png','Protocol/PAL/Image/PA-Targets/19.png',
                                            'Protocol/PAL/Image/PA-Targets/20.png'],
                                  'value': 'set3'},
                                  {'label': 'Random',
                                   'images': [],
                                   'value': 'rand'}]
        
        self.image_dspal_label = Label(text='dsPAL Image Set')
        self.image_dspal_dropdown = ImageSetDropdown(self.image_set_dspal)
        self.image_recall_label = Label(text='Recall Image Set')
        self.image_recall_dropdown = ImageSetDropdown(self.image_set_recall)

        self.menu_constructor(self.protocol)
        self.setting_gridlayout.rows += 2
        self.setting_gridlayout.add_widget(self.image_dspal_label)
        self.setting_gridlayout.add_widget(self.image_dspal_dropdown)
        self.setting_gridlayout.add_widget(self.image_recall_label)
        self.setting_gridlayout.add_widget(self.image_recall_dropdown)