"""
gvc — Git Visual Compare
Entry point: parse arguments, run git diff, render HTML, open a window.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _build_title(args: list[str]) -> str:
    """Construct a concise window title from the git diff arguments."""
    if not args:
        return "gvc: working tree"
    label = " ".join(args)
    if len(label) > 80:
        label = label[:77] + "..."
    return f"gvc: {label}"


def main() -> None:
    args = sys.argv[1:]

    # Build the git diff command.
    # -M enables rename detection with git's default 50% threshold.
    # User arguments are passed through verbatim.
    cmd = ["git", "diff", "-M"] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
        )
    except FileNotFoundError:
        sys.stderr.write("gvc: 'git' not found. Is git installed and in PATH?\n")
        sys.exit(1)

    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        sys.exit(result.returncode)

    raw = result.stdout

    # ------------------------------------------------------------------
    # Late imports: keep startup fast for error paths above
    # ------------------------------------------------------------------
    import webview  # noqa: PLC0415

    from gvc.app_api import AppApi
    from gvc.diff_parser import is_large, large_sentinel, parse
    from gvc.prefs import Prefs
    from gvc.renderer import render
    from gvc.window_manager import create_window, inject_geometry_tracker

    prefs = Prefs.load()

    # Large diff guard
    large = is_large(raw)
    if large:
        file_diffs = large_sentinel(raw)
        sentinel = file_diffs[0]
        html_doc = render(
            [],
            large=True,
            raw_size=sentinel.raw_size,
            raw_lines=sentinel.raw_lines,
            title=_build_title(args),
        )
    else:
        file_diffs = parse(raw)
        html_doc = render(file_diffs, title=_build_title(args))

    api = AppApi(prefs)
    title = _build_title(args)

    window = create_window(html_doc, title, prefs, api)

    def on_loaded() -> None:
        inject_geometry_tracker(window)

    window.events.loaded += on_loaded

    webview.start(private_mode=False)


if __name__ == "__main__":
    main()
