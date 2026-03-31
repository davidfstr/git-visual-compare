"""Create and manage pywebview windows."""

from __future__ import annotations

from typing import TYPE_CHECKING

import webview

if TYPE_CHECKING:
    from gvc.app_api import AppApi
    from gvc.prefs import Prefs

# Minimum window dimensions
_MIN_WIDTH = 100   # ~10 monospace columns at 13px
_MIN_HEIGHT = 100  # ~5 rows at 20px

# How far each new window is offset from the previous one
_STACK_X = 30
_STACK_Y = 30


def _get_screen_frame() -> tuple[int, int, int, int]:
    """
    Return (x, y, width, height) of the main screen's visible frame
    (i.e. excluding the macOS menu bar and Dock).

    Uses AppKit directly so this works before webview.start() is called.
    Falls back to a safe 1440×900 assumption if AppKit is unavailable.
    """
    try:
        import AppKit  # type: ignore
        screen = AppKit.NSScreen.mainScreen()
        if screen:
            # visibleFrame excludes the menu bar and dock
            vf = screen.visibleFrame()
            sf = screen.frame()
            # Cocoa uses bottom-left origin; convert y to top-left for pywebview
            # pywebview's y=0 is the top of the screen (below the menu bar)
            screen_h = int(sf.size.height)
            x = int(vf.origin.x)
            # Convert from bottom-left Cocoa origin to top-left pywebview origin
            y = screen_h - int(vf.origin.y) - int(vf.size.height)
            w = int(vf.size.width)
            h = int(vf.size.height)
            return x, y, w, h
    except Exception:
        pass
    return 0, 0, 1440, 900


def _clamp_geometry(
    x: int, y: int, width: int, height: int,
    sx: int, sy: int, sw: int, sh: int,
) -> tuple[int, int, int, int]:
    """Clamp window geometry to minimum size and keep it fully on-screen."""
    width = max(_MIN_WIDTH, width)
    height = max(_MIN_HEIGHT, height)
    # Clamp position so the window is never placed outside the screen
    x = max(sx, min(x, sx + sw - width))
    y = max(sy, min(y, sy + sh - height))
    return x, y, width, height


def create_window(
    html: str,
    title: str,
    prefs: "Prefs",
    api: "AppApi",
) -> webview.Window:
    """Create a new diff window and wire up lifecycle events."""
    sx, sy, sw, sh = _get_screen_frame()

    # Resolve width/height from prefs, replacing sentinel -1 with screen height
    from gvc.prefs import DEFAULT_WIDTH as _DEFAULT_WIDTH
    width = prefs.window_width if prefs.window_width > 0 else _DEFAULT_WIDTH
    height = prefs.window_height if prefs.window_height > 0 else sh

    # Cascade position from last opened window
    x, y = prefs.next_window_position()

    # Clamp everything to safe on-screen values
    x, y, width, height = _clamp_geometry(x, y, width, height, sx, sy, sw, sh)

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
    )

    api.register_window(window)
    prefs.record_window_opened(x, y)

    def on_shown() -> None:
        # Bring the app to the front so the new window isn't hidden behind
        # other apps (pywebview doesn't do this automatically on macOS).
        try:
            import AppKit  # type: ignore
            AppKit.NSApp.activateIgnoringOtherApps_(True)
        except Exception:
            pass

    def on_closed() -> None:
        api.unregister_window(window)

    window.events.shown += on_shown
    window.events.closed += on_closed

    return window


def inject_geometry_tracker(window: webview.Window) -> None:
    """
    Inject JS that saves window geometry to prefs whenever the window is resized.
    Called after the page finishes loading.

    Note: window.outerWidth/Height in WKWebView reflects the WebView's own frame,
    which equals the window's content area.  We save these as a reasonable proxy
    for window size; position is tracked separately via screenX/Y.
    """
    js = """
(function() {
    var _t = null;
    window.addEventListener('resize', function() {
        clearTimeout(_t);
        _t = setTimeout(function() {
            var w = window.outerWidth  || window.innerWidth;
            var h = window.outerHeight || window.innerHeight;
            var sx = window.screenX;
            var sy = window.screenY;
            // Only save if we have plausible values
            if (w > 50 && h > 50 && window.pywebview && window.pywebview.api) {
                window.pywebview.api.save_window_geometry(sx, sy, w, h);
            }
        }, 300);
    });
})();
"""
    try:
        window.evaluate_js(js)
    except Exception:
        pass
