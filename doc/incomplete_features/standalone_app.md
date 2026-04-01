## Building a Standalone .app

```bash
pip install pyinstaller
pyinstaller packaging/gvc.spec
```

The resulting `dist/gvc.app` is a self-contained macOS application bundle.
