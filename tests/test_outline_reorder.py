"""
Tests for reordering file rows in the outline (table of contents).

The default `diff_fixture` produces 5 file rows (added, deleted, modified,
renamed, binary) — comfortably more than the >= 3 rows these tests require.
"""

from contextlib import closing
from harness.app import GvcApp
from harness.diff_fixture import DiffFixture, make_large_diff_fixture
from harness.playwrightkit import expect, Locator, Page
import pytest
import time


# === Drag Handle: Mouse Actions ===

def test_can_click_and_drag_the_drag_handle_of_a_file_row_to_reorder_it(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    # ...and diff sections reorder to match (the new outline order)
    # ...and drag handle remains focused after drop
    
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    # Capture initial row order (by data-file-idx). Fixture provides 5 rows.
    initial_order = _outline_row_order(page)
    assert len(initial_order) >= 3, \
        f"fixture must produce >=3 outline rows; got {initial_order!r}"

    # Drag the LAST row's handle to just above the FIRST row.
    last_idx = initial_order[-1]
    first_idx = initial_order[0]
    # TODO: Rewrite to use concise Playwright-idiomatic style when drag_to()
    #       API available in PlaywrightKit. Expected concise form:
    #
    #           source = (page
    #               .locator("#file-outline .outline-row").last
    #               .locator(".outline-handle")
    #           )
    #           target = page.locator("#file-outline .outline-row").first
    #           source.drag_to(target, target_position={"x": 0, "y": 0})
    page.evaluate(f"""() => {{
        const sel = '.outline-row[data-file-idx=\"{last_idx}\"]';
        const firstSel = '.outline-row[data-file-idx=\"{first_idx}\"]';
        const lastRow = document.querySelector(sel);
        const firstRow = document.querySelector(firstSel);
        const outline = document.getElementById('file-outline');
        const handle = lastRow.querySelector('.outline-handle');
        const firstRect = firstRow.getBoundingClientRect();
        const dt = new DataTransfer();
        handle.dispatchEvent(new DragEvent('dragstart', {{
            bubbles: true, cancelable: true, dataTransfer: dt}}));
        outline.dispatchEvent(new DragEvent('dragover', {{
            bubbles: true, cancelable: true, dataTransfer: dt,
            clientY: firstRect.top + 1}}));
        outline.dispatchEvent(new DragEvent('drop', {{
            bubbles: true, cancelable: true, dataTransfer: dt}}));
        outline.dispatchEvent(new DragEvent('dragend', {{
            bubbles: true, cancelable: true, dataTransfer: dt}}));
    }}""")
    expected_order = [last_idx] + initial_order[:-1]

    # Ensure outline rows are reordered
    actual_outline_order = _outline_row_order(page)
    assert actual_outline_order == expected_order

    # Ensure diff sections are reordered to match
    actual_section_order = _diff_section_order(page)
    assert actual_section_order == expected_order

    # Ensure the dragged row's drag handle remains focused after drop
    assert _focused_outline_row_index(page) == last_idx


def test_can_right_click_or_control_click_a_drag_handle_to_show_reorder_dropdown_and_does_not_focus_any_menuitem(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
    subtests: pytest.Subtests,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    handle = _first_drag_handle_locator(page)
    menu = page.locator(".reorder-menu")
    menu_items = menu.locator("li[role='menuitem']")

    for click_modifier in ("right", "control"):
        with subtests.test(click_modifier=click_modifier):
            if click_modifier == "right":
                handle.click(button="right")
            elif click_modifier == "control":
                handle.click(modifiers=["Control"])
            else:
                raise AssertionError(f"Unrecognized click_modifier: {click_modifier!r}")

            # Ensure dropdown menu is visible with the 4 expected menu items
            expect(menu).to_be_visible()
            expect(menu_items).to_have_count(4)

            # Ensure no menu item is focused
            for i in range(4):
                expect(menu_items.nth(i)).not_to_be_focused()

            # Close the menu
            page.press("Escape")
            expect(menu).not_to_be_visible()


def test_can_click_drag_handle_to_focus_it(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    # Click the first drag handle
    handle = _first_drag_handle_locator(page)
    handle.click()

    # Ensure it is focused
    expect(handle).to_be_focused()


# === Dropdown Menu: Mouse Actions ===

@pytest.mark.skip('not yet automated')
def test_given_reorder_dropdown_menu_visible_when_select_move_to_top_then_file_row_moves_to_top_and_diff_sections_reorder_to_match(
    subtests: pytest.Subtests,
) -> None:
    # ...and drag handle becomes focused after reorder
    with subtests.test(first_row_selected=False):
        pytest.skip('not yet automated')

    with subtests.test(first_row_selected=True):
        pytest.skip('not yet automated')


def test_given_reorder_dropdown_menu_visible_when_select_move_up_then_file_row_moves_up_and_diff_sections_reorder_to_match(
    subtests: pytest.Subtests,
) -> None:
    # ...and drag handle becomes focused after reorder
    with subtests.test(first_row_selected=False):
        pytest.skip('not yet automated')

    with subtests.test(first_row_selected=True):
        pytest.skip('not yet automated')


@pytest.mark.skip('not yet automated')
def test_given_reorder_dropdown_menu_visible_when_select_move_to_bottom_then_file_row_moves_to_bottom_and_diff_sections_reorder_to_match(
    subtests: pytest.Subtests,
) -> None:
    # ...and drag handle becomes focused after reorder
    with subtests.test(last_row_selected=False):
        pytest.skip('not yet automated')

    with subtests.test(last_row_selected=True):
        pytest.skip('not yet automated')


def test_given_reorder_dropdown_menu_visible_when_select_move_down_then_file_row_moves_down_and_diff_sections_reorder_to_match(
    subtests: pytest.Subtests,
) -> None:
    # ...and drag handle becomes focused after reorder
    with subtests.test(last_row_selected=False):
        pytest.skip('not yet automated')

    with subtests.test(last_row_selected=True):
        pytest.skip('not yet automated')


@pytest.mark.skip('not yet automated')
def test_given_reorder_dropdown_menu_visible_when_right_click_or_control_click_a_different_drag_handle_then_current_dropdown_menu_closes_and_new_dropdown_menu_opens() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_reorder_dropdown_menu_visible_when_click_outside_menu_then_dropdown_menu_closes() -> None:
    pass


# === Drag Handle: Keyboard Actions ===

@pytest.mark.skip('not yet automated')
def test_given_drag_handle_focused_when_press_space_or_return_then_shows_reorder_dropdown_and_focuses_first_menuitem() -> None:
    pass


def test_given_drag_handle_focused_when_press_move_to_top_keyboard_shortcut_then_file_row_moves_to_top_and_diff_sections_reorder_to_match(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
    subtests: pytest.Subtests,
) -> None:
    # ...and drag handle remains focused after reorder
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    with subtests.test(first_row_selected=False):
        order_before = _outline_row_order(page)
        assert len(order_before) >= 3, \
            f"fixture must produce >=3 outline rows; got {order_before!r}"

        # Press Shift+ArrowUp on the last row's handle
        target_idx = order_before[-1]
        _drag_handle_locator(page, target_idx).press("Shift+ArrowUp")

        # 1. Ensure row jumped to the top
        # 2. Ensure diff sections mirror
        # 3. Ensure handle is still focused
        expected_order = [order_before[-1]] + order_before[:-1]
        assert _outline_row_order(page) == expected_order
        assert _diff_section_order(page) == expected_order
        assert _focused_outline_row_index(page) == target_idx

    with subtests.test(first_row_selected=True):
        order_before = _outline_row_order(page)

        # Press Shift+ArrowUp on the first row
        target_idx = order_before[0]
        _drag_handle_locator(page, target_idx).press("Shift+ArrowUp")

        # 1-2. Ensure no ordering change
        # 3. Ensure handle is still focused
        assert _outline_row_order(page) == order_before
        assert _diff_section_order(page) == order_before
        assert _focused_outline_row_index(page) == target_idx


def test_given_drag_handle_focused_when_press_move_up_keyboard_shortcut_then_file_row_moves_up_and_diff_sections_reorder_to_match(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
    subtests: pytest.Subtests,
) -> None:
    # ...and drag handle remains focused after reorder
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    with subtests.test(first_row_selected=False):
        order_before = _outline_row_order(page)
        assert len(order_before) >= 3, \
            f"fixture must produce >=3 outline rows; got {order_before!r}"

        # Press ArrowUp on a non-first row's handle
        target_idx = order_before[1]
        _drag_handle_locator(page, target_idx).press("ArrowUp")

        # 1. Ensure swaps with the row directly above it
        # 2. Ensure diff sections mirror
        # 3. Ensure handle is still focused
        expected_order = [order_before[1], order_before[0]] + order_before[2:]
        assert _outline_row_order(page) == expected_order
        assert _diff_section_order(page) == expected_order
        assert _focused_outline_row_index(page) == target_idx

    with subtests.test(first_row_selected=True):
        order_before = _outline_row_order(page)

        # Press ArrowUp on the first row
        target_idx = order_before[0]
        _drag_handle_locator(page, target_idx).press("ArrowUp")

        # 1-2. Ensure no ordering change
        # 3. Ensure handle is still focused
        assert _outline_row_order(page) == order_before
        assert _diff_section_order(page) == order_before
        assert _focused_outline_row_index(page) == target_idx


def test_given_drag_handle_focused_when_press_move_to_bottom_keyboard_shortcut_then_file_row_moves_to_bottom_and_diff_sections_reorder_to_match(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
    subtests: pytest.Subtests,
) -> None:
    # ...and drag handle remains focused after reorder
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    with subtests.test(last_row_selected=False):
        order_before = _outline_row_order(page)
        assert len(order_before) >= 3, \
            f"fixture must produce >=3 outline rows; got {order_before!r}"

        # Press Shift+ArrowDown on the first row's handle
        target_idx = order_before[0]
        _drag_handle_locator(page, target_idx).press("Shift+ArrowDown")

        # 1. Ensure row jumped to the bottom
        # 2. Ensure diff sections mirror
        # 3. Ensure handle is still focused
        expected_order = order_before[1:] + [order_before[0]]
        assert _outline_row_order(page) == expected_order
        assert _diff_section_order(page) == expected_order
        assert _focused_outline_row_index(page) == target_idx

    with subtests.test(last_row_selected=True):
        order_before = _outline_row_order(page)

        # Press Shift+ArrowDown on the last row
        target_idx = order_before[-1]
        _drag_handle_locator(page, target_idx).press("Shift+ArrowDown")

        # 1-2. Ensure no ordering change
        # 3. Ensure handle is still focused
        assert _outline_row_order(page) == order_before
        assert _diff_section_order(page) == order_before
        assert _focused_outline_row_index(page) == target_idx


def test_given_drag_handle_focused_when_press_move_down_keyboard_shortcut_then_file_row_moves_down_and_diff_sections_reorder_to_match(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
    subtests: pytest.Subtests,
) -> None:
    # ...and drag handle remains focused after reorder
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    with subtests.test(last_row_selected=False):
        order_before = _outline_row_order(page)
        assert len(order_before) >= 3, \
            f"fixture must produce >=3 outline rows; got {order_before!r}"

        # Press ArrowDown on a non-last row's handle
        target_idx = order_before[0]
        _drag_handle_locator(page, target_idx).press("ArrowDown")

        # 1. Ensure swaps with the row directly below it
        # 2. Ensure diff sections mirror
        # 3. Ensure handle is still focused
        expected_order = [order_before[1], order_before[0]] + order_before[2:]
        assert _outline_row_order(page) == expected_order
        assert _diff_section_order(page) == expected_order
        assert _focused_outline_row_index(page) == target_idx

    with subtests.test(last_row_selected=True):
        order_before = _outline_row_order(page)

        # Press ArrowDown on the last row
        target_idx = order_before[-1]
        _drag_handle_locator(page, target_idx).press("ArrowDown")

        # 1-2. Ensure no ordering change
        # 3. Ensure handle is still focused
        assert _outline_row_order(page) == order_before
        assert _diff_section_order(page) == order_before
        assert _focused_outline_row_index(page) == target_idx


# === Dropdown Menu: Keyboard Actions ===

@pytest.mark.skip('not yet automated')
def test_given_reorder_dropdown_menuitem_focused_when_press_down_arrow_then_next_menuitem_focused() -> None:
    pass


@pytest.mark.skip('not yet automated')
def test_given_reorder_dropdown_menuitem_focused_when_press_up_arrow_then_previous_menuitem_focused() -> None:
    pass


def test_given_reorder_dropdown_menuitem_focused_when_space_or_return_then_menuitem_action_performed(
    subtests: pytest.Subtests,
) -> None:
    with subtests.test(action="move_to_top"):
        # ...and diff sections reorder to match
        # ...and drag handle becomes focused after reorder
        with subtests.test(action="move_to_top", first_row_selected=False):
            pytest.skip('not yet automated')

        with subtests.test(action="move_to_top", first_row_selected=True):
            pytest.skip('not yet automated')

    with subtests.test(action="move_up"):
        # ...and diff sections reorder to match
        # ...and drag handle becomes focused after reorder
        with subtests.test(action="move_up", first_row_selected=False):
            pytest.skip('not yet automated')

        with subtests.test(action="move_up", first_row_selected=True):
            pytest.skip('not yet automated')

    with subtests.test(action="move_to_bottom"):
        # ...and diff sections reorder to match
        # ...and drag handle becomes focused after reorder
        with subtests.test(action="move_to_bottom", last_row_selected=False):
            pytest.skip('not yet automated')

        with subtests.test(action="move_to_bottom", last_row_selected=True):
            pytest.skip('not yet automated')

    with subtests.test(action="move_down"):
        # ...and diff sections reorder to match
        # ...and drag handle becomes focused after reorder
        with subtests.test(action="move_down", last_row_selected=False):
            pytest.skip('not yet automated')

        with subtests.test(action="move_down", last_row_selected=True):
            pytest.skip('not yet automated')


@pytest.mark.skip('not yet automated')
def test_given_reorder_dropdown_menuitem_focused_when_press_escape_then_drag_handle_focused() -> None:
    pass


# === Multiple Action Tests ===

def test_given_file_row_reordered_with_move_down_keyboard_shortcut_when_press_shortcut_again_then_file_row_moves_down_again(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
    subtests: pytest.Subtests,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    with subtests.test(wait_for_first_reorder_to_finish=True):
        order_before = _outline_row_order(page)
        assert len(order_before) >= 3, \
            f"fixture must produce >=3 outline rows; got {order_before!r}"

        # Press ArrowDown on the first row's handle (press() also focuses)
        target_idx = order_before[0]
        handle = _drag_handle_locator(page, target_idx)
        handle.press("ArrowDown")

        # Wait for the reordering animation to finish
        ANIMATION_MAX_DURATION_MS = (
            (_FLIP_DURATION_MS := 200) +
            (_SET_TIMEOUT_CLEANUP_MS := 20) +
            (_SAFETY_MARGIN_MS := 30)
        )
        time.sleep(ANIMATION_MAX_DURATION_MS / 1000)

        # Press ArrowDown again
        handle.press("ArrowDown")

        # Row should have moved down two positions
        expected_order = [order_before[1], order_before[2], order_before[0]] + order_before[3:]
        assert _outline_row_order(page) == expected_order
        assert _diff_section_order(page) == expected_order
        assert _focused_outline_row_index(page) == target_idx

    with subtests.test(wait_for_first_reorder_to_finish=False):
        order_before = _outline_row_order(page)

        # Press ArrowDown on the first row's handle twice without waiting
        target_idx = order_before[0]
        handle = _drag_handle_locator(page, target_idx)
        handle.press("ArrowDown")
        
        # (Do not wait for animation to finish)
        
        # Press ArrowDown again
        handle.press("ArrowDown")

        # Row should have moved down two positions
        expected_order = [order_before[1], order_before[2], order_before[0]] + order_before[3:]
        assert _outline_row_order(page) == expected_order
        assert _diff_section_order(page) == expected_order
        assert _focused_outline_row_index(page) == target_idx


def test_given_file_row_reordered_with_move_up_keyboard_shortcut_when_press_shortcut_again_then_file_row_moves_up_again(
    subtests: pytest.Subtests,
) -> None:
    with subtests.test(wait_for_first_reorder_to_finish=True):
        pytest.skip('not yet automated')

    with subtests.test(wait_for_first_reorder_to_finish=False):
        pytest.skip('not yet automated')


# === State Preservation Tests ===

def test_given_file_row_in_outline_reordered_when_click_file_path_in_row_then_still_scrolls_to_correct_file_diff(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    order_before = _outline_row_order(page)
    assert len(order_before) >= 3, \
        f"fixture must produce >=3 outline rows; got {order_before!r}"

    # Capture the filepath of the first outline row before reordering it
    target_idx = order_before[0]
    outline_row_link_before = page.locator(
        f"#file-outline .outline-row[data-file-idx='{target_idx}'] .outline-file"
    )
    outline_row_filepath_before = _filepath_from_outline_row_link(outline_row_link_before)

    # Reorder: Move the first outline row down one position.
    # NOTE: After this, the row at most risk of having a broken link is the
    #       one that just moved.
    _drag_handle_locator(page, target_idx).press("ArrowDown")

    # Ensure the moved outline row still links to the correct diff section,
    # by comparing the filepaths of the outline row and diff section.
    # NOTE: We assume that if the outline row link was clicked that the browser
    #       will scroll to the diff section automatically.
    if True:
        outline_row_link_after = page.locator(
            f"#file-outline .outline-row[data-file-idx='{target_idx}'] .outline-file"
        )
        outline_row_filepath_after = _filepath_from_outline_row_link(outline_row_link_after)
        assert outline_row_filepath_after == outline_row_filepath_before
        
        href = outline_row_link_after.get_attribute("href")
        assert href is not None and href.startswith("#"), \
            f"outline link href missing/unexpected: {href!r}"
        
        target_section_filepath_after = page.locator(f"{href} .file-path").text_content()
        assert target_section_filepath_after == outline_row_filepath_before


def test_given_diff_section_collapsed_and_marked_as_reviewed_when_related_file_row_in_outline_reordered_then_diff_section_still_collapsed_and_marked_as_reviewed(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    window = gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)
    page = gvc_app.page(window)

    order_before = _outline_row_order(page)
    assert len(order_before) >= 3, \
        f"fixture must produce >=3 outline rows; got {order_before!r}"

    # Pick a non-first row so it can be moved up without being at the top already
    target_idx = order_before[1]
    diff_section = page.locator(f"#file-{target_idx}")
    reviewed_label = diff_section.locator(".reviewed-label")
    reviewed_checkbox = diff_section.locator(".reviewed-check")

    # Click the reviewed label, which checks the box and collapses the section
    reviewed_label.click()
    expect(diff_section).not_to_have_attribute("open")
    expect(reviewed_checkbox).to_be_checked()

    # Reorder: Move the target row up one position
    _drag_handle_locator(page, target_idx).press("ArrowUp")

    # Ensure diff section remains collapsed and is still marked as reviewed
    expect(diff_section).not_to_have_attribute("open")
    expect(reviewed_checkbox).to_be_checked()


# === Other Tests ===

@pytest.mark.skip('not yet automated')
def test_drag_handle_glyph_is_not_selectable_as_text() -> None:
    pass


def test_given_large_diff_revealed_then_can_reorder_file_rows_in_outline(
    gvc_app: GvcApp,
) -> None:
    with closing(make_large_diff_fixture()) as fixture:
        window = gvc_app.run_cli(fixture.args, cwd=fixture.repo)
        page = gvc_app.page(window)

        # Reveal the full diff by clicking the large-diff gate
        gate = page.locator("#large-diff-gate")
        expect(gate).to_be_visible()
        gate.locator("a").click()
        expect(gate).not_to_be_visible()

        # Verify the outline now has >=3 rows
        order_before = _outline_row_order(page)
        assert len(order_before) >= 3, \
            f"large diff fixture must produce >=3 outline rows; got {order_before!r}"

        # Press ArrowDown on the first row's handle (move down keyboard shortcut)
        target_idx = order_before[0]
        _drag_handle_locator(page, target_idx).press("ArrowDown")

        # 1. Ensure swaps with the row directly below it
        # 2. Ensure diff sections mirror
        # 3. Ensure handle is still focused
        expected_order = [order_before[1], order_before[0]] + order_before[2:]
        assert _outline_row_order(page) == expected_order
        assert _diff_section_order(page) == expected_order
        assert _focused_outline_row_index(page) == target_idx


# === Utility ===

type _FileIndex = int


def _drag_handle_locator(page: Page, file_idx: _FileIndex) -> Locator:
    """Locator for the drag handle (☰) of the outline row with the given data-file-idx."""
    return page.locator(
        f"#file-outline .outline-row[data-file-idx='{file_idx}'] .outline-handle"
    )


def _first_drag_handle_locator(page: Page) -> Locator:
    """Locator for the drag handle (☰) of the first outline row, in DOM order."""
    return page.locator("#file-outline .outline-row").first.locator(".outline-handle")


def _outline_row_order(page: Page) -> list[_FileIndex]:
    """Return the current data-file-idx values of all outline rows, in DOM order."""
    raw = page.evaluate("""
        () => Array.from(
            document.querySelectorAll('#file-outline .outline-row')
        ).map(r => r.getAttribute('data-file-idx'))
    """)
    assert isinstance(raw, list)
    return [int(x) for x in raw]


def _focused_outline_row_index(page: Page) -> _FileIndex | None:
    """
    Return the data-file-idx of the outline row whose drag handle currently
    has focus, or None if no drag handle is focused.
    """
    raw = page.evaluate("""() => {
        const a = document.activeElement;
        if (!a || !a.classList || !a.classList.contains('outline-handle')) return null;
        const row = a.closest('.outline-row');
        return row ? row.getAttribute('data-file-idx') : null;
    }""")
    if raw is None:
        return None
    assert isinstance(raw, str)
    return int(raw)


def _filepath_from_outline_row_link(outline_link: Locator) -> str:
    """
    Return the displayed file path from a `.outline-file` anchor, stripping
    the leading status icon (the `.outline-status` span's text).
    """
    text = outline_link.text_content() or ""
    icon = outline_link.locator(".outline-status").text_content() or ""
    return text.removeprefix(icon)


def _diff_section_order(page: Page) -> list[_FileIndex]:
    """Return the file indices of all diff sections in #diff-content, in DOM order."""
    raw = page.evaluate("""() => Array.from(
        document.querySelectorAll('#diff-content > details.file-section')
    ).map(s => s.id.slice('file-'.length))""")
    assert isinstance(raw, list)
    return [int(x) for x in raw]
