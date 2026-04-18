"""Render a list of FileDiff objects into a self-contained HTML document."""

from functools import cache
from gvc.diff_parser import LargeDiffInfo
import html
import importlib.resources
from typing import assert_never, TYPE_CHECKING

if TYPE_CHECKING:
    from gvc.diff_parser import FileDiff


# ------------------------------------------------------------------------------
# Public API

def render(
    file_diffs: list[FileDiff] | LargeDiffInfo,
) -> str:
    """Return a complete HTML document string for the given diff."""
    css, js, html_template = _assets()

    if isinstance(file_diffs, LargeDiffInfo):
        outline_html = ""
        diff_html = _render_large_diff_gate(file_diffs)
    elif isinstance(file_diffs, list):
        outline_html = _render_outline(file_diffs)
        diff_parts = [_render_file(fd, i) for i, fd in enumerate(file_diffs)]
        diff_html = "\n".join(diff_parts) if diff_parts else (
            '<p style="padding:24px;color:var(--hunk-fg)">No changes.</p>'
        )
    else:
        assert_never(file_diffs)

    doc = html_template
    doc = doc.replace("/* INLINE_CSS */", css)
    doc = doc.replace("/* INLINE_JS */", js)
    doc = doc.replace("<!-- OUTLINE_HTML -->", outline_html)
    doc = doc.replace("<!-- DIFF_HTML -->", diff_html)
    return doc



# ------------------------------------------------------------------------------
# Large Diff Gate

def _render_large_diff_gate(large_diff_info: LargeDiffInfo) -> str:
    size_mb = large_diff_info.byte_count / 1_000_000
    return (
        f'<div id="large-diff-gate">'
        f'This is a large diff ({size_mb:.1f} MB, ~{large_diff_info.line_count:,} lines). '
        f'<a href="#" onclick="revealFullDiff(); return false;">Click here to load.</a>'
        f'</div>'
    )



# ------------------------------------------------------------------------------
# Outline Rendering

def _render_outline(file_diffs: list["FileDiff"]) -> str:
    parts: list[str] = []
    parts.append(
        '<div id="outline-controls">'
        '<button class="outline-ctrl-btn" onclick="setAllSections(true)">Expand all</button>'
        '<button class="outline-ctrl-btn" onclick="setAllSections(false)">Collapse all</button>'
        '</div>'
    )
    for idx, fd in enumerate(file_diffs):
        status_icon, status_label, file_path = _diff_header(fd)
        file_path_e = _e(file_path)
        parts.append(
            f'<a class="outline-file" href="#file-{idx}" title="{status_label}: {file_path_e}">'
            f'<span class="outline-status">{status_icon}</span>{file_path_e}</a>'
        )
    return "\n".join(parts)


def _diff_header(fd: FileDiff) -> tuple[str, str, str]:
    status_icon, status_label = _STATUS_ICONS.get(
        fd.status,
        (_UNKNOWN_STATUS_ICON, fd.status.capitalize()))
    if fd.status == "renamed":
        file_path = f"{fd.old_path} → {fd.new_path}"
    else:
        file_path = fd.new_path or fd.old_path
    return status_icon, status_label, file_path



# ------------------------------------------------------------------------------
# Per-File Rendering

_STATUS_ICONS = {
    "added":    ("➕", "Added"),
    "deleted":  ("❌", "Deleted"),
    "modified": ("✏️", "Modified"),
    "renamed":  ("🚚", "Renamed"),
    "binary":   ("📄", "Binary"),
}
_UNKNOWN_STATUS_ICON = "❓"


def _render_file(fd: FileDiff, idx: int) -> str:
    status_icon, status_label, file_path = _diff_header(fd)
    file_path_e = _e(file_path)

    parts: list[str] = []
    parts.append(
        f'<details class="file-section" id="file-{idx}" open>'
        f'<summary>'
        f'<span class="file-status-icon" title="{status_label}">{status_icon}</span>'
        f'<span class="file-path">{file_path_e}</span>'
        f'</summary>'
    )

    if fd.status == "binary":
        parts.append('<p style="padding:6px 12px;color:var(--hunk-fg)">Binary file differs</p>')
    elif not fd.hunks:
        parts.append('<p style="padding:6px 12px;color:var(--hunk-fg)">No changes</p>')
    else:
        parts.append('<table class="diff-table"><tbody>')
        for hunk in fd.hunks:
            # Hunk seam row
            parts.append(
                '<tr class="line-hunk">'
                '<td class="ln-old"></td>'
                '<td class="ln-new"></td>'
                f'<td class="content"><span class="line-marker"> </span>{_e(hunk.header)}</td>'
                '</tr>'
            )
            for line in hunk.lines:
                if line.kind == "added":
                    row_class = "line-added"
                    marker = "+"
                elif line.kind == "removed":
                    row_class = "line-removed"
                    marker = "-"
                elif line.kind == "context":
                    row_class = "line-context"
                    marker = " "
                elif line.kind == "noeol":
                    parts.append(
                        '<tr class="line-noeol">'
                        '<td class="ln-old"></td>'
                        '<td class="ln-new"></td>'
                        f'<td class="content"><span class="line-marker"> </span>{_e(line.text)}</td>'
                        '</tr>'
                    )
                    continue
                else:
                    assert_never(line.kind)

                content_html = _render_content(line.text, line.trailing_ws)
                parts.append(
                    f'<tr class="{row_class}">'
                    f'<td class="ln-old">{_lineno(line.old_lineno)}</td>'
                    f'<td class="ln-new">{_lineno(line.new_lineno)}</td>'
                    f'<td class="content"><span class="line-marker">{marker}</span>{content_html}</td>'
                    '</tr>'
                )
        parts.append('</tbody></table>')

    parts.append('</details>')
    return "".join(parts)



# ------------------------------------------------------------------------------
# Utility: Asset Loading

@cache
def _assets() -> tuple[str, str, str]:
    _CSS = _load_asset("diff.css")
    _JS = _load_asset("diff.js")
    _HTML_TEMPLATE = _load_asset("diff.html")
    return _CSS, _JS, _HTML_TEMPLATE


def _load_asset(name: str) -> str:
    pkg = importlib.resources.files("gvc") / "assets" / name
    return pkg.read_text(encoding="utf-8")


# ------------------------------------------------------------------------------
# Utility: HTML

def _e(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(text, quote=False)


def _lineno(n: int | None) -> str:
    return str(n) if n is not None else ""


def _render_content(text: str, trailing_ws: bool) -> str:
    """
    Return HTML for a content cell: escape, expand tabs, optionally
    wrap trailing whitespace in a highlight span.
    """
    expanded = _expand_tabs(text)
    if trailing_ws:
        stripped = expanded.rstrip(" ")
        ws = expanded[len(stripped):]
        return _e(stripped) + f'<span class="trailing-ws">{_e(ws)}</span>'
    return _e(expanded)


def _expand_tabs(text: str, tabsize: int = 4) -> str:
    """Expand tabs to spaces (4-column per macOS convention)."""
    return text.expandtabs(tabsize)


# ------------------------------------------------------------------------------
