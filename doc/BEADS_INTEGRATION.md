# Beads Integration

This project uses [Beads](https://gastownhall.github.io/beads/) (`bd`) for issue tracking, configured so that **nothing Beads-specific is committed to the repository**.

## How it works

`bd` normally stores its database in a `.beads/` directory at the repo root. Instead this project uses `BEADS_DIR` to point `bd` at a directory outside the repo:

```
~/.local/share/beads/git-visual-compare/
```

`BEADS_DIR` is set via `direnv`, which reads `.envrc` automatically when you `cd` into the project.

## File inventory

- `.envrc`
    - Location: repo root
    - Tracked by git?: No — global gitignore
    - Purpose: Sets `BEADS_DIR` via direnv
- `CLAUDE.local.md`
    - Location: repo root
    - Tracked by git?: No — global gitignore
    - Purpose: Beads workflow instructions for Claude
- `.claude/settings.local.json`
    - Location: `.claude/`
    - Tracked by git?: No — global gitignore
    - Purpose: `bd prime` hooks on SessionStart/PreCompact
- Beads workspace
    - Location: `~/.local/share/beads/git-visual-compare/`
    - Tracked by git?: N/A (outside repo)
    - Purpose: Dolt database, config

## Setup steps (for a new machine)

1. **Install `bd`** — install the CLI only; do not run `bd init` yet
   (see [Installation](https://gastownhall.github.io/beads/getting-started/installation))

2. **Install and configure direnv**
   ```bash
   brew install direnv
   echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
   ```

3. **Add local-only files to your global gitignore** (once per machine, not per clone)
   ```bash
   echo '**/.envrc' >> ~/.config/git/ignore
   echo '**/CLAUDE.local.md' >> ~/.config/git/ignore
   ```

4. **Create and approve the `.envrc`** (from the repo root)
   ```bash
   echo 'export BEADS_DIR="$HOME/.local/share/beads/git-visual-compare"' > .envrc
   direnv allow
   ```

5. **Initialize the Beads workspace**
   ```bash
   bd init --quiet
   ```
   This creates `~/.local/share/beads/git-visual-compare/` and syncs from the remote.

6. **Move the repository-wide Claude Code integration to be local instead** — `bd init` writes these to `CLAUDE.md` and `.claude/settings.json` by default; we keep them in `.local` variants instead:
   - Move new sections in `CLAUDE.md` to `CLAUDE.local.md`, leaving `CLAUDE.md` in its original state
   - Move new `.claude/settings.json` hooks (`bd prime` on SessionStart and PreCompact)
     to `.claude/settings.local.json`, leaving `.claude/settings.json` in its original state

## Why configure in `.local` files?

The use of Beads is currently being experimented with, so I do not want to commit any of its
integration hooks to git at this time.
