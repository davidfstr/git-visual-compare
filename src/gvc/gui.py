"""
Persistent GUI server process.
- Binds a Unix domain socket immediately on startup (minimises the race
  window during which a second CLI invocation might launch a second server).
- Opens the first diff window from the request file path in argv[1].
- Listens on the socket for subsequent window requests (each message is a
  request file path sent by cli.py).
- Stays alive after all windows are closed (standard macOS document-app
  behavior) so the next request opens instantly.
"""

import AppKit
from contextlib import closing
import datetime as dt
from Foundation import NSObject
from gvc import paths
from importlib.metadata import version
import os
from pathlib import Path
from PyObjCTools import AppHelper
import socket
import sys
import threading
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gvc.app_api import AppApi


# NOTE: Must hold explicit references to these handlers to prevent them from
#       being garbage collected. NSMenuItem - which targets its handler - does
#       not retain its target.
_about_panel_handler: object | None = None
_menu_handler: object | None = None


# ------------------------------------------------------------------------------
# Main

def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python -m gvc.gui <tmpfile>")
    request_filepath = Path(sys.argv[1])
    
    # Redirect stderr to a persistent log file so tracebacks are observable.
    log_dirpath = paths.user_log_dir()
    log_dirpath.mkdir(parents=True, exist_ok=True)
    log_filepath = log_dirpath / "gvc.log"
    # NOTE: Replace log whenever process restarts, to prevent growing without bound
    sys.stderr = log_filepath.open("w", buffering=1)
    _log(f"gvc started pid={os.getpid()}")

    # Bind the socket FIRST — before importing webview — so that a second
    # concurrent CLI invocation can find the socket as soon as possible.
    from gvc.ipc import gui_socket_path
    sock_path = gui_socket_path()
    with closing(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Delete any preexisting Unix socket
        sock_path.unlink(missing_ok=True)
        server_sock.bind(str(sock_path))
        _log(f"primary socket bound: {sock_path}")
        testmode_close = None
        try:
            server_sock.listen(5)  # maximum backlog of 5 pending connections

            # Load heavier GUI dependencies
            import webview  # isort:skip
            _log("webview imported")

            from gvc.app_api import AppApi
            from gvc.prefs import Prefs
            from gvc.window_manager import disable_automatic_tabbing

            # Disable macOS automatic window tabbing before creating any windows,
            # otherwise every window gets a tab bar that duplicates the title.
            disable_automatic_tabbing()

            # Configure Dock name, About Box contents, and app icon.
            # NOTE: Must run before webview.start()
            _configure_app_identity()

            # Single shared AppApi for all windows in this process
            api = AppApi(Prefs.load())

            # Start test mode, if requested
            if os.environ.get("GVC_TEST_MODE"):
                from gvc import testmode
                testmode_close = testmode.start(api)
                _log("testmode started")

            # Start socket listener thread
            t = threading.Thread(
                target=_socket_listener,
                args=(server_sock, api),
                # Thread does not keep process alive
                daemon=True,
            )
            t.start()

            # Create hidden keepalive window, to keep the Cocoa event loop alive
            # after all visible diff windows are closed, which is standard macOS
            # document-app behavior.
            webview.create_window("gvc", html="", hidden=True)

            # Open the first window from the request file path in argv
            from gvc.ipc import GuiRequest
            req = GuiRequest.read_from(request_filepath)
            _open_window(req.title, req.diff_bytes, api)
            _log("first window created; entering event loop")

            # Run the Cocoa event loop, until Cmd+Q or webview.stop() called
            webview.start(func=lambda: _setup_menus_soon(api), private_mode=False)
        finally:
            if testmode_close is not None:
                testmode_close()
            sock_path.unlink(missing_ok=True)


def _configure_app_identity() -> None:
    """
    Set the Dock icon and About Box contents. Must run before webview.start().
    
    NOTE: When gvc is running as unbundled, the Dock tooltip will still
    show "Python" rather than "gvc" because macOS caches the display name
    at launch time from the .app bundle's Info.plist, which isn't available
    when gvc is running as unbundled.
    """
    import AppKit
    from Foundation import NSBundle, NSProcessInfo
    from importlib.resources import as_file, files

    # Define app name for the App menu
    NSProcessInfo.processInfo().setProcessName_("gvc")
    
    # NOTE: Duplicated in gvc.spec and _configure_app_identity() and stub_app.py
    bundle_info_overrides: dict[str, object]
    if True:
        _BUNDLE_NAME = "gvc"
        _COPYRIGHT = "Copyright © 2026 David Foster"
        _VERSION = version("gvc")
        
        bundle_info_overrides = {
            "CFBundleDisplayName": _BUNDLE_NAME,
            "CFBundleName": _BUNDLE_NAME,
            "CFBundleShortVersionString": _VERSION,
            "CFBundleVersion": _VERSION,
            "NSHumanReadableCopyright": _COPYRIGHT,
        }

    # Define app metadata for the About Box
    bundle_info = NSBundle.mainBundle().infoDictionary()
    for k, v in bundle_info_overrides.items():
        bundle_info[k] = v
    
    # Define app icon for the Dock icon and About Box
    icon_resource = files("gvc").joinpath("assets/icon.png")
    with as_file(icon_resource) as icon_path:
        image = AppKit.NSImage.alloc().initWithContentsOfFile_(str(icon_path))
    if image is not None:
        # Register as the named system image so About panel / NSImage.imageNamed_
        # lookups return the gvc icon
        image.setName_("NSApplicationIcon")
        AppKit.NSApplication.sharedApplication().setApplicationIconImage_(image)


def _socket_listener(server_sock: socket.socket, api: AppApi) -> None:
    """
    Background thread: accept incoming connections from cli.py.
    Each connection sends a single request file path (UTF-8, no framing needed
    since the connection is closed after sending).
    """
    from gvc.ipc import GuiRequest, receive

    server_sock.settimeout(1.0)

    while True:
        try:
            conn, _ = server_sock.accept()
        except socket.timeout:
            continue
        except OSError:
            # Socket closed. Server shutting down.
            break

        try:
            with closing(conn):
                request_filepath = receive(conn)
            req = GuiRequest.read_from(request_filepath)
            _open_window(req.title, req.diff_bytes, api)
        except Exception:
            # Never crash the listener
            traceback.print_exc()


# ------------------------------------------------------------------------------
# Request: Open Window

def _open_window(title: str, diff_bytes: bytes, api: AppApi) -> None:
    """Parse diff bytes and open a new diff window. Thread-safe."""
    from gvc.diff_parser import LargeDiffInfo, parse
    from gvc.renderer import render
    from gvc.window_manager import create_window

    large_diff_info = LargeDiffInfo.try_parse(diff_bytes)
    html_doc = render(parse(diff_bytes), large_diff_info)

    create_window(html_doc, title, api)


# ------------------------------------------------------------------------------
# Menus

def _setup_menus_soon(api: AppApi) -> None:
    """
    Customizes menus.

    Must be called from a background thread.
    """
    AppHelper.callAfter(_define_about_panel)
    AppHelper.callAfter(_define_menus, api)


def _define_about_panel() -> None:
    """
    Alters the About menu item to use an About Window with the app's full title,
    "Git Visual Compare (gvc)".
    
    Must be called from the Cocoa main thread.
    """
    import AppKit
    from Foundation import NSObject
    
    # Create about panel handler
    global _about_panel_handler
    class AboutPanelHandler(NSObject):
        def showAboutPanel_(self, sender: object) -> None:
            AppKit.NSApplication.sharedApplication().orderFrontStandardAboutPanelWithOptions_(
                {
                    # Override CFBundleDisplayName with a custom app title
                    "ApplicationName": "Git Visual Compare (gvc)"
                }
            )
    handler = AboutPanelHandler.alloc().init()
    _about_panel_handler = handler

    # Register about panel handler
    app = AppKit.NSApplication.sharedApplication()
    main_menu = app.mainMenu()
    if main_menu is None:
        print(f"Main menu not found. Cannot define About Panel.", file=sys.stderr)
        return
    # NOTE: There is no obvious more-reliable way (than index 0) to identify this menuitem
    app_menu_item = main_menu.itemAtIndex_(0)
    if app_menu_item is None:
        print(f"App menu item not found. Cannot define About Panel.", file=sys.stderr)
        return
    app_menu = app_menu_item.submenu()
    if app_menu is None:
        print(f"App menu not found. Cannot define About Panel.", file=sys.stderr)
        return
    for i in range(app_menu.numberOfItems()):
        item = app_menu.itemAtIndex_(i)
        # Look for the About menuitem that pywebview defined in cocoa.py
        if item.action() == "orderFrontStandardAboutPanel:":
            about_item = item  # rename
            about_item.setTarget_(handler)  # override pywebview
            about_item.setAction_("showAboutPanel:")  # override pywebview
            break
    else:
        print(f"About menuitem not found. Cannot define About Panel.", file=sys.stderr)
        return


def _define_menus(api: AppApi) -> None:
    """
    Adds a File menu with Close, Find items to the Edit menu,
    and Font Size items to the View menu.

    Must be called from the Cocoa main thread.
    """
    app = AppKit.NSApplication.sharedApplication()
    main_menu = app.mainMenu()
    if main_menu is None:
        print("Main menu not found. Cannot define menus.", file=sys.stderr)
        return

    global _menu_handler

    class GvcMenuHandler(NSObject):
        def openFind_(self, sender: object) -> None:
            title = _key_window_title()
            if title is not None:
                threading.Thread(
                    target=_run_js_in_window_titled, args=(api, title, "openFindBar()"), daemon=True
                ).start()

        def findNext_(self, sender: object) -> None:
            title = _key_window_title()
            if title is not None:
                threading.Thread(
                    target=_run_js_in_window_titled, args=(api, title, "menuFindStep(1)"), daemon=True
                ).start()

        def findPrevious_(self, sender: object) -> None:
            title = _key_window_title()
            if title is not None:
                threading.Thread(
                    target=_run_js_in_window_titled, args=(api, title, "menuFindStep(-1)"), daemon=True
                ).start()

        def increaseFontSize_(self, sender: object) -> None:
            threading.Thread(
                target=_run_js_in_some_window, args=(api, "changeFontSize(1)"), daemon=True
            ).start()

        def decreaseFontSize_(self, sender: object) -> None:
            threading.Thread(
                target=_run_js_in_some_window, args=(api, "changeFontSize(-1)"), daemon=True
            ).start()

    handler = GvcMenuHandler.alloc().init()
    _menu_handler = handler

    # File menu
    if True:
        file_menu = AppKit.NSMenu.alloc().init()
        file_menu.setTitle_("File")
        # NOTE: No target. performClose: goes through the responder chain to the key window.
        file_menu.addItemWithTitle_action_keyEquivalent_(
            "Close Window", "performClose:", "w"
        )
        
        file_menu_item = AppKit.NSMenuItem.alloc().init()
        file_menu_item.setTitle_("File")
        file_menu_item.setSubmenu_(file_menu)
        
        # Insert File menu between app menu and Edit menu
        main_menu.insertItem_atIndex_(file_menu_item, 1)

    # Edit menu
    for i in range(main_menu.numberOfItems()):
        item = main_menu.itemAtIndex_(i)
        submenu = item.submenu()
        if not (submenu is not None and str(submenu.title()) == "Edit"):
            continue
        
        submenu.addItem_(AppKit.NSMenuItem.separatorItem())

        find_item = submenu.addItemWithTitle_action_keyEquivalent_(
            "Find…", "openFind:", "f"
        )
        find_item.setTarget_(handler)

        find_next = submenu.addItemWithTitle_action_keyEquivalent_(
            "Find Next", "findNext:", "g"
        )
        find_next.setTarget_(handler)

        find_prev = submenu.addItemWithTitle_action_keyEquivalent_(
            "Find Previous", "findPrevious:", "g"
        )
        find_prev.setTarget_(handler)
        find_prev.setKeyEquivalentModifierMask_(
            AppKit.NSCommandKeyMask | AppKit.NSShiftKeyMask
        )
        
        break
    else:
        print("Edit menu not found. Cannot add Find items.", file=sys.stderr)

    # View menu
    for i in range(main_menu.numberOfItems()):
        item = main_menu.itemAtIndex_(i)
        submenu = item.submenu()
        if not (submenu is not None and str(submenu.title()) == "View"):
            continue
        
        # Insert menuitems in reverse order, resulting in final order:
        # - Increase Font Size
        # - Decrease Font Size
        # - ───
        # - Enter Full Screen
        
        submenu.insertItem_atIndex_(AppKit.NSMenuItem.separatorItem(), 0)

        decrease = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Decrease Font Size", "decreaseFontSize:", "-"
        )
        decrease.setTarget_(handler)
        submenu.insertItem_atIndex_(decrease, 0)

        increase = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Increase Font Size", "increaseFontSize:", "+"
        )
        increase.setTarget_(handler)
        submenu.insertItem_atIndex_(increase, 0)
        
        break
    else:
        print("View menu not found. Cannot add Font Size items.", file=sys.stderr)


def _key_window_title() -> str | None:
    """
    Returns the title of the current key window.
    
    Must be called on the main thread.
    """
    kw = AppKit.NSApp.keyWindow()
    return str(kw.title()) if kw is not None else None


def _run_js_in_window_titled(api: AppApi, title: str, js: str) -> None:
    """
    Executes js in the pywebview window with the given title.
    
    Must be called on a background thread.
    """
    for w in api.open_windows():
        if w.title == title:
            w.evaluate_js(js)
            break
    else:
        raise ValueError(f'No such window: {title}')


def _run_js_in_some_window(api: AppApi, js: str) -> None:
    """
    Executes js in any open pywebview window, if there is one.
    
    Must be called on a background thread.
    """
    windows = api.open_windows()
    if windows:
        windows[0].evaluate_js(js)


# ------------------------------------------------------------------------------
# Utility: Logging

def _log(message: str) -> None:
    """Writes a timestamped progress line to the log (sys.stderr)."""
    print(
        f"[{dt.datetime.now().isoformat(timespec='milliseconds')}] {message}",
        file=sys.stderr,
        flush=True,
    )


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
