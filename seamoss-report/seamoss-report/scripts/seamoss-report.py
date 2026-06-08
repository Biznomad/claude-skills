#!/usr/bin/env python3
"""
Sea Moss Gel Kitchen Report — Holistic Vitalis
Pulls Shopify orders, resolves Mix & Match flavors, outputs kitchen-ready jar counts.

Usage:
  python3 seamoss-report.py                    # last 7 days
  python3 seamoss-report.py 7                  # last 7 days
  python3 seamoss-report.py 2026-04-08 2026-04-15  # specific range
  python3 seamoss-report.py --output /tmp/report.txt  # save to file

Runs on Vitalis VPS (76.13.111.134) where Shopify API token lives.
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

# ── Config ──────────────────────────────────────────────────────────
SHOP = "holisticvitalis.myshopify.com"
TOKEN = "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"
API_VERSION = "2024-01"
BASE = f"https://{SHOP}/admin/api/{API_VERSION}"
HEADERS = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}
TZ = "-04:00"  # EDT

GEL_FLAVORS = {
    "caribbean sunrise": "Caribbean Sunrise",
    "elderberry & soursop": "Elderberry & Soursop",
    "elderberry and soursop": "Elderberry & Soursop",
    "electric dragon": "Electric Dragon",
    "pineapple skies": "Pineapple Skies",
    "st lucia gold": "St Lucia Gold",
    "strawberry banana oasis": "Strawberry Banana Oasis",
}

BUNDLE_FLAVORS = {
    "tropical trio": ["Caribbean Sunrise", "Pineapple Skies", "Strawberry Banana Oasis"],
    "wellness trio": ["Elderberry & Soursop", "St Lucia Gold", "Electric Dragon"],
    "powerhouse": ["Caribbean Sunrise", "Elderberry & Soursop", "Electric Dragon",
                    "Pineapple Skies", "St Lucia Gold", "Strawberry Banana Oasis"],
}

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

# ── Parse args ──────────────────────────────────────────────────────
output_file = None
args = [a for a in sys.argv[1:] if a != "--output"]
for i, a in enumerate(sys.argv[1:]):
    if a == "--output" and i + 2 < len(sys.argv):
        output_file = sys.argv[i + 2]
        args = [x for x in args if x != output_file]

if len(args) == 2 and "-" in args[0]:
    start_date = args[0]
    end_date = args[1]
elif len(args) == 1 and args[0].isdigit():
    days_back = int(args[0])
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back - 1)).strftime("%Y-%m-%d")
else:
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")

start = f"{start_date}T00:00:00{TZ}"
end = f"{end_date}T23:59:59{TZ}"

# ── Fetch orders ────────────────────────────────────────────────────
all_orders = []
url = f"{BASE}/orders.json"
params = {"created_at_min": start, "created_at_max": end, "status": "any", "limit": 250}

while url:
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        print(f"ERROR: Shopify API returned {resp.status_code}: {resp.text[:300]}")
        sys.exit(1)
    data = resp.json()
    all_orders.extend(data.get("orders", []))
    link = resp.headers.get("Link", "")
    url = None
    params = None
    if 'rel="next"' in link:
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split("<")[1].split(">")[0]
                break

# ── Helpers ─────────────────────────────────────────────────────────
def is_gel_product(t):
    exclude = ["gummies", "gummy", "capsule", "soap", "face mask", "raw sea moss",
               "raw full spectrum", "raw purple", "raw royal", "raw st lucia", "mushroom"]
    for ex in exclude:
        if ex in t:
            return False
    return "sea moss gel" in t or "mix & match" in t

def normalize_flavor(raw):
    r = raw.strip().lower()
    for key, val in GEL_FLAVORS.items():
        if key in r:
            return val
    return raw.strip()

def day_label(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return DAYS[d.weekday()]

# ── Count jars ──────────────────────────────────────────────────────
flavor_jars = defaultdict(int)
daily_jars = defaultdict(int)
daily_flavor = defaultdict(lambda: defaultdict(int))
total_jars = 0
gel_order_ids = set()
mm_no_flavor = 0
total_orders = len(all_orders)

for order in all_orders:
    for item in order.get("line_items", []):
        title = (item.get("title", "") or "")
        t = title.lower()
        variant = (item.get("variant_title", "") or "").lower()
        qty = item.get("quantity", 0)
        properties = item.get("properties", []) or []
        day = order.get("created_at", "")[:10]

        # Check named bundles first
        is_bundle = False
        for bkey, bflavors in BUNDLE_FLAVORS.items():
            if bkey in t:
                is_bundle = True
                gel_order_ids.add(order.get("name"))
                for flavor in bflavors:
                    flavor_jars[flavor] += qty
                    daily_flavor[day][flavor] += qty
                    total_jars += qty
                    daily_jars[day] += qty
                break

        if is_bundle:
            continue

        if not is_gel_product(t):
            continue

        gel_order_ids.add(order.get("name"))

        if "mix & match" in t:
            gel_props = [p for p in properties if p.get("name", "").lower().startswith("gel")]
            if gel_props:
                for p in gel_props:
                    flavor = normalize_flavor(p["value"])
                    flavor_jars[flavor] += qty
                    daily_flavor[day][flavor] += qty
                    total_jars += qty
                    daily_jars[day] += qty
            else:
                mm_no_flavor += qty
                jars = 3 * qty
                flavor_jars["UNKNOWN (no flavor data)"] += jars
                total_jars += jars
                daily_jars[day] += jars
        else:
            for key, val in GEL_FLAVORS.items():
                if key in t:
                    if "3-pack" in variant or "3 jars" in variant or "trio" in t:
                        jars = 3 * qty
                    elif "2-pack" in variant:
                        jars = 2 * qty
                    else:
                        jars = 1 * qty
                    flavor_jars[val] += jars
                    daily_flavor[day][val] += jars
                    total_jars += jars
                    daily_jars[day] += jars
                    break

# ── Format report ───────────────────────────────────────────────────
lines = []
W = 65

def p(s=""):
    lines.append(s)

# Parse dates for display
sd = datetime.strptime(start_date, "%Y-%m-%d")
ed = datetime.strptime(end_date, "%Y-%m-%d")
date_range = f"{sd.strftime('%b %d')} - {ed.strftime('%b %d, %Y')}"

p()
p("=" * W)
p("  HOLISTIC VITALIS — SEA MOSS GEL PRODUCTION REPORT")
p(f"  {date_range}")
p(f"  Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
p("=" * W)
p()
p(f"  TOTAL JARS NEEDED:  {total_jars:,}")
p(f"  GEL ORDERS:         {len(gel_order_ids):,} of {total_orders:,} total orders")
if mm_no_flavor:
    p(f"  * {mm_no_flavor * 3} jars from {mm_no_flavor} Mix & Match orders missing flavor data")
p()

# ── Flavor table ────────────────────────────────────────────────────
p("-" * W)
p("  JARS BY FLAVOR")
p("-" * W)

known = sorted(
    [(f, j) for f, j in flavor_jars.items() if "UNKNOWN" not in f],
    key=lambda x: x[1], reverse=True
)
unknown = [(f, j) for f, j in flavor_jars.items() if "UNKNOWN" in f]

for flavor, jars in known:
    pct = (jars / total_jars * 100) if total_jars else 0
    bar = "#" * int(pct / 2)
    p(f"  {flavor:<30} {jars:>5} jars  ({pct:>4.1f}%)  {bar}")
for flavor, jars in unknown:
    p(f"  {flavor:<30} {jars:>5} jars")
p(f"  {'-'*30} {'-----':>5}")
p(f"  {'TOTAL':<30} {total_jars:>5} jars")
p()

# ── Daily totals ────────────────────────────────────────────────────
p("-" * W)
p("  DAILY JAR COUNT")
p("-" * W)
for day in sorted(daily_jars.keys()):
    dl = day_label(day)
    bar = "#" * (daily_jars[day] // 10)
    p(f"  {day} ({dl})  {daily_jars[day]:>5} jars  {bar}")
p(f"  {'TOTAL':>16}  {total_jars:>5} jars")
num_days = len(daily_jars)
if num_days:
    p(f"  {'AVG/DAY':>16}  {total_jars // num_days:>5} jars")
p()

# ── Daily x Flavor grid ────────────────────────────────────────────
p("-" * W)
p("  DAILY BREAKDOWN BY FLAVOR")
p("-" * W)

flavor_names = [f for f, _ in known]
short = [f[:7] for f in flavor_names]

header = f"  {'Date':<14}" + "".join(f"{s:>8}" for s in short) + f"{'TOTAL':>8}"
p(header)
p(f"  {'-'*14}" + ("-" * 8) * len(short) + "-" * 8)

for day in sorted(daily_jars.keys()):
    dl = day_label(day)
    row = f"  {day} ({dl})  "
    dt = 0
    for flavor in flavor_names:
        c = daily_flavor[day].get(flavor, 0)
        dt += c
        row += f"{c:>8}"
    row += f"{dt:>8}"
    p(row)

p(f"  {'-'*14}" + ("-" * 8) * len(short) + "-" * 8)
totals_row = f"  {'TOTAL':<14}"
for flavor in flavor_names:
    totals_row += f"{flavor_jars[flavor]:>8}"
totals_row += f"{total_jars:>8}"
p(totals_row)
p()

# ── Notes ───────────────────────────────────────────────────────────
p("-" * W)
p("  NOTES")
p("-" * W)
p("  - Mix & Match flavors resolved from customer checkout selections")
p("  - Tropical Trio = Caribbean Sunrise + Pineapple Skies + Strawberry Banana")
p("  - Wellness Trio = Elderberry & Soursop + St Lucia Gold + Electric Dragon")
p("  - Powerhouse Bundle = 1 of each flavor (6 jars)")
p("  - If bundle compositions have changed, update BUNDLE_FLAVORS in script")
p()

# ── Output ──────────────────────────────────────────────────────────
report = "\n".join(lines)
print(report)

if output_file:
    with open(output_file, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {output_file}")
