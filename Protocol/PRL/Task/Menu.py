# Imports #
from Classes.Menu import MenuBase


class ConfigureScreen(MenuBase):
    def __init__(self,**kwargs):
        super(ConfigureScreen,self).__init__(**kwargs)

        self.protocol = 'PRL'
        self.protocol_name = 'Probabilistic Reversal Learning'
        self.protocol_title_label.text = self.protocol_name

        self.menu_constructor(self.protocol)