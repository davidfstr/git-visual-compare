"""Shared IPC helpers: socket path and temp-file protocol."""

from __future__ import annotations

import json
from pathlib import Path
import platformdirs
import socket
import traceback


def gui_socket_path() -> Path:
    """Return the path to the GUI server's Unix domain socket."""
    d = Path(platformdirs.user_runtime_dir("gvc"))
    d.mkdir(parents=True, exist_ok=True)
    return d / "gui.sock"


def write_tmp_file(raw: bytes, title: str) -> Path:
    """
    Write diff bytes + JSON metadata to a temp file.
    Returns the path.  Caller is responsible for cleanup on error.
    """
    import tempfile

    meta = json.dumps({"title": title})
    with tempfile.NamedTemporaryFile(delete=False, suffix=".gvc", mode="wb") as f:
        f.write(meta.encode("utf-8"))
        f.write(b"\n")
        f.write(raw)
        return Path(f.name)


def read_tmp_file(path: Path) -> tuple[bytes, str]:
    """
    Read and delete a temp file written by write_tmp_file.
    Returns (raw_diff_bytes, title).
    """
    data = path.read_bytes()
    path.unlink(missing_ok=True)
    newline = data.index(b"\n")
    meta = json.loads(data[:newline])
    raw = data[newline + 1 :]
    return raw, meta.get("title", "gvc")


def try_send(sock_path: Path, tmp_path: Path) -> bool:
    """
    Try to connect to the GUI server and send the temp file path.
    Returns True on success, False if no server is listening.
    Removes a stale socket file on ConnectionRefusedError.
    """
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(str(sock_path))
        sock.sendall(str(tmp_path).encode("utf-8"))
        sock.close()
        return True
    except FileNotFoundError:
        return False
    except ConnectionRefusedError:
        # Stale socket file — remove it so the next launch starts fresh
        sock_path.unlink(missing_ok=True)
        return False
    except Exception:
        traceback.print_exc()
        return False
