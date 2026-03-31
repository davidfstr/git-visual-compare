"""
GUI subprocess: reads diff data from a temp file, renders HTML, opens a window.
Invoked by cli.py as: python -m gvc._gui <tmpfile>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import webview

from gvc.app_api import AppApi
from gvc.diff_parser import is_large, large_sentinel, parse
from gvc.prefs import Prefs
from gvc.renderer import render
from gvc.window_manager import create_window, inject_geometry_tracker


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python -m gvc._gui <tmpfile>")

    tmp_path = Path(sys.argv[1])

    try:
        data = tmp_path.read_bytes()
    finally:
        # Clean up the temp file regardless of what happens next
        tmp_path.unlink(missing_ok=True)

    # First line is JSON metadata; remainder is raw diff bytes
    newline = data.index(b"\n")
    meta = json.loads(data[:newline])
    raw = data[newline + 1 :]

    title = meta.get("title", "gvc")

    prefs = Prefs.load()

    # Large diff guard
    large = is_large(raw)
    if large:
        sentinels = large_sentinel(raw)
        s = sentinels[0]
        html_doc = render(
            [],
            large=True,
            raw_size=s.raw_size,
            raw_lines=s.raw_lines,
            title=title,
        )
    else:
        file_diffs = parse(raw)
        html_doc = render(file_diffs, title=title)

    api = AppApi(prefs)
    window = create_window(html_doc, title, prefs, api)

    def on_loaded() -> None:
        inject_geometry_tracker(window)

    window.events.loaded += on_loaded

    webview.start(private_mode=False)


if __name__ == "__main__":
    main()
