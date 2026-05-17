// @ts-check
"use strict";

const FLIP_DURATION_MS = 200;

/** Setup the drag handles (☰) adjacent to each row in the file outline. */
function setupReorder() {
    const outline = document.getElementById("file-outline");
    if (!outline) { throw new Error("#file-outline not found"); }

    // NOTE: All handlers are delegated from the outline element so that
    //       we don't have to re-attach when rows are added or rearranged.
    outline.addEventListener("dragstart", _onOutlineDragStart);
    outline.addEventListener("dragover", _onOutlineDragOver);
    outline.addEventListener("dragend", _onOutlineDragEnd);
    outline.addEventListener("drop", (e) => { e.preventDefault(); });
    outline.addEventListener("keydown", _onOutlineKeydown);
    outline.addEventListener("contextmenu", _onOutlineContextMenu);
    outline.addEventListener("click", _onOutlineClick);
}

function _onOutlineClick(/** @type {Event} */ e) {
    // When drag handle clicked, focus it
    // NOTE: WebKit doesn't focus <button>s on click by default
    if (!(e instanceof MouseEvent)) { throw new Error("click event is not a MouseEvent"); }
    const target = e.target;
    if (!(target instanceof Element)) { throw new Error("click target is not an Element"); }
    const handle = target.closest(".outline-handle");
    if (!(handle instanceof HTMLElement)) return;  // click was not on a handle
    handle.focus();
}

// -----------------------------------------------------------------------------
// Drag Gestures

/** @type {HTMLElement | null} */
let _dragRow = null;

function _onOutlineDragStart(/** @type {Event} */ e) {
    // When drag handle dragged, start moving the corresponding row
    if (!(e instanceof DragEvent)) { throw new Error("dragstart event is not a DragEvent"); }
    const target = e.target;
    if (!(target instanceof Element)) { throw new Error("dragstart target is not an Element"); }
    const handle = target.closest(".outline-handle");
    if (!handle) return;  // drag started on a non-handle element (e.g. text drag from anchor)
    const row = handle.closest(".outline-row");
    if (!(row instanceof HTMLElement)) { throw new Error(".outline-handle is not inside an .outline-row"); }

    _dragRow = row;
    row.classList.add("dragging");
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = "move";
        // NOTE: Required in Firefox to start a drag
        e.dataTransfer.setData("text/plain", "");
    }
}

function _onOutlineDragOver(/** @type {Event} */ e) {
    // While drag handle dragging, move corresponding row
    if (!(e instanceof DragEvent)) { throw new Error("dragover event is not a DragEvent"); }
    const dragRow = _dragRow;
    if (!dragRow) return;  // foreign drag (e.g. file dragged over window from Finder)
    e.preventDefault();
    if (e.dataTransfer) {
        e.dataTransfer.dropEffect = "move";
    }

    const outline = document.getElementById("file-outline");
    if (!outline) { throw new Error("#file-outline not found"); }

    const rows = /** @type {HTMLElement[]} */(
        Array.from(outline.querySelectorAll(".outline-row"))
    );
    const y = e.clientY;

    // Find row whose vertical midpoint is below the cursor, to insert before it.
    /** @type {HTMLElement | null} */
    let insertBefore = null;
    for (const r of rows) {
        if (r === dragRow) continue;
        const rect = r.getBoundingClientRect();
        const mid = rect.top + rect.height / 2;
        if (y < mid) {
            insertBefore = r;
            break;
        }
    }

    // If drop target slot already in correct location, exit
    const currentNext = dragRow.nextElementSibling;
    if (insertBefore === dragRow || insertBefore === currentNext) return;

    // Skip the dragged row from the flip animation;
    // the OS-provided drag ghost already represents its motion.
    const otherRows = rows.filter((r) => r !== dragRow);
    
    _reorderOutlineRowsWithAnimation(otherRows, () => {
        if (insertBefore) {
            outline.insertBefore(dragRow, insertBefore);
        } else {
            outline.appendChild(dragRow);
        }
    });
}

function _onOutlineDragEnd() {
    // Stop dragging the row
    if (!_dragRow) return;
    const droppedRow = _dragRow;
    droppedRow.classList.remove("dragging");
    _dragRow = null;

    // Reorder file sections to mirror the new row order in the outline
    _mirrorOutlineOrderToFileSections();

    // Keep focus on the drag handle of the dropped row so that
    // keyboard shortcuts can chain off of the just-completed drag.
    const handle = droppedRow.querySelector(".outline-handle");
    if (handle instanceof HTMLElement) handle.focus();
}

// -----------------------------------------------------------------------------
// Move Actions (Keyboard + Menu)

function _moveRow(
    /** @type {HTMLElement} */ row,
    /** @type {"top" | "up" | "down" | "bottom"} */ direction)
{
    const outline = document.getElementById("file-outline");
    if (!outline) { throw new Error("#file-outline not found"); }
    const rows = /** @type {HTMLElement[]} */(
        Array.from(outline.querySelectorAll(".outline-row"))
    );
    const idx = rows.indexOf(row);
    if (idx === -1) { throw new Error("row not found in #file-outline"); }

    /** @type {HTMLElement | null} */
    let insertBefore;
    if (direction === "top") {
        if (idx === 0) return;
        insertBefore = rows[0];
    } else if (direction === "up") {
        if (idx === 0) return;
        insertBefore = rows[idx - 1];
    } else if (direction === "down") {
        if (idx === rows.length - 1) return;
        // Insert before the row two slots below, i.e. after current next row
        insertBefore = rows[idx + 2] ?? null;
    } else if (direction === "bottom") {
        if (idx === rows.length - 1) return;
        insertBefore = null;
    } else {
        throw new Error(`unreachable: unknown direction ${direction}`);
    }

    _reorderAllOutlineRows(() => {
        if (insertBefore) {
            outline.insertBefore(row, insertBefore);
        } else {
            outline.appendChild(row);
        }
    });
    _mirrorOutlineOrderToFileSections();
}

// -----------------------------------------------------------------------------
// Reorder Animation

function _reorderAllOutlineRows(/** @type {() => void} */ mutate) {
    const outline = document.getElementById("file-outline");
    if (!outline) { throw new Error("#file-outline not found"); }
    const rows = /** @type {HTMLElement[]} */(
        Array.from(outline.querySelectorAll(".outline-row"))
    );
    _reorderOutlineRowsWithAnimation(rows, mutate);
}

function _reorderOutlineRowsWithAnimation(
    /** @type {HTMLElement[]} */ elements,
    /** @type {() => void} */ mutate)
{
    // Capture original rectangles of elements
    /** @type {Map<HTMLElement, number>} */
    const oldTops = new Map();
    for (const el of elements) {
        oldTops.set(el, el.getBoundingClientRect().top);
    }

    // Mutate order of elements in the DOM
    mutate();

    // 1. Translate each element's rectangle to its original Y offset,
    //    so that it starts visually in its original location
    // 2. Use a transition transform to animate the translation to zero,
    //    so that the animation ends with the element in the visual location
    //    implied by the new DOM ordering
    for (const el of elements) {
        const oldTop = oldTops.get(el);
        if (oldTop === undefined) { throw new Error("element missing from oldTops map"); }
        const newTop = el.getBoundingClientRect().top;
        const delta = oldTop - newTop;
        if (delta === 0) continue;  // element did not move

        el.style.transition = "none";
        el.style.transform = `translateY(${delta}px)`;
        // Force reflow so the next assignment takes effect as a transition
        void el.offsetWidth;
        el.style.transition = `transform ${FLIP_DURATION_MS}ms ease`;
        el.style.transform = "";

        setTimeout(() => {
            el.style.transition = "";
        }, FLIP_DURATION_MS + 20);
    }
}

// -----------------------------------------------------------------------------
// Mirror Outline Order to File Sections

function _mirrorOutlineOrderToFileSections() {
    const outline = document.getElementById("file-outline");
    const content = document.getElementById("diff-content");
    if (!outline) { throw new Error("#file-outline not found"); }
    if (!content) { throw new Error("#diff-content not found"); }

    const sections = /** @type {HTMLElement[]} */(
        Array.from(content.querySelectorAll(":scope > details.file-section"))
    );

    const desiredIds = /** @type {string[]} */(
        Array.from(outline.querySelectorAll(".outline-row"))
            .map((r) => r.getAttribute("data-file-idx"))
            .filter((s) => s !== null)
            .map((s) => `file-${s}`)
    );

    _reorderOutlineRowsWithAnimation(sections, () => {
        for (const id of desiredIds) {
            const section = document.getElementById(id);
            if (!(section instanceof HTMLElement)) { throw new Error('section for outline row not found'); }
            content.appendChild(section);
        }
    });
}

// -----------------------------------------------------------------------------
// Keyboard Events

function _onOutlineKeydown(/** @type {Event} */ e) {
    if (!(e instanceof KeyboardEvent)) { throw new Error("keydown event is not a KeyboardEvent"); }
    const target = e.target;
    if (!(target instanceof HTMLElement)) { throw new Error("keydown target is not an HTMLElement"); }
    const handle = target.closest(".outline-handle");
    if (!(handle instanceof HTMLElement)) return;  // key was pressed on a non-handle element (e.g. focused anchor)
    const row = handle.closest(".outline-row");
    if (!(row instanceof HTMLElement)) { throw new Error(".outline-handle is not inside an .outline-row"); }

    /** @type {"top" | "up" | "bottom" | "down" | null} */
    let direction = null;
    if (e.key === "ArrowUp") {
        direction = e.shiftKey ? "top" : "up";
    } else if (e.key === "ArrowDown") {
        direction = e.shiftKey ? "bottom" : "down";
    }

    if (direction !== null) {
        e.preventDefault();
        _moveRow(row, direction);
        // Restore focus to the drag handle explicitly,
        // because it can lose focus after being detached and reattached during the move
        handle.focus();
    } else if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        _openReorderMenu(handle, row, /*focusFirstItem=*/true);
    }
}

// -----------------------------------------------------------------------------
// Dropdown Menu

/** @type {HTMLElement | null} */
let _openMenu = null;

function _onOutlineContextMenu(/** @type {Event} */ e) {
    if (!(e instanceof MouseEvent)) { throw new Error("contextmenu event is not a MouseEvent"); }
    const target = e.target;
    if (!(target instanceof HTMLElement)) { throw new Error("contextmenu target is not an HTMLElement"); }
    const handle = target.closest(".outline-handle");
    if (!(handle instanceof HTMLElement)) return;  // right-clicked on a non-handle element
    const row = handle.closest(".outline-row");
    if (!(row instanceof HTMLElement)) { throw new Error(".outline-handle is not inside an .outline-row"); }

    e.preventDefault();
    _openReorderMenu(handle, row, /*focusFirstItem=*/false, e.clientX, e.clientY);
}

function _openReorderMenu(
    /** @type {HTMLElement} */ handle,
    /** @type {HTMLElement} */ row,
    /** @type {boolean} */ focusFirstItem,
    /** @type {number | undefined} */ clientX = undefined,
    /** @type {number | undefined} */ clientY = undefined)
{
    // Close any other reorder menu that was open previously on a different drag handle
    _closeReorderMenu();

    // Create menu
    const menu = document.createElement("ul");
    {
        menu.className = "reorder-menu";
        menu.setAttribute("role", "menu");
        menu.tabIndex = -1;

        /** @type {{label: string, shortcut: string, action: "top" | "up" | "bottom" | "down"}[]} */
        const items = [
            { label: "Move to Top", shortcut: "⇧ ↑", action: "top" },
            { label: "Move Up", shortcut: "↑", action: "up" },
            { label: "Move to Bottom", shortcut: "⇧ ↓", action: "bottom" },
            { label: "Move Down", shortcut: "↓", action: "down" },
        ];

        for (const it of items) {
            const li = document.createElement("li");
            li.setAttribute("role", "menuitem");
            li.tabIndex = 0;
            const labelSpan = document.createElement("span");
            labelSpan.textContent = it.label;
            const shortcutSpan = document.createElement("span");
            shortcutSpan.className = "menu-shortcut";
            shortcutSpan.textContent = it.shortcut;
            li.appendChild(labelSpan);
            li.appendChild(shortcutSpan);
            li.addEventListener("click", () => {
                _moveRow(row, it.action);
                // Focus the handle before removing the menu, so WebKit's focus
                // restoration on element removal doesn't steal focus to <body>.
                handle.focus();
                _closeReorderMenu();
            });
            li.addEventListener("keydown", (ev) => {
                if (!(ev instanceof KeyboardEvent)) { throw new Error("keydown event is not a KeyboardEvent"); }
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    _moveRow(row, it.action);
                    handle.focus();
                    _closeReorderMenu();
                } else if (ev.key === "ArrowDown") {
                    ev.preventDefault();
                    const next = li.nextElementSibling;
                    if (next instanceof HTMLElement) next.focus();
                } else if (ev.key === "ArrowUp") {
                    ev.preventDefault();
                    const prev = li.previousElementSibling;
                    if (prev instanceof HTMLElement) prev.focus();
                }
            });
            menu.appendChild(li);
        }

        document.body.appendChild(menu);
    }

    // Position menu
    let x, y;
    if (clientX !== undefined && clientY !== undefined) {
        x = clientX;
        y = clientY;
    } else {
        const rect = handle.getBoundingClientRect();
        x = rect.left;
        y = rect.bottom + 2;
    }
    // Clamp to viewport
    const menuRect = menu.getBoundingClientRect();
    if (x + menuRect.width > window.innerWidth) {
        x = Math.max(0, window.innerWidth - menuRect.width - 4);
    }
    if (y + menuRect.height > window.innerHeight) {
        y = Math.max(0, window.innerHeight - menuRect.height - 4);
    }
    menu.style.left = x + "px";
    menu.style.top = y + "px";

    _openMenu = menu;

    // Focus first item if requested
    if (focusFirstItem) {
        const first = menu.querySelector("li[role='menuitem']");
        if (!(first instanceof HTMLElement)) { throw new Error("menu has no menuitem to focus"); }
        first.focus();
    }

    // Listen for click/keydown on document to dismiss menu
    // NOTE: Defer listener registration so that the click which opened
    //       the menu doesn't immediately match the outside-click handler.
    setTimeout(() => {
        document.addEventListener("mousedown", _onDocumentMouseDownForMenu, true);
        document.addEventListener("keydown", _onDocumentKeyDownForMenu, true);
    }, 0);
}

function _closeReorderMenu() {
    if (_openMenu && _openMenu.parentNode) {
        _openMenu.parentNode.removeChild(_openMenu);
    }
    _openMenu = null;
    document.removeEventListener("mousedown", _onDocumentMouseDownForMenu, true);
    document.removeEventListener("keydown", _onDocumentKeyDownForMenu, true);
}

function _onDocumentMouseDownForMenu(/** @type {Event} */ e) {
    if (!_openMenu) return;
    const target = e.target;
    if (target instanceof Node && _openMenu.contains(target)) return;
    _closeReorderMenu();
}

function _onDocumentKeyDownForMenu(/** @type {Event} */ e) {
    if (!(e instanceof KeyboardEvent)) { throw new Error("keydown event is not a KeyboardEvent"); }
    if (e.key === "Escape") {
        e.preventDefault();
        _closeReorderMenu();
    }
}

// -----------------------------------------------------------------------------
