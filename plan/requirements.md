# Git Visual Compare (gvc) — Requirements Specification

**Version:** 1.0.0  
**Date:** 2026-03-31

Based on full conversation in:
- inception.md

## Overview

`gvc` is a lightweight GUI tool for viewing `git diff` output in a native macOS
window, using a style closely matching GitX's `--diff` mode. It is implemented
in Python using pywebview for the UI layer and the locally installed `git` for
generating diffs.

---

## 1. Command-Line Interface

### 1.1 Basic Syntax

```
gvc [options] [<git-diff-args>...]
```

`gvc` passes its arguments through to `git diff`. Examples:

```bash
gvc HEAD~3 HEAD
gvc abc123 def456
gvc abc123 def456 -- src/foo.py src/bar.py
gvc --cached
gvc                  # working tree changes (unstaged)
gvc -w HEAD~1 HEAD   # ignore whitespace
gvc -U20 HEAD~1 HEAD # 20 lines of context
```

### 1.2 Supported Options

| Option | Description |
|--------|-------------|
| `-w` | Ignore whitespace (passed to `git diff`) |
| `-U<n>` | Context lines (passed to `git diff`, git default of 3 if omitted) |
| `--cached` / `--staged` | Diff staged changes |
| `-- <paths>` | Limit diff to specific files |
| Any valid `git diff` arg | Passed through to `git diff` |

### 1.3 Rename Detection

Rename detection is enabled by default (`-M` with git's default 50% threshold).

### 1.4 Error Handling

- If `git diff` fails (e.g. invalid args, not in a repo), print the error to
  stderr and exit with a non-zero exit code. No window is opened.

---

## 2. Window Behavior

### 2.1 Multiple Windows

Each `gvc` invocation opens a new, separate window.

### 2.2 Window Size & Position

- **Initial size:** Wide enough to display ~100 columns of monospace text;
  tall enough to span from the top of the screen to the bottom.
- **Position memory:** The app remembers the last window size and position.
- **Stacking:** New windows open offset X pixels to the right and Y pixels
  down from the last-opened window. In the common case where the window is
  full top-to-bottom, there is no room to shift down, so only the horizontal
  offset applies.

### 2.3 Window Lifecycle

- **Cmd+W:** Closes the current window.
- **Cmd+Q:** Quits the application (closes all windows).
- Closing the last window does **not** quit the app; it stays running with
  no windows (standard macOS document-app convention).

---

## 3. Diff Display

### 3.1 Layout

1. **File outline** (top of window): A static list of all files in the diff.
   - Each file shows a status indicator (Added / Modified / Deleted / Renamed).
     Icons or emoji are acceptable for status indicators.
   - For renames, show both old and new paths
     (e.g. "old/path.py -> new/path.py").
   - Clicking a file scrolls to that file's section in the diff.
2. **File sections** (below the outline): One collapsible section per file.
   - Default state: expanded.
   - Collapsible via a disclosure triangle on the file header.
   - **Expand all / Collapse all** toggle available.

### 3.2 Line Display

- **Line numbers:** Both old and new line numbers displayed, GitX-style
  (see inception-screenshots/3.png).
- **Font:** System monospace default.
- **Font size:** Adjustable via Cmd+Plus / Cmd+Minus. Applies to all open
  windows. Remembered across sessions.
- **Tabs:** Rendered at 4-column width (macOS convention).

### 3.3 Color Scheme

#### Light Mode (GitX-style defaults)
| Element | Background Color |
|---------|-----------------|
| Added lines | Light green |
| Removed lines | Light red/pink |
| Trailing whitespace on added lines | Distinct highlight (e.g. darker green) |
| Hunk seam lines (`@@...@@`) | Blue/purple tint |

#### Dark Mode
Reasonable dark-mode equivalents of the above (dark green tint, dark red tint,
etc.), chosen for adequate contrast.

### 3.4 Rename Display

Renamed files display a header like:
"Dockerfile.lambda renamed to src/crystal_on_aws/Dockerfile.lambda"
(see inception-screenshots/5.png).

### 3.5 Binary Files

Binary files in the diff display "Binary file differs" (matching git's output).

### 3.6 Large Diff Guard

If the total diff output exceeds **1 MB** or **10,000 lines**, the diff is not
rendered immediately. Instead, display a message:

> "This is a large diff (X files, Y lines). Click here to load."

Clicking the link/button loads and renders the full diff.

---

## 4. Light & Dark Mode

- Detect the operating system's current appearance mode (light/dark).
- Switch immediately when the OS mode changes (e.g. sunrise/sunset auto
  transition) without requiring a relaunch or window reopen.

---

## 5. Find

### 5.1 Find Bar

- Appears at the **top** of the window.
- Activated via **Cmd+F**.
- Contains:
  - Text input field
  - Toggle buttons (VS Code style) for:
    - Case-insensitive matching (on by default)
    - Whole word match
    - Regex

### 5.2 Navigation

- **Cmd+G:** Find Next
- **Shift+Cmd+G:** Find Previous
- When Find Next/Previous wraps around the document, briefly flash a large
  wrap-around icon (e.g. large centered overlay) in the center of the window.

---

## 6. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Cmd+F | Open Find bar |
| Cmd+G | Find Next |
| Shift+Cmd+G | Find Previous |
| Cmd+Plus | Increase font size |
| Cmd+Minus | Decrease font size |
| Cmd+W | Close window |
| Cmd+Q | Quit application |

---

## 7. Technical Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.14+ |
| UI framework | pywebview (native platform WebView) |
| Diff generation | Local `git` installation |
| Packaging (macOS) | PyInstaller (.app bundle) |
| Distribution | pip / pipx / uv installable; also as standalone .app |

---

## 8. Persistence

The following settings are persisted across sessions:
- Window size and position
- Font size

---

## 9. Future Extensions

Listed here for reference; explicitly out of scope for v1.0.0:

- `gvc -C /path/to/repo diff ...` (run against a specific repo)
- Menu bar (File: Close Window, Quit; Edit: Find, Find Next, Find Previous)
- Automatic updates via appcast / Sparkle-style mechanism
- About box
- E2E automated tests with Playwright (test names in given-when-then format)
- `git difftool -d` integration for use with tools like Fork
- Windows / Linux packaging
