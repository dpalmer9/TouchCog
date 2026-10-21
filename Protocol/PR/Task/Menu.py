"""Configuration menu screen for the Progressive Ratio (PR) protocol."""
# Imports
from Classes.Menu import MenuBase

class ConfigureScreen(MenuBase):
    """Menu screen for configuring and starting the Progressive Ratio protocol.

    Sets the PR protocol identifiers and screen name, updates the menu title
    label, and builds the settings grid from the PR configuration file.

    Attributes
    ----------
    protocol : str
        Protocol identifier ``'PR'``; used by the base class to load the PR task module.
    protocol_name : str
        Set to the display name ``'Progressive Ratio'`` (shown in the title label), then
        reset to ``'PR'`` by ``menu_constructor``.
    name : str
        Screen name ``'PR_configscreen'``.
    """
    def __init__(self, **kwargs):
        """Initialise the PR configuration screen and build its settings grid.

        Initialises the base menu screen, sets the protocol identifiers and the
        screen name ``'PR_configscreen'``, sets the title label text to the
        protocol name, and builds the settings grid for the PR protocol.

        Parameters
        ----------
        **kwargs : dict
            Additional keyword arguments passed to :class:`kivy.uix.screenmanager.Screen`.

        Notes
        -----
        The settings grid is built by :meth:`menu_constructor` from
        ``Protocol/PR/Configuration.ini`` (``TaskParameters`` section, or
        ``DebugParameters`` when debug mode is enabled).
        """
        super(ConfigureScreen, self).__init__(**kwargs)
        self.protocol = 'PR'
        self.protocol_name = 'Progressive Ratio'
        self.name = self.protocol + '_configscreen'
        self.protocol_title_label.text = self.protocol_name
        self.name = self.protocol + '_configscreen'
        self.menu_constructor(self.protocol)
