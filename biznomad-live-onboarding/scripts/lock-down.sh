#!/bin/bash
# biznomad-live-onboarding / lock-down.sh
# Re-locks the Ops bot's permission gate to just the operator + owner after
# day-1 onboarding completes. Run this once the owner's user_id is captured.
#
# Usage: bash lock-down.sh <slug> <owner-user-id> [--operator-id <id>]
#
# Example:
#   bash lock-down.sh vicelle 8675309001
#   bash lock-down.sh dlluxe 1234567890 --operator-id 5165464044

set -euo pipefail

DEFAULT_OPERATOR_ID="5165464044"  # ← update if Naeem's Telegram user_id is different

SLUG="${1:-}"
OWNER_ID="${2:-}"
OPERATOR_ID="$DEFAULT_OPERATOR_ID"

[[ -z "$SLUG" ]]     && { echo "Usage: $0 <slug> <owner-user-id> [--operator-id <id>]"; exit 1; }
[[ -z "$OWNER_ID" ]] && { echo "❌ owner user_id required (positional arg 2)"; exit 1; }
[[ ! "$SLUG"     =~ ^[a-z0-9][a-z0-9-]{0,30}$ ]] && { echo "❌ invalid slug"; exit 1; }
[[ ! "$OWNER_ID" =~ ^[0-9]{6,15}$ ]] && { echo "❌ owner user_id must be numeric"; exit 1; }
shift 2

while [[ $# -gt 0 ]]; do
  case "$1" in
    --operator-id) OPERATOR_ID="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

CONFIG="$HOME/.claude/skills/biznomad-client-ai-team/clients/$SLUG.json"
[[ ! -f "$CONFIG" ]] && { echo "❌ no client config at $CONFIG"; exit 1; }
SSH_TARGET=$(jq -r '.vps.ssh_alias // .vps.ssh_target // empty' "$CONFIG")
[[ -z "$SSH_TARGET" ]] && SSH_TARGET="$SLUG"

ALLOW_LIST="$OPERATOR_ID,$OWNER_ID"

echo "═══ Locking down Ops for $SLUG ═══"
echo "  Allowed user_ids: $ALLOW_LIST"
echo ""

ssh "$SSH_TARGET" SLUG="$SLUG" ALLOW_LIST="$ALLOW_LIST" 'bash -s' <<'REMOTE_EOF'
set -euo pipefail
ENV=/root/.hermes/profiles/${SLUG}-ops/.env

echo "── Tightening allowlist ──"
sed -i "s/^GATEWAY_ALLOW_ALL_USERS=.*/GATEWAY_ALLOW_ALL_USERS=false/" "$ENV"
sed -i "s/^TG_ALLOWED_USER_IDS=.*/TG_ALLOWED_USER_IDS=${ALLOW_LIST}/" "$ENV"
sed -i "s/^TELEGRAM_ALLOWED_USERS=.*/TELEGRAM_ALLOWED_USERS=${ALLOW_LIST}/" "$ENV"
grep -E "^(GATEWAY_ALLOW_ALL_USERS|TG_ALLOWED|TELEGRAM_ALLOWED)" "$ENV" | sed 's/^/  /'

echo ""
echo "── Restart Ops gateway ──"
systemctl restart hermes-gateway-${SLUG}-ops.service
sleep 6
echo "  Ops: $(systemctl is-active hermes-gateway-${SLUG}-ops.service)"
REMOTE_EOF

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS=$(date +"%Y-%m-%dT%H:%M:%S%z")
mkdir -p "$SKILL_DIR/clients"
echo "$TS  locked down · owner_user_id=$OWNER_ID · allowlist=$ALLOW_LIST" >> "$SKILL_DIR/clients/${SLUG}.onboarding-log.txt"

echo ""
echo "✓ Ops for $SLUG is now locked to: $ALLOW_LIST"
echo "  Onboarding complete. Tomorrow at 9am ET, Intel introduces herself."
