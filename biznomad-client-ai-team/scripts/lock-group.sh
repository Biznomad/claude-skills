#!/bin/bash
# Lock all of a client's bots to ONLY respond to the configured team-room chat_id.
# Run this AFTER you've created the Telegram group and captured its chat_id.
#
# Usage: bash lock-group.sh <slug> <chat_id>
# Example: bash lock-group.sh dlluxe -1001234567890

set -euo pipefail

SLUG="${1:-}"
CHAT_ID="${2:-}"
if [[ -z "$SLUG" || -z "$CHAT_ID" ]]; then
  echo "Usage: $0 <slug> <chat_id>"
  echo "Example: $0 dlluxe -1001234567890"
  echo ""
  echo "How to get the chat_id of your team-room group:"
  echo "  1. After creating the group + adding bots, send /whoami in the group"
  echo "  2. ssh root@<vps> 'journalctl -u hermes-gateway-<slug>-ops.service -n 50'"
  echo "  3. The negative number (e.g. -1001234567890) is the supergroup chat_id"
  exit 1
fi

# Slug validator (codex hi#4)
if ! [[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]{0,30}$ ]]; then
  echo "❌ Invalid slug '$SLUG'"; exit 1
fi
# chat_id validator — Telegram group ids are negative integers
if ! [[ "$CHAT_ID" =~ ^-?[0-9]+$ ]]; then
  echo "❌ Invalid chat_id '$CHAT_ID' — must be an integer"; exit 1
fi

SSH_TARGET="${BIZNOMAD_SSH:-root@187.77.10.20}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$SKILL_DIR/clients/$SLUG.json"

# Determine roles from existing profiles — use fixed-string match (codex hi#4)
ROLES=$(ssh "$SSH_TARGET" "hermes profile list 2>/dev/null" 2>/dev/null \
  | awk -v s="${SLUG}-" '$0 ~ s {for(i=1;i<=NF;i++) if(index($i,s)==1) print $i}' \
  | sed "s/^${SLUG}-//" | sort -u)

if [[ -z "$ROLES" ]]; then
  echo "❌ No profiles found matching ${SLUG}-* on $SSH_TARGET"
  exit 1
fi

echo "═══ Locking the following bots to group $CHAT_ID ═══"
for role in $ROLES; do echo "  - ${SLUG}-${role}"; done

ssh "$SSH_TARGET" bash -s -- "$SLUG" "$CHAT_ID" "$ROLES" <<'REMOTE_EOF'
set -euo pipefail
SLUG="$1"; CHAT_ID="$2"; ROLES="$3"

for role in $ROLES; do
  ENV=/root/.hermes/profiles/${SLUG}-${role}/.env
  if grep -q "^TELEGRAM_GROUP_ALLOWED_CHATS=" "$ENV"; then
    sed -i "s|^TELEGRAM_GROUP_ALLOWED_CHATS=.*|TELEGRAM_GROUP_ALLOWED_CHATS=${CHAT_ID}|" "$ENV"
  else
    echo "TELEGRAM_GROUP_ALLOWED_CHATS=${CHAT_ID}" >> "$ENV"
  fi
  echo "  ✓ ${SLUG}-${role}: TELEGRAM_GROUP_ALLOWED_CHATS=${CHAT_ID}"
done

echo ""
echo "Restarting…"
for role in $ROLES; do
  systemctl restart "hermes-gateway-${SLUG}-${role}.service"
done
sleep 6

echo ""
echo "═══ POST-LOCK STATUS ═══"
for role in $ROLES; do
  ACTIVE=$(systemctl is-active "hermes-gateway-${SLUG}-${role}.service")
  ERRS=$(journalctl -u "hermes-gateway-${SLUG}-${role}.service" --since "10 sec ago" --no-pager 2>/dev/null | grep -ciE "error|exception" || echo 0)
  printf "  %-25s %-8s  errors(10s): %s\n" "${SLUG}-${role}" "$ACTIVE" "$ERRS"
done
REMOTE_EOF

# Update the client config file with the chat_id so we have a record
if [[ -f "$CONFIG" ]]; then
  tmp=$(mktemp)
  jq --arg cid "$CHAT_ID" '.telegram_team_group_chat_id = ($cid | tonumber)' "$CONFIG" > "$tmp" && mv "$tmp" "$CONFIG"
  echo ""
  echo "✓ Updated $CONFIG with telegram_team_group_chat_id = $CHAT_ID"
fi

echo ""
echo "Done. Now in the team room, send: @<bot_username> /whoami — only the @mentioned bot should reply."
