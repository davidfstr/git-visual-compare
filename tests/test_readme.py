"""Tests that everything documented in README.md actually works."""

import pytest


# === Test: Features ===

# NOTE: The following key Features are documented in the README and
#       therefore must continue to work

@pytest.mark.skip('covered by: === Test: Light and Dark Mode ===')
def test_supports_light_and_dark_mode() -> None:
    pass


@pytest.mark.skip('covered by: === Test: Find ===')
def test_supports_find_in_diff_window() -> None:
    pass


@pytest.mark.skip('covered by: === Test: Font Size Adjustable ===')
def test_supports_adjustable_font_size_in_diff_window() -> None:
    pass


@pytest.mark.skip('covered by: test_given_diff_window_visible_then_shows_added_and_deleted_and_modified_and_renamed_and_binary_files_with_correct_icons_and_paths')
def test_shows_table_of_contents_in_diff_window() -> None:
    pass


@pytest.mark.skip('covered by: test_when_file_in_toc_clicked_then_scrolls_diff_of_file_into_view')
def test_can_jump_to_any_file_from_the_table_of_contents() -> None:
    pass


@pytest.mark.skip('covered by: === Test: Collapsible File Sections ===')
def test_supports_collapsible_file_sections_in_diff_window() -> None:
    pass


# === Test: Usage ===

@pytest.mark.skip('covered by: === Test: Git Diff Options ===')
def test_usage_section_examples_work() -> None:
    pass


# TODO: Replace section name with a specific test covering this scenario
@pytest.mark.skip('covered by: === Test: Application: Lifecycle ===')
def test_cli_returns_immediately_without_blocking() -> None:
    pass


# === Test: Keyboard Shortcuts ===

@pytest.mark.skip('covered by: test_when_command_f_pressed_then_find_bar_appears')
def test_command_f_opens_find_bar() -> None:
    pass


@pytest.mark.skip('covered by: test_given_marks_visible_when_press_command_g_to_find_next_then_next_mark_is_made_current_and_scrolled_into_view')
def test_command_g_does_find_next_given_find_bar_is_visible() -> None:
    pass


@pytest.mark.skip('covered by: test_given_marks_visible_when_press_shift_command_g_to_find_previous_then_previous_mark_is_made_current_and_scrolled_into_view')
def test_shift_command_g_does_find_previous_given_find_bar_is_visible() -> None:
    pass


@pytest.mark.skip('covered by: test_when_command_plus_or_equals_pressed_then_font_size_increases_in_all_diff_windows')
def test_command_plus_increases_font_size() -> None:
    pass


@pytest.mark.skip('covered by: test_when_command_minus_pressed_then_font_size_decreases_in_all_diff_windows')
def test_command_minus_decreases_font_size() -> None:
    pass


@pytest.mark.skip('covered by: test_given_diff_window_exists_when_press_command_w_then_topmost_diff_window_closes')
def test_command_w_closes_frontmost_diff_window() -> None:
    pass


@pytest.mark.skip('covered by: test_when_gvc_gui_running_when_press_command_q_then_gui_quits')
def test_command_q_quits_the_gvc_gui() -> None:
    pass
