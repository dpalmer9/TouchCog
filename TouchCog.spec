# -*- mode: python ; coding: utf-8 -*-

import os
from kivy_deps import sdl2, glew

block_cipher = None

datas = [
    ('Config.ini', '.'),
    ('Protocol', 'Protocol'),
    ('Classes', 'Classes'),
    ('Language', 'Language'),
    ('Battery', 'Battery'),
    ('bin', 'bin')
]

a = Analysis(['C:\\Users\\MOUSETRAP-DAN\\Documents\\TouchCog\\TouchCog\\KivyMenuInterface.py'],
             pathex=['.'],
             binaries=[],
             datas=datas,
             # Hidden imports remain crucial for Kivy and its libraries.
             hiddenimports=[
                'kivy.core.video.video_ffpyplayer',
                'kivy.core.audio.audio_ffpyplayer',
                'kivy.deps.gstreamer',
                'ffpyplayer.player',
                'ffpyplayer.tools',
                'pandas',
                # Protocol task modules are loaded at runtime by file path from the bundled
                # Protocol/ data folder, so what they import must be bundled explicitly.
                'numpy',
                'random',
                'statistics',
                'traceback',
                'gc',
                'math',
                'collections',
                'importlib.util',
                'Classes.DataFiles',
                'kivy.effects.scroll',
                'kivy.graphics.texture',
                'kivy.loader',
                'kivy.metrics',
                'kivy.uix.behaviors',
                'kivy.uix.checkbox',
                'kivy.uix.effectwidget',
                'kivy.uix.image',
                'kivy.uix.togglebutton',
                'kivy.uix.video',
                'kivy.uix.widget'
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='TouchCog',
          debug=False,
          strip=False,
          upx=True,
          console=True,
          icon=None) # Optional: Add an icon file

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               # This line for Kivy's binaries is still correct.
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               name='TouchCog')