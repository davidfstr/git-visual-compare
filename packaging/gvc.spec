# PyInstaller spec for gvc.app (macOS)
# Usage: pyinstaller packaging/gvc.spec

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    [str(Path("src/gvc/__main__.py").resolve())],
    pathex=[str(Path("src").resolve())],
    binaries=[],
    datas=[
        ("src/gvc/assets", "gvc/assets"),
    ],
    hiddenimports=[
        # pywebview Cocoa backend
        "webview",
        "webview.platforms.cocoa",
        # PyObjC frameworks used by pywebview
        "objc",
        "Foundation",
        "AppKit",
        "WebKit",
        "CoreFoundation",
        # platformdirs
        "platformdirs",
        "platformdirs.macos",
    ],
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
    name="gvc",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=str(Path("packaging/entitlements.plist").resolve()),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="gvc",
)

app = BUNDLE(
    coll,
    name="gvc.app",
    icon=None,
    bundle_identifier="com.gvc.gvc",
    info_plist={
        # Allow dark mode (do not force Aqua/light mode)
        "NSRequiresAquaSystemAppearance": False,
        # Agent app: no Dock icon, no menu bar (invoked from terminal)
        "LSUIElement": True,
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "NSHumanReadableCopyright": "",
        # Allow reading files (needed if we ever support -C /path flag)
        "NSDocumentsFolderUsageDescription": "gvc reads git repositories.",
    },
)
