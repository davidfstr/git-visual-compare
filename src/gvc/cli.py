"""
gvc -- Git Visual Compare

Entry point:
- Runs git diff
- Hand offs diff data to the persistent GUI server process
"""

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

    cmd = ["git", "diff", "--find-renames"] + args
    try:
        result = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError:
        sys.stderr.write("gvc: 'git' not found. Is git installed and in PATH?\n")
        sys.exit(1)
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        sys.exit(result.returncode)

    from gvc._ipc import GuiRequest, gui_socket_path, try_send

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
        # No GUI server running. Launch one, with the initial request.
        subprocess.Popen(
            [sys.executable, "-m", "gvc._gui", str(request_filepath)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    main()
