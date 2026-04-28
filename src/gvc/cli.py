"""
gvc -- Git Visual Compare

Entry point:
- Runs git diff
- Hand offs diff data to the persistent GUI server process
"""

from collections.abc import Iterator
from contextlib import contextmanager
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import time


# ------------------------------------------------------------------------------
# Main

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
        # No GUI server running. Launch one.
        bundle_exe = _enclosing_app_executable()
        if bundle_exe is not None:
            # Already running inside an .app bundle. Launch GUI from the same bundle.
            subprocess.Popen(
                [str(bundle_exe), "--gui-server", str(request_filepath)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif not os.environ.get("GVC_NO_STUB_APP"):
            # Locate/create stub .app
            _launch_via_stub_app(request_filepath)
        else:
            # Launch the GUI from source
            # NOTE: Because the GUI lacks an enclosing .app when launched in
            #       this way, its Dock icon will NOT say "gvc"
            subprocess.Popen(
                [sys.executable, "-m", "gvc.gui", str(request_filepath)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def _launch_via_stub_app(request_filepath: Path) -> None:
    """
    Generate (if needed) and launch the stub .app via `open -a`.
    
    Captures timing and `open` output to <log_dir>/cli.log.
    """
    from gvc import paths, stub_app

    log_dir = paths.user_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "cli.log").open("w", buffering=1) as cli_log:        
        def _log(message: str) -> None:
            print(
                f"[{dt.datetime.now().isoformat(timespec='milliseconds')}] {message}",
                file=cli_log,
                flush=True,
            )

        _log(f"cli pid={os.getpid()} launching stub")

        with _timed() as duration:
            app_path = stub_app.ensure_exists()
        _log(f"stub_app.ensure_exists() -> {app_path} ({duration.value:.2f}s)")

        with _timed() as duration:
            result = subprocess.run(
                [
                    "open",
                    "--new",
                    # Register the .app as the bundle identity before the
                    # process starts. This registration is what makes the
                    # Dock icon show "gvc" (from the .app) rather than "Python"
                    # (from the "python" process).
                    "-a", str(app_path),
                    "--args", "--gui-server", str(request_filepath),
                ],
                stdout=cli_log,
                stderr=cli_log,
                check=False,
            )
        _log(f"open exit={result.returncode} ({duration.value:.2f}s)")


# ------------------------------------------------------------------------------
# Utility

def _enclosing_app_executable() -> Path | None:
    """If running inside an .app bundle, return its Contents/MacOS/gvc path."""
    for parent in Path(sys.executable).parents:
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


@contextmanager
def _timed() -> Iterator[DurationCell]:
    """
    Context which measures how long it takes to execute.
    
    Example:
        with _timed() as duration:
            ...
        _log(f"did the thing ({duration.value:.2f}s)")
    """
    delta_cell = DurationCell()
    t0 = time.monotonic()
    yield delta_cell
    delta_cell.value = time.monotonic() - t0


class DurationCell:
    """Holds a duration value (a timedelta). Immutable after initialization."""
    _value: dt.timedelta | None
    
    def __init__(self) -> None:
        self._value = None
    
    def _set_value(self, value: dt.timedelta) -> None:
        if self._value is not None:
            raise ValueError('Duration already set')
        self._value = value
    def _get_value(self) -> dt.timedelta:
        if self._value is None:
            raise ValueError('Duration not yet computed')
        return self._value
    value = property(_get_value, _set_value)


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
