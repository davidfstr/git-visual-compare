
To release a new version of gvc:

1. Prepare a release commit

> Prepare a release commit for the next release - v1.2.0 - in the same style as `git show v1.1.0`

2. Verify that CI passes

3. Build and publish to PyPI

```
poetry build
poetry publish
```
