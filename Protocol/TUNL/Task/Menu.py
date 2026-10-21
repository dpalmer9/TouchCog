"""Settings menu screen for the Trial-Unique Non-Matching to Location (TUNL) task."""
# Imports #
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from Classes.Menu import MenuBase


class ConfigureScreen(MenuBase):
    """Settings menu screen for the Trial-Unique Non-Matching to Location task.

    Builds the shared task settings grid from ``Protocol/TUNL/Configuration.ini``
    (``DebugParameters`` in debug mode, otherwise ``TaskParameters``).

    Attributes
    ----------
    protocol : str
        Task folder name, ``'TUNL'``.
    protocol_name : str
        Set to the display title ``'Trial-Unique Non-Matching to Location'`` (shown in the title label), then reset
        to ``'TUNL'`` by ``menu_constructor``.
    name : str
        Screen name, ``'TUNL_configscreen'``.
    """

    def __init__(self,**kwargs):
        """Set the TUNL title and screen name and build the settings grid.

        Parameters
        ----------
        **kwargs : dict
            Passed to ``MenuBase``.
        """
        super(ConfigureScreen,self).__init__(**kwargs)
        self.protocol = 'TUNL'
        self.name = self.protocol_name + '_menuscreen'
        self.protocol_name = 'Trial-Unique Non-Matching to Location'
        self.protocol_title_label.text = self.protocol_name
        self.name = self.protocol + '_configscreen'
        self.menu_constructor(self.protocol)
            
        
        
