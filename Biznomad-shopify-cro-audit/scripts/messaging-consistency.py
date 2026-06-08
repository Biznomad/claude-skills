#!/usr/bin/env python3
"""
Messaging Consistency Scan — reusable across any Biznomad client Shopify store.

Scans live theme assets + Shopify pages + product descriptions for:
- Banned phrases (FTC/health claims, brand violations, client-specific rules)
- Missing required brand vocabulary
- Inconsistent review-count / social-proof numbers

Configuration (all via env vars — no hardcoded values):
  SHOPIFY_STORE           e.g. mystore.myshopify.com
  SHOPIFY_TOKEN           Admin API token (read_products + read_themes + read_content)
  THEME_ID                Numeric theme ID (live theme)
  OUTPUT_DIR              Where to write messaging.md (default: ./audit-output/)
  CACHE_DIR               Theme snapshot dir produced by fetch_theme_assets.py
  LOCAL_THEME_DIR         Optional local theme checkout for comparison (can be empty)
  COMPLIANCE_PROFILE      Path to client compliance-profile.json (see SKILL.md for schema)
  STRICT_MODE             Set to "1" to disable all allowlists (full FTC scan)

CLI flags:
  --strict    Equivalent to STRICT_MODE=1

Data files (produced by a prior API fetch, stored in OUTPUT_DIR or CWD):
  pages_full.json         Shopify pages dump  {"pages":[...]}
  products_full.json      Shopify products dump {"products":[...]}
"""
import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# --- Config from environment ---
STORE      = os.environ.get("SHOPIFY_STORE", "")
TOKEN      = os.environ.get("SHOPIFY_TOKEN", "")
THEME_ID   = os.environ.get("THEME_ID", "")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./audit-output")
LOCAL_THEME = os.environ.get("LOCAL_THEME_DIR", "")
COMPLIANCE_PROFILE = os.environ.get("COMPLIANCE_PROFILE", "")
STRICT_MODE = os.environ.get("STRICT_MODE", "0") == "1" or "--strict" in sys.argv

if not STORE or not THEME_ID:
    print("ERROR: SHOPIFY_STORE and THEME_ID must be set as env vars.")
    sys.exit(1)

_store_slug   = STORE.replace(".myshopify.com", "").replace(".", "-")
_default_cache = os.path.join(".theme-cache", _store_slug, THEME_ID)
CACHE_DIR = os.environ.get("CACHE_DIR", _default_cache)

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "messaging.md")

CONTEXT_CHARS = 40

# Helper to locate data files
def _data_path(name):
    for d in [OUTPUT_DIR, "."]:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None

PAGES_FILE    = _data_path("pages_full.json")
PRODUCTS_FILE = _data_path("products_full.json")


# ---------------------------------------------------------------------------
# FALSE-POSITIVE SUPPRESSION
# ---------------------------------------------------------------------------
# Matches in the same paragraph/element are suppressed when these context
# patterns are present. Disables when STRICT_MODE=True (--strict flag).
# Source: FTC/FDA boilerplate phrases that legitimately contain banned words.
DISCLAIMER_CONTEXT_PATTERNS = [
    re.compile(r"not\s+intended\s+to\s+(?:diagnose|treat|cure|prevent)", re.IGNORECASE),
    re.compile(r"these\s+statements\s+have\s+not\s+been\s+evaluated", re.IGNORECASE),
    re.compile(r"food\s+and\s+drug\s+administration", re.IGNORECASE),
    re.compile(r"FDA\s+(?:has\s+not|disclaimer)", re.IGNORECASE),
    re.compile(r"not\s+been\s+evaluated\s+by\s+the\s+(?:FDA|Food)", re.IGNORECASE),
]

# CSS property values that can contain words like "stroke", "fill", "transform"
# triggering false positives in theme Liquid/JSON files.
CSS_PROPERTY_BLOCKLIST = re.compile(
    r"""(?:stroke|fill|transform|translate|rotate|scale)\s*:\s*[^;'"]+""",
    re.IGNORECASE
)


def is_false_positive(line, matched_text):
    """
    Return True if this match should be suppressed as a false positive.
    Suppression is disabled when STRICT_MODE is enabled.
    """
    if STRICT_MODE:
        return False
    # Suppress CSS property hits
    if CSS_PROPERTY_BLOCKLIST.search(line):
        return True
    # Suppress FDA disclaimer context
    for pat in DISCLAIMER_CONTEXT_PATTERNS:
        if pat.search(line):
            return True
    return False


# ---------------------------------------------------------------------------
# BANNED PHRASES & REQUIRED VOCAB
# ---------------------------------------------------------------------------
# Load from compliance-profile.json if provided, otherwise use defaults.
# Non-supplement clients: supply their own compliance-profile.json with
# industry-appropriate rules (e.g., apparel, healthcare, legal).
# See SKILL.md for the compliance-profile.json schema.

if COMPLIANCE_PROFILE and os.path.exists(COMPLIANCE_PROFILE):
    with open(COMPLIANCE_PROFILE) as _f:
        _profile = json.load(_f)
    BANNED_PHRASES  = _profile.get("banned_phrases_compiled", _profile.get("banned_phrases", {}))
    REQUIRED_VOCAB  = _profile.get("required_vocab", {})
    # Profile-level allowlist overrides
    if not _profile.get("allowlists", {}).get("fda_disclaimer", True):
        DISCLAIMER_CONTEXT_PATTERNS.clear()
    if not _profile.get("allowlists", {}).get("css_properties", True):
        # Rebuild CSS blocklist as a pattern that matches nothing
        CSS_PROPERTY_BLOCKLIST = re.compile(r"(?!)")
    print(f"Loaded compliance profile: {COMPLIANCE_PROFILE}")
else:
    # --- DEFAULT: supplement/health brand rules ---
    # For non-supplement clients, create a compliance-profile.json with their
    # own banned_phrases and set COMPLIANCE_PROFILE env var.
    BANNED_PHRASES = {
        "boosts immunity": {
            "regex": r"boost(?:s|ing|ed)?\s+immunit(?:y|ies)",
            "tier": "CRITICAL",
            "why": "FTC/FDA health claim — implies disease prevention without approval",
            "fix": 'Replace with "supports immune function" or "supports healthy immune response"'
        },
        "boosts energy": {
            "regex": r"boost(?:s|ing|ed)?\s+energy",
            "tier": "CRITICAL",
            "why": "Vague benefit claim — can trigger ad policy flags",
            "fix": 'Replace with "Stress & Energy Support" or "supports healthy energy levels"'
        },
        "boosts health": {
            "regex": r"boost(?:s|ing|ed)?\s+health",
            "tier": "CRITICAL",
            "why": "Unsubstantiated structure/function claim",
            "fix": 'Replace with "supports overall wellness" or remove'
        },
        "boosts": {
            "regex": r"boost(?:s|ing|ed)?\s+(?:your\s+)?(?:body|wellness|performance|metabolism|digestion|libido|mood)",
            "tier": "HIGH",
            "why": "General 'boosts' claims trigger ad policy reviews",
            "fix": 'Replace with "supports [function]"'
        },
        "cure": {
            "regex": r"\bcure(?:s|d|ing)?\b",
            "tier": "CRITICAL",
            "why": "Disease claim — illegal without FDA approval",
            "fix": "Remove or rephrase entirely — no cure claims permitted"
        },
        "treat": {
            "regex": r"\btreat(?:s|ed|ment|ing)?\s+(?:disease|condition|disorder|diabetes|cancer|arthritis|inflammation|pain|anxiety|depression)",
            "tier": "CRITICAL",
            "why": "Disease treatment claim — illegal without FDA approval",
            "fix": "Remove disease-specific treatment language"
        },
        "heal": {
            "regex": r"\bheal(?:s|ed|ing)?\s+(?:disease|condition|the body|diabetes|cancer|gut|leaky|wound)",
            "tier": "CRITICAL",
            "why": "Disease healing claim — illegal without FDA approval",
            "fix": "Remove disease-specific healing language"
        },
        "doctor-recommended": {
            "regex": r"doctor[\s\-]?recommended",
            "tier": "HIGH",
            "why": "Requires substantiation — can't use without documented physician endorsement",
            "fix": "Remove unless specific documented recommendation is on file"
        },
        "clinically proven": {
            "regex": r"clinically\s+(?:proven|tested|studied|validated)",
            "tier": "HIGH",
            "why": "Requires peer-reviewed clinical trial substantiation for this product",
            "fix": "Remove or replace with 'traditionally used' / 'research-backed' with citation"
        },
        "92 minerals": {
            "regex": r"92\s+minerals",
            "tier": "MEDIUM",
            "why": "Superseded by brand standard '90+ minerals' — outdated specific claim",
            "fix": 'Replace with "90+ minerals" per current brand guidelines'
        },
        "102 minerals": {
            "regex": r"102\s+minerals",
            "tier": "MEDIUM",
            "why": "Superseded by brand standard '90+ minerals' — inflated unsupported claim",
            "fix": 'Replace with "90+ minerals" per current brand guidelines'
        },
        "92 of 102": {
            "regex": r"92\s+of\s+102",
            "tier": "MEDIUM",
            "why": "Superseded by '90+ minerals' — specific numbers need scientific citation",
            "fix": 'Replace with "90+ minerals"'
        },
        "prevent": {
            "regex": r"\bprevent(?:s|ed|ing|ion)?\s+(?:disease|cancer|diabetes|illness|infection|covid|flu|cold)",
            "tier": "CRITICAL",
            "why": "Disease prevention claim — illegal without FDA approval",
            "fix": "Remove disease-specific prevention language"
        },
        "diagnose": {
            "regex": r"\bdiagnose(?:s|d|ing)?\b",
            "tier": "CRITICAL",
            "why": "Medical diagnostic claim — requires FDA approval",
            "fix": "Remove entirely"
        },
        "reverse": {
            "regex": r"\breverse(?:s|d|ing)?\s+(?:diabetes|aging|disease|condition|inflammation|cancer)",
            "tier": "CRITICAL",
            "why": "Disease reversal claim — illegal without FDA approval",
            "fix": "Remove disease-specific reversal language"
        },
    }

    REQUIRED_VOCAB = {
        "90+ minerals": {
            "regex": r"90\+\s*minerals",
            "tier": "BRAND-REQUIRED",
            "note": "Preferred mineral claim per brand guidelines"
        },
        "nutrient-dense": {
            "regex": r"nutrient[\-\s]?dense",
            "tier": "BRAND-REQUIRED",
            "note": "Core brand descriptor"
        },
        "Stress & Energy Support": {
            "regex": r"stress\s*&?\s*energy\s+support",
            "tier": "BRAND-REQUIRED",
            "note": "Approved structure/function claim for energy"
        },
        "supports healthy": {
            "regex": r"supports?\s+healthy\s+\w+",
            "tier": "BRAND-PREFERRED",
            "note": "FDA-safe structure/function claim format"
        },
    }

# Review count / social proof patterns
REVIEW_PATTERNS = {
    "review_count": re.compile(
        r"(?:(\d[\d,]*)\s*\+?\s*(?:reviews?|ratings?|customers?|orders?|purchasers?|buyers?|people|subscribers?))",
        re.IGNORECASE
    ),
    "star_rating": re.compile(
        r"(\d\.\d)\s*(?:out\s+of\s+5|\/5|stars?)",
        re.IGNORECASE
    ),
    "large_number": re.compile(
        r"([\d,]+\+?)\s+(?:happy\s+)?customers?",
        re.IGNORECASE
    ),
}

# Storage
banned_findings = defaultdict(list)
vocab_found     = defaultdict(list)
review_findings = []


def get_context(text, match):
    start = max(0, match.start() - CONTEXT_CHARS)
    end = min(len(text), match.end() + CONTEXT_CHARS)
    snippet = text[start:end].replace("\n", " ").replace("\r", "")
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet.strip()


def scan_text(text, source_label, source_url=None):
    lines = text.splitlines()

    # Scan banned phrases
    for phrase_key, cfg in BANNED_PHRASES.items():
        pattern = re.compile(cfg["regex"], re.IGNORECASE)
        for lineno, line in enumerate(lines, 1):
            for m in pattern.finditer(line):
                # False-positive suppression
                if is_false_positive(line, m.group(0)):
                    continue
                ctx = get_context(line, m)
                banned_findings[phrase_key].append({
                    "source": source_label,
                    "url": source_url,
                    "line": lineno,
                    "context": ctx,
                    "tier": cfg["tier"],
                    "why": cfg["why"],
                    "fix": cfg["fix"],
                    "matched": m.group(0),
                })

    # Scan required vocab
    for vocab_key, cfg in REQUIRED_VOCAB.items():
        pattern = re.compile(cfg["regex"], re.IGNORECASE)
        for lineno, line in enumerate(lines, 1):
            for m in pattern.finditer(line):
                ctx = get_context(line, m)
                vocab_found[vocab_key].append({
                    "source": source_label,
                    "url": source_url,
                    "line": lineno,
                    "context": ctx,
                })

    # Scan review counts
    for pat_key, pattern in REVIEW_PATTERNS.items():
        for m in pattern.finditer(text):
            lineno = text[:m.start()].count("\n") + 1
            ctx = get_context(text, m)
            review_findings.append({
                "type": pat_key,
                "source": source_label,
                "url": source_url,
                "line": lineno,
                "context": ctx,
                "matched": m.group(0),
                "value": m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0),
            })


def scan_theme_cache():
    print(f"Scanning live theme cache under {CACHE_DIR}...")
    cache_root = Path(CACHE_DIR)
    if not cache_root.exists():
        print(f"  WARN: cache dir not found: {CACHE_DIR}")
        return
    candidates = sorted(cache_root.rglob("_manifest.json"))
    cache_path = candidates[-1].parent if candidates else cache_root
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
    if not LOCAL_THEME:
        return
    print(f"Scanning local theme (stale reference): {LOCAL_THEME}")
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


def analyze_review_inconsistencies():
    """Find conflicting review counts and star ratings."""
    numbers_by_type = defaultdict(set)
    for r in review_findings:
        val = r["value"].replace(",", "").replace("+", "").strip()
        if val.isdigit():
            numbers_by_type[r["type"]].add(int(val))

    issues = []
    if len(numbers_by_type.get("review_count", set())) > 1:
        issues.append(("Multiple review counts found", sorted(numbers_by_type["review_count"])))
    if len(numbers_by_type.get("star_rating", set())) > 1:
        stars = set()
        for r in review_findings:
            if r["type"] == "star_rating":
                try:
                    stars.add(float(r["value"]))
                except Exception:
                    pass
        if len(stars) > 1:
            issues.append(("Multiple star ratings found", sorted(stars)))
    if len(numbers_by_type.get("large_number", set())) > 1:
        issues.append(("Multiple customer counts found", sorted(numbers_by_type["large_number"])))
    return issues


def write_report():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    strict_note = " [STRICT MODE — allowlists disabled]" if STRICT_MODE else ""
    lines = []
    lines.append(f"# Messaging Consistency Audit — {STORE}{strict_note}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  **Theme ID:** {THEME_ID} (live)")
    lines.append("")
    if not STRICT_MODE:
        lines.append("> **Note:** FDA disclaimer boilerplate and CSS property hits are automatically")
        lines.append("> suppressed as false positives. Run with `--strict` to see all raw matches.")
        lines.append("")
    lines.append("---")
    lines.append("")

    total_banned = 0
    banned_by_phrase = {}

    def _render_tier(tier_name, tier_key, section_title):
        nonlocal total_banned
        found = False
        section_lines = []
        section_lines.append(f"## {section_title}")
        section_lines.append("")
        for phrase_key, cfg in BANNED_PHRASES.items():
            if cfg["tier"] != tier_key:
                continue
            hits = banned_findings[phrase_key]
            if not hits:
                continue
            found = True
            seen = set()
            unique_hits = []
            for h in hits:
                key = (h["source"], h["context"])
                if key not in seen:
                    seen.add(key)
                    unique_hits.append(h)
            banned_by_phrase[phrase_key] = len(unique_hits)
            total_banned += len(unique_hits)
            section_lines.append(f"### `{phrase_key}` — {len(unique_hits)} occurrence(s)")
            section_lines.append(f"**Why:** {cfg['why']}")
            section_lines.append(f"**Fix:** {cfg['fix']}")
            section_lines.append("")
            for h in unique_hits:
                section_lines.append(f"- **`{h['source']}`** line {h['line']} | matched: `{h['matched']}`")
                section_lines.append(f"  > `{h['context']}`")
                if h["url"]:
                    section_lines.append(f"  > URL: {h['url']}")
                section_lines.append("")
        if not found:
            section_lines.append(f"_No {tier_name.lower()} violations found._")
            section_lines.append("")
        section_lines.append("---")
        section_lines.append("")
        return section_lines

    lines.extend(_render_tier("CRITICAL", "CRITICAL", "TIER 1 — CRITICAL Violations (FDA/FTC compliance risk)"))
    lines.extend(_render_tier("HIGH", "HIGH", "TIER 2 — HIGH Risk Phrases (ad policy / brand risk)"))
    lines.extend(_render_tier("MEDIUM", "MEDIUM", "TIER 3 — MEDIUM Risk Phrases (outdated/unsupported claims)"))

    # Required vocabulary
    lines.append("## TIER 4 — Required Brand Vocabulary Check")
    lines.append("")
    lines.append("| Term | Found | Occurrences |")
    lines.append("|------|-------|-------------|")
    for vocab_key, cfg in REQUIRED_VOCAB.items():
        count = len(vocab_found[vocab_key])
        status = "YES" if count > 0 else "MISSING"
        lines.append(f"| `{vocab_key}` | {status} | {count} |")
    lines.append("")
    for vocab_key, cfg in REQUIRED_VOCAB.items():
        hits = vocab_found[vocab_key]
        if not hits:
            lines.append(f"- **MISSING:** `{vocab_key}` — {cfg['note']}")
            lines.append(f"  > Add this phrase to product pages, headers, or key sections")
        else:
            lines.append(f"- **FOUND:** `{vocab_key}` ({len(hits)} occurrences) — {cfg['note']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Review inconsistencies
    lines.append("## TIER 5 — Review Count / Social Proof Inconsistencies")
    lines.append("")
    review_issues = analyze_review_inconsistencies()
    if review_issues:
        for issue_label, values in review_issues:
            lines.append(f"### WARNING: {issue_label}")
            lines.append(f"Values found: {values}")
            lines.append("")
    else:
        lines.append("_No review count inconsistencies detected._")
        lines.append("")

    lines.append("### All Review/Count Mentions Found")
    lines.append("")
    seen_review = set()
    for r in review_findings:
        key = (r["source"], r["matched"])
        if key in seen_review:
            continue
        seen_review.add(key)
        lines.append(f"- **`{r['source']}`** line {r['line']} | `{r['matched']}`")
        lines.append(f"  > `{r['context']}`")
        lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## Banned Term Count by Phrase")
    lines.append("")
    lines.append("| Phrase | Count | Tier |")
    lines.append("|--------|-------|------|")
    for phrase_key, cfg in BANNED_PHRASES.items():
        count = banned_by_phrase.get(phrase_key, 0)
        lines.append(f"| `{phrase_key}` | {count} | {cfg['tier']} |")
    lines.append("")
    lines.append(f"**Total banned-phrase violations (unique, after false-positive suppression):** {total_banned}")
    lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nReport written to: {OUTPUT_FILE}")
    print(f"Total banned-phrase violations: {total_banned}")
    print("Banned by phrase:")
    for k, v in banned_by_phrase.items():
        print(f"  {k}: {v}")
    return total_banned, banned_by_phrase, review_issues


if __name__ == "__main__":
    scan_theme_cache()
    scan_local_theme()
    scan_pages()
    scan_products()
    write_report()
