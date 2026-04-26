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
import sys
import threading
import time
import traceback
from typing import TYPE_CHECKING, cast
import webview
from webview.platforms.cocoa import BrowserView

if TYPE_CHECKING:
    from gvc.app_api import AppApi


# ------------------------------------------------------------------------------
# Start

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
            _log_test_socket(f"listening on {sock_path}")
            while True:
                try:
                    conn, _ = srv.accept()
                except socket.timeout:
                    continue
                except OSError:
                    _log_test_socket("listener stopping due to socket close")
                    break
                try:
                    _log_test_socket("accepted connection")
                    _handle_request(conn, api)
                except Exception:
                    _log_test_socket("request handler raised; traceback follows")
                    traceback.print_exc()
    finally:
        _log_test_socket("removing socket path")
        sock_path.unlink(missing_ok=True)


# ------------------------------------------------------------------------------
# Handle Request

def _handle_request(conn: socket.socket, api: AppApi) -> None:
    started_at = time.monotonic()  # capture
    with closing(conn):
        # Force the conn into Python's timeout mode so recv() goes through
        # poll()/select() before the syscall. Without this (blocking mode,
        # timeout=None), accepted AF_UNIX conns on macOS + Python 3.14
        # intermittently don't wake up on peer writes, and recv() hangs
        # indefinitely with zero bytes delivered even though the peer's
        # sendall() has returned. The 3s bound keeps the handler from being
        # trapped forever if that recurs.
        # NOTE: Duplicated in _handle_request (testmode.py) and receive (ipc.py)
        conn.settimeout(3.0)
        
        chunks: list[bytes] = []
        try:
            while chunk := conn.recv(4096):
                chunks.append(chunk)
        except TimeoutError:
            _log_test_socket(
                f"conn.recv timed out with "
                f"{sum(len(c) for c in chunks)} bytes received"
            )
            return
        raw = b"".join(chunks)
        _log_test_socket(f"received {len(raw)} bytes")
        req = json.loads(raw.decode("utf-8").strip())
        method = req.get("method")
        _log_test_socket(f"dispatching method={method!r}")

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
                    _log_test_socket(
                        f"eval_js begin window_id={window_id!r} src_chars={len(src)}"
                    )
                    result = window.evaluate_js(src)
                    _log_test_socket("eval_js end")
                except Exception as e:
                    _log_test_socket(f"eval_js raised {type(e).__name__}: {e}")
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
                except Exception as e:
                    result = {"error": str(e)}
                else:
                    result = {"ok": None}
        elif method == "select_menuitem":
            shortcut = req.get("shortcut")
            if not isinstance(shortcut, str):
                result = {"error": "shortcut must be str"}
            else:
                try:
                    _select_menuitem_for_shortcut(shortcut)
                except Exception as e:
                    result = {"error": str(e)}
                else:
                    result = {"ok": None}
        elif method == "show_about_panel_and_list_texts":
            try:
                result = _show_about_panel_and_list_texts()
            except Exception as e:
                result = {"error": str(e)}
        else:
            result = {"error": f"unknown method: {method!r}"}

        response = (json.dumps(result) + "\n").encode("utf-8")
        conn.sendall(response)
        elapsed = time.monotonic() - started_at
        _log_test_socket(
            f"response sent method={method!r} bytes={len(response)} elapsed={elapsed:.3f}s"
        )


# ------------------------------------------------------------------------------
# Request: _set_window_appearance

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


# ------------------------------------------------------------------------------
# Request: _select_menuitem_for_shortcut

_MODIFIER_MAP: dict[str, int] = {
    "Meta": AppKit.NSCommandKeyMask,
    "Shift": AppKit.NSShiftKeyMask,
    "Control": AppKit.NSControlKeyMask,
    "Alt": AppKit.NSAlternateKeyMask,
}

_RELEVANT_MODIFIER_BITS: int = (
    AppKit.NSCommandKeyMask
    | AppKit.NSShiftKeyMask
    | AppKit.NSControlKeyMask
    | AppKit.NSAlternateKeyMask
)


def _select_menuitem_for_shortcut(shortcut: str) -> None:
    """Find and trigger the menu item matching `shortcut` (e.g. "Meta+f")."""
    key_char, modifier_mask = _parse_shortcut(shortcut)

    def _trigger() -> None:
        app = AppKit.NSApplication.sharedApplication()
        main_menu = app.mainMenu()
        if main_menu is None:
            raise RuntimeError("Main menu not found")
        item = _find_menuitem_by_key(main_menu, key_char, modifier_mask)
        if item is None:
            raise RuntimeError(
                f"No menu item for shortcut={shortcut!r} "
                f"(key={key_char!r} mask={modifier_mask:#010x})"
            )
        app.sendAction_to_from_(item.action(), item.target(), item)

    _run_on_main_thread(_trigger, timeout=5.0)


def _parse_shortcut(shortcut: str) -> tuple[str, int]:
    """
    Parses a shortcut string like "Meta+f" or "Shift+Meta+g" into
    (key_char, modifier_mask).

    Edge case: "Meta++" parses as key="+" with Meta modifier.
    """
    # NOTE: Uses the same modifier names as PlaywrightKit's pressKey format.
    parts = shortcut.split("+")
    modifiers: list[str] = []
    key_parts: list[str] = []
    for part in parts:
        if part in _MODIFIER_MAP:
            modifiers.append(part)
        else:
            key_parts.append(part)
    key = "+".join(key_parts)
    mask = 0
    for m in modifiers:
        mask |= _MODIFIER_MAP[m]
    return key, mask


def _find_menuitem_by_key(
    menu: AppKit.NSMenu,
    key_char: str,
    modifier_mask: int,
) -> AppKit.NSMenuItem | None:
    """Recursively walk `menu` to find an item with matching key+modifier."""
    for i in range(menu.numberOfItems()):
        item = menu.itemAtIndex_(i)
        if item.isSeparatorItem():
            continue
        item_key = str(item.keyEquivalent())
        item_mask = int(item.keyEquivalentModifierMask()) & _RELEVANT_MODIFIER_BITS
        if item_key == key_char and item_mask == modifier_mask:
            return item
        submenu = item.submenu()
        if submenu is not None:
            found = _find_menuitem_by_key(submenu, key_char, modifier_mask)
            if found is not None:
                return found
    return None


# ------------------------------------------------------------------------------
# Request: _show_about_panel_and_list_texts

def _show_about_panel_and_list_texts() -> list[str]:
    app = AppKit.NSApplication.sharedApplication()
    _run_on_main_thread(lambda: _trigger_about_menu_item(app), timeout=5.0)
    texts = _run_on_main_thread(lambda: _list_about_panel_texts(app), timeout=5.0)
    return texts


def _trigger_about_menu_item(app: AppKit.NSApplication) -> None:
    main_menu = app.mainMenu()
    if main_menu is None:
        raise RuntimeError("Main menu not found")
    app_menu_item = main_menu.itemAtIndex_(0)
    if app_menu_item is None:
        raise RuntimeError("App menu item not found")
    app_menu = app_menu_item.submenu()
    if app_menu is None:
        raise RuntimeError("App menu not found")

    for i in range(app_menu.numberOfItems()):
        item = app_menu.itemAtIndex_(i)
        if item.action() == "showAboutPanel:":
            item.target().showAboutPanel_(item)
            return
    raise RuntimeError("About menu item not found")


def _list_about_panel_texts(app: AppKit.NSApplication) -> list[str]:
    # Locate About Panel window
    for window in app.windows():
        if type(window).__name__ == "NSPanel" and window.title() == "":
            break
    else:
        return []

    content_view = window.contentView()
    assert content_view is not None

    observed: list[str] = []
    _collect_string_values_from_descendent_views(content_view, observed)
    return observed


def _collect_string_values_from_descendent_views(view: AppKit.NSView, out: list[str]) -> None:
    # Collect string value from this view
    if hasattr(view, "stringValue"):
        value = view.stringValue()
        assert isinstance(value, str)
        out.append(value)

    # Recursively explore descendent views
    for subview in view.subviews():
        _collect_string_values_from_descendent_views(subview, out)


# ------------------------------------------------------------------------------
# Utility

def _log_test_socket(message: str) -> None:
    print(f"[gvc testmode] {message}", file=sys.stderr, flush=True)


def _run_on_main_thread[_T](func: Callable[[], _T], timeout: float) -> _T:
    done = threading.Event()
    result: _T | None = None
    error: BaseException | None = None
    def _block() -> None:
        nonlocal error, result
        try:
            result = func()
        except BaseException as e:
            error = e
        finally:
            done.set()

    NSOperationQueue.mainQueue().addOperationWithBlock_(_block)
    if not done.wait(timeout=timeout):
        raise TimeoutError("timed out waiting for main-thread operation")
    if error is not None:
        raise error
    return cast(_T, result)


# ------------------------------------------------------------------------------
