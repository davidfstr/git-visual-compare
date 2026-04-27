"""
Builds ./dist/gvc.app via PyInstaller.

Run with: `poetry run python build_app.py`

Pass -e to build an editable app whose Python source is loaded live from
src/gvc/ (no rebuild needed after editing .py files or assets):
  `poetry run python build_app.py -e`
"""

import argparse
from gvc.stub_app import build_icns
import os
from pathlib import Path
import shutil
import subprocess


_ROOT = Path(__file__).resolve().parent
_ICON_ICNS = _ROOT / "build/icon.icns"
_SPEC = _ROOT / "gvc.spec"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build gvc.app via PyInstaller.")
    parser.add_argument(
        "-e", "--editable",
        action="store_true",
        help="Build an editable app that loads Python source live from src/gvc/",
    )
    args = parser.parse_args()

    # Generate build/icon.icns from the source PNG
    _ICON_ICNS.parent.mkdir(parents=True, exist_ok=True)
    build_icns(_ICON_ICNS)

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
