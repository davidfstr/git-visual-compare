"""
Registers fixtures shared by all test modules.
"""

from collections.abc import Generator
from harness.app import GvcApp
from harness.diff_fixture import DiffFixture, make_diff_fixture
from harness.sandbox import GvcSandbox
import pytest
from typing import Any


# ------------------------------------------------------------------------------
# Fixtures

@pytest.fixture
def gvc_sandbox(
    request: pytest.FixtureRequest,
) -> Generator[GvcSandbox, None, None]:
    sandbox = GvcSandbox()
    try:
        yield sandbox
    finally:
        # If the test which this fixture was used in failed (during its "call" phase)
        # then print the sandbox's log files before destroying the sandbox
        rep_call: pytest.TestReport | None = getattr(request.node, "rep_call", None)
        if rep_call is not None and rep_call.failed:
            sandbox.print_log()
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
