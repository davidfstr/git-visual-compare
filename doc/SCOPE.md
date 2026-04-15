# Scope

What kinds of future features are aligned with the vision of GVC?

### In Scope

- Visual diffs of text files

### In Scope - not yet implemented

Code contributions that add any of the following features are welcome.

- Support popular operating systems, beyond just macOS (e.g. Windows and Linux)
- Diffs of files that are OUTSIDE a git repository, so long as the git binary is still installed/usable to perform diff computations
- Invocation via the “git difftool“ protocol

### Out of Scope

Proposals to add the following kinds of features will be rejected.

- Diffs of image files
- Diffs of other kinds of binary files
- Viewing the commit graph of a git repository

### Undecided whether in scope or not

- 3 way merge & Conflict resolution visualization. The “git mergetool“ protocol.
- Syntax highlighting in diffs
- Languages other than English
- Interactive revert of individual hunks
