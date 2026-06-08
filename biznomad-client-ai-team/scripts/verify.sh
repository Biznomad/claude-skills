#!/bin/bash
# Health check for a client's AI team deployment.
#
# Usage: bash verify.sh <slug>

set -euo pipefail

SLUG="${1:-}"
if [[ -z "$SLUG" ]]; then
  echo "Usage: $0 <slug>"
  exit 1
fi

# Slug validator (codex hi#4)
if ! [[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]{0,30}$ ]]; then
  echo "❌ Invalid slug '$SLUG'"; exit 1
fi

SSH_TARGET="${BIZNOMAD_SSH:-root@187.77.10.20}"

ssh "$SSH_TARGET" bash -s -- "$SLUG" <<'REMOTE_EOF'
# No `set -e` — verify is read-only and should continue past quirks
set -uo pipefail
SLUG="$1"

echo "═══ ${SLUG} AI Team — health ═══"
echo ""

# Find all profiles matching this slug — fixed-string prefix (codex hi#4)
PROFS=$(hermes profile list 2>/dev/null \
  | awk -v p="${SLUG}-" '{for(i=1;i<=NF;i++) if(index($i,p)==1) print $i}' \
  | sort -u)

if [[ -z "$PROFS" ]]; then
  echo "❌ No profiles found for slug '$SLUG'"
  exit 1
fi

echo "Service status:"
for PROF in $PROFS; do
  SVC="hermes-gateway-${PROF}.service"
  ACTIVE=$(systemctl is-active "$SVC" 2>&1)
  PID=$(systemctl show "$SVC" -p MainPID --value 2>&1)
  UPTIME=""
  HAS_KIMI="NO"
  if [[ "$PID" != "0" && -n "$PID" ]]; then
    UPTIME=$(ps -o etime= -p "$PID" 2>/dev/null | xargs)
    HAS_KIMI=$(tr "\0" "\n" < /proc/$PID/environ 2>/dev/null | grep -c "^KIMI_API_KEY=" || echo 0)
    [[ "$HAS_KIMI" -gt 0 ]] && HAS_KIMI=YES || HAS_KIMI=NO
  fi
  ERRS=$(journalctl -u "$SVC" --since "5 min ago" --no-pager 2>/dev/null | grep -ciE "error|conflict|exception" 2>/dev/null)
  ERRS=${ERRS:-0}
  printf "  %-30s %-8s  up=%-10s  kimi=%-3s  errors(5m)=%s\n" "$PROF" "$ACTIVE" "$UPTIME" "$HAS_KIMI" "$ERRS"
done

echo ""
echo "Bot usernames (token getMe check):"
for PROF in $PROFS; do
  ENV=/root/.hermes/profiles/${PROF}/.env
  TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$ENV" 2>/dev/null | cut -d= -f2)
  if [[ -n "$TOKEN" ]]; then
    UN=$(curl -s --max-time 5 "https://api.telegram.org/bot$TOKEN/getMe" \
         | python3 -c "import sys,json
try:
    d=json.load(sys.stdin)
    r=d.get('result',{})
    ok=d.get('ok')
    print(('@'+r.get('username','?')) if ok else 'INVALID')
except: print('PARSE_ERR')" 2>/dev/null)
    printf "  %-30s %s\n" "$PROF" "$UN"
  fi
done

echo ""
echo "Permission gates (key presence only — values redacted, codex med#3):"
for PROF in $PROFS; do
  ENV=/root/.hermes/profiles/${PROF}/.env
  printf "  %-30s " "$PROF"
  for key in TELEGRAM_REQUIRE_MENTION TELEGRAM_OBSERVE_UNMENTIONED_GROUP_MESSAGES GATEWAY_ALLOW_ALL_USERS TELEGRAM_ALLOWED_USERS TELEGRAM_GROUP_ALLOWED_CHATS; do
    if grep -q "^$key=" "$ENV"; then
      # For booleans, show value (small surface); for user-IDs / chat-IDs redact
      case "$key" in
        TELEGRAM_REQUIRE_MENTION|TELEGRAM_OBSERVE_UNMENTIONED_GROUP_MESSAGES|GATEWAY_ALLOW_ALL_USERS)
          VAL=$(grep "^$key=" "$ENV" | cut -d= -f2)
          printf "%s=%s " "$key" "${VAL:-(empty)}"
          ;;
        *)
          printf "%s=<SET> " "$key"
          ;;
      esac
    else
      printf "%s=MISSING " "$key"
    fi
  done
  echo ""
done

echo ""
echo "Shared memory:"
if [[ -d "/root/.hermes/shared/$SLUG" ]]; then
  ls -1 "/root/.hermes/shared/$SLUG/" | sed 's|^|  |'
else
  echo "  ❌ /root/.hermes/shared/$SLUG/ MISSING"
fi
echo ""
echo "Symlinks into profile memories:"
for PROF in $PROFS; do
  LINK="/root/.hermes/profiles/$PROF/memories/shared"
  if [[ -L "$LINK" ]]; then
    TGT=$(readlink "$LINK")
    printf "  %-30s → %s ✓\n" "$PROF" "$TGT"
  else
    printf "  %-30s ❌ shared symlink missing\n" "$PROF"
  fi
done

echo ""
echo "Kanban board:"
hermes kanban boards list 2>/dev/null | grep -E "^[ ●]+ +${SLUG}\b" || echo "  ❌ Board '${SLUG}' missing — run: hermes kanban boards create ${SLUG}"
REMOTE_EOF
