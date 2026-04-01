"""Persistent user preferences, stored as JSON."""

from __future__ import annotations

import fcntl
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import platformdirs

_APP_NAME = "gvc"
_PREFS_FILE = "prefs.json"


@dataclass
class Prefs:
    font_size: int = 13

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
            known = {f for f in cls.__dataclass_fields__}
            return cls(**{k: v for k, v in data.items() if k in known})
        except (json.JSONDecodeError, TypeError):
            return cls()

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
