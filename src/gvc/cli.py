"""
gvc -- Git Visual Compare
Entry point: parse arguments, run git diff, hand off to GUI subprocess.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
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
    cmd = ["git", "diff", "-M"] + args

    try:
        result = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError:
        sys.stderr.write("gvc: 'git' not found. Is git installed and in PATH?\n")
        sys.exit(1)

    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        sys.exit(result.returncode)

    raw = result.stdout

    # Write diff data + metadata to a temp file for the GUI subprocess.
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".gvc", mode="wb"
    ) as tmp:
        # Header line: JSON metadata, then a newline, then raw diff bytes
        meta = json.dumps({"title": _build_title(args)})
        tmp.write(meta.encode("utf-8"))
        tmp.write(b"\n")
        tmp.write(raw)
        tmp_path = tmp.name

    # Launch the GUI in a detached subprocess and exit immediately.
    subprocess.Popen(
        [sys.executable, "-m", "gvc._gui", tmp_path],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    main()
