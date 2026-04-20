// PlaywrightKit Runtime Library — the in-page JS half of PlaywrightKit.
//
// Python (`_jsbridge.py`) templates __GVC_KIND__, __GVC_CHAIN__, __GVC_ARG__
// into this source as JSON literals and ships it through the host's
// eval_js(window_id, src) transport. On the first call it installs the
// runtime as window.pwk; subsequent calls reuse it.
//
// Returns either {ok: <value>} or {error: <string>} so Python can unwrap.

(function (kind, chain, arg) {
    if (!window.pwk) {
        window.pwk = (function () {
            function resolveAll(ops) {
                var current = [document];
                for (var i = 0; i < ops.length; i++) {
                    var op = ops[i];
                    if (op.op === 'locator') {
                        var next = [];
                        for (var j = 0; j < current.length; j++) {
                            var found = current[j].querySelectorAll(op.selector);
                            for (var k = 0; k < found.length; k++) next.push(found[k]);
                        }
                        current = next;
                    } else if (op.op === 'nth') {
                        var idx = op.index < 0 ? current.length + op.index : op.index;
                        current = (idx >= 0 && idx < current.length) ? [current[idx]] : [];
                    } else {
                        throw new Error('unknown chain op: ' + op.op);
                    }
                }
                return current;
            }

            function resolveOne(ops) {
                var all = resolveAll(ops);
                return all.length > 0 ? all[0] : null;
            }

            // Playwright-like visibility: element attached, not display:none /
            // visibility:hidden / collapse, non-zero opacity, has at least one
            // non-zero bounding rect.
            function isVisible(el) {
                if (!el || !el.isConnected) return false;
                var s = getComputedStyle(el);
                if (s.display === 'none') return false;
                if (s.visibility === 'hidden' || s.visibility === 'collapse') return false;
                if (parseFloat(s.opacity) === 0) return false;
                var rect = el.getBoundingClientRect();
                if (rect.width === 0 && rect.height === 0) return false;
                return true;
            }

            function op(kind, chain, arg) {
                switch (kind) {
                    case 'count':
                        return resolveAll(chain).length;
                    case 'textContent': {
                        var el = resolveOne(chain);
                        return el === null ? null : el.textContent;
                    }
                    case 'innerText': {
                        var el = resolveOne(chain);
                        return el === null ? null : el.innerText;
                    }
                    case 'getAttribute': {
                        var el = resolveOne(chain);
                        return el === null ? null : el.getAttribute(arg);
                    }
                    case 'hasAttribute': {
                        var el = resolveOne(chain);
                        return el === null ? false : el.hasAttribute(arg);
                    }
                    case 'inputValue': {
                        var el = resolveOne(chain);
                        return el === null ? null : el.value;
                    }
                    case 'isVisible':
                        return isVisible(resolveOne(chain));
                    case 'computedCss': {
                        var el = resolveOne(chain);
                        if (el === null) return null;
                        return getComputedStyle(el)[arg];
                    }
                    case 'classList': {
                        var el = resolveOne(chain);
                        return el === null ? null : Array.prototype.slice.call(el.classList);
                    }
                    case 'click': {
                        var el = resolveOne(chain);
                        if (el === null) throw new Error('click: no matching element');
                        el.click();
                        return null;
                    }
                    case 'evaluate': {
                        var el = resolveOne(chain);
                        return (new Function('el', 'return (' + arg + ')(el);'))(el);
                    }
                    case 'evaluatePage': {
                        return (new Function('return (' + arg + ')();'))();
                    }
                    default:
                        throw new Error('unknown op: ' + kind);
                }
            }

            return { op: op, resolveAll: resolveAll, resolveOne: resolveOne, isVisible: isVisible };
        })();
    }

    try {
        return { ok: window.pwk.op(kind, chain, arg) };
    } catch (e) {
        return { error: (e && e.message) ? e.message : String(e) };
    }
})(__GVC_KIND__, __GVC_CHAIN__, __GVC_ARG__)
