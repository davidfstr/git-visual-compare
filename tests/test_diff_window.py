"""
Tests that the appearance of diff windows is correct and that immediately
visible controls have the expected behavior.
"""

from gvc import window_manager
from harness.app import GvcApp
from harness.diff_fixture import DiffFixture, EXPECTED_FILES
from harness.playwrightkit import Page, expect
import pytest
import time
from unittest.mock import MagicMock, patch


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

def test_given_light_mode_when_diff_window_appears_then_window_background_while_appearing_is_light() -> None:
    _assert_background_color_for_dark_mode(is_dark=False, expected_color="#ffffff")


def test_given_dark_mode_when_diff_window_appears_then_window_background_while_appearing_is_dark() -> None:
    _assert_background_color_for_dark_mode(is_dark=True, expected_color="#0d1117")


def test_given_light_mode_then_shows_correct_diff_colors(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    gvc_app.set_appearance(window, "light")
    page = gvc_app.page(window)

    _expect_css_var(page, "--added-bg", "#bbf5cc")
    _expect_css_var(page, "--removed-bg", "#ffc0c8")


def test_given_dark_mode_then_shows_correct_diff_colors(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    gvc_app.set_appearance(window, "dark")
    page = gvc_app.page(window)

    _expect_css_var(page, "--added-bg", "#124a28")
    _expect_css_var(page, "--removed-bg", "#4a1220")


@pytest.mark.skip('not yet automated')
def test_when_transition_between_light_and_dark_mode_then_diff_colors_change() -> None:
    pass


def _assert_background_color_for_dark_mode(*, is_dark: bool, expected_color: str) -> None:
    mock_window = MagicMock()
    mock_api = MagicMock()
    mock_api.open_windows.return_value = []

    with (
        patch.object(window_manager, "_is_dark_mode", return_value=is_dark),
        patch.object(window_manager, "_get_screen_frame", return_value=(0, 0, 1440, 900)),
        patch("webview.create_window", return_value=mock_window) as mock_create,
    ):
        window_manager.create_window(html="<html/>", title="Test", api=mock_api)

    _, kwargs = mock_create.call_args
    assert kwargs["background_color"] == expected_color


def _expect_css_var(page: Page, var: str, expected: str, timeout: float = 5.0) -> None:
    """Polls until the CSS custom property `var` on :root equals `expected`."""
    deadline = time.monotonic() + timeout  # capture
    actual: object = None
    while time.monotonic() < deadline:
        actual = page.evaluate(
            f"() => getComputedStyle(document.documentElement).getPropertyValue('{var}').trim()"
        )
        if actual == expected:
            return
        time.sleep(0.05)
    raise AssertionError(f"CSS var {var!r}: expected {expected!r}, got {actual!r}")


# === Test: Table of Contents ===

# TODO: Readme calls this "table of contents" but code calls this feature "outline".
#       Pick a term and use it consistently everywhere.

def test_given_diff_window_visible_then_shows_added_and_deleted_and_modified_and_renamed_and_binary_files_with_correct_icons_and_paths(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    entries = page.locator("#file-outline .outline-file")
    expect(entries).to_have_count(len(EXPECTED_FILES))

    # Verify icon-path pairs match the expected set
    # NOTE: Output order is not defined, so compare expected vs. actual as a set
    actual: dict[str, str] = {}
    for i in range(len(EXPECTED_FILES)):
        entry = entries.nth(i)
        icon = entry.locator(".outline-status").text_content()
        text = entry.text_content()
        assert icon is not None and text is not None
        assert text.startswith(icon), \
            f"entry {i} textContent {text!r} does not start with icon {icon!r}"
        actual[icon] = text.removeprefix(icon)
    assert actual == EXPECTED_FILES


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


def test_when_header_of_file_section_clicked_given_section_expanded_then_section_collapses(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    # File sections render as <details open>; clicking the <summary>
    # relies on standard HTML behavior to toggle the `open` attribute.
    section = page.locator("#file-0")
    expect(section).to_have_attribute("open", "")

    # Collapse
    section.locator("summary").click()
    expect(section).not_to_have_attribute("open")

    # Expand
    section.locator("summary").click()
    expect(section).to_have_attribute("open", "")


@pytest.mark.skip('covered by: test_when_header_of_file_section_clicked_given_section_expanded_then_section_collapses')
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
