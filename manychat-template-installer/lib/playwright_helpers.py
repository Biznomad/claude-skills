"""Playwright helpers for the ManyChat installer.

Small, focused utilities — kept here so install.py stays readable.
All functions are sync (we use playwright.sync_api).
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

try:
    from playwright.sync_api import Page, TimeoutError as PWTimeoutError
except ImportError:  # pragma: no cover
    Page = Any  # type: ignore
    PWTimeoutError = Exception  # type: ignore

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def wait_for_text(page: Page, text: str, timeout: int = 30000) -> bool:
    """Wait until visible page text contains `text`. Return True/False.

    Uses Playwright's built-in `wait_for_selector` with a text= engine
    so we don't have to poll inner_text() manually.
    """
    try:
        page.wait_for_selector(f"text={text}", timeout=timeout)
        return True
    except PWTimeoutError:
        return False


def click_when_visible(page: Page, selector: str, timeout: int = 10000, optional: bool = False) -> bool:
    """Wait for selector to be visible then click it.

    If `optional`, swallow timeouts and return False (caller decides whether to
    care). Otherwise raise the underlying PWTimeoutError.
    """
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        page.click(selector)
        return True
    except PWTimeoutError:
        if optional:
            return False
        raise


def screenshot_on_error(page: Page | None, out_path: Path) -> None:
    """Best-effort screenshot capture for failure forensics."""
    if page is None:
        return
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_path), full_page=True)
        print(f"[FORENSIC] screenshot saved -> {out_path}")
    except Exception as e:  # pragma: no cover
        print(f"[WARN] could not capture screenshot: {e}")


def _all_text_inputs(page: Page) -> list[Any]:
    """Return locators for every editable text surface inside a flow editor.

    ManyChat's flow editor uses a mix of <textarea>, contentEditable divs, and
    rich-text spans. We try a broad set of selectors and let the caller filter.
    """
    # TODO: confirm selectors — ManyChat flow editor uses multiple block types
    selectors = [
        "[data-test=message-text-input]",
        "textarea[data-block-type=text]",
        "div[contenteditable=true]",
        "[data-test=button-label-input]",
        "[data-test=quick-reply-input]",
    ]
    locators = []
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() > 0:
            locators.append(loc)
    return locators


def text_replace_in_visible_blocks(page: Page, overrides: dict[str, str]) -> int:
    """For every editable block on the page, replace `{{key}}` with `overrides[key]`.

    Returns the number of replacements applied (not unique keys; one per block
    edit). Logs a warning for any `{{key}}` we encounter that has no override.
    """
    if not overrides:
        return 0

    replacements = 0
    seen_unknown: set[str] = set()

    for loc in _all_text_inputs(page):
        count = loc.count()
        for i in range(count):
            handle = loc.nth(i)
            try:
                current = handle.inner_text(timeout=2000)
            except PWTimeoutError:
                continue
            if "{{" not in current:
                continue

            new_text = current
            for match in PLACEHOLDER_RE.findall(current):
                if match in overrides:
                    new_text = new_text.replace(f"{{{{{match}}}}}", overrides[match])
                else:
                    seen_unknown.add(match)

            if new_text == current:
                continue

            # Different write paths for different element types
            try:
                handle.fill(new_text)
            except Exception:
                # contentEditable path
                handle.evaluate("(el, val) => { el.innerText = val; }", new_text)
                # Fire input event so ManyChat picks up the change
                handle.evaluate("(el) => el.dispatchEvent(new Event('input', {bubbles: true}))")
            replacements += 1

    if seen_unknown:
        print(f"[WARN] placeholders with no YAML mapping: {sorted(seen_unknown)}")
    # Give the editor a beat to autosave before we navigate away
    time.sleep(1.5)
    return replacements


def safe_goto(page: Page, url: str, retries: int = 3) -> None:
    """Navigate to a URL with simple exponential backoff."""
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return
        except PWTimeoutError as e:
            last_exc = e
            time.sleep(2 ** attempt)
    if last_exc:
        raise last_exc
