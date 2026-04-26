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

from contextlib import closing
import datetime as dt
from gvc import paths
from importlib.metadata import version
import os
from pathlib import Path
import socket
import sys
import threading
import traceback
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from gvc.app_api import AppApi

# Handles showing the app's About Panel.
# NOTE: Must hold an explicit reference to the handler to prevent it from being
#       garbage collected. NSMenuItem - which targets this handler - does not
#       retain its target.
_about_panel_handler: object | None = None


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
    print(f"gvc started {dt.datetime.now().isoformat(timespec='seconds')}", file=sys.stderr, flush=True)

    # Bind the socket FIRST — before importing webview — so that a second
    # concurrent CLI invocation can find the socket as soon as possible.
    from gvc.ipc import gui_socket_path
    sock_path = gui_socket_path()
    with closing(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Delete any preexisting Unix socket
        sock_path.unlink(missing_ok=True)
        server_sock.bind(str(sock_path))
        testmode_close = None
        try:
            server_sock.listen(5)  # maximum backlog of 5 pending connections

            # Load heavier GUI dependencies
            import webview  # isort:skip

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

            # Run the Cocoa event loop, until Cmd+Q or webview.stop() called
            webview.start(func=_define_about_panel_soon, private_mode=False)
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

    # Define app metadata for the About Box
    # NOTE: Duplicated in gvc.spec and _configure_app_identity()
    bundle_info = NSBundle.mainBundle().infoDictionary()
    bundle_info["CFBundleName"] = "gvc"
    bundle_info["CFBundleDisplayName"] = "gvc"
    bundle_info["CFBundleShortVersionString"] = version("gvc")
    bundle_info["CFBundleVersion"] = version("gvc")
    bundle_info["NSHumanReadableCopyright"] = "Copyright © 2026 David Foster"

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


def _open_window(title: str, diff_bytes: bytes, api: AppApi) -> None:
    """Parse diff bytes and open a new diff window. Thread-safe."""
    from gvc.diff_parser import LargeDiffInfo, parse
    from gvc.renderer import render
    from gvc.window_manager import create_window

    large_diff_info = LargeDiffInfo.try_parse(diff_bytes)
    html_doc = render(parse(diff_bytes), large_diff_info)

    create_window(html_doc, title, api)


def _define_about_panel_soon() -> None:
    """
    Alters the About menu item to use an About Window with the app's full title,
    "Git Visual Compare (gvc)".
    
    Must be called from a background thread.
    """
    from PyObjCTools import AppHelper
    AppHelper.callAfter(_define_about_panel)


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


if __name__ == "__main__":
    main()
