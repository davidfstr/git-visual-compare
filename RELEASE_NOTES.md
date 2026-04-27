Release Notes
-------------

### main

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
