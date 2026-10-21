# Headless check: ImageButton fires on_release exactly once per pressed interval.
import os, sys
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from kivy.input.motionevent import MotionEvent
from Classes.Protocol import ImageButton


class FakeTouch(MotionEvent):
	def depack(self, args):
		self.sx, self.sy = args
		super().depack(args)


def run(always_release, path):
	btn = ImageButton(always_release=always_release, size_hint=(None, None), size=(100, 100), pos=(0, 0))
	counts = {'press': 0, 'release': 0}
	btn.bind(on_press=lambda *a: counts.__setitem__('press', counts['press'] + 1))
	btn.bind(on_release=lambda *a: counts.__setitem__('release', counts['release'] + 1))
	touch = FakeTouch('fake', 1, (0.0, 0.0))
	touch.scale_for_screen(1000, 1000)

	def at(x):
		touch.move((x / 1000., 50 / 1000.))
		touch.scale_for_screen(1000, 1000)

	def dispatch(name):
		# normal propagation, then grabbed-widget re-dispatch as EventLoop does
		getattr(btn, name)(touch)
		for w in touch.grab_list[:]:
			if w() is btn:
				touch.grab_current = btn
				getattr(btn, name)(touch)
				touch.grab_current = None

	for step, x in path:
		at(x)
		if step == 'down':
			dispatch('on_touch_down')
		elif step == 'move':
			dispatch('on_touch_move')
		else:
			dispatch('on_touch_up')
	return counts


for ar in (True, False):
	assert run(ar, [('down', 50), ('up', 50)]) == {'press': 1, 'release': 1}
	assert run(ar, [('down', 50), ('move', 300), ('up', 300)]) == {'press': 1, 'release': 1}
	assert run(ar, [('down', 50), ('move', 300), ('move', 50), ('up', 50)]) == {'press': 2, 'release': 2}
print('ok')
