## Getting Started

### Initial Setup

```bash
python -m venv venv
venv/bin/pip install -e ".[dev]"
```

This installs the package and development dependencies (like mypy).

To install your development copy of gvc globally:
```
pipx install -e .
```

### Type Checking Python

Run mypy to check for type errors:

```bash
mypy
```

The project uses strict mypy settings (`disallow_untyped_defs`, `disallow_incomplete_defs`, etc.) to ensure comprehensive type coverage. All function signatures must have complete type annotations.

### Type Checking JavaScript

The browser-side assets in `src/gvc/assets/` are plain JavaScript, but can be
typechecked by the TypeScript compiler in `--checkJs` mode. Each `.js` file
opts in by placing `// @ts-check` at the top; see `tsconfig.json` at the repo
root for compiler options.

TypeScript is pinned as a local dev dependency in `package.json`. After
`npm install`, run tsc via the local binary:

```bash
npm run tsc
```

### Import Sorting

Run isort to sort imports:

```bash
isort src
```

## Running gvc

Two ways to build and run:

**A. Unbundled (fast iteration, no build step):**

```bash
poetry run gvc [git-diff-args...]
```

**B. Bundled `.app` (correct Dock tooltip, Finder icon):**

```bash
poetry run python build_app.py
./dist/gvc.app/Contents/MacOS/gvc [git-diff-args...]
```

Use A for day-to-day work. Use B when you need the Dock tooltip to say "gvc"
instead of "Python" — macOS reads the tooltip once at launch from a bundle's
`Info.plist`, which only the `.app` has.
