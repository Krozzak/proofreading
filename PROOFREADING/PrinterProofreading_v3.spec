# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Trouver le chemin de tkinterdnd2
import tkinterdnd2
tkdnd_path = os.path.dirname(tkinterdnd2.__file__)

# Collecter tous les modules de skimage
skimage_datas, skimage_binaries, skimage_hiddenimports = collect_all('skimage')

a = Analysis(
    ['proofreading_v2.py'],
    pathex=[],
    binaries=skimage_binaries,
    datas=[(tkdnd_path, 'tkinterdnd2')] + skimage_datas,
    hiddenimports=['tkinterdnd2'] + skimage_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PrinterProofreading',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon/proofreader_icon.ico'],
)
