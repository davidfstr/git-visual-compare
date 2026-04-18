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

Three ways to build and run:

**A. Unbundled (fast iteration, no build step):**

```bash
poetry run gvc [git-diff-args...]
```

**B. Editable `.app` (fast iteration, build once edit many, correct Dock tooltip):**

```bash
poetry run python build_app.py -e
./dist/gvc.app/Contents/MacOS/gvc [git-diff-args...]
```

**C. Distribution `.app` (standalone):**

```bash
poetry run python build_app.py
./dist/gvc.app/Contents/MacOS/gvc [git-diff-args...]
```

Use A or B for day-to-day work. Prefer B over A when you need the `.app`
context (Dock tooltip says "gvc" instead of "Python", Finder icon, bundled
Python framework). With B, edits to `*.py`, `*.html`, `*.js`, and `*.css`
under `src/gvc/` are picked up on the next launch without rebuilding;
changes to any other files (e.g. `pyproject.toml`, `gvc.spec`, the app
icon) require rebuilding the `.app` shell. Use C to produce the bundle
that would ship to end users.

### Installing a development `gvc` on `PATH`

To invoke your working copy as just `gvc` from anywhere:

**For A** — install an editable console script via pipx:

```bash
pipx install -e .
```

**For B or C** — symlink the bundle's executable into a directory on `PATH`:

```bash
ln -s "$(pwd)/dist/gvc.app/Contents/MacOS/gvc" /usr/local/bin/gvc
```

The symlink survives rebuilds (the executable path inside the `.app` is
stable), so you only need to create it once.
