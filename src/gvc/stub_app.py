"""Generates ~/Applications/gvc.app as a lightweight stub .app bundle."""

from importlib.metadata import version as _pkg_version
from importlib.resources import as_file, files
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile


_BUNDLE_ID = "net.dafoster.gvc"
_BUNDLE_NAME = "gvc"
_COPYRIGHT = "Copyright © 2026 David Foster"
_VERSION = _pkg_version("gvc")

# All icon sizes that Finder icons use.
# We produce all these sizes when generating the .icns icon set for GVC to
# avoid blurry downscaling in the macOS Dock and in Finder's Get Info panel.
_ICON_SIZES = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]


def ensure_exists() -> Path:
    """
    Ensures a gvc.app stub bundle is present and up to date.
    Returns the path to the .app bundle (for launching via `open -a`).

    If gvc.app already exists in /Applications, that is returned as-is.
    Otherwise ensures ~/Applications/gvc.app is present and current,
    regenerating it when the gvc version or Python interpreter has changed.

    Respects GVC_STUB_APP_DIR: if set, places the stub there instead of
    ~/Applications.
    """
    system_app = _system_bundle_app()
    if system_app is not None:
        return system_app

    stub_app_dir = os.environ.get("GVC_STUB_APP_DIR")
    if stub_app_dir:
        app_path = Path(stub_app_dir) / "gvc.app"
    else:
        app_path = Path.home() / "Applications" / "gvc.app"

    if not _is_current(app_path):
        _generate(app_path)

    return app_path


def _system_bundle_app() -> Path | None:
    """Returns /Applications/gvc.app if it exists."""
    app = Path("/Applications/gvc.app")
    return app if app.exists() else None


def _is_current(app_path: Path) -> bool:
    """True if the stub bundle matches the running gvc version and sys.executable."""
    plist_path = app_path / "Contents" / "Info.plist"
    if not plist_path.exists():
        return False
    
    # Calculate .app bundle's signature
    try:
        with plist_path.open("rb") as f:
            info = plistlib.load(f)
    except (OSError, plistlib.InvalidFileException):
        return False
    else:
        bundle_signature = (
            info.get("CFBundleShortVersionString"),
            info.get("GVCPythonExecutable")
        )
    
    # Calculate this gvc process's signature
    my_signature = (
        _pkg_version("gvc"),
        sys.executable
    )
    
    return bundle_signature == my_signature


def _generate(app_path: Path) -> None:
    """Writes (or overwrites) the stub .app bundle at app_path."""
    if app_path.exists():
        shutil.rmtree(app_path)

    contents = app_path / "Contents"
    macos_dir = contents / "MacOS"
    resources_dir = contents / "Resources"
    macos_dir.mkdir(parents=True)
    resources_dir.mkdir(parents=True)

    # NOTE: Duplicated in gvc.spec and _configure_app_identity() and build_app.py
    info: dict[str, object] = {
        "CFBundleDisplayName": _BUNDLE_NAME,
        "CFBundleExecutable": _BUNDLE_NAME,
        "CFBundleIconFile": "icon.icns",
        "CFBundleIdentifier": _BUNDLE_ID,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": _BUNDLE_NAME,
        "CFBundlePackageType": "APPL",
        # Part of stub app's "currentness" identity
        "CFBundleShortVersionString": _VERSION,
        "CFBundleVersion": _VERSION,
        # Part of stub app's "currentness" identity
        "GVCPythonExecutable": sys.executable,
        "LSUIElement": False,
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": _COPYRIGHT,
    }
    with (contents / "Info.plist").open("wb") as f:
        plistlib.dump(info, f)

    exe_path = macos_dir / _BUNDLE_NAME
    exe_path.write_text(
        f"#!/bin/sh\nexec {shlex.quote(sys.executable)} -m gvc \"$@\"\n",
        encoding="utf-8",
    )
    exe_path.chmod(exe_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    build_icns(resources_dir / "icon.icns")


def build_icns(dest_icns: Path) -> None:
    """Generates an .icns file at dest_icns from the bundled icon.png."""
    icon_resource = files("gvc").joinpath("assets/icon.png")
    with as_file(icon_resource) as icon_png:
        with tempfile.TemporaryDirectory() as tmp_dir:
            iconset_dir = Path(tmp_dir) / "icon.iconset"
            iconset_dir.mkdir()
            for size, filename in _ICON_SIZES:
                subprocess.run(
                    [
                        "sips", "-z", str(size), str(size),
                        str(icon_png), "--out", str(iconset_dir / filename),
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                )
            subprocess.run(
                ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(dest_icns)],
                check=True,
            )
