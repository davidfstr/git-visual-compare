"""
Testing mode. Presents a test-only API to control gvc from automated tests.

Active only when GVC_TEST_MODE is set.
"""

import AppKit
from collections.abc import Callable
from contextlib import closing
from Foundation import NSOperationQueue
from gvc import paths
import json
import os
from pathlib import Path
import socket
import threading
import time
import traceback
from typing import TYPE_CHECKING
import webview
from webview.platforms.cocoa import BrowserView

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
        elif method == "set_appearance":
            window_id = req.get("window_id")
            appearance = req.get("appearance")
            window = next(
                (w for w in api.open_windows() if w.uid == window_id),
                None,
            )
            if window is None:
                result = {"error": f"no window: {window_id!r}"}
            elif appearance not in ("light", "dark"):
                result = {"error": f"appearance must be 'light' or 'dark', got {appearance!r}"}
            else:
                try:
                    _set_window_appearance(window, appearance)
                    result = {"ok": None}
                except Exception as e:
                    result = {"error": str(e)}
        else:
            result = {"error": f"unknown method: {method!r}"}

        conn.sendall((json.dumps(result) + "\n").encode("utf-8"))


def _set_window_appearance(window: webview.Window, appearance: str) -> None:
    """Forces `window` into light or dark appearance; safe to call from a background thread."""
    # BrowserView for non-master windows is created via AppHelper.callAfter(),
    # which fires asynchronously on the Cocoa run loop.  Poll until it appears.
    deadline = time.monotonic() + 5.0  # capture
    while True:
        browser = BrowserView.instances.get(window.uid)
        if browser is not None:
            break
        if time.monotonic() > deadline:
            keys = list(BrowserView.instances.keys())
            raise RuntimeError(
                f"no BrowserView for window uid {window.uid!r} after 5s; "
                f"BrowserView.instances keys={keys!r}"
            )
        time.sleep(0.05)

    appearance_name = (
        AppKit.NSAppearanceNameDarkAqua
        if appearance == "dark"
        else AppKit.NSAppearanceNameAqua
    )

    done = threading.Event()
    error: BaseException | None = None
    def _block() -> None:
        nonlocal error
        try:
            ns_appearance = AppKit.NSAppearance.appearanceNamed_(appearance_name)
            browser.webview.setAppearance_(ns_appearance)
        except BaseException as e:
            error = e
        finally:
            done.set()
    NSOperationQueue.mainQueue().addOperationWithBlock_(_block)
    done.wait(timeout=5.0)
    if error is not None:
        raise error
