Release Notes
-------------

### main

* Code review tools
    * File section headers now have a "[ ] Reviewed" checkbox.
      Checking it collapses the section; unchecking it expands the section.

* Usability improvements
    * Collapsing a file section (via its header or the Reviewed checkbox) now
      attempts to keep the section header in view.

### v1.2.0 (May 10, 2026)

* Usability improvements
    * Selecting text in a diff to copy no longer includes line numbers
    * Clicking a file in the Table of Contents now expands its content if
      collapsed
    * "Wrap Around" overlay shown when Find wraps is now more readable,
      with a rounded rectangle background and a larger ⟳ icon
    * Empty file additions and deletions now show "Empty file" rather than
      "No changes". Renames without content changes still show "No changes".

* Development improvements
    * Tests can now be run in parallel

### v1.1.0 (April 28, 2026)

* Usability improvements
    * App has stable bundle identity that can be targeted with automation tools 
      like Keyboard Maestro
    * Menuitems with visible keyboard shortcuts exist for every supported keyboard shortcut

* Branding improvements
    * Dock icon shows app name ("gvc") when installed from PyPI/pip/pipx
    * About Panel shows full app name ("Git Visual Compare")

* Development improvements
    * `build_app.py` supports `-e`/`--editable` to build a `.app` that uses
      live `.py` files from the source tree rather than bundled copies.
    * Automated tests exist
    * Continuous integration is setup

* Bug fixes
    * "Click here to load" link for large diffs now works


### v1.0.0 (April 15, 2026)

* Initial release
    * Text file diffs, supporting all the options that `git diff` does
    * Dark mode and light mode support
    * Find / Find Again, to search diffs
    * Table of contents of files at top of diff window
    * Collapsible file sections
    * App icon/logo
    * 100% human-reviewed code, although drafted with assistance from
      Claude Opus 4.6 and Claude Sonnet 4.6
