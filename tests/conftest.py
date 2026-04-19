"""
Registers fixtures shared by all test modules.
"""

from collections.abc import Generator
from harness.app import GvcApp
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
