"""
Builds ./dist/gvc.app via PyInstaller.

Run with: `poetry run python build_app.py`
"""

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
    _build_icns()

    shutil.rmtree(_ROOT / "dist", ignore_errors=True)
    subprocess.run(
        ["pyinstaller", "--clean", "--noconfirm", str(_SPEC)],
        cwd=_ROOT,
        check=True,
    )
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


if __name__ == "__main__":
    sys.exit(main())
