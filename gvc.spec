# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for building ./dist/gvc.app.
# Invoke via `poetry run python build_app.py`.

from importlib.metadata import version as _pkg_version


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
    noarchive=False,
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
    bundle_identifier="net.dafoster.gvc",
    version=_VERSION,
    # NOTE: Duplicated in gvc.spec and _configure_app_identity()
    info_plist={
        "CFBundleName": "gvc",
        "CFBundleDisplayName": "gvc",
        "CFBundleShortVersionString": _VERSION,
        "CFBundleVersion": _VERSION,
        "NSHumanReadableCopyright": "Copyright © 2026 David Foster",
        "NSHighResolutionCapable": True,
        "LSUIElement": False,
    },
)
