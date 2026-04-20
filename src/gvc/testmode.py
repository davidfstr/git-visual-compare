"""
Testing mode. Presents a test-only API to control gvc from automated tests.

Active only when GVC_TEST_MODE is set.
"""

from collections.abc import Callable
from contextlib import closing
from gvc import paths
import json
import os
from pathlib import Path
import socket
import threading
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gvc.app_api import AppApi


def start(api: AppApi) -> Callable[[], None]:
    """
    Starts testing mode, returning a function to stop testing mode.
    """
    runtime_dir = paths.user_runtime_dir()
    pid_path = runtime_dir / "gvc.pid"
    sock_path = runtime_dir / "gui-test.sock"

    # Create PID file
    pid_path.write_text(str(os.getpid()))

    # Create and listen on gui-test.sock control socket
    threading.Thread(
        target=_open_test_socket_and_handle_requests,
        args=(sock_path, api),
        daemon=True,
    ).start()

    def close() -> None:
        sock_path.unlink(missing_ok=True)
        pid_path.unlink(missing_ok=True)
    return close


def _open_test_socket_and_handle_requests(sock_path: Path, api: AppApi) -> None:
    try:
        sock_path.unlink(missing_ok=True)
        with closing(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)) as srv:
            srv.bind(str(sock_path))
            srv.listen(5)
            srv.settimeout(1.0)
            while True:
                try:
                    conn, _ = srv.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                try:
                    _handle_request(conn, api)
                except Exception:
                    traceback.print_exc()
    finally:
        sock_path.unlink(missing_ok=True)


def _handle_request(conn: socket.socket, api: AppApi) -> None:
    with closing(conn):
        chunks: list[bytes] = []
        while chunk := conn.recv(4096):
            chunks.append(chunk)
        req = json.loads(b"".join(chunks).decode("utf-8").strip())
        method = req.get("method")

        if method == "ping":
            from importlib.metadata import version as _version
            result: object = {"pid": os.getpid(), "version": _version("gvc")}
        elif method == "list_windows":
            result = [
                {"id": w.uid, "title": w.title}
                for w in api.open_windows()
            ]
        elif method == "eval_js":
            window_id = req.get("window_id")
            src = req.get("src")
            window = next(
                (w for w in api.open_windows() if w.uid == window_id),
                None,
            )
            if window is None:
                result = {"error": f"no window: {window_id!r}"}
            elif not isinstance(src, str):
                result = {"error": f"src must be str, got {type(src).__name__}"}
            else:
                try:
                    # pywebview marshals evaluate_js to the Cocoa main thread
                    # and blocks until the JS returns. The JS itself wraps its
                    # return value as {ok: ...} or {error: ...}.
                    result = window.evaluate_js(src)
                except Exception as e:
                    result = {"error": f"evaluate_js raised: {e}"}
        else:
            result = {"error": f"unknown method: {method!r}"}

        conn.sendall((json.dumps(result) + "\n").encode("utf-8"))
