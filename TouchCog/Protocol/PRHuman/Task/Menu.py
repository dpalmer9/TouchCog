# Imports
from TouchCog.Classes.Menu import MenuBase

# TextInput(text="Test",id="Test1")


class ConfigureScreen(MenuBase):
    def __init__(self, **kwargs):
        super(ConfigureScreen, self).__init__(**kwargs)
        self.protocol = 'PRHuman'
        self.menu_constructor(self.protocol)
