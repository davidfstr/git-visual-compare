import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import TracebackType
from typing import Self


class GvcSandbox:
    """
    An isolated filesystem and environment for one test.

    Use GvcApp to actually run gvc inside this sandbox.

    Wraps a temporary directory that acts as the GVC_PLATFORMDIRS_ROOT
    for one test process, keeping it fully isolated from real gvc installations
    and from other concurrent tests.

    The root is created under /tmp (not pytest's usual/long tmp_path)
    so that socket paths stay within macOS's short 104-character
    Unix socket path limit.

    Supports the context-manager protocol: on exception, prints the sandbox's
    log files to stderr before tearing the sandbox down, so CI failures are
    debuggable even when the test creates the sandbox inline (without using
    the gvc_sandbox fixture).
    """
    
    # === Init ===

    def __init__(self) -> None:
        # NOTE: mkdtemp under /tmp gives a short absolute path (~18 chars)
        self.root = Path(tempfile.mkdtemp(dir="/tmp", prefix="gvc-"))
        # NOTE: Matches gvc.paths.user_runtime_dir() when GVC_PLATFORMDIRS_ROOT is set
        self.runtime_dir = self.root / "runtime"

        self.env = {
            **os.environ,
            "GVC_PLATFORMDIRS_ROOT": str(self.root),
            "GVC_TEST_MODE": "1",
            # Disable auto-bundling by default, for fast test startup time.
            # Use enable_stub_app() to opt in.
            "GVC_NO_STUB_APP": "1",
        }

    def enable_stub_app(self) -> Self:
        """
        Switches this sandbox to generate a real stub app.
        Removes GVC_NO_STUB_APP and redirects stub generation into the sandbox.
        """
        self.env.pop("GVC_NO_STUB_APP", None)
        self.env["GVC_STUB_APP_DIR"] = str(self.root / "stub_app")
        return self
    
    # === Context Manager ===

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                self.print_log()
        finally:
            self.close()

    def close(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
    
    # === Operations ===

    def print_log(self) -> None:
        """Prints this sandbox's log files (cli.log, gvc.log) to stderr."""
        log_dir = self.root / "log"
        for name in ("cli.log", "gvc.log"):
            log_path = log_dir / name
            print(f"\n--- {name} (sandbox={self.root}) begin ---", file=sys.stderr)
            try:
                print(log_path.read_text(encoding="utf-8", errors="replace"), file=sys.stderr)
            except FileNotFoundError:
                print(f"<{name} not found at {log_path}>", file=sys.stderr)
            except Exception as e:
                print(f"<failed to read {log_path}: {type(e).__name__}: {e}>", file=sys.stderr)
            print(f"--- {name} end ---", file=sys.stderr)
