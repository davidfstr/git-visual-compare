from contextlib import closing
from dataclasses import dataclass
import json
from pathlib import Path
import socket


class TestClient:
    """
    JSON-RPC client for the gui-test.sock control socket
    exposed by gvc when GVC_TEST_MODE=1.

    Each call opens a fresh connection: send the request,
    shutdown the write side so the server sees EOF, then read the response.
    """

    def __init__(self, sock_path: Path) -> None:
        self._sock_path = sock_path

    # === API ===

    def ping(self) -> dict[str, object]:
        """
        Raises:
        * GvcGuiNotDoneStarting
        """
        result = self._call("ping")
        assert isinstance(result, dict)
        return result

    def list_windows(self) -> list[WindowInfo]:
        """
        Raises:
        * GvcGuiNotDoneStarting
        """
        result = self._call("list_windows")
        assert isinstance(result, list)
        return [WindowInfo(id=w["id"], title=w["title"]) for w in result]

    # === Utility ===

    def _call(self, method: str) -> object:
        """
        Raises:
        * GvcGuiNotDoneStarting
        """
        with closing(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)) as s:
            s.settimeout(2.0)
            try:
                s.connect(str(self._sock_path))
            except FileNotFoundError:
                raise GvcGuiNotDoneStarting()
            s.sendall(json.dumps({"method": method}).encode("utf-8"))
            s.shutdown(socket.SHUT_WR)
            data = b""
            while chunk := s.recv(4096):
                data += chunk
        return json.loads(data.decode("utf-8").strip())


class GvcGuiNotDoneStarting(Exception):
    pass


@dataclass(frozen=True)
class WindowInfo:
    id: str
    title: str
