#!/bin/bash
# Daily KPI digest — cron this for 13:00 UTC (8am ET) or your local 8am.
# Reads bot's data files + spend.json, posts summary to TELEGRAM_GROUP.
set -e
source "$(dirname "$0")/../.env"
DATA="${DATA_DIR:-/root/two-and-through-ops/data}"
SPEND="$(dirname "$0")/../spend.json"
LEADS=$(jq 'length' "$DATA/leads.json" 2>/dev/null || echo 0)
JOBS=$(jq 'length' "$DATA/jobs.json" 2>/dev/null || echo 0)
QUOTES=$(jq 'length' "$DATA/quotes.json" 2>/dev/null || echo 0)
INVOICES=$(jq 'length' "$DATA/invoices.json" 2>/dev/null || echo 0)
REV=$(jq '[.[] | (.amount // 0)] | add // 0' "$DATA/invoices.json" 2>/dev/null || echo 0)
TODAY_SPEND=$(jq '.today // 0' "$SPEND" 2>/dev/null || echo 0)
CPL=$(jq -r '.cpl // "—"' "$SPEND" 2>/dev/null || echo "—")
TODAY=$(date -u +%Y-%m-%d)
MSG="📊 *Daily Digest — $TODAY*
Leads: $LEADS  |  Quotes: $QUOTES  |  Jobs: $JOBS  |  Revenue: \$$REV
Ad spend today: \$$TODAY_SPEND  |  CPL: $CPL"
curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
  -d chat_id="$GROUP_ID" -d parse_mode=Markdown --data-urlencode text="$MSG" \
  -o /dev/null
