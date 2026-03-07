# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('assets/*', 'assets'),
    ('prompts.json', '.'),
    ('theme_colors.json', '.'),
    ('документация/*', 'документация'),
]

# Добавляем customtkinter если он нужен (обычно хуки сами справляются, но для верности)
import customtkinter
import os
ctk_path = os.path.dirname(customtkinter.__file__)
added_files.append((ctk_path, 'customtkinter'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Wordy',
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
    icon=['assets\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Wordy',
)
