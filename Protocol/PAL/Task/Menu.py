"""Settings menu screen for the Paired Associates Learning (PAL) task."""
# Imports #
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.app import App
from Classes.Menu import MenuBase, ImageSetDropdown, ImageSetItem


class ConfigureScreen(MenuBase):
    """Settings menu screen for the Paired Associates Learning task.

    Builds the shared task settings grid from ``Protocol/PAL/Configuration.ini``
    (``DebugParameters`` in debug mode, otherwise ``TaskParameters``).

    Adds two image-set dropdowns (dsPAL and Recall) below the standard settings.

    Attributes
    ----------
    protocol : str
        Task folder name, ``'PAL'``.
    protocol_name : str
        Set to the display title ``'Paired Associates Learning'`` (shown in the title label), then reset
        to ``'PAL'`` by ``menu_constructor``.
    name : str
        Screen name, ``'PAL_configscreen'``.
    """

    def __init__(self,**kwargs):
        """Build the PAL settings grid plus the dsPAL and Recall image-set dropdowns.

        Defines ``image_set_dspal`` (options set1, set2, set3 and rand) and
        ``image_set_recall`` (options set1, set2, set3 and rand) as lists of
        ``{'label', 'images', 'value'}`` dicts, builds the standard grid with
        ``menu_constructor``, then appends two label/dropdown pairs to
        ``setting_gridlayout`` (two extra rows). The ``rand`` options carry no images.

        Parameters
        ----------
        **kwargs : dict
            Passed to ``MenuBase``.

        Notes
        -----
        The selections are read back with the rest of the grid by
        ``read_grid_parameters`` under the normalized label keys
        ``'dspal_image_set'`` and ``'recall_image_set'``.
        """
        super(ConfigureScreen,self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.protocol = 'PAL'
        self.protocol_name = 'Paired Associates Learning'
        self.protocol_title_label.text = self.protocol_name
        self.name = self.protocol + '_configscreen'

        self.image_set_dspal = [{'label': 'Image Set 1',
                                 'images': [f'{self.app.app_root}/Protocol/PAL/Image/PAL-Targets/zigzags.png',f'{self.app.app_root}/Protocol/PAL/Image/PAL-Targets/shapes.png',f'{self.app.app_root}/Protocol/PAL/Image/PAL-Targets/ghost.png'],
                                 'value': 'set1'},
                                  {'label': 'Image Set 2',
                                   'images': [f'{self.app.app_root}/Protocol/PAL/Image/PAL-Targets/camera.png',f'{self.app.app_root}/Protocol/PAL/Image/PAL-Targets/ghost.png',f'{self.app.app_root}/Protocol/PAL/Image/PAL-Targets/ovals.png'],
                                   'value': 'set2'},
                                  {'label': 'Image Set 3',
                                   'images': [f'{self.app.app_root}/Protocol/PAL/Image/PAL-Targets/lines.png',f'{self.app.app_root}/Protocol/PAL/Image/PAL-Targets/shapes.png',f'{self.app.app_root}/Protocol/PAL/Image/PAL-Targets/zigzags.png'],
                                   'value': 'set3'},
                                  {'label': 'Random',
                                   'images': [],
                                   'value': 'rand'}]

        self.image_set_recall = [{'label': 'Image Set 1',
                                 'images': [f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/1.png',f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/2.png',
                                            f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/4.png',f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/5.png',
                                            f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/6.png'],
                                 'value': 'set1'},
                                {'label': 'Image Set 2',
                                 'images': [f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/3.png',f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/7.png',
                                            f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/9.png',f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/10.png',
                                            f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/12.png'],
                                 'value': 'set2'},
                                 {'label': 'Image Set 3',
                                  'images': [f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/8.png',f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/14.png',
                                            f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/15.png',f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/19.png',
                                            f'{self.app.app_root}/Protocol/PAL/Image/PA-Targets/20.png'],
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