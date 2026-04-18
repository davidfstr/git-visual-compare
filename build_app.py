"""
Builds ./dist/gvc.app via PyInstaller.

Run with: `poetry run python build_app.py`

Pass -e to build an editable app whose Python source is loaded live from
src/gvc/ (no rebuild needed after editing .py files or assets):
  `poetry run python build_app.py -e`
"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


_ROOT = Path(__file__).resolve().parent
_ICON_PNG = _ROOT / "src/gvc/assets/icon.png"
_ICONSET = _ROOT / "build/icon.iconset"
_ICON_ICNS = _ROOT / "build/icon.icns"
_SPEC = _ROOT / "gvc.spec"

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build gvc.app via PyInstaller.")
    parser.add_argument(
        "-e", "--editable",
        action="store_true",
        help="Build an editable app that loads Python source live from src/gvc/",
    )
    args = parser.parse_args()

    _build_icns()

    # Rebuild dist/gvc.app
    shutil.rmtree(_ROOT / "dist", ignore_errors=True)
    subprocess.run(
        ["pyinstaller", "--clean", "--noconfirm", str(_SPEC)],
        cwd=_ROOT,
        env={
            **os.environ,
            **(
                {"GVC_NOARCHIVE": "1"}
                if args.editable else {}
            )
        },
        check=True,
    )
    if args.editable:
        _symlink_editable_app_to_source_tree()

    print(f"\nBuilt: {_ROOT / 'dist' / 'gvc.app'}")


def _build_icns() -> None:
    """Generates build/icon.icns from the source PNG using sips + iconutil."""
    if _ICONSET.exists():
        shutil.rmtree(_ICONSET)
    _ICONSET.mkdir(parents=True)

    for size, filename in _ICON_SIZES:
        subprocess.run(
            ["sips", "-z", str(size), str(size),
             str(_ICON_PNG), "--out", str(_ICONSET / filename)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    subprocess.run(
        ["iconutil", "-c", "icns", str(_ICONSET), "-o", str(_ICON_ICNS)],
        check=True,
    )


def _symlink_editable_app_to_source_tree() -> None:
    """
    Replaces parts of the bundled gvc .app with symlinks to live gvc .py files.
    """
    # Preconditions:
    # - A PyInstaller-managed symlink exists from
    #     Contents/Frameworks/gvc
    #   to
    #     Contents/Resources/gvc/
    # - Loose .pyc files are placed by --noarchive into:
    #     Contents/Resources/gvc/
    # 
    # Symlink
    #     Contents/Resources/gvc/
    # to
    #     src/gvc/
    # so that the app imports live .py source files.
    # 
    # Then no app rebuild is required to reflect edits to the source files.
    bundle_gvc = _ROOT / "dist/gvc.app/Contents/Resources/gvc"
    src_gvc = _ROOT / "src/gvc"
    shutil.rmtree(bundle_gvc)
    bundle_gvc.symlink_to(src_gvc)
    print(f"Editable: {bundle_gvc} -> {src_gvc}")


if __name__ == "__main__":
    main()
