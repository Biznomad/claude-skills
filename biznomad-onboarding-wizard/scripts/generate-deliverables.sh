#!/bin/bash
# biznomad-onboarding-wizard / generate-deliverables.sh
# v2 (post-codex): all templating via render.py — no sed substitution,
# no heredoc-embedded-python.
#
# Renders the 3 (or 4 if beta) markdown deliverables onto the client's VPS
# from templates with their actual data substituted in.
#
# Usage:
#   bash generate-deliverables.sh <slug> [--beta]
#
# Reads:  ~/.claude/skills/biznomad-client-ai-team/clients/{slug}.json
# Writes: /root/.hermes/shared/{slug}/{YOUR-AI-TEAM,SAMPLE-WEEK,RUNBOOK,BETA-AGREEMENT}.md
#
# Requires: jq, python3, ssh access to client VPS

set -euo pipefail

SLUG="${1:-}"
BETA=false
[[ "${2:-}" == "--beta" ]] && BETA=true

if [[ -z "$SLUG" ]]; then
  echo "Usage: $0 <slug> [--beta]"; exit 1
fi

# ── slug validator (codex hi#4) ──
if ! [[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]{0,30}$ ]]; then
  echo "❌ Invalid slug '$SLUG'"; exit 1
fi

CLIENT_TEAM_SKILL="$HOME/.claude/skills/biznomad-client-ai-team"
WIZARD_SKILL="$HOME/.claude/skills/biznomad-onboarding-wizard"
CONFIG="$CLIENT_TEAM_SKILL/clients/$SLUG.json"
TEMPLATES="$WIZARD_SKILL/templates"
RENDER="$CLIENT_TEAM_SKILL/scripts/render.py"

[[ ! -f "$CONFIG" ]] && { echo "❌ client config missing: $CONFIG"; exit 1; }
[[ ! -f "$RENDER" ]] && { echo "❌ render.py missing at $RENDER"; exit 1; }
command -v jq >/dev/null || { echo "❌ jq required"; exit 1; }
command -v python3 >/dev/null || { echo "❌ python3 required"; exit 1; }

# Portable ISO timestamp
iso_now() { date +"%Y-%m-%dT%H:%M:%S%z"; }

# ── Build the rendering context (single JSON, augmented for the templates) ──
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Tier → bot count + roles + agent count phrasing
TIER=$(jq -r .tier "$CONFIG")
case "$TIER" in
  solo)        BOT_COUNT=2; ROLES="ops marketing"; AGENT_PHRASE="183 specialist consultants" ;;
  standard)    BOT_COUNT=3; ROLES="ops social intel"; AGENT_PHRASE="183 specialist consultants" ;;
  full)        BOT_COUNT=4; ROLES="ops social marketing intel"; AGENT_PHRASE="183 specialist consultants" ;;
  enterprise)  BOT_COUNT=4; ROLES="ops social marketing intel"; AGENT_PHRASE="183 specialist consultants plus your niche-specific bench" ;;
  *) echo "❌ Unknown tier: $TIER"; exit 1 ;;
esac

# Resolve actual bot usernames — prefer config.telegram_bot_usernames[role], else default pattern
get_un() {
  local role="$1"
  local actual=$(jq -r --arg r "$role" '.telegram_bot_usernames[$r] // empty' "$CONFIG")
  if [[ -n "$actual" && "$actual" != "null" ]]; then
    echo "${actual#@}"
  else
    local title=""
    case "$role" in
      ops)        title="Ops" ;;
      social)     title="Social" ;;
      marketing)  title="Marketing" ;;
      intel)      title="Intel" ;;
    esac
    local init=$(jq -r .client_init "$CONFIG")
    echo "${init}_${title}_Bot"
  fi
}

UN_OPS=$(get_un ops)
UN_SOCIAL=$(get_un social)
UN_MARKETING=$(get_un marketing)
UN_INTEL=$(get_un intel)

# SSH target detection
SSH_TARGET=$(jq -r '.vps.ssh_target // empty' "$CONFIG")
[[ -z "$SSH_TARGET" || "$SSH_TARGET" == "null" ]] && SSH_TARGET=$(jq -r --arg s "$SLUG" '.vps.ssh_alias // $s' "$CONFIG")
[[ -z "$SSH_TARGET" || "$SSH_TARGET" == "null" ]] && SSH_TARGET="$SLUG"

# Stack summary (string built via jq, safe)
STACK_SUMMARY=$(jq -r '
  [
    (if .platforms.shopify_domain // "" != "" then "Shopify (\(.platforms.shopify_domain))" else empty end),
    (if .platforms.klaviyo_account_id // "" != "" then "Klaviyo" else empty end),
    (if .platforms.ghl_location // "" != "" then "GoHighLevel CRM" else empty end),
    (if .platforms.manychat // "" != "" and .platforms.manychat != null then "ManyChat" else empty end),
    (if .platforms.meta_ad_account // "" != "" and .platforms.meta_ad_account != null then "Meta Ads" else empty end)
  ] | if length == 0 then "nothing wired up yet — we will set it up together" else join(", ") end
' "$CONFIG")

EMAIL_TOOL="email"
[[ "$(jq -r '.platforms.klaviyo_account_id // ""' "$CONFIG")" != "" ]] && EMAIL_TOOL="Klaviyo"

# Beta dates
BETA_START_DATE=$(date +"%B %d, %Y")
if BETA_GRADUATION_DATE=$(date -v +45d +"%B %d, %Y" 2>/dev/null); then : ; else
  BETA_GRADUATION_DATE=$(date -d "+45 days" +"%B %d, %Y" 2>/dev/null || echo "approximately 45 days from start")
fi

# Build per-bot intro block
TIMEZONE_SHORT=$(jq -r .owner_timezone "$CONFIG" | sed 's|.*/||' | tr '[:lower:]' '[:upper:]')
BOTS_BLOCK=""
for role in $ROLES; do
  case "$role" in
    ops)        DESC="**Operations Manager** — runs your numbers, server health, daily revenue rundown"; UNAME=$UN_OPS ;;
    social)     DESC="**Brand Voice Concierge** — owns your customer-facing copy + email + IG voice"; UNAME=$UN_SOCIAL ;;
    marketing)  DESC="**Paid Media Strategist** — your Meta/Google/TikTok ads + ROAS guardian"; UNAME=$UN_MARKETING ;;
    intel)      DESC="**Competitive Analyst** — daily competitor + market signal feed"; UNAME=$UN_INTEL ;;
  esac
  BOTS_BLOCK="${BOTS_BLOCK}### @${UNAME}
${DESC}

"
done

# Conditional rows + "five things to ask" — empty for tiers that lack the bot
ROW_SOCIAL=""; ROW_MARKETING=""; ROW_INTEL=""
Q3=""; Q4=""; Q5=""
if [[ " $ROLES " == *" social "* ]]; then
  ROW_SOCIAL="| Content, brand voice, email copy, IG/TikTok captions | **@${UN_SOCIAL}** |"$'\n'
  Q3="3. **\`@${UN_SOCIAL} draft a post about [topic]\`** — see your voice nailed"$'\n'
fi
if [[ " $ROLES " == *" marketing "* ]]; then
  ROW_MARKETING="| Paid ads — Meta, Google, TikTok, ad creative briefs | **@${UN_MARKETING}** |"$'\n'
  Q4="4. **\`@${UN_MARKETING} audit my current ads\`** — get a wasted-spend report"$'\n'
fi
if [[ " $ROLES " == *" intel "* ]]; then
  ROW_INTEL="| Competitor moves, market trends, customer research | **@${UN_INTEL}** |"$'\n'
  Q5="5. **\`@${UN_INTEL} what are competitors doing this week?\`** — get the rundown"$'\n'
fi

# Day-specific blocks (only render bot-specific lines for bots that exist for this tier)
DAY1_INTEL=""; DAY1_MARKETING=""; DAY3_INTEL=""; DAY7_MARKETING_BLOCK=""
if [[ " $ROLES " == *" intel "* ]]; then
  DAY1_INTEL="
**Your Intel bot** sets up shop:
> *Hey, I'm @${UN_INTEL}. By tomorrow morning I'll have your top 5 competitors mapped and daily scans running. First brief drops Friday.*
"
  DAY3_INTEL="**Your Intel bot** delivers the first competitive map:
- Your 5 closest competitors ranked by threat level
- What angles they're using that you're not
- One specific weakness you could exploit
"
fi
if [[ " $ROLES " == *" marketing "* ]]; then
  DAY1_MARKETING="
**Your Marketing bot** runs a quick ad-health audit:
> *Hi! I'm @${UN_MARKETING}. Send me your ad-account access when you can. I'll pull a wasted-spend audit and 3 hook tests by end of week.*
"
  DAY7_MARKETING_BLOCK="
💰 Marketing surfaced:
  - X creative angles that work (vs the X that don't)
  - Current ROAS, target ROAS, gap analysis
  - 3 new ad concepts ready for your approval"
fi

KLAVIYO_PLACEHOLDER=""
[[ "$(jq -r '.platforms.klaviyo_account_id // ""' "$CONFIG")" != "" ]] && KLAVIYO_PLACEHOLDER="X emails drafted (you approved Y)"

VERTICAL=$(jq -r .vertical "$CONFIG")
NICHE_TREND_PLACEHOLDER="One trending angle in $VERTICAL worth testing"

# Headache-driven deep dive
HEADACHES=$(jq -r '.headaches // [] | .[]' "$CONFIG" 2>/dev/null | head -3 || true)
HEADACHE_DEEP_DIVE=""
if [[ -n "$HEADACHES" ]]; then
  HEADACHE_DEEP_DIVE="Based on what you told us in onboarding, here are the deep dives queued for your week 2:

"
  while IFS= read -r h; do
    [[ -z "$h" ]] && continue
    DESC=$(jq -r --arg h "$h" '.[$h].day14_deep_dive // empty' "$TEMPLATES/headache-agent-map.json" 2>/dev/null)
    HUMAN=$(jq -r --arg h "$h" '.[$h].human_label // empty' "$TEMPLATES/headache-agent-map.json" 2>/dev/null)
    [[ -n "$DESC" ]] && HEADACHE_DEEP_DIVE="${HEADACHE_DEEP_DIVE}- **${HUMAN}**: ${DESC}
"
  done <<< "$HEADACHES"
else
  HEADACHE_DEEP_DIVE="Tell your Ops bot what your biggest headache is right now. They'll trigger a focused specialist deep-dive on it within the week.
"
fi

# Build the FULL context JSON via jq — never via shell interpolation
SLUG_UPPER=$(echo "$SLUG" | tr '[:lower:]' '[:upper:]' | sed 's/[-_]//g')

jq \
  --arg BOT_COUNT "$BOT_COUNT" \
  --arg AGENT_COUNT "$AGENT_PHRASE" \
  --arg SSH_TARGET "$SSH_TARGET" \
  --arg GENERATED_AT "$(iso_now)" \
  --arg BETA_START_DATE "$BETA_START_DATE" \
  --arg BETA_GRADUATION_DATE "$BETA_GRADUATION_DATE" \
  --arg EMAIL_TOOL "$EMAIL_TOOL" \
  --arg STACK_SUMMARY "$STACK_SUMMARY" \
  --arg KLAVIYO_PLACEHOLDER "$KLAVIYO_PLACEHOLDER" \
  --arg NICHE_TREND_PLACEHOLDER "$NICHE_TREND_PLACEHOLDER" \
  --arg TIMEZONE "$TIMEZONE_SHORT" \
  --arg OPS_USERNAME "$UN_OPS" \
  --arg SOCIAL_USERNAME "$UN_SOCIAL" \
  --arg MARKETING_USERNAME "$UN_MARKETING" \
  --arg INTEL_USERNAME "$UN_INTEL" \
  --arg SLUG_UPPER "$SLUG_UPPER" \
  --arg BOTS_BLOCK "$BOTS_BLOCK" \
  --arg ROW_SOCIAL "$ROW_SOCIAL" \
  --arg ROW_MARKETING "$ROW_MARKETING" \
  --arg ROW_INTEL "$ROW_INTEL" \
  --arg Q3 "$Q3" \
  --arg Q4 "$Q4" \
  --arg Q5 "$Q5" \
  --arg DAY1_INTEL "$DAY1_INTEL" \
  --arg DAY1_MARKETING "$DAY1_MARKETING" \
  --arg DAY3_INTEL "$DAY3_INTEL" \
  --arg DAY7_MARKETING_BLOCK "$DAY7_MARKETING_BLOCK" \
  --arg HEADACHE_DEEP_DIVE "$HEADACHE_DEEP_DIVE" \
  '. + {
    BOT_COUNT: $BOT_COUNT,
    AGENT_COUNT: $AGENT_COUNT,
    SSH_TARGET: $SSH_TARGET,
    GENERATED_AT: $GENERATED_AT,
    BETA_START_DATE: $BETA_START_DATE,
    BETA_GRADUATION_DATE: $BETA_GRADUATION_DATE,
    EMAIL_TOOL: $EMAIL_TOOL,
    STACK_SUMMARY: $STACK_SUMMARY,
    KLAVIYO_PLACEHOLDER: $KLAVIYO_PLACEHOLDER,
    NICHE_TREND_PLACEHOLDER: $NICHE_TREND_PLACEHOLDER,
    TIMEZONE: $TIMEZONE,
    OPS_USERNAME: $OPS_USERNAME,
    SOCIAL_USERNAME: $SOCIAL_USERNAME,
    MARKETING_USERNAME: $MARKETING_USERNAME,
    INTEL_USERNAME: $INTEL_USERNAME,
    SLUG_UPPER: $SLUG_UPPER,
    BOTS_BLOCK: $BOTS_BLOCK,
    ROW_SOCIAL: $ROW_SOCIAL,
    ROW_MARKETING: $ROW_MARKETING,
    ROW_INTEL: $ROW_INTEL,
    Q3: $Q3,
    Q4: $Q4,
    Q5: $Q5,
    DAY1_INTEL: $DAY1_INTEL,
    DAY1_MARKETING: $DAY1_MARKETING,
    DAY3_INTEL: $DAY3_INTEL,
    DAY7_MARKETING_BLOCK: $DAY7_MARKETING_BLOCK,
    HEADACHE_DEEP_DIVE: $HEADACHE_DEEP_DIVE,
    INIT: .client_init,
    SLUG: .slug,
    CLIENT_NAME: .client_name,
    OWNER_NAME: .owner_name,
    OWNER_TG_ID: (.owner_telegram_id | tostring)
  }' "$CONFIG" > "$TMP/ctx.json"

# Render each template via render.py (NO sed, NO inline python heredocs)
echo "→ Rendering deliverables via render.py, SSH target: $SSH_TARGET"
python3 "$RENDER" --config "$TMP/ctx.json" --template "$TEMPLATES/YOUR-AI-TEAM.md" --output "$TMP/YOUR-AI-TEAM.md"
python3 "$RENDER" --config "$TMP/ctx.json" --template "$TEMPLATES/SAMPLE-WEEK.md"  --output "$TMP/SAMPLE-WEEK.md"
python3 "$RENDER" --config "$TMP/ctx.json" --template "$TEMPLATES/RUNBOOK.md"      --output "$TMP/RUNBOOK.md"
if [[ "$BETA" == "true" ]]; then
  python3 "$RENDER" --config "$TMP/ctx.json" --template "$TEMPLATES/BETA-AGREEMENT.md" --output "$TMP/BETA-AGREEMENT.md"
fi

# ── ship to client VPS ──
echo "→ Shipping deliverables to $SSH_TARGET:/root/.hermes/shared/$SLUG/"
ssh "$SSH_TARGET" "mkdir -p /root/.hermes/shared/$SLUG"
for f in "$TMP"/*.md; do
  fname=$(basename "$f")
  scp -q "$f" "$SSH_TARGET":/root/.hermes/shared/$SLUG/"$fname"
  echo "  ✓ $fname"
done

# ── stash local copies ──
LOCAL_DIR="$HOME/.$SLUG/deliverables"
mkdir -p "$LOCAL_DIR"
cp "$TMP"/*.md "$LOCAL_DIR/"
echo ""
echo "✓ Local copies in $LOCAL_DIR/"

echo ""
echo "═══ DELIVERABLES READY ═══"
echo "On client VPS: /root/.hermes/shared/$SLUG/"
for f in "$TMP"/*.md; do echo "  - $(basename "$f")"; done
