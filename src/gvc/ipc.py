"""Shared IPC helpers: socket path and temp-file protocol."""

from contextlib import closing
from dataclasses import dataclass
import json
from pathlib import Path
import platformdirs
import socket
import tempfile
import traceback


@dataclass(frozen=True)
class GuiRequest:
    title: str
    diff_bytes: bytes

    def write_to(self, filepath: Path) -> None:
        """Write request to the given filepath."""
        meta = json.dumps({"title": self.title})
        data = meta.encode("utf-8") + b"\n" + self.diff_bytes
        filepath.write_bytes(data)

    def write_to_temp_file(self) -> Path:
        """Write request to a new temp file and return its path."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".gvc", mode="wb") as f:
            tmp_path = Path(f.name)
            self.write_to(tmp_path)
        return tmp_path

    @staticmethod
    def read_from(filepath: Path) -> GuiRequest:
        """Read and delete a request file."""
        data = filepath.read_bytes()
        filepath.unlink(missing_ok=True)
        newline = data.index(b"\n")
        meta = json.loads(data[:newline])
        raw = data[newline + 1 :]
        return GuiRequest(title=meta.get("title", "gvc"), diff_bytes=raw)


def gui_socket_path() -> Path:
    """
    Return the path to the GUI server's Unix domain socket,
    which may or may not exist.
    """
    d = Path(platformdirs.user_runtime_dir("gvc"))
    d.mkdir(parents=True, exist_ok=True)
    return d / "gui.sock"


def try_send(sock_path: Path, request_filepath: Path) -> bool:
    """
    Try to connect to the GUI server and send the request file path.
    Returns True on success, False if no server is listening.
    
    Removes a stale socket file on ConnectionRefusedError.
    """
    try:
        with closing(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)) as sock:
            sock.settimeout(2.0)
            sock.connect(str(sock_path))
            sock.sendall(str(request_filepath).encode("utf-8"))
        return True
    except FileNotFoundError:
        return False
    except ConnectionRefusedError:
        # Stale socket file. Remove it so the next launch starts fresh.
        sock_path.unlink(missing_ok=True)
        return False
    except Exception:
        traceback.print_exc()
        return False


def receive(conn: socket.socket) -> Path:
    chunks: list[bytes] = []
    while chunk := conn.recv(4096):
        chunks.append(chunk)
    return Path(b"".join(chunks).decode("utf-8").strip())
