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

# Default window dimensions
_DEFAULT_WIDTH = 1200

# How far each new window is offset from the previous one
_STACK_X = 30
_STACK_Y = 30


def _is_dark_mode() -> bool:
    """Return True if the OS is currently in Dark Mode.

    Uses NSUserDefaults rather than NSApp.effectiveAppearance() because this
    is called before webview.start() initialises the Cocoa application, at
    which point NSApp is still None.
    """
    from Foundation import NSUserDefaults  # type: ignore
    defaults = NSUserDefaults.standardUserDefaults()
    return defaults.stringForKey_("AppleInterfaceStyle") == "Dark"


def _get_screen_frame() -> tuple[int, int, int, int]:
    """
    Return (x, y, width, height) of the main screen's visible frame
    (i.e. excluding the macOS menu bar and Dock).

    Uses AppKit directly so this works before webview.start() is called.
    Falls back to a safe 1440×900 assumption if AppKit is unavailable.
    """
    import AppKit  # type: ignore
    screen = AppKit.NSScreen.mainScreen()
    if screen:
        vf = screen.visibleFrame()
        sf = screen.frame()
        screen_h = int(sf.size.height)
        x = int(vf.origin.x)
        # Convert from bottom-left Cocoa origin to top-left pywebview origin
        y = screen_h - int(vf.origin.y) - int(vf.size.height)
        w = int(vf.size.width)
        h = int(vf.size.height)
        return x, y, w, h
    return 0, 0, 1440, 900


def _disable_automatic_tabbing() -> None:
    """Disable macOS automatic window tabbing at the class level.

    Must be called once before any windows are created.  Without this,
    every NSWindow gets an ``NSTabBar`` accessory view that duplicates
    the window title as a tab label.
    """
    import AppKit  # type: ignore
    AppKit.NSWindow.setAllowsAutomaticWindowTabbing_(False)


def create_window(
    html: str,
    title: str,
    prefs: "Prefs",  # noqa: ARG001 — reserved for font_size pass-through in future
    api: "AppApi",
) -> webview.Window:
    """Create a new diff window and wire up lifecycle events."""
    sx, sy, sw, sh = _get_screen_frame()

    existing = api.open_windows()
    if existing:
        # Base position and size on the most-recently-opened window
        prev = existing[-1]
        x = prev.x + _STACK_X
        y = prev.y + _STACK_Y
        width = max(_MIN_WIDTH, prev.width)
        height = max(_MIN_HEIGHT, prev.height)
    else:
        # First window: top-left of the usable screen area, sensible defaults
        x = sx
        y = sy
        width = _DEFAULT_WIDTH
        height = sh

    # Keep the window fully on-screen
    width = min(width, sw)
    height = min(height, sh)
    x = max(sx, min(x, sx + sw - width))
    y = max(sy, min(y, sy + sh - height))

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
        # Match the WebView's initial background to the OS appearance so there
        # is no white flash during the window-open animation in dark mode.
        background_color="#0d1117" if _is_dark_mode() else "#ffffff",
    )

    api.register_window(window)

    def on_shown() -> None:
        # Bring the app to the front so the new window isn't hidden behind
        # other apps (pywebview doesn't do this automatically on macOS).
        import AppKit  # type: ignore
        AppKit.NSApp.activateIgnoringOtherApps_(True)

    def on_closed() -> None:
        api.unregister_window(window)

    window.events.shown += on_shown
    window.events.closed += on_closed

    return window
