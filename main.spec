# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

sys.path.insert(0, os.path.abspath('.'))
from c_bridge import ensure_c_engines_built

# Ensure all 3 C math binaries (engine.exe, matrix_engine.exe, numlab_engine.exe) are built before packaging
ensure_c_engines_built(force=True)

hiddenimports = [
    'config',
    'c_bridge',
    'widgets',
    'home_tab',
    'root_tab',
    'matrix_tab',
    'errors_tab',
    'optimization_tab',
    'interpolation_tab',
    'integration_tab',
    'ode_tab',
    'license_manager',
    'license_gate',
]
hiddenimports += collect_submodules('matplotlib')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('build', 'build'), ('app_icon.ico', '.')],
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
    a.binaries,
    a.datas,
    [],
    name='Numerical_Analysis_Suite',
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
    icon=['app_icon.ico'],
)
