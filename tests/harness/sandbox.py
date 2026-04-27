import os
from pathlib import Path
import shutil
import tempfile
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
    """

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

    def close(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
