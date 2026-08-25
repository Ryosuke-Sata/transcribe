# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
)


# ==========================================
# Whisperのデータファイル
# ==========================================

datas = collect_data_files(
    "whisper"
)


# ==========================================
# tiktokenの動的import
# ==========================================

hiddenimports = collect_submodules(
    "tiktoken_ext"
)


# ==========================================
# Analysis
# ==========================================

a = Analysis(
    [
        "transcribe.py",
    ],
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


pyz = PYZ(
    a.pure
)


# ==========================================
# EXE
#
# 最初の動作確認ではconsole=Trueにする。
# エラーが出た場合に内容を確認できるため。
# ==========================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Transcribe",
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


# ==========================================
# onedir
# ==========================================

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Transcribe",
)