from collections.abc import Callable
import time
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from harness.playwrightkit._locator import Locator


DEFAULT_TIMEOUT = 5.0  # seconds
POLL_INTERVAL = 0.05


_UNSET: object = object()
_T = TypeVar("_T")


class LocatorAssertions:
    """
    Retrying assertions on a Locator, mirroring playwright.sync_api.expect(loc).

    Each assertion polls (re-resolving the locator each time) until the
    condition holds or the timeout expires, then raises AssertionError
    with the last observed value.
    """

    def __init__(self, locator: Locator, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._locator = locator
        self._timeout = timeout

    # === Positive ===

    def to_have_count(self, count: int) -> None:
        self._retry(
            predicate=lambda: (self._locator.count(), lambda v: v == count),
            describe=lambda v: f"expected count {count}, got {v}",
        )

    def to_have_text(self, text: str) -> None:
        self._retry(
            predicate=lambda: (
                self._locator.text_content() or "",
                lambda v: _normalize_ws(v) == _normalize_ws(text),
            ),
            describe=lambda v: f"expected text {text!r}, got {v!r}",
        )

    def to_contain_text(self, text: str) -> None:
        self._retry(
            predicate=lambda: (
                self._locator.text_content() or "",
                lambda v: text in v,
            ),
            describe=lambda v: f"expected text to contain {text!r}, got {v!r}",
        )

    def to_be_visible(self) -> None:
        self._retry(
            predicate=lambda: (self._locator.is_visible(), lambda v: v is True),
            describe=lambda v: f"expected visible, got is_visible={v}",
        )

    def to_be_in_viewport(self, ratio: float | None = None) -> None:
        """
        Asserts that the element's bounding rect intersects the viewport.

        With `ratio` omitted or 0, any intersection counts. With `ratio` in
        (0, 1], at least that fraction of the element's area must lie inside
        the viewport. Mirrors Playwright's expect(loc).to_be_in_viewport(ratio).
        """
        self._retry(
            predicate=lambda: (
                self._locator._page._op("inViewport", self._locator._chain, ratio),
                lambda v: v is True,
            ),
            describe=lambda v: f"expected in viewport (ratio={ratio}), got in_viewport={v}",
        )

    def to_have_attribute(self, name: str, value: object = _UNSET) -> None:
        if value is _UNSET:
            self._retry(
                predicate=lambda: (
                    self._locator._page._op("hasAttribute", self._locator._chain, name),
                    lambda v: bool(v),
                ),
                describe=lambda v: f"expected attribute {name!r} to be present, hasAttribute={v}",
            )
        else:
            self._retry(
                predicate=lambda: (
                    self._locator.get_attribute(name),
                    lambda v: v == value,
                ),
                describe=lambda v: f"expected attribute {name!r}={value!r}, got {v!r}",
            )

    def to_have_css(self, prop: str, value: str) -> None:
        self._retry(
            predicate=lambda: (
                self._locator._page._op("computedCss", self._locator._chain, prop),
                lambda v: v == value,
            ),
            describe=lambda v: f"expected CSS {prop}={value!r}, got {v!r}",
        )

    def to_have_class(self, class_name: str) -> None:
        self._retry(
            predicate=lambda: (
                self._locator._page._op("classList", self._locator._chain),
                lambda v: isinstance(v, list) and class_name in v,
            ),
            describe=lambda v: f"expected class {class_name!r} in {v!r}",
        )

    # === Negated ===

    def not_to_have_count(self, count: int) -> None:
        self._retry(
            predicate=lambda: (self._locator.count(), lambda v: v != count),
            describe=lambda v: f"expected count != {count}, got {v}",
        )

    def not_to_have_text(self, text: str) -> None:
        self._retry(
            predicate=lambda: (
                self._locator.text_content() or "",
                lambda v: _normalize_ws(v) != _normalize_ws(text),
            ),
            describe=lambda v: f"expected text != {text!r}, got {v!r}",
        )

    def not_to_contain_text(self, text: str) -> None:
        self._retry(
            predicate=lambda: (
                self._locator.text_content() or "",
                lambda v: text not in v,
            ),
            describe=lambda v: f"expected text to not contain {text!r}, got {v!r}",
        )

    def not_to_be_visible(self) -> None:
        self._retry(
            predicate=lambda: (self._locator.is_visible(), lambda v: v is False),
            describe=lambda v: f"expected not visible, got is_visible={v}",
        )

    def not_to_be_in_viewport(self, ratio: float | None = None) -> None:
        self._retry(
            predicate=lambda: (
                self._locator._page._op("inViewport", self._locator._chain, ratio),
                lambda v: v is False,
            ),
            describe=lambda v: f"expected not in viewport (ratio={ratio}), got in_viewport={v}",
        )

    def not_to_have_attribute(self, name: str, value: object = _UNSET) -> None:
        if value is _UNSET:
            self._retry(
                predicate=lambda: (
                    self._locator._page._op("hasAttribute", self._locator._chain, name),
                    lambda v: not bool(v),
                ),
                describe=lambda v: f"expected attribute {name!r} to be absent, hasAttribute={v}",
            )
        else:
            self._retry(
                predicate=lambda: (
                    self._locator.get_attribute(name),
                    lambda v: v != value,
                ),
                describe=lambda v: f"expected attribute {name!r} != {value!r}, got {v!r}",
            )

    def not_to_have_class(self, class_name: str) -> None:
        self._retry(
            predicate=lambda: (
                self._locator._page._op("classList", self._locator._chain),
                lambda v: isinstance(v, list) and class_name not in v,
            ),
            describe=lambda v: f"expected class {class_name!r} not in {v!r}",
        )

    # === Utility ===

    def _retry(
        self,
        predicate: Callable[[], tuple[_T, Callable[[_T], bool]]],
        describe: Callable[[_T], str],
    ) -> None:
        deadline = time.monotonic() + self._timeout  # capture
        while True:
            last_value, check = predicate()
            if check(last_value):
                return
            if time.monotonic() >= deadline:
                raise AssertionError(
                    f"{describe(last_value)} "
                    f"(timeout={self._timeout}s, locator={self._locator!r})"
                )
            time.sleep(POLL_INTERVAL)


def _normalize_ws(s: str) -> str:
    """Collapses whitespace runs to one space and strips; matches Playwright's text comparison."""
    return " ".join(s.split())


def expect(locator: Locator) -> LocatorAssertions:
    return LocatorAssertions(locator)
