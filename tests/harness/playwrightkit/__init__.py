"""
PlaywrightKit: a Playwright-shaped DOM facade over a narrow eval_js primitive.

Usage:

    from harness.playwrightkit import expect

    page = gvc_app.page(window_id)
    expect(page.locator('.outline-file')).to_have_count(5)

Each Python call on Page/Locator/expect translates into one eval_js
round-trip through TestClient. Assertions auto-retry with a polling
loop (default 5s timeout), matching Playwright's expect().

See README.md for history, interface overview, and divergences from
the real Playwright API.
"""

from harness.playwrightkit._expect import expect, LocatorAssertions
from harness.playwrightkit._locator import Locator
from harness.playwrightkit._page import Page


__all__ = ["expect", "Locator", "LocatorAssertions", "Page"]
