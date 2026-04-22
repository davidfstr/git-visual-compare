"""
Registers fixtures shared by all test modules.
"""

from collections.abc import Generator
from harness.app import GvcApp
from harness.diff_fixture import DiffFixture, make_diff_fixture
from harness.sandbox import GvcSandbox
from pathlib import Path
import pytest
import sys
from typing import Any


# ------------------------------------------------------------------------------
# Fixtures

@pytest.fixture
def gvc_sandbox(
    request: pytest.FixtureRequest,
) -> Generator[GvcSandbox, None, None]:
    sandbox = GvcSandbox()
    yield sandbox
    try:
        # If the test which this fixture was used in failed (during its "call" phase)
        # then print the sandbox's log file before destroying the sandbox
        rep_call: pytest.TestReport | None = getattr(request.node, "rep_call", None)
        if rep_call is not None and rep_call.failed:
            _print_gvc_log(sandbox.root)
    finally:
        sandbox.close()


@pytest.fixture
def gvc_app(gvc_sandbox: GvcSandbox) -> Generator[GvcApp, None, None]:
    app = GvcApp(gvc_sandbox)
    yield app
    app.close()


@pytest.fixture
def diff_fixture() -> Generator[DiffFixture, None, None]:
    """A temp git repo with a diff containing all five file statuses."""
    fixture = make_diff_fixture()
    yield fixture
    fixture.close()


# ------------------------------------------------------------------------------
# Hookwrappers

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    """
    For each phase of running a test, save's the phase's result on the test item:
    - item.rep_setup: pytest.TestReport
    - item.rep_call: pytest.TestReport
    - item.rep_teardown: pytest.TestReport
    """
    outcome = yield
    report: pytest.TestReport = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


# ------------------------------------------------------------------------------
# Internal Utility

def _print_gvc_log(sandbox_root: Path) -> None:
    log_path = sandbox_root / "log" / "gvc.log"
    print("\n--- gvc.log (on test failure) begin ---", file=sys.stderr)
    print(f"path={log_path}", file=sys.stderr)
    try:
        print(log_path.read_text(encoding="utf-8", errors="replace"), file=sys.stderr)
    except FileNotFoundError:
        print("<gvc.log not found>", file=sys.stderr)
    except Exception as e:
        print(f"<failed to read gvc.log: {type(e).__name__}: {e}>", file=sys.stderr)
    print("--- gvc.log (on test failure) end ---", file=sys.stderr)


# ------------------------------------------------------------------------------
