"""
gvc -- Git Visual Compare

Entry point:
- Runs git diff
- Hand offs diff data to the persistent GUI server process
"""

from pathlib import Path
import subprocess
import sys


def main() -> None:
    args = sys.argv[1:]
    
    # If invoked as `--gui-server <request_file>` by another gvc process,
    # act as the persistent GUI server instead of as the CLI.
    if args and args[0] == "--gui-server":
        from gvc.gui import main as gui_main
        sys.argv = [sys.argv[0]] + args[1:]
        gui_main()
        return

    cmd = ["git", "diff", "--find-renames"] + args
    try:
        result = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError:
        sys.stderr.write("gvc: 'git' not found. Is git installed and in PATH?\n")
        sys.exit(1)
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        sys.exit(result.returncode)

    from gvc.ipc import gui_socket_path, GuiRequest, try_send

    req = GuiRequest(
        title=_build_title(args),
        diff_bytes=result.stdout,
    )
    request_filepath = req.write_to_temp_file()
    
    # Create/notify GUI server of the request.
    # The GUI server will clean up the request file after processing it.
    sock_path = gui_socket_path()
    if try_send(sock_path, request_filepath):
        # Existing GUI server accepted the request
        pass
    else:
        # No GUI server running. Launch one:
        # - If this cli.py itself lives inside a distributed .app bundle, launch it.
        # - Otherwise fall back to an unbundled `python -m gvc.gui`.
        bundle_exe = _enclosing_app_executable()
        if bundle_exe is not None:
            argv = [str(bundle_exe), "--gui-server", str(request_filepath)]
        else:
            argv = [sys.executable, "-m", "gvc.gui", str(request_filepath)]
        subprocess.Popen(
            argv,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def _enclosing_app_executable() -> Path | None:
    """If cli.py lives inside a .app bundle, return its Contents/MacOS/gvc path."""
    for parent in Path(__file__).resolve().parents:
        if parent.suffix == ".app":
            return parent / "Contents" / "MacOS" / "gvc"
    return None


def _build_title(args: list[str]) -> str:
    if not args:
        return "gvc: working tree"
    label = " ".join(args)
    if len(label) > 80:
        label = label[:77] + "..."
    return f"gvc: {label}"


if __name__ == "__main__":
    main()
