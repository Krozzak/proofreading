# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules

datas = [('templates', 'templates'), ('static', 'static')]
hiddenimports = ['flask', 'werkzeug', 'jinja2', 'fitz', 'PIL', 'numpy', 'skimage', 'skimage.metrics', 'skimage.metrics._structural_similarity', 'scipy', 'scipy.ndimage']
datas += collect_data_files('skimage')
hiddenimports += collect_submodules('skimage')
hiddenimports += collect_submodules('scipy')


a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='LorealProofreading',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LorealProofreading',
)
