from harness.client import GvcGuiNotDoneStarting, TestClient, WindowInfo
from harness.playwrightkit import Page
from harness.sandbox import GvcSandbox
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import TracebackType
from typing import Literal, Self


class GvcApp:
    """
    A sandboxed gvc CLI/GUI installation.

    Use run_cli() to start the GUI process; it is NOT started automatically.
    """

    def __init__(self, sandbox: GvcSandbox) -> None:
        self.sandbox = sandbox
        self._client = TestClient(sandbox.runtime_dir / "gui-test.sock")
    
    # === Context Manager ===

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    # === CLI ===

    def run_cli(
        self,
        args: list[str] | None = None,
        cwd: str | Path | None = None,
        timeout: float = 5.0,
    ) -> WindowInfo:
        """
        Invokes the gvc CLI and returns the new diff window that opened.

        The CLI exits as soon as it has handed the request to the GUI (either
        by spawning a new GUI process or by sending to an existing one).

        `cwd` sets the working directory for the CLI, which controls the
        repository `git diff` runs against.
        """
        try:
            old_window_count = len(self._client.list_windows())
        except GvcGuiNotDoneStarting:
            old_window_count = 0

        result = subprocess.run(
            [sys.executable, "-m", "gvc.cli"] + (args or []),
            env=self.sandbox.env,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            timeout=3.0,
        )
        if result.returncode != 0:
            raise AssertionError(
                f'Expected gvc CLI to exit successfully but '
                f'it returned exit code {result.returncode}. '
                f'stderr: {result.stderr.decode("utf-8", errors="replace")!r}')

        windows = self.wait_for_windows(old_window_count + 1, timeout=timeout)
        return windows[-1]

    # === Window Inspection ===

    def wait_for_windows(self, count: int, timeout: float = 5.0) -> list[WindowInfo]:
        """
        Waits until exactly `count` windows are open, then returns them.

        Raises:
        * TimeoutError -- if the wait condition is not met within `timeout` seconds
        """
        deadline = time.monotonic() + timeout  # capture
        last_windows: list[WindowInfo] = []
        while time.monotonic() < deadline:
            try:
                last_windows = self._client.list_windows()
            except GvcGuiNotDoneStarting:
                pass
            else:
                if len(last_windows) == count:
                    return last_windows
            time.sleep(0.1)
        raise TimeoutError(
            f"Expected {count} window(s); last seen: {last_windows!r}"
        )

    # === DOM Access ===

    def page(self, window: WindowInfo) -> Page:
        """
        Returns a Playwright-shaped Page for the given window.

        The window must already exist (use wait_for_windows() first).
        """
        return Page(self._client, window.id)

    # === UI Access ===

    def set_appearance(self, window: WindowInfo, appearance: Literal["light", "dark"]) -> None:
        """
        Forces the diff window's WKWebView to render in "light" or "dark" mode,
        making @media (prefers-color-scheme: ...) CSS rules activate
        independently of the current OS setting.
        """
        self._client.set_appearance(window.id, appearance)

    def select_menuitem(self, shortcut: str) -> None:
        """
        Finds and triggers the menu item whose key equivalent matches `shortcut`
        (e.g. "Meta+f"). Same modifier-name format as page.press().
        """
        self._client.select_menuitem(shortcut)

    def show_about_panel_and_list_texts(self) -> list[str]:
        """Opens About via the app menu and returns visible text in the About panel."""
        return self._client.show_about_panel_and_list_texts()

    # === Close ===

    def close(self) -> None:
        """Terminates the GUI process if it is still running."""
        pid_path = self.sandbox.runtime_dir / "gvc.pid"
        try:
            pid = int(pid_path.read_text().strip())
        except FileNotFoundError:
            # Process never started or finished starting
            return
        except ValueError:
            # Pid file exists but process never finished writing pid to it
            # TODO: Wait a bit longer for pid to be written, then kill the process
            return

        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            # Process already exited
            return

        # Wait up to 3s for a clean exit, then force-kill
        deadline = time.monotonic() + 3.0  # capture
        while time.monotonic() < deadline:
            time.sleep(0.1)
            try:
                # HACK: This will not work on Windows
                os.kill(pid, 0)  # process exists? (POSIX-only)
            except ProcessLookupError:
                # Process exited
                return

        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            # Process already exited
            return
