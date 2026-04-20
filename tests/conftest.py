"""
Registers fixtures shared by all test modules.
"""

from collections.abc import Generator
from harness.app import GvcApp
from harness.diff_fixture import DiffFixture, make_diff_fixture
from harness.sandbox import GvcSandbox
import pytest


@pytest.fixture
def gvc_sandbox() -> Generator[GvcSandbox, None, None]:
    sandbox = GvcSandbox()
    yield sandbox
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
