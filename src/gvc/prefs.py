"""Persistent user preferences, stored as JSON."""

from __future__ import annotations

import fcntl
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

import platformdirs

_APP_NAME = "gvc"
_PREFS_FILE = "prefs.json"

# Cascade offset for stacked windows
STACK_OFFSET_X = 30
STACK_OFFSET_Y = 30

# Default window dimensions
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = -1  # -1 means: use full screen height (resolved at runtime)
DEFAULT_X = 100
DEFAULT_Y = 0


@dataclass
class Prefs:
    font_size: int = 13
    window_width: int = DEFAULT_WIDTH
    window_height: int = DEFAULT_HEIGHT
    window_x: int = DEFAULT_X
    window_y: int = DEFAULT_Y
    # Position of the most-recently-opened window, for stacking
    last_x: int = DEFAULT_X
    last_y: int = DEFAULT_Y

    # ------------------------------------------------------------------ #
    # Persistence                                                          #
    # ------------------------------------------------------------------ #

    @classmethod
    def _path(cls) -> Path:
        d = Path(platformdirs.user_data_dir(_APP_NAME))
        d.mkdir(parents=True, exist_ok=True)
        return d / _PREFS_FILE

    @classmethod
    def load(cls) -> "Prefs":
        path = cls._path()
        if not path.exists():
            return cls()
        try:
            with path.open("r") as fh:
                data = json.load(fh)
            # Only keep keys that exist in the dataclass to tolerate schema drift
            known = {f for f in cls.__dataclass_fields__}
            p = cls(**{k: v for k, v in data.items() if k in known})
        except (json.JSONDecodeError, TypeError):
            return cls()
        # Reset stored geometry if it looks corrupt (e.g. from a bad JS save)
        if p.window_width < 50 or p.window_height not in range(-1, 100_000):
            p.window_width = DEFAULT_WIDTH
            p.window_height = DEFAULT_HEIGHT
        return p

    def save(self) -> None:
        path = self._path()
        tmp = path.with_suffix(".tmp")
        with tmp.open("w") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                json.dump(asdict(self), fh, indent=2)
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        os.replace(tmp, path)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def next_window_position(self) -> tuple[int, int]:
        """Return (x, y) for the next window, cascaded from the last one."""
        return self.last_x + STACK_OFFSET_X, self.last_y + STACK_OFFSET_Y

    def record_window_opened(self, x: int, y: int) -> None:
        self.last_x = x
        self.last_y = y
        self.save()

    def record_window_geometry(
        self, x: int, y: int, width: int, height: int
    ) -> None:
        # Reject implausible values that may come from JS before the window
        # is fully laid out (e.g. zero dimensions on early resize events).
        if width < 50 or height < 50:
            return
        self.window_x = x
        self.window_y = y
        self.window_width = width
        self.window_height = height
        self.save()
