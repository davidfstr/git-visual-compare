from harness.client import GvcGuiNotDoneStarting, TestClient, WindowInfo
from harness.sandbox import GvcSandbox
import os
import signal
import subprocess
import sys
import time


class GvcApp:
    """
    A sandboxed gvc CLI/GUI installation.

    Use run_cli() to start the GUI process; it is NOT started automatically.
    """

    def __init__(self, sandbox: GvcSandbox) -> None:
        self.sandbox = sandbox
        self._client = TestClient(sandbox.runtime_dir / "gui-test.sock")

    # === CLI ===

    def run_cli(self, args: list[str] | None = None) -> subprocess.CompletedProcess[bytes]:
        """
        Invokes the gvc CLI and returns immediately.

        The CLI exits as soon as it has handed the request to the GUI (either
        by spawning a new GUI process or by sending to an existing one).
        """
        result = subprocess.run(
            [sys.executable, "-m", "gvc.cli"] + (args or []),
            env=self.sandbox.env,
            capture_output=True,
            timeout=3.0,
        )
        if result.returncode != 0:
            raise AssertionError(
                f'Expected gvc CLI to exit successfully but '
                f'it returned exit code {result.returncode}')
        return result

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
