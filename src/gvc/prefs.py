"""Persistent user preferences, stored as JSON."""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import platformdirs
import tempfile
from typing import TypedDict


_APP_NAME = "gvc"
_PREFS_FILE = "prefs.json"


@dataclass
class Prefs:
    font_size: int = 13

    # === Persistence ===

    @classmethod
    def _path(cls) -> Path:
        prefs_dirpath = Path(platformdirs.user_data_dir(_APP_NAME))
        prefs_dirpath.mkdir(parents=True, exist_ok=True)
        return prefs_dirpath / _PREFS_FILE

    @classmethod
    def load(cls) -> Prefs:
        path = cls._path()
        
        if not path.exists():
            # Missing prefs file. Use default prefs.
            return cls()
        
        # Read prefs file
        try:
            with path.open("r") as fh:
                data = json.load(fh)
            known_field_names = {f for f in cls.__dataclass_fields__}
            return cls(**{k: v for k, v in data.items() if k in known_field_names})
        except (json.JSONDecodeError, TypeError):
            # Malformed prefs file. Revert to default prefs silently.
            return cls()

    def save(self) -> None:
        path = self._path()
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as fh:
            json.dump(asdict(self), fh, indent=2)
        os.replace(fh.name, path)
    
    def to_dict(self) -> PrefsDict:
        return PrefsDict({
            "font_size": self.font_size,
        })


class PrefsDict(TypedDict):
    font_size: int
