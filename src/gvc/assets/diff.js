// @ts-check
"use strict";

// -------------------------------------------------------
// State

const find = {
    query: "",
    caseInsensitive: true,
    wholeWord: false,
    useRegex: false,
    /** @type {HTMLElement[]} */
    marks: [],
    current: -1,
};

// -------------------------------------------------------
// Init

// Wait for pywebview bridge
window.addEventListener("pywebviewready", async () => {
    try {
        const prefs = await window.pywebview.api.get_prefs();
        applyFontSize(prefs.font_size);
    } catch (e) {
        // Running standalone in a browser for development — ignore
    }
});

// Wait for DOM
document.addEventListener("DOMContentLoaded", () => {
    setupKeyboard();
    setupFindBar();
});

// -------------------------------------------------------
// Font Size

function applyFontSize(/** @type {number} */ size) {
    document.documentElement.style.setProperty("--font-size", size + "px");
}

// -------------------------------------------------------
// Keyboard Shortcuts

function setupKeyboard() {
    document.addEventListener("keydown", (e) => {
        const cmd = e.metaKey || e.ctrlKey;

        // Cmd+F — open find bar
        if (cmd && e.key === "f") {
            e.preventDefault();
            openFindBar();
            return;
        }

        // Escape — close find bar
        if (e.key === "Escape") {
            closeFindBar();
            return;
        }

        // Cmd+G — find next
        if (cmd && !e.shiftKey && e.key === "g") {
            e.preventDefault();
            findStep(1);
            return;
        }

        // Shift+Cmd+G — find previous
        if (cmd && e.shiftKey && e.key === "g") {
            e.preventDefault();
            findStep(-1);
            return;
        }

        // Cmd+= or Cmd++ — increase font size
        if (cmd && (e.key === "=" || e.key === "+")) {
            e.preventDefault();
            changeFontSize(1);
            return;
        }

        // Cmd+- — decrease font size
        if (cmd && e.key === "-") {
            e.preventDefault();
            changeFontSize(-1);
            return;
        }
    });
}

// -------------------------------------------------------
// Font Size Change

async function changeFontSize(/** @type {number} */ delta) {
    const current = parseFloat(
        getComputedStyle(document.documentElement).getPropertyValue("--font-size")
    ) || 13;
    const next = Math.max(8, Math.min(32, Math.round(current + delta)));
    applyFontSize(next);
    try {
        await window.pywebview.api.set_font_size(next);
    } catch (e) { /* standalone browser */ }
}

// -------------------------------------------------------
// Collapse / Expand All

function setAllSections(/** @type {boolean} */ open) {
    document.querySelectorAll("details.file-section").forEach((d) => {
        if (!(d instanceof HTMLDetailsElement)) { throw new Error('Expected <details> element') }
        d.open = open;
    });
}

// -------------------------------------------------------
// Find Bar

function setupFindBar() {
    const bar = document.getElementById("find-bar");
    const input = document.getElementById("find-input");
    const btnCase = document.getElementById("btn-case");
    const btnWord = document.getElementById("btn-word");
    const btnRegex = document.getElementById("btn-regex");
    const btnPrev = document.getElementById("btn-find-prev");
    const btnNext = document.getElementById("btn-find-next");
    const btnClose = document.getElementById("find-close");
    if (!bar) { throw new Error("find-bar not found"); }
    if (!(input instanceof HTMLInputElement)) { throw new Error("find-input not found or wrong type"); }
    if (!btnCase) { throw new Error("btn-case not found"); }
    if (!btnWord) { throw new Error("btn-word not found"); }
    if (!btnRegex) { throw new Error("btn-regex not found"); }
    if (!btnPrev) { throw new Error("btn-find-prev not found"); }
    if (!btnNext) { throw new Error("btn-find-next not found"); }
    if (!btnClose) { throw new Error("find-close not found"); }

    // Input change
    input.addEventListener("input", () => {
        find.query = input.value;
        runFind();
    });

    // Enter / Shift+Enter in input
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            findStep(e.shiftKey ? -1 : 1);
        }
    });

    // Toggle buttons
    btnCase.addEventListener("click", () => {
        find.caseInsensitive = !find.caseInsensitive;
        btnCase.setAttribute("aria-pressed", String(!find.caseInsensitive));
        runFind();
    });

    btnWord.addEventListener("click", () => {
        find.wholeWord = !find.wholeWord;
        btnWord.setAttribute("aria-pressed", String(find.wholeWord));
        runFind();
    });

    btnRegex.addEventListener("click", () => {
        find.useRegex = !find.useRegex;
        btnRegex.setAttribute("aria-pressed", String(find.useRegex));
        runFind();
    });

    btnPrev.addEventListener("click", () => findStep(-1));
    btnNext.addEventListener("click", () => findStep(1));
    btnClose.addEventListener("click", () => closeFindBar());
}

function openFindBar() {
    const bar = document.getElementById("find-bar");
    const input = document.getElementById("find-input");
    if (!bar) { throw new Error("find-bar not found"); }
    if (!(input instanceof HTMLInputElement)) { throw new Error("find-input not found or wrong type"); }
    
    bar.classList.remove("hidden");
    input.focus();
    input.select();
}

function closeFindBar() {
    const bar = document.getElementById("find-bar");
    if (!bar) { throw new Error("find-bar not found"); }
    
    bar.classList.add("hidden");
    clearMarks();
    find.current = -1;
}

// -------------------------------------------------------
// Find Implementation

function buildRegex(/** @type {string} */ query) {
    if (!query) return null;
    try {
        let pattern = find.useRegex ? query : escapeRegex(query);
        if (find.wholeWord) pattern = `\\b${pattern}\\b`;
        const flags = find.caseInsensitive ? "gi" : "g";
        return new RegExp(pattern, flags);
    } catch (e) {
        return null; // invalid regex
    }
}

function escapeRegex(/** @type {string} */ s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function runFind() {
    clearMarks();
    find.marks = [];
    find.current = -1;

    const input = document.getElementById("find-input");
    if (!(input instanceof HTMLInputElement)) { throw new Error("find-input not found or wrong type"); }
    
    if (!find.query) {
        input.classList.remove("no-match");
        return;
    }

    const regex = buildRegex(find.query);
    if (!regex) {
        input.classList.add("no-match");
        return;
    }

    const container = document.getElementById("diff-content");
    if (!container) return;

    // Walk all text nodes in the diff content
    const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null
    );

    const textNodes = [];
    let node;
    while ((node = walker.nextNode())) {
        textNodes.push(node);
    }

    for (const textNode of textNodes) {
        const text = textNode.nodeValue;
        if (!text) continue;

        const matches = [...text.matchAll(regex)];
        if (!matches.length) continue;

        // Build fragment replacing match spans with <mark> elements
        const frag = document.createDocumentFragment();
        let lastIndex = 0;

        for (const match of matches) {
            const start = match.index;
            const end = start + match[0].length;

            if (lastIndex < start) {
                frag.appendChild(document.createTextNode(text.slice(lastIndex, start)));
            }

            const mark = document.createElement("mark");
            mark.className = "find-match";
            mark.textContent = match[0];
            frag.appendChild(mark);
            find.marks.push(mark);

            lastIndex = end;
        }

        if (lastIndex < text.length) {
            frag.appendChild(document.createTextNode(text.slice(lastIndex)));
        }

        if (!textNode.parentNode) { throw new Error("textNode has no parent"); }
        textNode.parentNode.replaceChild(frag, textNode);
    }

    if (find.marks.length === 0) {
        input.classList.add("no-match");
    } else {
        input.classList.remove("no-match");
        findStep(1, true); // jump to first match without wrap flash
    }
}

function clearMarks() {
    // Replace each <mark> with its text content
    for (const mark of find.marks) {
        if (mark.parentNode) {
            const text = document.createTextNode(mark.textContent);
            mark.parentNode.replaceChild(text, mark);
        }
    }
    find.marks = [];
    // Normalise text nodes that were split during marking
    const container = document.getElementById("diff-content");
    if (container) container.normalize();
}

function findStep(/** @type {number} */ direction, /** @type {boolean} */ suppressWrapFlash = false) {
    if (!find.marks.length) return;

    const prev = find.current;

    if (prev >= 0 && prev < find.marks.length) {
        find.marks[prev].classList.remove("find-current");
    }

    find.current += direction;

    let wrapped = false;
    if (find.current >= find.marks.length) {
        find.current = 0;
        wrapped = true;
    } else if (find.current < 0) {
        find.current = find.marks.length - 1;
        wrapped = true;
    }

    const mark = find.marks[find.current];
    mark.classList.add("find-current");
    mark.scrollIntoView({ block: "center", inline: "nearest" });

    if (wrapped && !suppressWrapFlash) {
        flashWrapOverlay();
    }
}

// -------------------------------------------------------
// Wrap-Around Flash Overlay

/** @type {ReturnType<typeof setTimeout> | null} */
let _wrapTimer = null;

function flashWrapOverlay() {
    const overlay = document.getElementById("wrap-overlay");
    if (!overlay) return;

    if (_wrapTimer) {
        clearTimeout(_wrapTimer);
        overlay.classList.remove("visible");
        // Force reflow so the transition re-triggers
        void overlay.offsetWidth;
    }

    overlay.classList.add("visible");
    _wrapTimer = setTimeout(() => {
        overlay.classList.remove("visible");
        _wrapTimer = null;
    }, 800);
}

// -------------------------------------------------------
// Large Diff Gate

function revealFullDiff() {
    const gate = document.getElementById("large-diff-gate");
    const full = document.getElementById("full-diff-hidden");
    if (!gate || !full) return;

    // Move the full diff content into view
    const content = document.getElementById("diff-content");
    if (!content) { throw new Error("diff-content not found"); }
    content.innerHTML = "";
    if (!(full instanceof HTMLTemplateElement)) { throw new Error("full-diff-hidden is not a <template>"); }
    content.appendChild(full.content.cloneNode(true));
}

// -------------------------------------------------------
