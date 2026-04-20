from contextlib import closing
from dataclasses import dataclass
import json
from pathlib import Path
import socket
from typing import Any


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

    def eval_js(self, window_id: str, src: str) -> object:
        """
        Evaluates `src` in the webview of window `window_id`.

        `src` is expected to be an expression that evaluates to
        either {"ok": <any>} or {"error": <str>}; this method unwraps
        the envelope, raising EvalJsError on error.

        Raises:
        * EvalJsError
        """
        # NOTE: Should never raise GvcGuiNotDoneStarting because we already
        #       have a valid window_id, implying that gvc is done starting
        result = self._call("eval_js", window_id=window_id, src=src)
        if not isinstance(result, dict):
            raise EvalJsError(
                f"eval_js returned non-dict: {result!r}"
            )
        if "error" in result:
            raise EvalJsError(str(result["error"]))
        if "ok" not in result:
            raise EvalJsError(
                f"eval_js returned dict without ok/error: {result!r}"
            )
        return result["ok"]

    # === Utility ===

    def _call(self, method: str, **kwargs: Any) -> object:
        """
        Raises:
        * GvcGuiNotDoneStarting
        """
        payload: dict[str, Any] = {"method": method, **kwargs}
        with closing(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)) as s:
            s.settimeout(5.0)
            try:
                s.connect(str(self._sock_path))
            except FileNotFoundError:
                raise GvcGuiNotDoneStarting()
            s.sendall(json.dumps(payload).encode("utf-8"))
            s.shutdown(socket.SHUT_WR)
            data = b""
            while chunk := s.recv(4096):
                data += chunk
        return json.loads(data.decode("utf-8").strip())


class GvcGuiNotDoneStarting(Exception):
    pass


class EvalJsError(Exception):
    """Raised when eval_js returns an error envelope or the JS threw."""


@dataclass(frozen=True)
class WindowInfo:
    id: str
    title: str
