"""Tests that usage of the "gvc" command line utility behaves correctly."""

from harness.app import GvcApp
from harness.diff_fixture import DiffFixture
import pytest


# === Test: Application: Lifecycle ===

def test_when_gvc_run_in_terminal_given_no_gui_running_then_starts_gui_and_opens_new_diff_window(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    gvc_app.wait_for_windows(1)


def test_when_gvc_run_in_terminal_given_gui_running_then_opens_new_diff_window_in_existing_gui(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    gvc_app.wait_for_windows(1)

    gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    gvc_app.wait_for_windows(2)


@pytest.mark.skip('not yet automated')
def test_when_gvc_gui_running_when_press_command_q_then_gui_quits() -> None:
    pass


# === Test: Git Diff Options ===

# NOTE: Most of the following "git diff ..." examples are documented in
#       the README and therefore must continue to work

@pytest.mark.skip('not yet automated')
def test_can_show_diff_of_working_tree() -> None:
    # Command: gvc
    pass


@pytest.mark.skip('not yet automated')
def test_can_show_diff_of_staged_changes() -> None:
    # Command: gvc --cached
    pass


@pytest.mark.skip('not yet automated')
def test_can_show_diff_of_individual_commit() -> None:
    # Command: gvc HEAD~1 HEAD
    pass


@pytest.mark.skip('not yet automated')
def test_can_show_diff_of_commit_range() -> None:
    # Command: gvc HEAD~3 HEAD
    pass


@pytest.mark.skip('not yet automated')
def test_can_show_diff_between_arbitrary_commits() -> None:
    # Command: gvc abc123 def456
    pass


@pytest.mark.skip('not yet automated')
def test_can_show_diff_limited_to_specific_files_or_directories() -> None:
    # Command: gvc HEAD~1 HEAD -- src/foo.py
    pass


@pytest.mark.skip('not yet automated')
def test_can_show_diff_ignoring_whitespace() -> None:
    # Command: gvc -w HEAD~1 HEAD
    pass


@pytest.mark.skip('not yet automated')
def test_can_show_diff_with_additional_context_lines() -> None:
    # Command: gvc -U20 HEAD~1 HEAD
    pass
