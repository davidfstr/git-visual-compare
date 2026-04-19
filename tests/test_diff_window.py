"""
Tests that the appearance of diff windows is correct and that immediately 
visible controls have the expected behavior.
"""

import pytest


# === Test: Lifecycle ===

@pytest.mark.skip('not yet automated')
def test_when_open_new_diff_window_given_no_diff_windows_open_then_width_is_at_least_100_columns_and_height_is_maximum_that_fits_on_screen() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_when_open_new_diff_window_given_a_diff_window_is_open_then_size_matches_topmost_diff_window_and_position_is_offset_from_topmost_diff_window() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_diff_window_exists_when_press_command_w_then_topmost_diff_window_closes() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_can_resize_diff_window() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_cannot_resize_diff_window_to_be_smaller_than_5_rows_or_10_columns() -> None:
    pass


# === Test: Light and Dark Mode ===

@pytest.mark.skip('not yet automated')
def test_given_light_mode_when_diff_window_appears_then_window_background_while_appearing_is_light() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_dark_mode_when_diff_window_appears_then_window_background_while_appearing_is_dark() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_light_mode_then_shows_correct_diff_colors() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_dark_mode_then_shows_correct_diff_colors() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_when_transition_between_light_and_dark_mode_then_diff_colors_change() -> None:
    pass


# === Test: Table of Contents ===

# TODO: Readme calls this "table of contents" but code calls this feature "outline".
#       Pick a term and use it consistently everywhere.

@pytest.mark.skip('not yet automated')
def test_given_diff_window_visible_then_shows_added_and_deleted_and_modified_and_renamed_and_binary_files_with_correct_icons_and_paths() -> None:
    # Special case: Rename must show both old and new paths
    pass


@pytest.mark.skip('not yet automated')
def test_when_file_in_toc_clicked_then_scrolls_diff_of_file_into_view() -> None:
    pass


# === Test: Collapsible File Sections ===

@pytest.mark.skip('not yet automated')
def test_when_collapse_all_button_pressed_then_all_file_sections_collapse() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_when_expand_all_button_pressed_then_all_file_sections_expand() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_when_header_of_file_section_clicked_given_section_expanded_then_section_collapses() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_when_header_of_file_section_clicked_given_section_collapsed_then_section_expands() -> None:
    pass


# === Test: Git Diff Appearance ===

@pytest.mark.skip('not yet automated')
def test_given_diff_window_then_added_lines_start_with_plus_and_removed_lines_start_with_minus() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_diff_window_then_added_lines_and_removed_lines_and_unchanged_lines_are_colored_distinctly() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_diff_window_then_changed_lines_with_trailing_whitespace_have_that_whitespace_colored_distinctly() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_diff_window_then_two_line_gutters_have_consistent_background_color_regardless_of_adjacent_line_colors() -> None:
    pass
