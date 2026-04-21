"""
Tests that features interacting with the text of a displayed diff operate
correctly.
"""

from harness.app import GvcApp
from harness.diff_fixture import DiffFixture
from harness.playwrightkit import expect
import pytest


# === Test: Font Size Adjustable ===

@pytest.mark.skip('not yet automated')
def test_when_command_plus_or_equals_pressed_then_font_size_increases_in_all_diff_windows() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_when_command_minus_pressed_then_font_size_decreases_in_all_diff_windows() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_min_font_size_is_currently_8_pt() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_max_font_size_is_currently_32_pt() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_when_gvc_is_quit_and_reopened_and_new_diff_window_appears_then_uses_same_font_size_as_before_quit() -> None:
    pass


# === Test: Select and Copy ===

@pytest.mark.skip('fails: currently also selects line numbers')
def test_can_click_and_drag_within_diff_text_to_select_diff_text() -> None:
    # ...including + and - markers but excluding line numbers
    pass


@pytest.mark.skip('fails: currently also copies line numbers')
def test_given_diff_text_selected_when_press_command_c_then_copies_selected_text() -> None:
    # ...including + and - markers but excluding line numbers
    pass


# === Test: Find ===

def test_when_command_f_pressed_then_find_bar_appears(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    expect(page.locator("#find-bar")).not_to_be_visible()

    page.press("Meta+f")
    expect(page.locator("#find-bar")).to_be_visible()


@pytest.mark.skip('not yet automated')
def test_given_find_bar_visible_when_press_escape_then_find_bar_disappears() -> None:
    pass


def test_given_find_bar_visible_when_type_keyword_then_occurrences_of_keyword_in_file_paths_and_diff_content_are_marked(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    page.press("Meta+f")
    # "modified" appears in the outline path "modified.py" and in the diff
    # line "+modified line" inside the file section — verifying both locations.
    page.locator("#find-input").fill("modified")

    expect(page.locator("#file-outline mark.find-match")).not_to_have_count(0)
    expect(page.locator(".file-section mark.find-match")).not_to_have_count(0)


@pytest.mark.skip('not yet automated')
def test_given_marks_visible_when_press_command_g_to_find_next_then_next_mark_is_made_current_and_scrolled_into_view() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_marks_visible_when_press_shift_command_g_to_find_previous_then_previous_mark_is_made_current_and_scrolled_into_view() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_marks_visible_and_last_mark_is_current_when_press_command_g_to_find_next_then_wrap_around_overlay_briefly_appears() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_marks_visible_and_first_mark_is_current_when_press_shift_command_g_to_find_previous_then_wrap_around_overlay_briefly_appears() -> None:
    pass


# (TODO: Test case sensitive vs. case-insensitive matching)
# (TODO: Test whole word vs. non-whole word matching)
# (TODO: Test regex vs. non-regex matching)
