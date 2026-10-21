# Headless check: replace_screen keeps screen names unique; a repeated battery-finished call advances once.
import os, sys
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import KivyMenuInterface as kmi
from kivy.uix.screenmanager import Screen

app = kmi.MenuApp()
app.s_manager = kmi.ScreenManager()
app._pending_completions = set()
app.show_general_video = lambda *a, **k: None

# replace_screen: no duplicate names, newest screen wins
app.replace_screen(Screen(name='CPT_configscreen'))
new = Screen(name='CPT_configscreen')
app.replace_screen(new)
assert [s.name for s in app.s_manager.screens].count('CPT_configscreen') == 1
assert app.s_manager.get_screen('CPT_configscreen') is new

# double tap on a battery finish button must advance battery_index once
scheduled = []
kmi.Clock.schedule_once = lambda fn, t=0: scheduled.append(fn)
app.replace_screen(Screen(name='task'))
app.battery_active, app.battery_protocols, app.battery_index = True, ['A', 'B', 'C'], 0
app.handle_task_completion('task')
app.handle_task_completion('task')
for fn in scheduled:
	fn(0)
assert app.battery_index == 1, app.battery_index
print('ok')
