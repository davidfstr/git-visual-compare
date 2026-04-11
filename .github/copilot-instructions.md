# Project Guidelines

## Code Style

- Python ≥ 3.14 required. Use modern syntax (type unions with `|`, etc.). All type annotations deferred automatically.
- Use `TYPE_CHECKING` blocks for imports needed only by type checkers
- Full type annotations on all function signatures
- Strings use double quotes (`"`) rather than single quotes (`'`)
- Use `@dataclass` for structural data types
- Private functions: `_name()`; constants: `SCREAMING_SNAKE_CASE`
- Imports ordered alphabetically

## Architecture

Process-based GUI with Unix socket IPC. Two processes collaborate:

1. **CLI process** (`cli.py`): runs `git diff`, writes result to temp file, sends path via socket, exits immediately
2. **GUI server** (`gui.py`): persistent Cocoa event loop, listens on Unix socket, opens pywebview windows

Key module boundaries — see [doc/module_map.txt](../doc/module_map.txt) for the full map:

| Module | Responsibility |
|--------|---------------|
| `cli.py` | Entry point, git invocation, IPC client |
| `gui.py` | Server lifecycle, Cocoa event loop, socket listener |
| `ipc.py` | Stateless IPC helpers (socket path, temp file I/O) |
| `diff_parser.py` | Unified diff bytes → `list[FileDiff]` |
| `renderer.py` | Parsed diffs → self-contained HTML (CSS+JS inlined) |
| `window_manager.py` | pywebview window creation, cascading, dark mode |
| `app_api.py` | JS↔Python bridge for preferences |
| `prefs.py` | Persistent JSON settings with atomic writes |

Assets (CSS/JS/HTML) live in `src/gvc/assets/` and are inlined into rendered HTML at runtime — no HTTP server.

## Build and Test

```bash
# Setup
poetry install

# Run
poetry run gvc [git-diff-args...]
```

No automated test suite yet.

## Typecheck

Run typechecking with: `poetry run mypy`

This project uses mostly strict settings in `pyproject.toml`:
- `disallow_untyped_defs = true` — All functions must have type annotations
- `disallow_incomplete_defs = true` — Types must be fully specified
- `warn_no_return = true` — Functions must explicitly return or have `-> None`

It also uses this loose setting:
- `ignore_missing_imports = true` — Allows untyped libraries (pyobjc) without errors

## Conventions

- **Platform directories**: use `platformdirs` for all config/data/runtime/log paths — never hardcode `~/` paths
- **Dark mode**: detect via `NSUserDefaults` at window creation; CSS uses `@media prefers-color-scheme` for live following
- **Error handling in threads**: catch exceptions and call `traceback.print_exc()`; degrade gracefully on socket errors

## Documentation

- [doc/how_it_works.md](../doc/how_it_works.md) — architecture walkthrough
- [plan/requirements.md](../plan/requirements.md) — feature specification, keyboard shortcuts, rendering rules
- [plan/inception.md](../plan/inception.md) — design rationale and decision log
