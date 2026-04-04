# Project Guidelines

## Code Style

- Python ≥ 3.14 required. Use modern syntax (type unions with `|`, etc.)
- Strings use double quotes (`"`) rather than single quotes (`'`)
- Always include `from __future__ import annotations` at the top of modules
    - NOTE: Will eliminate soon, because Python 3.14+ always uses deferred annotations, which supercede this future's effect
- Use `TYPE_CHECKING` blocks for imports needed only by type checkers
- Full type annotations on all function signatures
- Use `@dataclass` for structural data types
- Private modules: `_name.py`; private functions: `_name()`; constants: `SCREAMING_SNAKE_CASE`
- Imports ordered: stdlib → third-party → local
    - NOTE: Will transition in the future to just alphabetical, without separating imports by category

## Architecture

Process-based GUI with Unix socket IPC. Two processes collaborate:

1. **CLI process** (`cli.py`): runs `git diff`, writes result to temp file, sends path via socket, exits immediately
2. **GUI server** (`_gui.py`): persistent Cocoa event loop, listens on Unix socket, opens pywebview windows

Key module boundaries — see [doc/module_map.txt](../doc/module_map.txt) for the full map:

| Module | Responsibility |
|--------|---------------|
| `cli.py` | Entry point, git invocation, IPC client |
| `_gui.py` | Server lifecycle, Cocoa event loop, socket listener |
| `_ipc.py` | Stateless IPC helpers (socket path, temp file I/O) |
| `diff_parser.py` | Unified diff bytes → `list[FileDiff]` |
| `renderer.py` | Parsed diffs → self-contained HTML (CSS+JS inlined) |
| `window_manager.py` | pywebview window creation, cascading, dark mode |
| `app_api.py` | JS↔Python bridge for preferences |
| `prefs.py` | Persistent JSON settings with atomic writes |

Assets (CSS/JS/HTML) live in `src/gvc/assets/` and are inlined into rendered HTML at runtime — no HTTP server.

## Build and Test

```bash
# Setup
python -m venv venv && venv/bin/pip install -e .

# Run
gvc [git-diff-args...]
```

No automated test suite yet.

## Conventions

- **Platform directories**: use `platformdirs` for all config/data/runtime/log paths — never hardcode `~/` paths
- **Dark mode**: detect via `NSUserDefaults` at window creation; CSS uses `@media prefers-color-scheme` for live following
- **Error handling in threads**: catch exceptions and call `traceback.print_exc()`; degrade gracefully on socket errors

## Documentation

- [doc/how_it_works.md](../doc/how_it_works.md) — architecture walkthrough
- [plan/requirements.md](../plan/requirements.md) — feature specification, keyboard shortcuts, rendering rules
- [plan/inception.md](../plan/inception.md) — design rationale and decision log
