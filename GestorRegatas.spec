# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_maraton.py'],
    pathex=[],
    binaries=[],
    datas=[('logo.png', '.'), ('regatas_maraton.db', '.'), ('/home/eesse/PROYECTOS TERMINADOS/GestorRegatasMaraton (ultimo final c.logo club)/venv/lib/python3.13/site-packages/PySide6/Qt/plugins', 'PySide6/Qt/plugins'), ('/home/eesse/PROYECTOS TERMINADOS/GestorRegatasMaraton (ultimo final c.logo club)/venv/lib/python3.13/site-packages/PySide6/Qt/lib', 'PySide6/Qt/lib')],
    hiddenimports=['shiboken6'],
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
    name='GestorRegatas',
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
    name='GestorRegatas',
)
