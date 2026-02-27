# -*- mode: python ; coding: utf-8 -*-
# Debug version with console window and onefile mode

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=[],
    datas=[
        ('../ui', 'ui'),
        ('../assets', 'assets'),  # Include all assets folder
        ('../modules', 'modules'),
        ('../tools/ffmpeg/bin', 'tools/ffmpeg/bin'),  # Include FFmpeg and FFprobe
        ('../tools/exiftool', 'tools/exiftool'),  # Include ExifTool and its dependencies
    ],
    hiddenimports=[
        'modules.downloader',
        'modules.config',
        'modules.memories_selector',
        'modules.paths',
        'modules.fusion',
        'modules.metadata',
        'modules.download_manager',
        'modules.download_worker',
        'modules.speed_tracker',
        'modules.state',
        'modules.zip_handler',
        'modules.json_loader',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SnapLoad-Debug',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SnapLoad-Debug'
)
