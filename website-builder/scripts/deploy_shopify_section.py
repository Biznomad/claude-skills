#!/usr/bin/env python3
"""
Push Liquid section files to a Shopify theme via Admin API.

Environment variables:
  SHOPIFY_DOMAIN   — e.g. store.myshopify.com
  SHOPIFY_TOKEN    — Admin API access token
  SHOPIFY_THEME_ID — Target theme ID (use unpublished theme for safety)

Usage:
  python deploy_shopify_section.py sections/trust-banner.liquid sections/faq.liquid
  python deploy_shopify_section.py sections/*.liquid
"""

import os
import sys
import time
import requests
from pathlib import Path

SHOP_DOMAIN = os.environ.get("SHOPIFY_DOMAIN", "")
ACCESS_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")
THEME_ID = os.environ.get("SHOPIFY_THEME_ID", "")
API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2024-01")

BASE_URL = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json",
}


def push_asset(theme_id, asset_key, content):
    """Push a file to a Shopify theme."""
    time.sleep(0.5)
    resp = requests.put(
        f"{BASE_URL}/themes/{theme_id}/assets.json",
        headers=HEADERS,
        json={"asset": {"key": asset_key, "value": content}},
    )
    if resp.status_code in (200, 201):
        print(f"  OK: {asset_key}")
        return True
    else:
        print(f"  FAIL ({resp.status_code}): {asset_key} — {resp.text[:200]}")
        return False


def main():
    if not all([SHOP_DOMAIN, ACCESS_TOKEN, THEME_ID]):
        print("Error: Set SHOPIFY_DOMAIN, SHOPIFY_TOKEN, SHOPIFY_THEME_ID env vars")
        sys.exit(1)

    files = sys.argv[1:]
    if not files:
        print("Usage: deploy_shopify_section.py <file.liquid> [file2.liquid ...]")
        sys.exit(1)

    print(f"Pushing {len(files)} section(s) to theme {THEME_ID} on {SHOP_DOMAIN}...\n")

    success = 0
    for filepath in files:
        path = Path(filepath)
        if not path.exists():
            print(f"  SKIP: {filepath} not found")
            continue
        asset_key = f"sections/{path.name}"
        content = path.read_text()
        if push_asset(THEME_ID, asset_key, content):
            success += 1

    print(f"\n{success}/{len(files)} sections pushed successfully.")


if __name__ == "__main__":
    main()
