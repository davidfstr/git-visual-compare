from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from harness.playwrightkit._page import Page


class Locator:
    """
    Lazy, re-resolving locator in the Playwright style.

    Locators are immutable; chaining (.locator(), .nth(), .first) returns a
    new Locator with the selector chain appended. Actions and readers each
    perform one eval_js round-trip which re-resolves the chain from document
    root every time. This matches Playwright's semantics and keeps state
    entirely in the DOM.
    """

    def __init__(self, page: Page, chain: list[dict[str, Any]]) -> None:
        self._page = page
        self._chain = chain

    # === Chaining ===

    def locator(self, selector: str) -> Locator:
        return Locator(
            self._page,
            self._chain + [{"op": "locator", "selector": selector}],
        )

    def nth(self, index: int) -> Locator:
        return Locator(
            self._page,
            self._chain + [{"op": "nth", "index": index}],
        )

    @property
    def first(self) -> Locator:
        return self.nth(0)

    @property
    def last(self) -> Locator:
        return self.nth(-1)

    # === Readers ===

    def count(self) -> int:
        result = self._page._op("count", self._chain)
        assert isinstance(result, int)
        return result

    def text_content(self) -> str | None:
        result = self._page._op("textContent", self._chain)
        if result is None:
            return None
        assert isinstance(result, str)
        return result

    def inner_text(self) -> str | None:
        result = self._page._op("innerText", self._chain)
        if result is None:
            return None
        assert isinstance(result, str)
        return result

    def get_attribute(self, name: str) -> str | None:
        result = self._page._op("getAttribute", self._chain, name)
        if result is None:
            return None
        assert isinstance(result, str)
        return result

    def input_value(self) -> str:
        result = self._page._op("inputValue", self._chain)
        if result is None:
            raise AssertionError(f"input_value: no element matched {self!r}")
        assert isinstance(result, str)
        return result

    def is_visible(self) -> bool:
        result = self._page._op("isVisible", self._chain)
        return bool(result)

    def evaluate(self, js: str) -> object:
        """
        Evaluates a JS function expression like `el => ...` against the first
        matched element. Escape hatch; prefer dedicated readers when possible.
        """
        return self._page._op("evaluate", self._chain, js)

    # === Actions ===

    def click(self) -> None:
        self._page._op("click", self._chain)

    # === Repr ===

    def __repr__(self) -> str:
        return f"Locator({self._chain!r})"
