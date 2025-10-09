# Imports
from Classes.Menu import MenuBase

class ConfigureScreen(MenuBase):
    def __init__(self, **kwargs):
        super(ConfigureScreen, self).__init__(**kwargs)
        self.protocol = 'PR'
        self.protocol_name = 'Progressive Ratio'
        self.name = self.protocol + '_configscreen'
        self.protocol_title_label.text = self.protocol_name
        self.name = self.protocol + '_configscreen'
        self.menu_constructor(self.protocol)
