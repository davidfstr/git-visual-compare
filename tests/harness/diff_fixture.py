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

    run("git", "init", "--quiet", "--initial-branch=main")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "Test")
    # Ensure `git diff` detects renames (override any global config)
    run("git", "config", "diff.renames", "true")

    # Commit 1: files that will be deleted / modified / renamed / binary-changed
    (repo / "deleted.py").write_text("to be deleted\n")
    # Add enough changed lines so that the rendered diff reliably exceeds any typical
    # viewport height. Needed by tests that assert scroll behavior.
    modified_old = "original line\n" + "".join(
        f"extra line {i} old\n" for i in range(100)
    )
    (repo / "modified.py").write_text(modified_old)
    # Give the rename candidate enough content that git is confident it's a rename
    (repo / "renamed_old.py").write_text(
        "\n".join(f"stable line {i}" for i in range(20)) + "\n"
    )
    (repo / "binary.bin").write_bytes(b"\x00\x01\x02\x03original-binary")
    run("git", "add", "--all")
    run("git", "commit", "--quiet", "--message", "initial")

    # Commit 2: add a new file; delete; modify; rename; change binary
    (repo / "added.py").write_text("brand new\n")
    (repo / "deleted.py").unlink()
    modified_new = "modified line\n" + "".join(
        f"extra line {i} new\n" for i in range(100)
    )
    (repo / "modified.py").write_text(modified_new)
    (repo / "renamed_old.py").rename(repo / "renamed_new.py")
    (repo / "binary.bin").write_bytes(b"\x00\x01\x02\x03changed-binary")
    run("git", "add", "--all")
    run("git", "commit", "--quiet", "--message", "second")

    return DiffFixture(repo=repo, args=["HEAD~1", "HEAD"])


def make_large_diff_fixture() -> DiffFixture:
    """
    Creates a temp git repo whose HEAD~1..HEAD diff exceeds the large-diff threshold
    (>10,000 lines), triggering the 'Click here to load' gate in the diff window.
    """
    repo = Path(tempfile.mkdtemp(prefix="gvc-large-diff-fixture-"))

    def run(*cmd: str) -> None:
        subprocess.run(cmd, cwd=repo, check=True, capture_output=True)

    run("git", "init", "--quiet", "--initial-branch=main")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "Test")
    run("git", "commit", "--quiet", "--message", "initial", "--allow-empty")

    # Add a file with enough lines to cross the 10,000-line large-diff threshold
    big_text = "\n".join(f"line {i:05d}" for i in range(11_000)) + "\n"
    (repo / "big.py").write_text(big_text)
    run("git", "add", "--all")
    run("git", "commit", "--quiet", "--message", "add big file")

    return DiffFixture(repo=repo, args=["HEAD~1", "HEAD"])
