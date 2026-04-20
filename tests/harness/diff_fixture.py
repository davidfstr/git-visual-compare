"""
Builds a reusable git repo exhibiting all five diff statuses:
added, deleted, modified, renamed, binary.
"""

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile


@dataclass(frozen=True)
class DiffFixture:
    """A temporary git repo and the gvc args that produce its all-statuses diff."""
    repo: Path
    args: list[str]

    def close(self) -> None:
        shutil.rmtree(self.repo, ignore_errors=True)


# Files emitted, keyed by the status icon they produce in the rendered TOC
EXPECTED_FILES: dict[str, str] = {
    "➕": "added.py",
    "❌": "deleted.py",
    "✏️": "modified.py",
    # Special case: Rename must show both old and new paths
    "🚚": "renamed_old.py → renamed_new.py",
    "📄": "binary.bin",
}


def make_diff_fixture() -> DiffFixture:
    """
    Creates a temp git repo with two commits. HEAD~1..HEAD produces a diff
    that contains one file of each status (added/deleted/modified/renamed/binary).
    """
    repo = Path(tempfile.mkdtemp(prefix="gvc-diff-fixture-"))

    def run(*cmd: str) -> None:
        subprocess.run(cmd, cwd=repo, check=True, capture_output=True)

    run("git", "init", "-q", "-b", "main")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "Test")
    # Ensure `git diff` detects renames (override any global config)
    run("git", "config", "diff.renames", "true")

    # Commit 1: files that will be deleted / modified / renamed / binary-changed
    (repo / "deleted.py").write_text("to be deleted\n")
    (repo / "modified.py").write_text("original line\n")
    # Give the rename candidate enough content that git is confident it's a rename
    (repo / "renamed_old.py").write_text(
        "\n".join(f"stable line {i}" for i in range(20)) + "\n"
    )
    (repo / "binary.bin").write_bytes(b"\x00\x01\x02\x03original-binary")
    run("git", "add", "-A")
    run("git", "commit", "-q", "-m", "initial")

    # Commit 2: add a new file; delete; modify; rename; change binary
    (repo / "added.py").write_text("brand new\n")
    (repo / "deleted.py").unlink()
    (repo / "modified.py").write_text("modified line\n")
    (repo / "renamed_old.py").rename(repo / "renamed_new.py")
    (repo / "binary.bin").write_bytes(b"\x00\x01\x02\x03changed-binary")
    run("git", "add", "-A")
    run("git", "commit", "-q", "-m", "second")

    return DiffFixture(repo=repo, args=["HEAD~1", "HEAD"])
