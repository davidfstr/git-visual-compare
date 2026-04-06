# NOTE: pywebview eagerly evaluates annotations of AppApi, which will fail
#       when a typechecking-only import is used, logging "unsupported callable"
#       to stderr
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gvc.prefs import Prefs, PrefsDict
    import webview


class AppApi:
    """
    Singleton which manages global app state, shared across all windows
    in a process.
    
    JavaScript API methods are called on a background thread by pywebview.
    """
    
    _MIN_FONT_SIZE = 8
    _MAX_FONT_SIZE = 32

    def __init__(self, prefs: Prefs) -> None:
        self._prefs = prefs
        # NOTE: All accesses must hold self._lock
        self._windows: list[webview.Window] = []
        self._lock = threading.Lock()
    
    # === Windows ===

    def register_window(self, window: webview.Window) -> None:
        """Called from window_manager after creating each window."""
        with self._lock:
            self._windows.append(window)

    def unregister_window(self, window: webview.Window) -> None:
        """Called when a window closes."""
        with self._lock:
            try:
                self._windows.remove(window)
            except ValueError:
                pass

    def open_windows(self) -> list[webview.Window]:
        """Return a snapshot of currently open diff windows."""
        with self._lock:
            return list(self._windows)  # clone

    # === JavaScript API ===
    
    def get_prefs(self) -> PrefsDict:
        """Return preferences dict to JS on page load."""
        return self._prefs.to_dict()

    def set_font_size(self, size: int) -> None:
        """Persist new font size and broadcast to all open windows."""
        size = max(self._MIN_FONT_SIZE, min(self._MAX_FONT_SIZE, int(size)))
        self._prefs.font_size = size
        self._prefs.save()

        js = f"applyFontSize({size});"
        for w in self.open_windows():
            w.evaluate_js(js)
