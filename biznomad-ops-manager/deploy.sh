#!/usr/bin/env bash
# Deploy biznomad-ops-manager for a new business.
#
# Usage:
#   export <SLUG>_KIMI_KEY=sk-kimi-xxxxx
#   bash deploy.sh businesses/<slug>.json
#
# What it does:
# 1. Reads the business config JSON.
# 2. Renders templates with substitution.
# 3. SCPs files to the target server (via jump_host if provided).
# 4. Installs Python deps, enables + starts the systemd service.
# 5. Sends a Telegram boot message to the configured group.
set -euo pipefail

CFG="${1:?usage: deploy.sh businesses/<slug>.json}"
[ -f "$CFG" ] || { echo "ERR: config not found: $CFG"; exit 1; }
command -v jq  >/dev/null || { echo "ERR: jq required"; exit 1; }

SLUG=$(jq -r .slug "$CFG")
AGENT_NAME=$(jq -r .agent_name "$CFG")
BUSINESS_NAME=$(jq -r .business_name "$CFG")
SSH_HOST=$(jq -r .server_ssh "$CFG")
JUMP=$(jq -r '.jump_host // ""' "$CFG")
BOT_TOKEN=$(jq -r .telegram_bot_token "$CFG")
GROUP=$(jq -r .telegram_group_id "$CFG")
ADMINS=$(jq -r '.admin_telegram_ids | join(",")' "$CFG")
KIMI_KEY_ENV=$(jq -r .kimi_api_key_env "$CFG")
KIMI_KEY="${!KIMI_KEY_ENV:?ERR: env var $KIMI_KEY_ENV is unset — export the Kimi key first}"
KIMI_BASE=$(jq -r .kimi_base "$CFG")
KIMI_MODEL=$(jq -r .kimi_model "$CFG")
KIMI_UA=$(jq -r .kimi_user_agent "$CFG")
DATA_DIR=$(jq -r .data_dir "$CFG")
CONFIG_FILE=$(jq -r .config_file "$CFG")
INSTALL=$(jq -r .install_dir "$CFG")
SVC=$(jq -r .service_name "$CFG")

ROOT=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

# Render env
cat > "$TMP/.env" <<EOF
TELEGRAM_TOKEN=$BOT_TOKEN
GROUP_ID=$GROUP
ADMIN_IDS=$ADMINS
KIMI_API_KEY=$KIMI_KEY
KIMI_API_BASE=$KIMI_BASE
KIMI_MODEL=$KIMI_MODEL
KIMI_USER_AGENT=$KIMI_UA
DATA_DIR=$DATA_DIR
CONFIG_FILE=$CONFIG_FILE
BUSINESS_NAME=$BUSINESS_NAME
AGENT_NAME=$AGENT_NAME
EOF

# Render systemd unit
sed -e "s|{{AGENT_NAME}}|$AGENT_NAME|g" \
    -e "s|{{BUSINESS_NAME}}|$BUSINESS_NAME|g" \
    -e "s|{{INSTALL_DIR}}|$INSTALL|g" \
    "$ROOT/templates/ops-bot.service" > "$TMP/$SVC.service"

cp "$ROOT/templates/ops_bot.py" "$TMP/ops_bot.py"

# Ship
if [ -n "$JUMP" ]; then
  scp "$TMP/ops_bot.py" "$TMP/.env" "$TMP/$SVC.service" "$JUMP:/tmp/"
  ssh "$JUMP" "scp /tmp/ops_bot.py /tmp/.env /tmp/$SVC.service $SSH_HOST:/tmp/ && \
    ssh $SSH_HOST 'mkdir -p $INSTALL/logs && \
      mv /tmp/ops_bot.py $INSTALL/ && \
      mv /tmp/.env $INSTALL/.env && chmod 600 $INSTALL/.env && \
      mv /tmp/$SVC.service /etc/systemd/system/$SVC.service && \
      pip3 install --break-system-packages -q python-telegram-bot httpx 2>&1 | tail -2 && \
      systemctl daemon-reload && systemctl enable --now $SVC.service && \
      sleep 2 && systemctl is-active $SVC.service'"
else
  scp "$TMP/ops_bot.py" "$TMP/.env" "$TMP/$SVC.service" "$SSH_HOST:/tmp/"
  ssh "$SSH_HOST" "mkdir -p $INSTALL/logs && \
    mv /tmp/ops_bot.py $INSTALL/ && \
    mv /tmp/.env $INSTALL/.env && chmod 600 $INSTALL/.env && \
    mv /tmp/$SVC.service /etc/systemd/system/$SVC.service && \
    pip3 install --break-system-packages -q python-telegram-bot httpx 2>&1 | tail -2 && \
    systemctl daemon-reload && systemctl enable --now $SVC.service && \
    sleep 2 && systemctl is-active $SVC.service"
fi

# Boot ping to group
curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d chat_id="$GROUP" -d parse_mode=HTML \
  --data-urlencode "text=🤖 <b>$AGENT_NAME deployed</b> for $BUSINESS_NAME. Try <code>/status</code> or just talk." \
  -o /dev/null
echo "OK — $AGENT_NAME live on $SSH_HOST (service=$SVC, install=$INSTALL)"
