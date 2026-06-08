#!/usr/bin/env python3
"""
Pricing Consistency Scan — reusable across any Biznomad client Shopify store.

Scans live theme assets + Shopify pages + product descriptions for pricing
mentions and flags conflicts against the canonical model supplied via env.

Configuration (all via env vars — no hardcoded values):
  SHOPIFY_STORE          e.g. mystore.myshopify.com
  SHOPIFY_TOKEN          Admin API token (read_products + read_themes + read_content)
  THEME_ID               Numeric theme ID (live theme)
  OUTPUT_DIR             Where to write pricing.md (default: ./audit-output/)
  CACHE_DIR              Theme snapshot dir produced by fetch_theme_assets.py
  LOCAL_THEME_DIR        Optional local theme checkout for comparison (can be empty)
  CANONICAL_PRICING_JSON Optional path to a JSON file with price_patterns key
                         (overrides the PRICE_PATTERNS dict below)

Data files (produced by a prior API fetch, stored in OUTPUT_DIR or CWD):
  pages_full.json        Shopify pages dump  {"pages":[...]}
  products_full.json     Shopify products dump {"products":[...]}

Usage:
  SHOPIFY_STORE=mystore.myshopify.com SHOPIFY_TOKEN=... THEME_ID=123 python3 pricing-consistency.py
"""
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# --- Config from environment ---
STORE     = os.environ.get("SHOPIFY_STORE", "")
TOKEN     = os.environ.get("SHOPIFY_TOKEN", "")
THEME_ID  = os.environ.get("THEME_ID", "")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./audit-output")
LOCAL_THEME = os.environ.get("LOCAL_THEME_DIR", "")

if not STORE or not THEME_ID:
    print("ERROR: SHOPIFY_STORE and THEME_ID must be set as env vars.")
    sys.exit(1)

# Build cache dir default matching fetch_theme_assets.py convention
_store_slug = STORE.replace(".myshopify.com", "").replace(".", "-")
_datestamp  = datetime.now().strftime("%Y%m%d")
_default_cache = os.path.join(".theme-cache", _store_slug, THEME_ID)
CACHE_DIR = os.environ.get("CACHE_DIR", _default_cache)

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "pricing.md")

# Data files (look in OUTPUT_DIR first, then CWD)
def _data_path(name):
    for d in [OUTPUT_DIR, "."]:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None

PAGES_FILE    = _data_path("pages_full.json")
PRODUCTS_FILE = _data_path("products_full.json")

# --- Pricing patterns ---
# Override by pointing CANONICAL_PRICING_JSON at a JSON file with {"price_patterns": {...}}
# Schema: { "<label>": { "regex": "...", "tier": "EXPECTED|SUSPICIOUS", "note": "..." } }
CANONICAL_PRICING_JSON = os.environ.get("CANONICAL_PRICING_JSON", "")
if CANONICAL_PRICING_JSON and os.path.exists(CANONICAL_PRICING_JSON):
    with open(CANONICAL_PRICING_JSON) as f:
        _cp = json.load(f)
    PRICE_PATTERNS = _cp["price_patterns"]
    CANONICAL_SUMMARY = _cp.get("canonical_summary", [])
else:
    # Default patterns — REPLACE per client via CANONICAL_PRICING_JSON env var
    # These are illustrative; update for the specific store being audited.
    PRICE_PATTERNS = {
        # Example: add client-specific prices here or load via CANONICAL_PRICING_JSON
    }
    CANONICAL_SUMMARY = []
    if not PRICE_PATTERNS:
        print("WARN: No price patterns configured. Set CANONICAL_PRICING_JSON env var")
        print("      pointing to a JSON file with {\"price_patterns\": {...}}")
        print("      See SKILL.md for the compliance-profile.json schema.")

# Context window for matches (characters either side)
CONTEXT_CHARS = 40

findings = {label: [] for label in PRICE_PATTERNS}


def get_context(text, match):
    """Return ~80-char context around a regex match."""
    start = max(0, match.start() - CONTEXT_CHARS)
    end = min(len(text), match.end() + CONTEXT_CHARS)
    snippet = text[start:end].replace("\n", " ").replace("\r", "")
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet.strip()


def scan_text(text, source_label, source_url=None):
    """Scan text for all price patterns. Record findings."""
    lines = text.splitlines()
    for label, cfg in PRICE_PATTERNS.items():
        pattern = re.compile(cfg["regex"], re.IGNORECASE)
        for lineno, line in enumerate(lines, 1):
            for m in pattern.finditer(line):
                ctx = get_context(line, m)
                findings[label].append({
                    "source": source_label,
                    "url": source_url,
                    "line": lineno,
                    "context": ctx,
                    "tier": cfg["tier"],
                    "note": cfg["note"],
                })


def scan_theme_cache():
    """Scan all cached live theme assets (most-recent run folder)."""
    print(f"Scanning live theme cache under {CACHE_DIR}...")
    cache_root = Path(CACHE_DIR)
    if not cache_root.exists():
        print(f"  WARN: cache dir not found: {CACHE_DIR}")
        return
    # Support both flat cache dir and dated sub-dirs from fetch_theme_assets.py
    candidates = sorted(cache_root.rglob("_manifest.json"))
    if candidates:
        cache_path = candidates[-1].parent  # Most recent dated folder
    else:
        cache_path = cache_root
    files = [f for f in cache_path.glob("*") if not f.name.startswith("_")]
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        original_key = fp.name.replace("__", "/")
        source_label = f"live-theme/{original_key}"
        source_url = f"https://{STORE}/admin/api/2024-10/themes/{THEME_ID}/assets.json?asset[key]={original_key}"
        scan_text(text, source_label, source_url)
    print(f"  Scanned {len(files)} theme cache files from {cache_path}")


def scan_local_theme():
    """Scan local theme directory for comparison (may be stale)."""
    if not LOCAL_THEME:
        return
    print(f"Scanning local theme (may be stale): {LOCAL_THEME}")
    theme_path = Path(LOCAL_THEME)
    if not theme_path.exists():
        print(f"  WARN: local theme not found: {LOCAL_THEME}")
        return
    count = 0
    for ext in [".liquid", ".json"]:
        for fp in theme_path.rglob(f"*{ext}"):
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            rel = str(fp.relative_to(theme_path))
            scan_text(text, f"local-theme/{rel}", None)
            count += 1
    print(f"  Scanned {count} local theme files")


def scan_pages():
    """Scan Shopify page body_html."""
    if not PAGES_FILE:
        print("  WARN: pages_full.json not found — skipping pages scan")
        return
    print(f"Scanning Shopify pages from {PAGES_FILE}...")
    with open(PAGES_FILE) as f:
        data = json.load(f)
    for page in data.get("pages", []):
        html = page.get("body_html") or ""
        if not html:
            continue
        source_label = f"page/{page['handle']}"
        source_url = f"https://{STORE}/admin/api/2024-10/pages/{page['id']}.json"
        scan_text(html, source_label, source_url)
    print(f"  Scanned {len(data.get('pages', []))} pages")


def scan_products():
    """Scan Shopify product body_html (descriptions)."""
    if not PRODUCTS_FILE:
        print("  WARN: products_full.json not found — skipping products scan")
        return
    print(f"Scanning Shopify products from {PRODUCTS_FILE}...")
    with open(PRODUCTS_FILE) as f:
        data = json.load(f)
    for prod in data.get("products", []):
        html = prod.get("body_html") or ""
        if not html:
            continue
        source_label = f"product/{prod['handle']}"
        source_url = f"https://{STORE}/admin/api/2024-10/products/{prod['id']}.json"
        scan_text(html, source_label, source_url)
    print(f"  Scanned {len(data.get('products', []))} products")


def write_report():
    """Write the markdown report."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    lines = []
    lines.append(f"# Pricing Consistency Audit — {STORE}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  **Theme ID:** {THEME_ID} (live)")
    lines.append("")

    if CANONICAL_SUMMARY:
        lines.append("## Canonical Pricing Model")
        lines.append("| Item | Price | Status |")
        lines.append("|------|-------|--------|")
        for row in CANONICAL_SUMMARY:
            lines.append(f"| {row.get('item','')} | {row.get('price', row.get('value', row.get('id','')))} | {row.get('status','')} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    expected_total = 0
    suspicious_total = 0

    lines.append("## TIER 1 — SUSPICIOUS Prices (need correction)")
    lines.append("")
    suspicious_labels = [l for l, cfg in PRICE_PATTERNS.items() if cfg["tier"] == "SUSPICIOUS"]
    for label in suspicious_labels:
        hits = findings[label]
        if not hits:
            continue
        lines.append(f"### `{label}` — {PRICE_PATTERNS[label]['note']} ({len(hits)} occurrences)")
        lines.append("")
        seen = set()
        for h in hits:
            key = (h["source"], h["context"])
            if key in seen:
                continue
            seen.add(key)
            suspicious_total += 1
            lines.append(f"- **`{h['source']}`** line {h['line']}")
            lines.append(f"  > `{h['context']}`")
            if h["url"]:
                lines.append(f"  > URL: {h['url']}")
            lines.append(f"  > **Fix:** Replace with canonical price. {PRICE_PATTERNS[label]['note']}")
            lines.append("")

    if suspicious_total == 0:
        lines.append("_No suspicious prices found._")
        lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## TIER 2 — EXPECTED Prices (informational, verify placement)")
    lines.append("")
    expected_labels = [l for l, cfg in PRICE_PATTERNS.items() if cfg["tier"] == "EXPECTED"]
    for label in expected_labels:
        hits = findings[label]
        if not hits:
            lines.append(f"### `{label}` — {PRICE_PATTERNS[label]['note']} — **0 occurrences (MISSING?)**")
            lines.append("")
            lines.append(f"  > WARN: '{label}' not found anywhere. Verify it appears on product/bundle pages.")
            lines.append("")
            continue
        lines.append(f"### `{label}` — {PRICE_PATTERNS[label]['note']} ({len(hits)} occurrences)")
        lines.append("")
        seen = set()
        for h in hits:
            key = (h["source"], h["context"])
            if key in seen:
                continue
            seen.add(key)
            expected_total += 1
            lines.append(f"- **`{h['source']}`** line {h['line']}")
            lines.append(f"  > `{h['context']}`")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- SUSPICIOUS price occurrences (unique): **{suspicious_total}**")
    lines.append(f"- EXPECTED price occurrences (unique): **{expected_total}**")
    lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nReport written to: {OUTPUT_FILE}")
    print(f"SUSPICIOUS: {suspicious_total} | EXPECTED: {expected_total}")
    return suspicious_total, expected_total


if __name__ == "__main__":
    scan_theme_cache()
    scan_local_theme()
    scan_pages()
    scan_products()
    write_report()
