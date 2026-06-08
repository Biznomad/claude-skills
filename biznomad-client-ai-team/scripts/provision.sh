#!/bin/bash
# biznomad-client-ai-team — provision.sh
# Reads clients/{slug}.json and deploys the 4-bot AI team for that client
# on the Biznomad VPS (or any VPS named via BIZNOMAD_SSH env var).
#
# Usage: bash provision.sh <slug>
# Example: bash provision.sh dlluxe
#
# v2 (post-codex): replaces sed templating with safe render.py, drops
# client-to-client profile cloning, fixes BSD portability bugs.

set -euo pipefail

SLUG="${1:-}"
if [[ -z "$SLUG" ]]; then
  echo "Usage: $0 <slug>"
  echo "Example: $0 dlluxe"
  exit 1
fi

# ───────────────────────── slug validator (codex hi#4) ─────────────────────────
if ! [[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]{0,30}$ ]]; then
  echo "❌ Invalid slug '$SLUG' — must be lowercase alphanumeric + hyphens, 1-31 chars"
  exit 1
fi

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$SKILL_DIR/clients/$SLUG.json"
TEMPLATES="$SKILL_DIR/templates"
RENDER="$SKILL_DIR/scripts/render.py"

if [[ ! -f "$CONFIG" ]]; then
  echo "❌ No config at $CONFIG"
  echo "   Copy templates/client.example.json to clients/$SLUG.json and fill it in."
  exit 1
fi

# ───────────────────────── portable helpers ─────────────────────────
# sha256 on Mac uses `shasum -a 256`, on Linux `sha256sum`
sha256_fp() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | cut -c1-12
  else
    shasum -a 256 | cut -c1-12
  fi
}

# ISO timestamp without `date -Iseconds` (BSD doesn't support it)
iso_now() {
  date +"%Y-%m-%dT%H:%M:%S%z"
}

# ───────────────────────── prereqs ─────────────────────────
command -v jq >/dev/null || { echo "❌ jq required (brew install jq)"; exit 1; }
command -v python3 >/dev/null || { echo "❌ python3 required"; exit 1; }
[[ -f "$RENDER" ]] || { echo "❌ render.py missing at $RENDER"; exit 1; }

# ───────────────────────── parse config (just for tier + roles + sanity) ─────────────────────────
CLIENT_NAME=$(jq -r .client_name "$CONFIG")
TIER=$(jq -r .tier "$CONFIG")

case "$TIER" in
  solo)        ROLES="ops marketing" ;;
  standard)    ROLES="ops social intel" ;;
  full)        ROLES="ops social marketing intel" ;;
  enterprise)  ROLES="ops social marketing intel" ;;
  *) echo "❌ Unknown tier: $TIER (use solo|standard|full|enterprise)"; exit 1 ;;
esac

# ───────────────────────── token fingerprint check (Vicelle lesson) ─────────────────────────
echo "═══ Token uniqueness check ═══"
FINGERPRINTS=""
for role in $ROLES; do
  TOKEN=$(jq -r ".telegram_bot_tokens.$role" "$CONFIG")
  if [[ "$TOKEN" == "null" || -z "$TOKEN" || "$TOKEN" == "PASTE_FROM_BOTFATHER_HERE" ]]; then
    echo "❌ Missing Telegram token for role: $role"
    echo "   Edit $CONFIG and fill in telegram_bot_tokens.$role from BotFather."
    exit 1
  fi
  FP=$(printf '%s' "$TOKEN" | sha256_fp)
  if [[ -n "$FINGERPRINTS" && "$FINGERPRINTS" == *"$FP"* ]]; then
    echo "❌ Duplicate Telegram token (fingerprint $FP) — two roles share the same token."
    echo "   Each bot needs its OWN token. Re-check BotFather and the config."
    exit 1
  fi
  FINGERPRINTS="${FINGERPRINTS}${FP},"
  echo "  ✓ $role token fingerprint $FP unique"
done

# ───────────────────────── render templates locally via render.py (no sed) ─────────────────────────
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo ""
echo "═══ Rendering templates locally via render.py (safe — no sed/shell injection) ═══"

# Build per-role JSON (config + role overlay) for the renderer
for role in $ROLES; do
  ROLE_TITLE=$(echo "$role" | head -c1 | tr '[:lower:]' '[:upper:]')$(echo "$role" | tail -c +2)
  mkdir -p "$TMP/$role"
  # Merge: top-level config + role-specific overlay + compliance/ads/voice expansions
  jq --arg role "$role" --arg role_title "$ROLE_TITLE" --arg created "$(iso_now)" \
     '. + {
       ROLE: $role, ROLE_TITLE: $role_title, CREATED_AT: $created,
       SLUG: .slug, CLIENT_NAME: .client_name, CLIENT_INIT: .client_init,
       OWNER_NAME: .owner_name, OWNER_TG_ID: (.owner_telegram_id|tostring),
       TIMEZONE: .owner_timezone, VERTICAL: .vertical, AUDIENCE: .audience,
       SHOPIFY_DOMAIN: (.platforms.shopify_domain // ""),
       KLAVIYO_ACCOUNT_ID: (.platforms.klaviyo_account_id // ""),
       GHL_LOCATION: (.platforms.ghl_location // ""),
       MANYCHAT: (.platforms.manychat // ""),
       SITE: (.platforms.site // ""),
       VOICE_USE: ((.voice_keywords_use // []) | join(", ")),
       VOICE_AVOID: ((.voice_keywords_avoid // []) | join(", ")),
       TELEGRAM_BOT_TOKEN: (.telegram_bot_tokens[$role] // ""),
       COMPLIANCE_NOTES: (if .compliance.fda_supplement_rules == true then "- NEVER makes FDA-banned claims (cures, treats, prevents, boosts immunity, clinically proven, doctor-recommended) — reframe to structure/function language (supports, promotes, helps maintain)" else "" end),
       COMPLIANCE_INLINE: (if .compliance.fda_supplement_rules == true then " — never disease cures, never clinically proven, never doctor-recommended" else "" end),
       ADS_BASELINE: (if (.active_ads_baseline.platform // "") != "" then "\(.active_ads_baseline.platform): $\(.active_ads_baseline.budget_per_day // "?")/day, \(.active_ads_baseline.roas_baseline // "?")x ROAS baseline" else "(none configured yet)" end)
     }' \
     "$CONFIG" > "$TMP/$role/ctx.json"

  python3 "$RENDER" --strict --config "$TMP/$role/ctx.json" --template "$TEMPLATES/$role.SOUL.md" --output "$TMP/$role/SOUL.md"
  python3 "$RENDER" --strict --config "$TMP/$role/ctx.json" --template "$TEMPLATES/env.template" --output "$TMP/$role/.env"
  echo "  ✓ $role: SOUL.md + .env rendered"
done
# Codex round-2 fix: brand.md + shared README use uppercase aliases too; build a shared ctx
jq --arg created "$(iso_now)" \
   '. + {
     SLUG: .slug, CLIENT_NAME: .client_name, CLIENT_INIT: .client_init,
     OWNER_NAME: .owner_name, OWNER_TG_ID: (.owner_telegram_id|tostring),
     TIMEZONE: .owner_timezone, VERTICAL: .vertical, AUDIENCE: .audience,
     SITE: (.platforms.site // ""),
     SHOPIFY_DOMAIN: (.platforms.shopify_domain // ""),
     KLAVIYO_ACCOUNT_ID: (.platforms.klaviyo_account_id // ""),
     GHL_LOCATION: (.platforms.ghl_location // ""),
     MANYCHAT: (.platforms.manychat // ""),
     VOICE_USE: ((.voice_keywords_use // []) | join(", ")),
     VOICE_AVOID: ((.voice_keywords_avoid // []) | join(", ")),
     COMPLIANCE_BLOCK: (if .compliance.fda_supplement_rules == true then "- FDA supplement rules apply: structure/function language only\n- Never: cures, treats, prevents, boosts immunity, clinically proven, doctor-recommended\n- Always: supports, promotes, helps maintain" else "(none configured)" end),
     ADS_BASELINE_BLOCK: (if (.active_ads_baseline.platform // "") != "" then "\(.active_ads_baseline.platform): $\(.active_ads_baseline.budget_per_day // "?")/day, \(.active_ads_baseline.roas_baseline // "?")x ROAS baseline" else "(none configured yet)" end),
     KLAVIYO_FLOWS_BLOCK: (if (.klaviyo_flows // {}) != {} then ((.klaviyo_flows | to_entries | map("- \(.key): \(.value)")) | join("\n")) else "(none configured)" end),
     CREATED_AT: $created
   }' "$CONFIG" > "$TMP/shared-ctx.json"
python3 "$RENDER" --strict --config "$TMP/shared-ctx.json" --template "$TEMPLATES/brand.md" --output "$TMP/brand.md"
python3 "$RENDER" --strict --config "$TMP/shared-ctx.json" --template "$TEMPLATES/shared.README.md" --output "$TMP/README.md"

# ───────────────────────── deploy to client VPS ─────────────────────────
SSH_TARGET="${BIZNOMAD_SSH:-root@187.77.10.20}"
echo ""
echo "═══ Deploying to $SSH_TARGET ═══"

REMOTE_TMP="/root/.ai-team-stage-$SLUG-$(date +%s)"
ssh "$SSH_TARGET" "mkdir -p '$REMOTE_TMP' && chmod 700 '$REMOTE_TMP'"

# Ship rendered files
scp -q -r "$TMP"/* "$SSH_TARGET:$REMOTE_TMP/"

BRAND_COLOR=$(jq -r '.brand_color_hex // "#888888"' "$CONFIG")
BRAND_EMOJI=$(jq -r '.brand_emoji // "📦"' "$CONFIG")

# Run the remote install (no client_name etc passed inline — read from staged files)
ssh "$SSH_TARGET" REMOTE_TMP="$REMOTE_TMP" SLUG="$SLUG" CLIENT_NAME="$CLIENT_NAME" BRAND_COLOR="$BRAND_COLOR" BRAND_EMOJI="$BRAND_EMOJI" ROLES="$ROLES" 'bash -s' <<'REMOTE_EOF'
set -euo pipefail
# Codex round-2 fix: trap MUST be inside the remote shell, not a sourced .guard file
trap 'rm -rf "$REMOTE_TMP"' EXIT
echo "▶ Creating Hermes profiles (no client-to-client cloning — sterile create)"
for role in $ROLES; do
  PROF="${SLUG}-${role}"
  if hermes profile list 2>/dev/null | grep -qE "^[ ◆][[:space:]]+${PROF}\b"; then
    echo "  ✓ $PROF already exists, skipping create"
  else
    # CRITICAL: no --clone-from. Codex flagged client-to-client cloning as an isolation breach.
    hermes profile create "$PROF" \
      --description "${CLIENT_NAME} ${role} agent" 2>&1 | tail -2
  fi
  # Install rendered SOUL.md + .env from the staged area
  cp "$REMOTE_TMP/$role/SOUL.md" "/root/.hermes/profiles/$PROF/SOUL.md"
  cp "$REMOTE_TMP/$role/.env"    "/root/.hermes/profiles/$PROF/.env"
  chmod 600 "/root/.hermes/profiles/$PROF/.env"
done

echo ""
echo "▶ Installing systemd units + patching EnvironmentFile"
for role in $ROLES; do
  PROF="${SLUG}-${role}"
  printf "n\ny\n" | hermes -p "$PROF" gateway install --system --run-as-user root 2>&1 | tail -1
  UNIT=/etc/systemd/system/hermes-gateway-${PROF}.service
  # Codex round-3: atomic normalize — systemd applies EnvironmentFile in declaration order.
  # If a partial unit has only the profile line and we naively insert the global line,
  # global ends up after profile and overrides per-bot tokens. Fix: strip both managed
  # lines, then re-insert in canonical order (global first, profile second) before ExecStart.
  sed -i \
    -e "\|^EnvironmentFile=/root/.hermes/.env\$|d" \
    -e "\|^EnvironmentFile=-/root/.hermes/profiles/$PROF/.env\$|d" \
    "$UNIT"
  # Sed /i puts text directly above ExecStart. Second insert pushes the first up.
  # Want: [global, profile, ExecStart]. So insert global FIRST (gets pushed up),
  # then profile SECOND (lands directly above ExecStart).
  sed -i "/^ExecStart=/i EnvironmentFile=/root/.hermes/.env" "$UNIT"
  sed -i "/^ExecStart=/i EnvironmentFile=-/root/.hermes/profiles/$PROF/.env" "$UNIT"
  echo "  ✓ normalized EnvironmentFile order in $UNIT"
done
systemctl daemon-reload

echo ""
echo "▶ Setting up shared memory namespace"
mkdir -p "/root/.hermes/shared/$SLUG"
cp "$REMOTE_TMP/brand.md" "/root/.hermes/shared/$SLUG/brand.md"
cp "$REMOTE_TMP/README.md" "/root/.hermes/shared/$SLUG/README.md"
for role in $ROLES; do
  if [[ ! -f "/root/.hermes/shared/$SLUG/$role.md" ]]; then
    cat > "/root/.hermes/shared/$SLUG/$role.md" <<HDR
# ${SLUG}-${role} — shared findings

Owned by: ${SLUG}-${role} agent
Read-by:  all ${CLIENT_NAME} agents
Updated:  on every significant decision or signal

---

HDR
  fi
done
[[ ! -f "/root/.hermes/shared/$SLUG/decisions.md" ]] && \
  echo "# ${CLIENT_NAME} — Decisions Log (human-written)" > "/root/.hermes/shared/$SLUG/decisions.md"
for role in $ROLES; do
  PROF="${SLUG}-${role}"
  ln -sfn "/root/.hermes/shared/$SLUG" "/root/.hermes/profiles/$PROF/memories/shared"
done
echo "  ✓ /root/.hermes/shared/$SLUG/ ($(ls /root/.hermes/shared/$SLUG | wc -l) files)"

echo ""
echo "▶ Initializing kanban board"
hermes kanban init 2>&1 | tail -1
# Hard-fail if board create fails — codex high #6
if ! hermes kanban boards list 2>/dev/null | grep -qE "^[ ●]+${SLUG}\b"; then
  if ! hermes kanban boards create "$SLUG" \
      --name "${CLIENT_NAME} AI Team" \
      --description "Coordination board for the ${CLIENT_NAME} Hermes agents" \
      --icon "$BRAND_EMOJI" \
      --color "$BRAND_COLOR" 2>&1 | tail -1; then
    echo "❌ Kanban board create failed. Investigate before proceeding."
    rm -rf "$REMOTE_TMP"
    exit 1
  fi
fi

echo ""
echo "▶ Starting all agents"
for role in $ROLES; do
  systemctl enable --now "hermes-gateway-${SLUG}-${role}.service" 2>&1 | tail -1
done
sleep 8

echo ""
echo "═══ DEPLOYMENT COMPLETE ═══"
for role in $ROLES; do
  PROF="${SLUG}-${role}"
  ACTIVE=$(systemctl is-active "hermes-gateway-${PROF}.service")
  printf "  hermes-gateway-%-30s %s\n" "${PROF}.service" "$ACTIVE"
done

# Clean up remote stage (also covered by trap, but explicit is good)
rm -rf "$REMOTE_TMP"
REMOTE_EOF

echo ""
echo "═══ Next steps (Phase 3 — manual) ═══"
echo ""
echo "1. In Telegram, create a group: '${CLIENT_NAME} AI Team'"
OWNER_NAME=$(jq -r .owner_name "$CONFIG")
echo "2. Add ${OWNER_NAME} + the ${TIER}-tier bots ($ROLES — usernames in BotFather)"
echo "3. Send /whoami in the group from owner's account"
echo "4. Capture the group chat_id (from journalctl or any bot's reply metadata)"
echo "5. Run: bash $SKILL_DIR/scripts/lock-group.sh $SLUG <chat_id>"
echo ""
echo "Don't forget BotFather privacy mode: /mybots → each bot → Bot Settings → Group Privacy → ENABLE"
