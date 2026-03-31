"""Create and manage pywebview windows."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import webview

if TYPE_CHECKING:
    from gvc.app_api import AppApi
    from gvc.prefs import Prefs

# How far each new window is offset from the previous one
_STACK_X = 30
_STACK_Y = 30


def _get_screen_height() -> int:
    """Return the main screen height in pixels, with a sensible fallback."""
    try:
        screens = webview.screens
        if screens:
            return screens[0].height
    except Exception:
        pass
    # Fallback: try PyObjC
    try:
        import AppKit  # type: ignore
        screen = AppKit.NSScreen.mainScreen()
        if screen:
            return int(screen.frame().size.height)
    except Exception:
        pass
    return 900


def create_window(
    html: str,
    title: str,
    prefs: "Prefs",
    api: "AppApi",
) -> webview.Window:
    """Create a new diff window and wire up lifecycle events."""

    # Determine position for this window
    x, y = prefs.next_window_position()

    # Resolve height
    height = prefs.window_height
    if height == -1:
        # Defer screen height lookup until after webview is initialised
        # (screens list may not be available yet); use a sentinel and fix up
        # in post_start.  For now, use a large value — the OS will constrain it.
        height = 2000  # will be clamped by the OS to screen height

    width = prefs.window_width

    window = webview.create_window(
        title=title,
        html=html,
        js_api=api,
        width=width,
        height=height,
        x=x,
        y=y,
        resizable=True,
        text_select=True,
        # Disable pywebview's built-in context menu — we don't need it
        # (not all backends support this flag; ignore errors)
    )

    api.register_window(window)
    prefs.record_window_opened(x, y)

    # Wire up resize/move → save geometry
    def on_resized(width: int, height: int) -> None:
        # pywebview doesn't give us x/y in this callback, so we can't save
        # position here.  We rely on JS to call save_window_geometry instead.
        pass

    def on_closed() -> None:
        api.unregister_window(window)

    window.events.closed += on_closed

    return window


def inject_geometry_tracker(window: webview.Window) -> None:
    """
    Inject a small JS snippet that calls pywebview.api.save_window_geometry
    whenever the window is resized.  Called after the page is loaded.
    """
    js = """
(function() {
    let _resizeTimer = null;
    window.addEventListener('resize', function() {
        clearTimeout(_resizeTimer);
        _resizeTimer = setTimeout(function() {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.save_window_geometry(
                    window.screenX, window.screenY,
                    window.outerWidth, window.outerHeight
                );
            }
        }, 300);
    });
})();
"""
    try:
        window.evaluate_js(js)
    except Exception:
        pass
