# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['smc_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('logo-sfc.png', '.')],
    hiddenimports=[],
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
    name='Safe Mac Cleaner',
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
    icon=['icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Safe Mac Cleaner',
)
app = BUNDLE(
    coll,
    name='Safe Mac Cleaner.app',
    icon='icon.icns',
    bundle_identifier='com.parvenuprompting.safemaccleaner',
    info_plist={
        'CFBundleDisplayName': 'Safe Mac Cleaner',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'LSMinimumSystemVersion': '13.0',
        'NSHighResolutionCapable': True,
    },
)
