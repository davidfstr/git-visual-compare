# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for building ./dist/gvc.app.
# Invoke via `poetry run python build_app.py`.

from importlib.metadata import version as _pkg_version
import os


_BUNDLE_ID = "net.dafoster.gvc"
_BUNDLE_NAME = "gvc"
_COPYRIGHT = "Copyright © 2026 David Foster"
_VERSION = _pkg_version("gvc")

a = Analysis(
    ["src/gvc/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[("src/gvc/assets", "gvc/assets")],
    hiddenimports=[
        "gvc.cli",
        "gvc.gui",
        "gvc.app_api",
        "gvc.diff_parser",
        "gvc.ipc",
        "gvc.prefs",
        "gvc.renderer",
        "gvc.window_manager",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=(os.environ.get("GVC_NOARCHIVE") == "1"),
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="gvc",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="gvc",
)
app = BUNDLE(
    coll,
    name="gvc.app",
    icon="build/icon.icns",
    bundle_identifier=_BUNDLE_ID,
    version=_VERSION,
    # NOTE: Duplicated in gvc.spec and _configure_app_identity() and stub_app.py
    info_plist={
        "CFBundleDisplayName": _BUNDLE_NAME,
        "CFBundleName": _BUNDLE_NAME,
        "CFBundleShortVersionString": _VERSION,
        "CFBundleVersion": _VERSION,
        "LSUIElement": False,
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": _COPYRIGHT,
    },
)
