#!/usr/bin/env python3
"""ManyChat Template Installer.

Installs a pre-built ManyChat Template into a target client account, then
overrides every {{placeholder}} text token per the YAML config.

Per CLAUDE.md project-isolation rule: per-client browser data dir, per-client
YAML, never share auth across clients.

Usage:
    python install.py --config configs/vicelle.yaml [--interactive-login] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Lazy imports so `python -c "import install"` smoke test works even when
# playwright isn't on the path yet.
try:
    from playwright.sync_api import (
        BrowserContext,
        Page,
        TimeoutError as PWTimeoutError,
        sync_playwright,
    )
except ImportError:  # pragma: no cover
    sync_playwright = None  # type: ignore
    BrowserContext = Any  # type: ignore
    Page = Any  # type: ignore
    PWTimeoutError = Exception  # type: ignore

SKILL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL_ROOT))

from lib.playwright_helpers import (  # noqa: E402
    click_when_visible,
    screenshot_on_error,
    text_replace_in_visible_blocks,
    wait_for_text,
)
from lib.yaml_loader import load_config  # noqa: E402

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
PLACEHOLDER_TAG_PREFIX = "PLACEHOLDER_"

MANYCHAT_BASE = "https://manychat.com"
LOGIN_URL = f"{MANYCHAT_BASE}/login"


# ---------------------------------------------------------------------------
# Browser session
# ---------------------------------------------------------------------------

def browser_data_dir(client_slug: str) -> Path:
    """Per-client persistent profile dir (enforces project isolation)."""
    return Path.home() / ".manychat-installer-browser-data" / client_slug


def launch_context(client_slug: str, headless: bool = False) -> tuple[Any, BrowserContext]:
    """Launch Chromium with persistent context for this client only."""
    if sync_playwright is None:
        raise RuntimeError("Install playwright first: pip install playwright && playwright install chromium")
    data_dir = browser_data_dir(client_slug)
    data_dir.mkdir(parents=True, exist_ok=True)
    pw = sync_playwright().start()
    context = pw.chromium.launch_persistent_context(
        user_data_dir=str(data_dir),
        headless=headless,
        viewport={"width": 1440, "height": 900},
        args=["--disable-blink-features=AutomationControlled"],
    )
    return pw, context


def ensure_logged_in(page: Page, interactive: bool) -> None:
    """Confirm a live ManyChat session, prompt for human login if not."""
    page.goto(f"{MANYCHAT_BASE}/app", wait_until="domcontentloaded")
    # TODO: confirm selector — element that proves authenticated state (sidebar avatar?)
    try:
        page.wait_for_selector("[data-test=app-sidebar], .app-sidebar, nav[role=navigation]", timeout=8000)
        return
    except PWTimeoutError:
        pass

    if not interactive:
        raise RuntimeError(
            "No active ManyChat session for this client. Re-run with --interactive-login "
            "and complete the login (incl. 2FA) in the opened browser window."
        )

    print("\n[LOGIN] Browser window is open. Log in to the CORRECT client account.")
    print("        Press <Enter> here AFTER you see the ManyChat dashboard loaded.\n")
    page.goto(LOGIN_URL)
    input("Press Enter once logged in... ")
    # TODO: confirm selector — re-check post-login
    page.wait_for_selector("[data-test=app-sidebar], .app-sidebar, nav[role=navigation]", timeout=30000)


# ---------------------------------------------------------------------------
# Install wizard
# ---------------------------------------------------------------------------

def install_template(page: Page, template_url: str, target_page_name: str) -> None:
    """Walk the 4-step install wizard for a Template URL."""
    print(f"[INSTALL] Opening template URL: {template_url}")
    page.goto(template_url, wait_until="domcontentloaded")

    # Step 1: pick the page (account may have multiple connected pages)
    # TODO: confirm selector — page picker radio or dropdown
    try:
        page.wait_for_selector("[data-test=template-install-page-picker]", timeout=15000)
        page.click(f"text={target_page_name}")
    except PWTimeoutError:
        # Single-page accounts may skip this step
        print("[INSTALL] Page picker not shown (single-page account?), continuing.")

    # Step 2: permissions / scopes confirm
    # TODO: confirm selector — "Continue" / "Next" button on permissions step
    click_when_visible(page, "button:has-text('Continue')", timeout=10000, optional=True)

    # Step 3: review what will be installed
    # TODO: confirm selector — review screen
    click_when_visible(page, "button:has-text('Install')", timeout=10000)

    # Step 4: wait for completion toast / redirect to Automation list
    print("[INSTALL] Waiting for completion...")
    if not wait_for_text(page, "Install complete", timeout=120000):
        # Fallback: poll for flow list page
        page.wait_for_url(re.compile(r".*/automation.*"), timeout=120000)
    print("[INSTALL] Template installed.")


# ---------------------------------------------------------------------------
# Override pass
# ---------------------------------------------------------------------------

def list_installed_flows(page: Page, expected_names: list[str]) -> list[str]:
    """Return the flow names actually present in the account that match expected."""
    # TODO: confirm selector — Automation > Flows list rows
    page.goto(f"{MANYCHAT_BASE}/app#automation", wait_until="domcontentloaded")
    page.wait_for_selector("[data-test=flow-list], .flow-list, [data-qa=automation-list]", timeout=20000)
    rows = page.locator("[data-test=flow-row], .flow-row").all_inner_texts()
    found = [name for name in expected_names if any(name in row for row in rows)]
    missing = [name for name in expected_names if name not in found]
    if missing:
        print(f"[WARN] Expected flows not found: {missing}")
    return found


def open_flow(page: Page, flow_name: str) -> None:
    """Open a flow by its display name."""
    # TODO: confirm selector — flow row click target
    page.click(f"text={flow_name}")
    page.wait_for_selector("[data-test=flow-canvas], .flow-canvas", timeout=20000)


def override_flow_placeholders(page: Page, flow_name: str, overrides: dict[str, str], dry_run: bool) -> int:
    """Walk visible message blocks in flow and replace placeholder tokens.

    Returns the count of replacements made.
    """
    open_flow(page, flow_name)
    if dry_run:
        print(f"[DRY] would override placeholders in '{flow_name}'")
        return 0
    return text_replace_in_visible_blocks(page, overrides)


# ---------------------------------------------------------------------------
# Tag / Field renames
# ---------------------------------------------------------------------------

def rename_placeholder_tags(page: Page, tag_renames: dict[str, str], dry_run: bool) -> int:
    """Rename PLACEHOLDER_* tags per YAML map."""
    # TODO: confirm selector — Settings > Tags page URL/UI
    page.goto(f"{MANYCHAT_BASE}/app#settings/tags", wait_until="domcontentloaded")
    page.wait_for_selector("[data-test=tag-list], .tag-list", timeout=15000)
    count = 0
    for old, new in tag_renames.items():
        if not old.startswith(PLACEHOLDER_TAG_PREFIX):
            print(f"[WARN] Skipping non-placeholder tag rename: {old}")
            continue
        if dry_run:
            print(f"[DRY] rename tag {old} -> {new}")
            count += 1
            continue
        # TODO: confirm selector — per-row "edit" button
        row = page.locator(f"[data-test=tag-row]:has-text('{old}')")
        if row.count() == 0:
            print(f"[WARN] Tag not found: {old}")
            continue
        row.locator("button[data-test=edit-tag]").click()
        input_box = page.locator("input[data-test=tag-name-input]")
        input_box.fill(new)
        page.click("button:has-text('Save')")
        count += 1
    return count


def rename_placeholder_fields(page: Page, field_renames: dict[str, str], dry_run: bool) -> int:
    """Rename PLACEHOLDER_* custom fields per YAML map."""
    # TODO: confirm selector — Settings > Custom Fields page
    page.goto(f"{MANYCHAT_BASE}/app#settings/fields", wait_until="domcontentloaded")
    page.wait_for_selector("[data-test=field-list], .field-list", timeout=15000)
    count = 0
    for old, new in field_renames.items():
        if dry_run:
            print(f"[DRY] rename field {old} -> {new}")
            count += 1
            continue
        row = page.locator(f"[data-test=field-row]:has-text('{old}')")
        if row.count() == 0:
            print(f"[WARN] Field not found: {old}")
            continue
        row.locator("button[data-test=edit-field]").click()
        input_box = page.locator("input[data-test=field-name-input]")
        input_box.fill(new)
        page.click("button:has-text('Save')")
        count += 1
    return count


# ---------------------------------------------------------------------------
# Verify pass
# ---------------------------------------------------------------------------

def verify_no_placeholders(page: Page, flow_names: list[str]) -> list[tuple[str, str]]:
    """Re-open each flow and regex-scan visible text for any surviving {{tokens}}.

    Returns list of (flow_name, surviving_token).
    """
    survivors: list[tuple[str, str]] = []
    for name in flow_names:
        open_flow(page, name)
        # TODO: confirm selector — canvas text content scrape
        body = page.locator("[data-test=flow-canvas], .flow-canvas").inner_text()
        for m in PLACEHOLDER_RE.findall(body):
            survivors.append((name, m))
    return survivors


# ---------------------------------------------------------------------------
# Post-install actions
# ---------------------------------------------------------------------------

def run_post_install_actions(page: Page, actions: list[dict[str, Any]], dry_run: bool) -> None:
    """Execute optional post-install hooks declared in YAML (subscribe owner, etc)."""
    for action in actions:
        kind = action.get("type")
        if dry_run:
            print(f"[DRY] post-install action: {kind} {action}")
            continue
        if kind == "subscribe_owner_to_admin_notifications":
            # TODO: confirm selector — Settings > Notifications page
            page.goto(f"{MANYCHAT_BASE}/app#settings/notifications")
            page.click("[data-test=toggle-admin-notifications]")
        elif kind == "set_default_reply":
            # TODO: confirm selector — default reply textarea
            page.goto(f"{MANYCHAT_BASE}/app#automation/default-reply")
            page.fill("[data-test=default-reply-textarea]", action.get("text", ""))
            page.click("button:has-text('Save')")
        else:
            print(f"[WARN] Unknown post-install action: {kind}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_overrides(cfg: dict[str, Any]) -> dict[str, str]:
    """Flatten the YAML `placeholders` map into `{key: replacement_string}`."""
    out: dict[str, str] = {}
    for key, value in (cfg.get("placeholders") or {}).items():
        if isinstance(value, dict):
            # nested (e.g. product_1: {name: ..., url: ...}) -> product_1_name etc
            for sub, sub_val in value.items():
                out[f"{key}_{sub}"] = str(sub_val)
        else:
            out[key] = str(value)
    return out


def write_log_header(cfg: dict[str, Any]) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")
    log_dir = SKILL_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{cfg['client_slug']}-{ts}.log"
    log_path.write_text(f"# ManyChat installer run {ts}\n# Client: {cfg['client_slug']}\n")
    return log_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install + customize a ManyChat template.")
    parser.add_argument("--config", required=True, help="Path to client YAML")
    parser.add_argument("--interactive-login", action="store_true", help="Allow human login prompt")
    parser.add_argument("--dry-run", action="store_true", help="Walk but do not mutate")
    parser.add_argument("--headless", action="store_true", help="Run headless (not recommended first time)")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    client_slug = cfg["client_slug"]
    overrides = build_overrides(cfg)
    print(f"[BOOT] client={client_slug} placeholders={len(overrides)} dry_run={args.dry_run}")

    log_path = write_log_header(cfg)
    print(f"[BOOT] log -> {log_path}")

    pw, context = launch_context(client_slug, headless=args.headless)
    page = context.new_page()
    try:
        ensure_logged_in(page, interactive=args.interactive_login)

        install_template(page, cfg["template_url"], cfg["target_page_name"])

        flow_names: list[str] = cfg.get("flows", [])
        installed = list_installed_flows(page, flow_names)
        print(f"[FLOWS] installed={len(installed)}/{len(flow_names)}")

        total_replacements = 0
        for flow_name in installed:
            n = override_flow_placeholders(page, flow_name, overrides, dry_run=args.dry_run)
            print(f"[OVERRIDE] {flow_name}: {n} replacements")
            total_replacements += n

        tags_renamed = rename_placeholder_tags(page, cfg.get("tag_renames", {}), dry_run=args.dry_run)
        fields_renamed = rename_placeholder_fields(page, cfg.get("field_renames", {}), dry_run=args.dry_run)

        run_post_install_actions(page, cfg.get("post_install_actions", []), dry_run=args.dry_run)

        survivors = verify_no_placeholders(page, installed) if not args.dry_run else []

        # Report
        print("\n=========== ManyChat Installer Report ===========")
        print(f"client_slug:       {client_slug}")
        print(f"flows installed:   {len(installed)} / {len(flow_names)}")
        print(f"placeholders set:  {total_replacements}")
        print(f"tags renamed:      {tags_renamed}")
        print(f"fields renamed:    {fields_renamed}")
        print(f"survivors:         {len(survivors)}")
        if survivors:
            print("FAIL — surviving placeholders:")
            for flow, tok in survivors:
                print(f"  {flow}: {{{{{tok}}}}}")
            return 1
        print("PASS")
        return 0

    except Exception as e:
        screenshot_on_error(page, SKILL_ROOT / "logs" / f"{client_slug}-error.png")
        print(f"[FATAL] {e!r}", file=sys.stderr)
        return 1
    finally:
        try:
            context.close()
        finally:
            pw.stop() if pw else None


if __name__ == "__main__":
    sys.exit(main())
