## How It Works

The first `gvc` invocation launches a persistent background process that owns all diff windows (one Dock icon, no matter how many windows). Subsequent invocations connect to the running process via a Unix domain socket and ask it to open a new window. The process stays alive after all windows are closed, so the next `gvc` call opens instantly.

Diffs are rendered as self-contained HTML with inlined CSS and JS — no HTTP server, no network access required.
