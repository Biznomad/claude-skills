---
name: seamoss-report
description: Generate weekly sea moss gel production reports for Holistic Vitalis kitchen team. Pulls Shopify orders, resolves Mix & Match flavor selections, and outputs jar counts by flavor with daily breakdown. Use when user says "seamoss report", "gel report", "kitchen report", "jar count", "gel count", "production report", "how many jars", "sea moss orders", or "/seamoss-report".
---

# Sea Moss Gel Production Report

Generate kitchen-team-ready jar count reports from Holistic Vitalis Shopify orders.

## What It Does

1. Pull all orders from Shopify Admin API for the given date range
2. Filter to sea moss gel products only (exclude gummies, capsules, soaps, raw moss, face masks)
3. Resolve Mix & Match orders via `Gel 1`/`Gel 2`/`Gel 3` line item properties
4. Expand named bundles (Tropical Trio, Wellness Trio, Powerhouse) into individual flavor jars
5. Output clean report: total jars, jars by flavor, daily breakdown, daily x flavor grid

## How to Run

The script runs on **Vitalis VPS (76.13.111.134)** where the Shopify API token lives.

```bash
# Copy script to VPS and run
scp ~/.claude/skills/seamoss-report/seamoss-report/scripts/seamoss-report.py root@76.13.111.134:/tmp/seamoss-report.py
ssh root@76.13.111.134 "python3 /tmp/seamoss-report.py"                            # last 7 days
ssh root@76.13.111.134 "python3 /tmp/seamoss-report.py 14"                         # last 14 days
ssh root@76.13.111.134 "python3 /tmp/seamoss-report.py 2026-04-08 2026-04-15"      # specific range
ssh root@76.13.111.134 "python3 /tmp/seamoss-report.py --output /tmp/report.txt"   # save to file
```

## Workflow

When user requests a report:

1. Copy `scripts/seamoss-report.py` to VPS via scp
2. Determine date range — default last 7 days, or parse user request ("this week", "last 2 weeks", specific dates)
3. Run script on VPS via ssh
4. Display report output to user
5. Optionally save to file if requested

## Bundle Compositions

Update `BUNDLE_FLAVORS` in script if store changes bundle contents:

| Bundle | Flavors |
|--------|---------|
| Tropical Trio | Caribbean Sunrise, Pineapple Skies, Strawberry Banana Oasis |
| Wellness Trio | Elderberry & Soursop, St Lucia Gold, Electric Dragon |
| Powerhouse | All 6 flavors (1 jar each) |

## Store

- **Shop:** holisticvitalis.myshopify.com
- **API token:** Hardcoded in script (sourced from VPS `/root/Holistic-Vitalis/hv-cro-monitor/.env`)
- **Gel flavors:** Caribbean Sunrise, Elderberry & Soursop, Electric Dragon, Pineapple Skies, St Lucia Gold, Strawberry Banana Oasis
