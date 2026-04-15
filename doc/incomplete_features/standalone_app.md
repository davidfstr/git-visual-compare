GVC will support being distributed as a .app package.

Upon first launch the .app will offer to install the `gvc` CLI tool,
which will symlink to a binary/trampoline inside the .app package.

When the .app is running, the `gvc` CLI tool is installed, and no other
windows in the app are open, an instructional window will appear explaining
how to run `gvc ...` from the command line.

---

# FUTURE BUILD INSTRUCTIONS

## Building a Standalone .app

```bash
pip install pyinstaller
pyinstaller packaging/gvc.spec
```

The resulting `dist/gvc.app` is a self-contained macOS application bundle.
