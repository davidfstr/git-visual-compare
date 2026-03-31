"""
gvc -- Git Visual Compare
Entry point: run git diff, hand off diff data to the persistent GUI process.
"""

from __future__ import annotations

import subprocess
import sys


def _build_title(args: list[str]) -> str:
    if not args:
        return "gvc: working tree"
    label = " ".join(args)
    if len(label) > 80:
        label = label[:77] + "..."
    return f"gvc: {label}"


def main() -> None:
    args = sys.argv[1:]

    cmd = ["git", "diff", "-M"] + args
    try:
        result = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError:
        sys.stderr.write("gvc: 'git' not found. Is git installed and in PATH?\n")
        sys.exit(1)

    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        sys.exit(result.returncode)

    from gvc._ipc import gui_socket_path, try_send, write_tmp_file

    sock_path = gui_socket_path()
    tmp_path = write_tmp_file(result.stdout, _build_title(args))

    if try_send(sock_path, tmp_path):
        # Existing GUI server accepted the request — we're done.
        return

    # No server running.  Launch one; it will open the first window from argv.
    subprocess.Popen(
        [sys.executable, "-m", "gvc._gui", str(tmp_path)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    main()
