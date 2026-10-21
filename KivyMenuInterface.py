"""Entry point that launches the TouchCog Kivy menu application."""
##############################################################################
#                      Kivy Launcher Interface                               #
#                      by: Daniel Palmer PhD                                 #
#                      revisions: Filip Kosel PhD                            #
#                      Version: 2.0.0                                        #
##############################################################################

# Thin entry point. The interface lives in the Interface package:
#   Startup (config + window setup), Menus, Battery, Video, App.
# Interface.Startup must be imported before anything that loads kivy.core.window.
import Interface.Startup
from Interface.App import MenuApp

__all__ = ['MenuApp']

if __name__ == '__main__':
	MenuApp().run()
