"""Settings menu screen for the Probabilistic Reversal Learning (PRL) task."""
# Imports #
from Classes.Menu import MenuBase


class ConfigureScreen(MenuBase):
    """Settings menu screen for the Probabilistic Reversal Learning task.

    Builds the shared task settings grid from ``Protocol/PRL/Configuration.ini``
    (``DebugParameters`` in debug mode, otherwise ``TaskParameters``).

    Attributes
    ----------
    protocol : str
        Task folder name, ``'PRL'``.
    protocol_name : str
        Set to the display title ``'Probabilistic Reversal Learning'`` (shown in the title label), then reset
        to ``'PRL'`` by ``menu_constructor``.
    name : str
        Screen name, ``'PRL_configscreen'``.
    """

    def __init__(self,**kwargs):
        """Set the PRL title and screen name and build the settings grid.

        Parameters
        ----------
        **kwargs : dict
            Passed to ``MenuBase``.
        """
        super(ConfigureScreen,self).__init__(**kwargs)

        self.protocol = 'PRL'
        self.protocol_name = 'Probabilistic Reversal Learning'
        self.protocol_title_label.text = self.protocol_name
        self.name = self.protocol + '_configscreen'

        self.menu_constructor(self.protocol)