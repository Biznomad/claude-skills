#!/usr/bin/env bash
#
# new-client.sh — scaffold a new client workspace for empire-builder
#
# Usage:
#   bash ~/.claude/skills/empire-builder/scripts/new-client.sh <slug>
#
# Creates:
#   ~/.claude/skills/empire-builder/clients/<slug>/
#   ├── .planning/          (GSD workspace — gsd-new-project lands here)
#   ├── outbox/             (staged artifacts ready for founder to publish)
#   │   └── content-pieces/ (weekly content batches)
#   ├── SESSION_STATE.md    (growth loop running journal)
#   ├── metrics.json        (machine-readable progress tracker)
#   └── loop-config.md      (growth loop config — filled in at Stage 3)
#
set -uo pipefail

SKILL_DIR="${HOME}/.claude/skills/empire-builder"
CLIENTS_DIR="${SKILL_DIR}/clients"

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
ok()    { printf '  \033[0;32m✓\033[0m %s\n' "$*"; }
warn()  { printf '  \033[0;33m!\033[0m %s\n' "$*"; }
step()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

if [ -z "${1:-}" ]; then
  warn "Usage: $0 <slug>"
  warn "Example: $0 manifest-and-thrive"
  exit 1
fi

SLUG="$1"
CLIENT_DIR="${CLIENTS_DIR}/${SLUG}"

step "Scaffolding client workspace for: $SLUG"

# Create directory structure
mkdir -p \
  "${CLIENT_DIR}/.planning" \
  "${CLIENT_DIR}/outbox/content-pieces" \
  "${CLIENT_DIR}/outbox/resources"

ok "directories created"

# Create SESSION_STATE.md if it doesn't exist
STATE_FILE="${CLIENT_DIR}/SESSION_STATE.md"
if [ ! -f "$STATE_FILE" ]; then
  cat > "$STATE_FILE" <<EOF
# SESSION_STATE — ${SLUG}

Growth loop running journal. Newest entry at top.
Read this at the start of every Stage 3 run.

---

## Initial setup — $(date +%Y-%m-%d)

**Status:** Interview pending → build pending → growth loop not yet started
**Member count:** 0
**Content pieces shipped:** 0
**Run count:** 0

Next loop track: (a)
EOF
  ok "SESSION_STATE.md created"
fi

# Create metrics.json if it doesn't exist
METRICS_FILE="${CLIENT_DIR}/metrics.json"
if [ ! -f "$METRICS_FILE" ]; then
  cat > "$METRICS_FILE" <<EOF
{
  "slug": "${SLUG}",
  "last_run": null,
  "member_count": 0,
  "member_count_goal": 50,
  "content_pieces_shipped": 0,
  "content_goal_per_week": 3,
  "track_last_run": null,
  "run_count": 0,
  "churn_rate_last_month": 0,
  "mrr": 0
}
EOF
  ok "metrics.json created"
fi

# Create a placeholder loop-config.md (filled in at Stage 3)
LOOP_CONFIG="${CLIENT_DIR}/loop-config.md"
if [ ! -f "$LOOP_CONFIG" ]; then
  cat > "$LOOP_CONFIG" <<EOF
# Growth Loop Config — ${SLUG}

> To be filled in at Stage 3 from templates/loop-config.md + client config.
> See: ~/.claude/skills/empire-builder/templates/loop-config.md
EOF
  ok "loop-config.md placeholder created"
fi

# Create client config if it doesn't exist (copy from schema)
CONFIG_FILE="${CLIENTS_DIR}/${SLUG}.json"
if [ ! -f "$CONFIG_FILE" ]; then
  # Copy schema as starting point with slug pre-filled
  SCHEMA="${CLIENTS_DIR}/_schema.json"
  if [ -f "$SCHEMA" ]; then
    # Use sed to fill in the slug (basic substitution — model fills the rest via interview)
    sed "s/\"slug\": \"REQUIRED[^\"]*\"/\"slug\": \"${SLUG}\"/" "$SCHEMA" > "$CONFIG_FILE"
    # Set interview_complete to false
    sed -i '' 's/"interview_complete": false/"interview_complete": false/' "$CONFIG_FILE" 2>/dev/null || \
    sed -i 's/"interview_complete": false/"interview_complete": false/' "$CONFIG_FILE"
    ok "client config created: clients/${SLUG}.json"
  else
    warn "Schema not found at ${SCHEMA} — create config manually"
  fi
fi

bold ""
bold "Client workspace ready: clients/${SLUG}/"
echo ""
echo "  Next steps:"
echo "  1. Run the interview (SKILL.md §1) to fill in clients/${SLUG}.json"
echo "  2. After interview, Stage 1 will bootstrap GSD in clients/${SLUG}/.planning/"
echo "  3. Stage 2 will populate clients/${SLUG}/outbox/ with staged artifacts"
echo "  4. Stage 3 growth loop will run weekly after launch"
echo ""
echo "  To check workspace:"
echo "    ls clients/${SLUG}/"
echo "    cat clients/${SLUG}/SESSION_STATE.md"
