# -*- mode: python ; coding: utf-8 -*-

from kivy_deps import sdl2, glew

block_cipher = None

# This is the standard, built-in way to include entire directories and files.
# No external 'pyinstaller-utils' or 'Tree' function is needed.
datas = [
    ('Screen.ini', '.'),
    ('Protocol', 'Protocol'),
    ('Classes', 'Classes')
]

a = Analysis(['C:\\Users\\MOUSETRAP-DAN\\desktop\\tccomp\\KivyMenuInterface.py'],
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
                'pandas'
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
          console=False,
          icon='') # Optional: Add an icon file

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               # This line for Kivy's binaries is still correct.
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               name='TouchCog')