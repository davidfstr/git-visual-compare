from harness.client import TestClient
from harness.playwrightkit._jsbridge import op as _op
from harness.playwrightkit._locator import Locator
from typing import Any


class Page:
    """
    A Playwright-shaped handle to the DOM of one diff window.

    Each call translates into exactly one eval_js round-trip.
    """

    def __init__(self, client: TestClient, window_id: str) -> None:
        self._client = client
        self._window_id = window_id

    # === Locators ===

    def locator(self, selector: str) -> Locator:
        return Locator(self, [{"op": "locator", "selector": selector}])

    # === Readers ===

    def evaluate(self, js: str) -> object:
        """
        Evaluates a no-arg JS function expression like `() => ...` against the page.
        """
        return _op(self, "evaluatePage", [], js)

    # === Internal (used by Locator / LocatorAssertions) ===

    def _op(self, kind: str, chain: list[dict[str, Any]], arg: object = None) -> object:
        return _op(self, kind, chain, arg)
