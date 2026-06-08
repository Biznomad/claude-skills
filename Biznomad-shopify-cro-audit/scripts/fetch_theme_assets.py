#!/usr/bin/env python3
"""
Fetch all liquid/json assets from a live Shopify theme and cache locally.
Uses Shopify Admin API 2024-10.

Configuration (all via env vars — no hardcoded values):
  SHOPIFY_STORE    e.g. mystore.myshopify.com
  SHOPIFY_TOKEN    Admin API token with read_themes scope
  THEME_ID         Numeric theme ID (live theme)
  CACHE_DIR        Override cache root (default: ./.theme-cache/<store-slug>/<theme-id>/<YYYYMMDD-HHMM>/)
  OUTPUT_DIR       Override output root (default: ./audit-output/)

Flags:
  --refresh / --no-cache    Ignore cached files and re-fetch everything
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from pathlib import Path

# --- Config from environment (no hardcoded values) ---
STORE    = os.environ.get("SHOPIFY_STORE", "")
TOKEN    = os.environ.get("SHOPIFY_TOKEN", "")
THEME_ID = os.environ.get("THEME_ID", "")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./audit-output")

if not STORE or not TOKEN or not THEME_ID:
    print("ERROR: SHOPIFY_STORE, SHOPIFY_TOKEN, and THEME_ID must be set as env vars.")
    sys.exit(1)

# Build a collision-safe cache dir: .theme-cache/<store-slug>/<theme-id>/<YYYYMMDD-HHMM>/
_store_slug = STORE.replace(".myshopify.com", "").replace(".", "-")
_datestamp  = datetime.now().strftime("%Y%m%d-%H%M")
_default_cache = os.path.join(".theme-cache", _store_slug, THEME_ID, _datestamp)
CACHE_DIR = os.environ.get("CACHE_DIR", _default_cache)

# --refresh / --no-cache flag
FORCE_REFRESH = "--refresh" in sys.argv or "--no-cache" in sys.argv

API_BASE = f"https://{STORE}/admin/api/2024-10"

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def shopify_get(path):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": TOKEN})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def fetch_asset(key):
    cache_path = os.path.join(CACHE_DIR, key.replace("/", "__"))
    if not FORCE_REFRESH and os.path.exists(cache_path):
        return open(cache_path).read()
    try:
        encoded_key = urllib.parse.quote(key, safe="")
        data = shopify_get(f"/themes/{THEME_ID}/assets.json?asset[key]={encoded_key}")
        asset = data.get("asset", {})
        content = asset.get("value", asset.get("attachment", ""))
        with open(cache_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)
        return content
    except Exception as e:
        print(f"  WARN: could not fetch {key}: {e}")
        return ""


def main():
    refresh_msg = " (--refresh: ignoring cache)" if FORCE_REFRESH else ""
    print(f"Loading asset list from {STORE} theme {THEME_ID}{refresh_msg}...")
    print(f"Cache dir: {CACHE_DIR}")
    data = shopify_get(f"/themes/{THEME_ID}/assets.json")
    keys = [
        a["key"] for a in data["assets"]
        if a["key"].endswith(".liquid") or a["key"].endswith(".json")
    ]
    print(f"Found {len(keys)} liquid/json assets. Fetching...")

    fetched = 0
    skipped = 0
    for i, key in enumerate(keys):
        cache_path = os.path.join(CACHE_DIR, key.replace("/", "__"))
        if not FORCE_REFRESH and os.path.exists(cache_path):
            skipped += 1
            continue
        if i > 0 and i % 10 == 0:
            time.sleep(0.5)  # Rate limit courtesy
        fetch_asset(key)
        fetched += 1
        if fetched % 20 == 0:
            print(f"  Fetched {fetched} new assets ({skipped} cached)...")

    print(f"Done. {fetched} new, {skipped} from cache. Total: {fetched + skipped}")

    # Save manifest
    manifest = {
        "store": STORE,
        "theme_id": THEME_ID,
        "fetched_at": _datestamp,
        "keys": keys,
        "total": len(keys),
        "cache_dir": CACHE_DIR,
    }
    with open(os.path.join(CACHE_DIR, "_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written to {CACHE_DIR}/_manifest.json")
    return keys


if __name__ == "__main__":
    main()
