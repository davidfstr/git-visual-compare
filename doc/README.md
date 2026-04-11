This directory contains developer-facing documentation for understanding
how gvc works and how to extend it.

🚧 As of 2026-03-31, this directory's contents is **very messy** - mostly
semi-organized AI output - and needs full human-driven makeover.

## Getting Started

### Initial Setup

```bash
python -m venv venv
venv/bin/pip install -e ".[dev]"
```

This installs the package and development dependencies (like mypy).

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
