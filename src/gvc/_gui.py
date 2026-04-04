"""
Persistent GUI server process.
- Binds a Unix domain socket immediately on startup (minimises the race
  window during which a second CLI invocation might launch a second server).
- Opens the first diff window from the temp file path in argv[1].
- Listens on the socket for subsequent window requests (each message is a
  temp file path sent by cli.py).
- Stays alive after all windows are closed (standard macOS document-app
  behaviour) so the next request opens instantly.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import platformdirs
import socket
import sys
import threading
import traceback


def _open_window(raw: bytes, title: str, api, prefs_loader) -> None:
    """Parse diff bytes and open a new diff window. Thread-safe."""
    from gvc.diff_parser import is_large, large_sentinel, parse
    from gvc.renderer import render
    from gvc.window_manager import create_window

    prefs = prefs_loader()

    large = is_large(raw)
    if large:
        s = large_sentinel(raw)[0]
        html_doc = render([], large=True, raw_size=s.raw_size, raw_lines=s.raw_lines)
    else:
        html_doc = render(parse(raw))

    create_window(html_doc, title, prefs, api)


def _socket_listener(server_sock: socket.socket, api, prefs_loader) -> None:
    """
    Background thread: accept incoming connections from cli.py.
    Each connection sends a single temp file path (UTF-8, no framing needed
    since the connection is closed after sending).
    """
    from gvc._ipc import GuiRequest

    server_sock.settimeout(1.0)

    while True:
        try:
            conn, _ = server_sock.accept()
        except socket.timeout:
            continue
        except OSError:
            # Socket closed — server shutting down
            break

        try:
            chunks: list[bytes] = []
            while chunk := conn.recv(4096):
                chunks.append(chunk)
            conn.close()
            tmp_path = Path(b"".join(chunks).decode("utf-8").strip())
            req = GuiRequest.read_from(tmp_path)
            _open_window(req.diff_bytes, req.title, api, prefs_loader)
        except Exception:
            # Never crash the listener
            traceback.print_exc()


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python -m gvc._gui <tmpfile>")
    
    # Redirect stderr to a persistent log file so tracebacks are observable.
    log_dirpath = Path(platformdirs.user_log_dir("gvc"))
    log_dirpath.mkdir(parents=True, exist_ok=True)
    log_filepath = log_dirpath / "gvc.log"
    # NOTE: Replace log whenever process restarts, to prevent growing without bound
    sys.stderr = log_filepath.open("w", buffering=1)
    print(f"gvc started {dt.datetime.now().isoformat(timespec='seconds')}", file=sys.stderr, flush=True)

    # ------------------------------------------------------------------
    # Bind the socket FIRST — before importing webview — so that a second
    # concurrent CLI invocation can find the socket as soon as possible.
    # ------------------------------------------------------------------
    from gvc._ipc import gui_socket_path

    sock_path = gui_socket_path()
    server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_path.unlink(missing_ok=True)
    server_sock.bind(str(sock_path))
    server_sock.listen(5)

    # ------------------------------------------------------------------
    # Now load the heavier GUI dependencies
    # ------------------------------------------------------------------
    import webview  # noqa: PLC0415

    from gvc.app_api import AppApi
    from gvc.prefs import Prefs
    from gvc.window_manager import _disable_automatic_tabbing

    # Disable macOS automatic window tabbing before creating any windows,
    # otherwise every window gets a tab bar that duplicates the title.
    _disable_automatic_tabbing()

    # Single shared AppApi for all windows in this process
    api = AppApi(Prefs.load())

    # Start socket listener thread (daemon: dies with the process)
    t = threading.Thread(
        target=_socket_listener,
        args=(server_sock, api, Prefs.load),
        daemon=True,
    )
    t.start()

    # Hidden sentinel window — keeps the Cocoa event loop alive after all
    # visible diff windows are closed (standard macOS document-app behaviour).
    webview.create_window("gvc", html="", hidden=True)

    # Open the first window from the temp file path in argv
    from gvc._ipc import GuiRequest

    req = GuiRequest.read_from(Path(sys.argv[1]))
    _open_window(req.diff_bytes, req.title, api, Prefs.load)

    # Run the Cocoa event loop; returns only on Cmd+Q / webview.stop()
    webview.start(private_mode=False)

    # Cleanup
    server_sock.close()
    sock_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
