# PlaywrightKit

A small library for building a **Playwright-shaped DOM testing API** on top of
a narrow, application-provided `eval_js` primitive.

Python tests describe what they want to check against a remote browser-like
context ("this locator should have text X"); PlaywrightKit translates each call
into a single JavaScript snippet, ships it over `eval_js`, unwraps the result,
and retries assertions until they hold.

## History

PlaywrightKit was extracted from the `gvc` (git-visual-compare) test harness,
where we wanted to drive the DOM of `pywebview`-hosted diff windows from
`pytest`. The real [Playwright] library expects to control a browser it
launches itself via CDP/WebKit; it had no way to attach to an already-running
`pywebview` window that exposes only a custom `webview.Window.evaluate_js(src)`
call over a Unix socket.

Rather than invent an ad-hoc query API, we copied the shape of
`playwright.sync_api` — `Page`, `Locator`, `expect(...)` with retrying
assertions — and implemented it on top of `eval_js`. The result is small
enough to live next to the tests it supports, but structured so it can be
lifted out into its own library when another project needs the same shape.

[Playwright]: https://playwright.dev/python/

## What it provides

The public surface (`from harness.playwrightkit import ...`):

- **`Page`** — a handle to one browser-like context, identified by an opaque
  window id. Methods: `locator(selector)`, `evaluate(js)`, `press(key)`
  (dispatches a `KeyboardEvent` to `document`).
- **`Locator`** — a lazy, immutable selector chain.
    - Chaining via `.locator()`, `.nth()`, `.first`, `.last` returns a new
      locator and performs **zero** round-trips.
    - Readers and actions each perform **one** round-trip and re-resolve from
      the document root (matching Playwright semantics).
        - Readers: `count`, `text_content`, `inner_text`, `get_attribute`,
          `input_value`, `is_visible`, `evaluate`.
        - Actions: `click`, `fill`, `press`.
- **`expect(locator)`** — returns a `LocatorAssertions` that polls until the
  condition holds or a 5 s timeout expires (50 ms poll interval).
    - Supports `to_have_count`, `to_have_text`, `to_contain_text`,
      `to_be_visible`, `to_be_in_viewport`, `to_have_attribute`,
      `to_have_css`, `to_have_class`, and the `not_*` variants of each.

Internally:

- **`_runtime.js`** — the PlaywrightKit **Runtime Library**, the in-page JS
  half of the library. Idempotently installs itself as `window.pwk` on the
  first call, dispatches one op per invocation, returns `{ok: ...}` or
  `{error: ...}`.
- **`_jsbridge.py`** — templates kind/chain/arg into the runtime source as
  JSON literals and calls through to the host's `eval_js`.

Each Python call on `Page`/`Locator`/`expect` is exactly one `eval_js`
round-trip; state lives entirely in the DOM.

## Known divergences from real Playwright

PlaywrightKit deliberately mirrors Playwright where it can, but it is not a
drop-in replacement. Current divergences:

- **No browser lifecycle.** No `sync_playwright()`, `browser_type.launch()`,
  `new_context()`, or `new_page()`. The host application is responsible for
  creating browser-like contexts and handing window ids to the tests.
- **No navigation.** No `page.goto()`, `page.reload()`, back/forward,
  network interception, or download handling.
- **Selectors.** Only CSS selectors via `querySelectorAll` are supported.
  Playwright's `text=`, `role=`, `>>`, XPath, and layout engines are **not**
  implemented.
- **Narrower locator chaining.** `.locator()`, `.nth()`, `.first`, `.last`
  only. No `.filter()`, `.and_()`, `.or_()`, `.get_by_*()`.
- **Actions.** `click()`, `fill()` (sets `el.value` + fires an `input`
  event), and `press(key)` (dispatches a synthesized `KeyboardEvent` —
  `Page.press` targets `document`, `Locator.press` targets the resolved
  element). No hover, drag, file upload, mouse events, focus,
  scroll-into-view, or text selection. `fill`/`press` take a single chain
  and a single argument; no multi-target op shape exists yet, so actions
  needing a source *and* target (e.g. `drag_to`) would be the first to
  introduce one.
- **Clipboard.** No clipboard read/write. `navigator.clipboard` is
  typically blocked in `pywebview` contexts, so tests that need to
  inspect the clipboard should add a host-side RPC (e.g. `pbpaste` on
  macOS, `NSPasteboard`) rather than a PlaywrightKit op.
- **Text selection.** Synthesized `MouseEvent`s do not drive native text
  selection in most webviews; a future `select_text`-style op should use
  the JS `Selection`/`Range` API (`getSelection().setBaseAndExtent(...)`)
  rather than mouse-down/move/up.
- **Visibility heuristic.** `isVisible` checks `display`, `visibility`,
  `opacity`, and bounding rect — it does **not** consult Playwright's full
  actionability model (pointer-events, overlap, stable position, etc.).
- **Assertion surface.** The positive/`not_*` assertions listed above only;
  no `to_have_value`, `to_be_enabled`, `to_be_checked`, soft assertions,
  or custom timeouts per-assertion (timeout is fixed at construction).
  `to_be_in_viewport` accepts `ratio` but omits Playwright's full
  actionability checks (no stable-position / scroll-settling heuristics).
- **Text normalization.** `to_have_text` collapses whitespace runs to a
  single space and strips — approximating Playwright but not identical.
- **No auto-waiting on actions.** `click()` fails immediately if no element
  matches; Playwright would wait and retry.
- **Error types.** Failures surface as `AssertionError` (for `expect`) or the
  host's `EvalJsError` (for transport/JS errors), not `TimeoutError` /
  `Error` subclasses from `playwright._impl`.

## Extracting PlaywrightKit from gvc

PlaywrightKit is currently vendored under `tests/harness/playwrightkit/` and
couples to gvc's test harness in a few small places. To lift it out into a
standalone package, roughly:

1. **Define a transport protocol.** PlaywrightKit only needs an object with
   an `eval_js(window_id: str, src: str) -> object` method whose return value
   is a `{"ok": ...}` / `{"error": str}` dict. Today `_jsbridge.op` reaches
   into `page._client.eval_js(...)`; replace with a typed `Protocol` (or ABC)
   that the host implements. `EvalJsError` (currently in `harness.client`)
   would move into the library or be parameterized.
2. **Parameterize the "window id" concept.** The library treats ids as
   opaque strings. Nothing about their provenance (Unix socket, CDP target,
   pywebview uid, tab guid) leaks into PlaywrightKit — just keep it a `str`.
3. **Relocate `Page` construction.** `GvcApp.page(window_id)` is the
   current factory. Consumers would call `Page(transport, window_id)`
   directly, or the library could expose a helper factory.
4. **Package the runtime JS.** `_jsbridge.py` loads `_runtime.js` via
   `importlib.resources.files("harness.playwrightkit")`. Update the package
   name (e.g. `"playwrightkit"`) and ensure the `.js` is declared as package
   data in `pyproject.toml`.
5. **Decide on dependencies.** The library is pure stdlib Python today
   (`time`, `json`, `importlib.resources`, `typing`). Keep it that way on
   extraction — no `anyio`, no `playwright` import.
6. **Tests for the library itself.** Gvc's tests exercise the library by
   proxy. An extracted package should add self-tests that drive a minimal
   host (e.g. a `pytest-playwright`-backed shim, or a headless browser
   harness) to verify each op/assertion independently of gvc.

The module layout (`_page.py`, `_locator.py`, `_expect.py`, `_jsbridge.py`,
`_runtime.js`) is already library-shaped; the main disentangling work is
replacing the three import sites that mention `harness.client` /
`harness.playwrightkit` with a clean protocol boundary.
