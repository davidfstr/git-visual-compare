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

    def set_appearance(self, window_id: str, appearance: str) -> None:
        """
        Forces the WKWebView for `window_id` to render in light or dark mode,
        making @media (prefers-color-scheme: ...) CSS rules activate
        independently of the OS setting.

        `appearance` must be "light" or "dark".
        """
        result = self._call("set_appearance", window_id=window_id, appearance=appearance)
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(str(result["error"]))

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

    def select_menuitem(self, shortcut: str) -> None:
        """
        Finds and triggers the menu item whose key equivalent matches `shortcut`
        (e.g. "Meta+f", "Shift+Meta+g").

        Uses the same modifier-name format as PlaywrightKit's press() / pressKey.

        Raises:
        * RuntimeError -- if no matching menu item is found
        """
        result = self._call("select_menuitem", shortcut=shortcut)
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(str(result["error"]))

    def show_about_panel_and_list_texts(self) -> list[str]:
        result = self._call("show_about_panel_and_list_texts")
        if not isinstance(result, list):
            raise RuntimeError(f"unexpected result type: {type(result).__name__}")
        if not all(isinstance(item, str) for item in result):
            raise RuntimeError(f"unexpected result payload: {result!r}")
        return result

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
            chunks: list[bytes] = []
            try:
                while chunk := s.recv(4096):
                    chunks.append(chunk)
            except TimeoutError:
                gvc_log = self._read_gvc_log(self._sock_path)
                raise TimeoutError(
                    f"Timed out waiting for gui-test.sock response "
                    f"(method={method!r}, sock={self._sock_path}, partial_bytes={sum(len(c) for c in chunks)})\n"
                    f"--- gvc.log snapshot begin ---\n"
                    f"{gvc_log}\n"
                    f"--- gvc.log snapshot end ---"
                )
            data = b"".join(chunks)
        return json.loads(data.decode("utf-8").strip())

    @staticmethod
    def _read_gvc_log(sock_path: Path) -> str:
        """Best-effort read of the gvc log for a given test sandbox."""
        # Sandbox layout: <sandbox>/runtime/gui-test.sock, <sandbox>/log/gvc.log
        log_path = sock_path.parent.parent / "log" / "gvc.log"
        try:
            return log_path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return f"<gvc log file not found: {log_path}>"
        except Exception as e:
            return f"<failed to read {log_path}: {type(e).__name__}: {e}>"


class GvcGuiNotDoneStarting(Exception):
    pass


class EvalJsError(Exception):
    """Raised when eval_js returns an error envelope or the JS threw."""


@dataclass(frozen=True)
class WindowInfo:
    id: str
    title: str
