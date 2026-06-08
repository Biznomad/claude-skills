#!/usr/bin/env python3
"""
Push a JSON template to a Shopify theme and optionally assign products.

Environment variables:
  SHOPIFY_DOMAIN       — e.g. store.myshopify.com
  SHOPIFY_TOKEN        — Admin API access token
  SHOPIFY_THEME_ID     — Target theme ID (staging/unpublished)
  SHOPIFY_LIVE_THEME_ID — Live theme ID (for fallback template)

Usage:
  # Push template to staging theme
  python deploy_shopify_template.py templates/product.custom.json

  # Push + assign products
  python deploy_shopify_template.py templates/product.custom.json --products 123,456,789

  # Push + create fallback on live theme
  python deploy_shopify_template.py templates/product.custom.json --fallback --products 123,456
"""

import argparse
import json
import os
import sys
import time
import requests
from pathlib import Path

SHOP_DOMAIN = os.environ.get("SHOPIFY_DOMAIN", "")
ACCESS_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")
THEME_ID = os.environ.get("SHOPIFY_THEME_ID", "")
LIVE_THEME_ID = os.environ.get("SHOPIFY_LIVE_THEME_ID", "")
API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2024-01")

BASE_URL = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json",
}


def api_get(endpoint):
    time.sleep(0.5)
    return requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)


def api_put(endpoint, payload):
    time.sleep(0.5)
    return requests.put(f"{BASE_URL}{endpoint}", headers=HEADERS, json=payload)


def push_template(theme_id, template_key, content):
    """Push a JSON template to a theme."""
    resp = api_put(
        f"/themes/{theme_id}/assets.json",
        {"asset": {"key": template_key, "value": content}},
    )
    if resp.status_code in (200, 201):
        print(f"  OK: {template_key} on theme {theme_id}")
        return True
    else:
        print(f"  FAIL ({resp.status_code}): {resp.text[:300]}")
        return False


def create_fallback(template_key):
    """Copy live theme's base template as fallback for the custom suffix."""
    if not LIVE_THEME_ID:
        print("  SKIP fallback: SHOPIFY_LIVE_THEME_ID not set")
        return False

    # Derive base template key (e.g. product.custom.json → product.json)
    parts = template_key.split("/")[-1].split(".")
    base_key = f"templates/{parts[0]}.json"

    print(f"  Fetching {base_key} from live theme {LIVE_THEME_ID}...")
    resp = api_get(f"/themes/{LIVE_THEME_ID}/assets.json?asset[key]={base_key}")
    if resp.status_code == 200:
        fallback_content = resp.json()["asset"]["value"]
    else:
        print(f"  WARN: Could not fetch {base_key}, using minimal fallback")
        fallback_content = json.dumps({"sections": {"main": {"type": f"main-{parts[0]}", "settings": {}}}, "order": ["main"]})

    return push_template(LIVE_THEME_ID, template_key, fallback_content)


def assign_products(product_ids, template_suffix):
    """Assign products to the template suffix."""
    success = 0
    for pid in product_ids:
        resp = api_put(
            f"/products/{pid}.json",
            {"product": {"id": int(pid), "template_suffix": template_suffix}},
        )
        if resp.status_code == 200:
            title = resp.json()["product"].get("title", pid)
            print(f"  OK: {title} → template_suffix='{template_suffix}'")
            success += 1
        else:
            print(f"  FAIL ({resp.status_code}): product {pid}")
    return success


def main():
    parser = argparse.ArgumentParser(description="Deploy Shopify JSON template")
    parser.add_argument("template", help="Path to JSON template file")
    parser.add_argument("--products", help="Comma-separated product IDs to assign")
    parser.add_argument("--fallback", action="store_true", help="Create fallback on live theme")
    args = parser.parse_args()

    if not all([SHOP_DOMAIN, ACCESS_TOKEN, THEME_ID]):
        print("Error: Set SHOPIFY_DOMAIN, SHOPIFY_TOKEN, SHOPIFY_THEME_ID env vars")
        sys.exit(1)

    path = Path(args.template)
    if not path.exists():
        print(f"Error: {path} not found")
        sys.exit(1)

    template_key = f"templates/{path.name}"
    content = path.read_text()

    # Extract template suffix from filename (e.g. product.custom.json → custom)
    parts = path.stem.split(".")
    template_suffix = parts[1] if len(parts) > 1 else ""

    print(f"Deploying {template_key} to theme {THEME_ID}...\n")

    # 1. Push to staging theme
    if not push_template(THEME_ID, template_key, content):
        sys.exit(1)

    # 2. Create fallback on live theme if requested
    if args.fallback:
        print(f"\nCreating fallback on live theme {LIVE_THEME_ID}...")
        create_fallback(template_key)

    # 3. Assign products if specified
    if args.products:
        product_ids = [p.strip() for p in args.products.split(",")]
        print(f"\nAssigning {len(product_ids)} products to '{template_suffix}'...")
        assign_products(product_ids, template_suffix)

    print("\nDone.")


if __name__ == "__main__":
    main()
