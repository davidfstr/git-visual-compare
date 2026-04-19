"""Wrapper around platformdirs that honors GVC_PLATFORMDIRS_ROOT for test sandboxing."""

import os
from pathlib import Path
import platformdirs


_APP_NAME = "gvc"


def _sandbox_root() -> Path | None:
    v = os.environ.get("GVC_PLATFORMDIRS_ROOT")
    return Path(v) if v else None


def user_runtime_dir() -> Path:
    root = _sandbox_root()
    return (
        # Use a short flat subdir of the sandbox root rather than the full platformdirs path
        # because Unix socket paths have a 104-char limit on macOS
        root / "runtime" if root is not None
        else Path(platformdirs.user_runtime_dir(_APP_NAME))
    )


def user_data_dir() -> Path:
    root = _sandbox_root()
    return (
        root / "data" if root is not None
        else Path(platformdirs.user_data_dir(_APP_NAME))
    )


def user_log_dir() -> Path:
    root = _sandbox_root()
    return (
        root / "log" if root is not None
        else Path(platformdirs.user_log_dir(_APP_NAME))
    )
