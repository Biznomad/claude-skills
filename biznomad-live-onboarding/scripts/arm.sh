#!/bin/bash
# biznomad-live-onboarding / arm.sh
# Arms a client's Ops bot for in-group live onboarding of the business owner.
#
# Usage: bash arm.sh <slug> [options]
# Options:
#   --owner-name "Name"            Override owner first name (else from config)
#   --operator-name "Naeem"        Operator first name (default: Naeem)
#   --whatsapp-number "16783299051" Operator WhatsApp (default below)
#
# Examples:
#   bash arm.sh vicelle
#   bash arm.sh dlluxe --owner-name "Tanya" --whatsapp-number "16783299051"
#   bash arm.sh liquidwizdom --operator-name "Naeem"

set -euo pipefail

DEFAULT_WHATSAPP="16783299051"
DEFAULT_OPERATOR="Naeem"

# ── slug + flags ──────────────────────────────────────────────────────
SLUG="${1:-}"
[[ -z "$SLUG" ]] && { echo "Usage: $0 <slug> [--owner-name X] [--operator-name X] [--whatsapp-number N]"; exit 1; }
[[ ! "$SLUG" =~ ^[a-z0-9][a-z0-9-]{0,30}$ ]] && { echo "❌ Invalid slug '$SLUG'"; exit 1; }
shift

OWNER_FIRST_NAME=""
OPERATOR_NAME="$DEFAULT_OPERATOR"
WHATSAPP="$DEFAULT_WHATSAPP"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner-name)       OWNER_FIRST_NAME="$2"; shift 2 ;;
    --operator-name)    OPERATOR_NAME="$2"; shift 2 ;;
    --whatsapp-number)  WHATSAPP="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# ── locate inputs ─────────────────────────────────────────────────────
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$HOME/.claude/skills/biznomad-client-ai-team/clients/$SLUG.json"
TPL_SOUL="$SKILL_DIR/templates/soul-handoff-block.md"
TPL_PLAYBOOK="$SKILL_DIR/templates/playbook-group-only-block.md"
TPL_WHATSAPP="$SKILL_DIR/templates/whatsapp-message.txt"
TPL_TRIGGER="$SKILL_DIR/templates/telegram-trigger.txt"
LOG_DIR="$SKILL_DIR/clients"; mkdir -p "$LOG_DIR"

[[ ! -f "$CONFIG" ]]        && { echo "❌ no client config at $CONFIG"; exit 1; }
[[ ! -f "$TPL_SOUL" ]]      && { echo "❌ missing soul template"; exit 1; }
[[ ! -f "$TPL_PLAYBOOK" ]]  && { echo "❌ missing playbook template"; exit 1; }
command -v jq >/dev/null    || { echo "❌ jq required"; exit 1; }

# ── extract from config ───────────────────────────────────────────────
CLIENT_NAME=$(jq -r .client_name "$CONFIG")
[[ -z "$OWNER_FIRST_NAME" ]] && OWNER_FIRST_NAME=$(jq -r '.owner_name' "$CONFIG" | awk '{print $1}')
OPS_USERNAME=$(jq -r '.telegram_bot_usernames.ops // empty' "$CONFIG" | sed 's/^@//')
SSH_TARGET=$(jq -r '.vps.ssh_alias // .vps.ssh_target // empty' "$CONFIG")
[[ -z "$SSH_TARGET" ]] && SSH_TARGET="$SLUG"
OWNER_LOWER=$(echo "$OWNER_FIRST_NAME" | tr '[:upper:]' '[:lower:]')

echo "═══ Arming live onboarding for $SLUG ═══"
echo "  Client:        $CLIENT_NAME"
echo "  Owner:         $OWNER_FIRST_NAME"
echo "  Operator:      $OPERATOR_NAME"
echo "  Ops bot:       @$OPS_USERNAME"
echo "  SSH:           $SSH_TARGET"
echo ""

# ── render templates with substitution ────────────────────────────────
render() {
  sed \
    -e "s|{{OWNER_FIRST_NAME}}|$OWNER_FIRST_NAME|g" \
    -e "s|{{OWNER_LOWER}}|$OWNER_LOWER|g" \
    -e "s|{{CLIENT_NAME}}|$CLIENT_NAME|g" \
    -e "s|{{OPERATOR_NAME}}|$OPERATOR_NAME|g" \
    -e "s|{{OPS_USERNAME}}|$OPS_USERNAME|g" \
    -e "s|{{SLUG}}|$SLUG|g" \
    "$1"
}

TMP=$(mktemp -d); trap "rm -rf $TMP" EXIT
render "$TPL_SOUL"     > "$TMP/soul-block.md"
render "$TPL_PLAYBOOK"  > "$TMP/playbook-block.md"
render "$TPL_WHATSAPP"  > "$TMP/whatsapp.txt"
render "$TPL_TRIGGER"   > "$TMP/trigger.txt"

# ── ship and apply on client VPS ──────────────────────────────────────
scp -q "$TMP/soul-block.md" "$TMP/playbook-block.md" "$SSH_TARGET:/tmp/"

ssh "$SSH_TARGET" SLUG="$SLUG" OWNER_FIRST_NAME="$OWNER_FIRST_NAME" OWNER_LOWER="$OWNER_LOWER" 'bash -s' <<'REMOTE_EOF'
set -euo pipefail

SOUL=/root/.hermes/profiles/${SLUG}-ops/SOUL.md
PLAYBOOK=/root/.hermes/shared/${SLUG}/obsidian-vault/70-Onboarding/playbooks/ops-onboarding.md
ENV=/root/.hermes/profiles/${SLUG}-ops/.env

[[ ! -f "$SOUL" ]]     && { echo "❌ SOUL.md missing — has biznomad-client-ai-team provisioned this client?"; exit 1; }
[[ ! -f "$PLAYBOOK" ]] && { echo "❌ playbook missing — has biznomad-live-onboarding's vault been built?"; exit 1; }

# 1. Widen Ops gate
echo "── Widen Ops permission gate (temporary) ──"
sed -i "s/^GATEWAY_ALLOW_ALL_USERS=.*/GATEWAY_ALLOW_ALL_USERS=true/" "$ENV"
sed -i "s/^TG_ALLOWED_USER_IDS=.*/TG_ALLOWED_USER_IDS=/" "$ENV"
sed -i "s/^TELEGRAM_ALLOWED_USERS=.*/TELEGRAM_ALLOWED_USERS=/" "$ENV"
grep -E "^(GATEWAY_ALLOW_ALL_USERS|TG_ALLOWED|TELEGRAM_ALLOWED|TELEGRAM_REQUIRE_MENTION)" "$ENV" | sed 's/^/  /'

# 2. Patch SOUL.md with owner-handoff protocol (idempotent)
echo ""
echo "── Patch Ops SOUL.md (owner-handoff protocol) ──"
if grep -qF "<!-- OWNER-HANDOFF -->" "$SOUL"; then
  echo "  ✓ already patched (idempotent skip)"
else
  echo "" >> "$SOUL"
  cat /tmp/soul-block.md >> "$SOUL"
  echo "  ✓ appended"
fi

# 3. Patch playbook with group-only rule (idempotent)
echo ""
echo "── Patch ops-onboarding playbook (group-only mode) ──"
if grep -qF "<!-- GROUP-ONLY-MODE -->" "$PLAYBOOK"; then
  echo "  ✓ already patched (idempotent skip)"
else
  # Insert after frontmatter
  python3 - "$PLAYBOOK" /tmp/playbook-block.md <<PYEOF
import sys
target = sys.argv[1]
insert_file = sys.argv[2]
text = open(target).read()
insert = open(insert_file).read()
parts = text.split('---', 2)
if len(parts) >= 3:
    new = '---' + parts[1] + '---\n\n' + insert + parts[2]
else:
    new = insert + '\n\n' + text
open(target, 'w').write(new)
PYEOF
  echo "  ✓ inserted at top"
fi

# 4. Clean up shipped templates
rm -f /tmp/soul-block.md /tmp/playbook-block.md

# 5. Restart Ops gateway
echo ""
echo "── Restart Ops gateway ──"
systemctl restart hermes-gateway-${SLUG}-ops.service
sleep 6
echo "  Ops: $(systemctl is-active hermes-gateway-${SLUG}-ops.service)"
REMOTE_EOF

# ── log the arming ────────────────────────────────────────────────────
TS=$(date +"%Y-%m-%dT%H:%M:%S%z")
echo "$TS  armed for live onboarding · operator=$OPERATOR_NAME · owner=$OWNER_FIRST_NAME" >> "$LOG_DIR/${SLUG}.onboarding-log.txt"

# ── print the deliverables ────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════════════"
OWNER_UPPER=$(echo "$OWNER_FIRST_NAME" | tr '[:lower:]' '[:upper:]')
echo "  COPY-PASTE 1: WHATSAPP MESSAGE FOR $OWNER_UPPER"
echo "════════════════════════════════════════════════════════════════════"
cat "$TMP/whatsapp.txt"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  COPY-PASTE 2: TELEGRAM IN-GROUP TRIGGER"
echo "  (paste in the \"$CLIENT_NAME AI Team\" group after adding $OWNER_FIRST_NAME)"
echo "════════════════════════════════════════════════════════════════════"
cat "$TMP/trigger.txt"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  AFTER ONBOARDING — RUN THIS TO LOCK DOWN"
echo "════════════════════════════════════════════════════════════════════"
echo "  bash $SKILL_DIR/scripts/lock-down.sh $SLUG <owner-telegram-user-id>"
echo ""
echo "  Get owner's user_id from journal:"
echo "  ssh $SSH_TARGET 'journalctl -u hermes-gateway-${SLUG}-ops.service --since \"1 hour ago\" | grep -oE \"user_id[\\\":= ]+[0-9]+\" | sort -u'"
echo "════════════════════════════════════════════════════════════════════"
