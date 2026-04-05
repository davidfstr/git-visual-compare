"""Parse unified diff output from ``git diff`` into structured data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

LineKind = Literal["context", "added", "removed", "hunk", "noeol"]


@dataclass
class LineDiff:
    kind: LineKind
    old_lineno: int | None  # None for added lines and hunk headers
    new_lineno: int | None  # None for removed lines and hunk headers
    text: str               # raw content, leading +/-/space stripped for content lines
    trailing_ws: bool = False  # True only for added lines with trailing whitespace


@dataclass
class Hunk:
    header: str             # raw "@@ -l,s +l,s @@ ..." line
    lines: list[LineDiff] = field(default_factory=list)


@dataclass
class FileDiff:
    status: Literal["added", "deleted", "modified", "renamed", "binary"]
    old_path: str
    new_path: str
    hunks: list[Hunk] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DIFF_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")
_RENAME_FROM = re.compile(r"^rename from (.+)$")
_RENAME_TO = re.compile(r"^rename to (.+)$")
_OLD_FILE = re.compile(r"^--- (?:a/)?(.+)$")
_NEW_FILE = re.compile(r"^\+\+\+ (?:b/)?(.+)$")
_HUNK_HEADER = re.compile(r"^(@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*)$")
_BINARY = re.compile(r"^Binary files .+ differ$")
_NO_EOL = r"\ No newline at end of file"

# Large diff thresholds
_LARGE_DIFF_BYTE_COUNT = 1_048_576   # 1 MB
_LARGE_DIFF_LINE_COUNT = 10_000


@dataclass(frozen=True)
class LargeDiffInfo:
    byte_count: int
    line_count: int

    @staticmethod
    def try_parse(diff_bytes: bytes) -> LargeDiffInfo | None:
        byte_count = len(diff_bytes)
        line_count = diff_bytes.count(b"\n")
        if byte_count > _LARGE_DIFF_BYTE_COUNT or line_count > _LARGE_DIFF_LINE_COUNT:
            return LargeDiffInfo(byte_count=byte_count, line_count=line_count)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse(raw: bytes) -> list[FileDiff]:
    """Parse unified diff bytes into a list of FileDiff objects."""
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()

    file_diffs: list[FileDiff] = []
    current: FileDiff | None = None
    current_hunk: Hunk | None = None
    old_lineno = 0
    new_lineno = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # New file diff header
        m = _DIFF_HEADER.match(line)
        if m:
            current = FileDiff(
                status="modified",
                old_path=m.group(1),
                new_path=m.group(2),
            )
            file_diffs.append(current)
            current_hunk = None
            i += 1
            continue

        if current is None:
            i += 1
            continue

        # Rename detection
        m = _RENAME_FROM.match(line)
        if m:
            current.old_path = m.group(1)
            current.status = "renamed"
            i += 1
            continue

        m = _RENAME_TO.match(line)
        if m:
            current.new_path = m.group(1)
            current.status = "renamed"
            i += 1
            continue

        # new file / deleted file mode lines
        if line.startswith("new file mode"):
            current.status = "added"
            i += 1
            continue

        if line.startswith("deleted file mode"):
            current.status = "deleted"
            i += 1
            continue

        # Binary
        if _BINARY.match(line):
            current.status = "binary"
            i += 1
            continue

        # --- / +++ lines (skip, we already have paths from the header)
        if line.startswith("--- ") or line.startswith("+++ "):
            # But pick up /dev/null to confirm add/delete status
            if line == "--- /dev/null":
                current.status = "added"
            elif line == "+++ /dev/null":
                current.status = "deleted"
            i += 1
            continue

        # Hunk header
        m = _HUNK_HEADER.match(line)
        if m:
            current_hunk = Hunk(header=m.group(1))
            current.hunks.append(current_hunk)
            old_lineno = int(m.group(2))
            new_lineno = int(m.group(4))
            i += 1
            continue

        if current_hunk is None:
            # Between diff header and first hunk (extended header lines)
            i += 1
            continue

        # No newline at end of file marker
        if line == _NO_EOL:
            current_hunk.lines.append(LineDiff(
                kind="noeol", old_lineno=None, new_lineno=None, text=line
            ))
            i += 1
            continue

        # Content lines
        if line.startswith("+"):
            content = line[1:]
            trailing = len(content) != len(content.rstrip(" \t"))
            current_hunk.lines.append(LineDiff(
                kind="added",
                old_lineno=None,
                new_lineno=new_lineno,
                text=content,
                trailing_ws=trailing,
            ))
            new_lineno += 1
        elif line.startswith("-"):
            current_hunk.lines.append(LineDiff(
                kind="removed",
                old_lineno=old_lineno,
                new_lineno=None,
                text=line[1:],
            ))
            old_lineno += 1
        elif line.startswith(" "):
            current_hunk.lines.append(LineDiff(
                kind="context",
                old_lineno=old_lineno,
                new_lineno=new_lineno,
                text=line[1:],
            ))
            old_lineno += 1
            new_lineno += 1
        # else: unrecognised line in hunk body — skip silently

        i += 1

    return file_diffs
