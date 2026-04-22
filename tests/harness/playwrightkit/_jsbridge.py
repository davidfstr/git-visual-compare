"""
Templates and dispatches JS for a single eval_js round-trip.
"""

from importlib.resources import files
import json
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from harness.playwrightkit._page import Page


_RUNTIME_SRC = (files("harness.playwrightkit") / "_runtime.js").read_text(encoding="utf-8")


def op(page: Page, kind: str, chain: list[dict[str, Any]], arg: object = None) -> object:
    """
    Builds the runtime+op JS, dispatches it over eval_js, returns the unwrapped result.

    Raises harness.client.EvalJsError if the PlaywrightKit runtime or the
    underlying evaluate_js raised.
    """
    src = (
        _RUNTIME_SRC
        .replace("__GVC_KIND__", json.dumps(kind))
        .replace("__GVC_CHAIN__", json.dumps(chain))
        .replace("__GVC_ARG__", json.dumps(arg))
    )
    return page._client.eval_js(page._window_id, src)
