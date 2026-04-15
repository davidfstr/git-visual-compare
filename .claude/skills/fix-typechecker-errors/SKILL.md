---
name: fix-typechecker-errors
description: Fix mypy type errors by investigating root causes instead of silencing the checker. Use when mypy reports errors and you need to decide the best way to fix them.
disable-model-invocation: true
argument-hint: "[optional: specific errors to focus on]"
---

# Fix Typechecker Errors

When asked to fix mypy errors, follow this hierarchy of approaches:

## 1. Root Cause Fixes (Best)

**Adjust the actual type annotation or implementation.**

The goal here is to fix the problem at its source rather than suppress it.

There are several approaches to fixing the root cause. Here are a few commonly-observed patterns:

- Fix a type annotation to accurately reflect what the code does
    - Narrow over-broad type annotations (e.g., `Window | None` → `Window` when the function never returns None)
    - Use union types only when multiple values are actually possible

**Why this works:** Root cause fixes cascade through the codebase. When you fix the return type of a function, all callers automatically benefit—they no longer need workarounds or assertions. The type system becomes an accurate reflection of reality.

### 1.1. Narrow over-broad type annotations

Example of narrowing an over-broad return type annotation:
```python
# Before: Too broad return type
def create_window(...) -> webview.Window | None:
    window = webview.create_window(...)
    return window  # Always non-None, but type says it might be

# After: Correct return type
def create_window(...) -> webview.Window:
    window = webview.create_window(...)
    return window
```

### 1.2. Handle real failure modes with an explicit check-and-raise

When a function genuinely *can* return `None` (or some other sentinel) on failure, don't use `assert isinstance(...)` to narrow the type — that conflates a real runtime failure with a programmer-error check. `assert` can be stripped with `python -O`, and reading an assertion tells the next reader "this can't happen," which is the wrong message.

**Before reaching for `assert isinstance(...)`, verify the stub is actually wrong.** Read the source of the function if you can. If `None` is a genuine failure mode, handle it explicitly:

```python
# Before: assert conflates "can't happen" with "handle the failure"
window = webview.create_window(...)
assert isinstance(window, webview.Window)  # wrong: None is a real failure mode

# After: explicit check-and-raise preserves the failure semantics
window = webview.create_window(...)
if window is None:
    raise Exception("Failed to create window")
```

This both narrows the type (mypy sees the guard) and handles the failure honestly. The distinction from section 2 below: use `assert isinstance()` only when the type stub is provably overly permissive and `None`/other values cannot occur in practice.

### 1.N. (TODO: Add more patterns, each with an example)

## 2. Runtime Validation with isinstance() (Good)

**Use `isinstance() + assert` when type inference fails but you know the runtime type for certain.**

Examples:
- `assert isinstance(result, bool)` when `result = x == y` (comparison always returns bool, but mypy infers Any from untyped libraries)
- `assert isinstance(window, webview.Window)` when a function call always succeeds but type stubs are overly permissive

**Why this is better than cast():** An assert validates *at runtime*. If your assumption is wrong, it fails immediately and loudly, revealing the bug. A `cast()` silently trusts your assumption—if it's wrong, bad data propagates through the program and causes subtle failures much later. Runtime validation catches bugs when they happen, not weeks later in production.

**When to use it:** Appropriate when the operation provably returns a specific type and you have confidence in that proof. Not appropriate when the type is genuinely uncertain.

Example:
```python
# Problem: mypy infers Any from pyobjc
result = defaults.stringForKey_("AppleInterfaceStyle") == "Dark"

# Solution: Validate at runtime
result = defaults.stringForKey_("AppleInterfaceStyle") == "Dark"
assert isinstance(result, bool)
return result
```

## 3. cast() — Last Resort (Report for Review)

Use `cast()` only when runtime validation is impossible or impractical. The danger: `cast()` silently accepts bad data. If your assumption is wrong, the bad data flows through the program undetected.

```python
# Avoid unless necessary; this trusts the assertion and fails silently if wrong
return cast(bool, defaults.stringForKey_("AppleInterfaceStyle") == "Dark")
```

**When you use cast():** Always call it out explicitly in your response. The user needs to verify your reasoning.

## 4. # type: ignore — Last Resort (Report for Review)

Use `# type: ignore` only when there's genuinely no other option.

```python
import AppKit  # type: ignore[import-untyped]
```

Always specify the error code (not a bare `# type: ignore`). When you add one: call it out explicitly for human review. Consider whether the real fix is a stub correction or type annotation change instead.

## My Workflow

**Initial response:**
1. **Attempt fixes** using the hierarchy above (root cause → isinstance() → cast() → type: ignore)
2. **Flag any workarounds** — If I use `cast()` or `# type: ignore`, I call it out explicitly and explain why
3. **Ask for review** — I'll explicitly ask you to review/correct my changes and volunteer that I'm interested in learning from any corrections you make (if you have time to explain your reasoning)

**If you choose to show me corrections (optional):**
4. **Interview you** about your changes and why you made them (don't assume my initial fixes were wrong)
5. **Extract principles** — What patterns did you use that I should understand better?
6. **Update my skill** with what I learned

The interview/learning part only happens if you're willing to share your reasoning. If you're in a rush, no problem — just use the fixes and move on.

## Technique: Getting Type Information

If a type error is confusing and you need to understand what mypy actually inferred for an expression, wrap it in `reveal_type()`:

```python
# Temporarily add this to understand the inferred type
result = defaults.stringForKey_("AppleInterfaceStyle") == "Dark"
reveal_type(result)  # mypy will emit: Revealed type is "Any"
```

Run `mypy` and it will output a note showing the inferred type. `reveal_type()` is a builtin that mypy understands (no import needed). After investigating, remove it. This is invaluable for understanding type inference mismatches between what's declared and what's actually inferred.
