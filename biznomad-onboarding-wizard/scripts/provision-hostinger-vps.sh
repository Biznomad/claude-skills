#!/bin/bash
# biznomad-onboarding-wizard / provision-hostinger-vps.sh
# Automates the Hostinger API VPS provisioning that we did manually for Vicelle.
#
# Usage:
#   HOSTINGER_TOKEN=xxxx bash provision-hostinger-vps.sh \
#       --hostname vicelle-vps.vicellenaturals.com \
#       --slug vicelle \
#       --ssh-pubkey ~/.ssh/id_ed25519.pub
#
# Env required:  HOSTINGER_TOKEN
# Flags:         --hostname (FQDN required by Hostinger)
#                --slug (used in cred file path: ~/.{slug}/vps-credentials.txt)
#                --ssh-pubkey (path to .pub key to install on VPS for root SSH)
#                --template-id (default: 1189 — Ubuntu 24.04 with Claude Code)
#                --dc-id (default: 24 — Boston 2, closest to US ET)
#                --vps-id (default: pick first VPS in state=initial)

set -euo pipefail

# ──────────── parse args ────────────
TEMPLATE_ID=1189
DC_ID=24
HOSTNAME=""
SLUG=""
SSH_PUBKEY="$HOME/.ssh/id_ed25519.pub"
VPS_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hostname)    HOSTNAME="$2"; shift 2 ;;
    --slug)        SLUG="$2"; shift 2 ;;
    --ssh-pubkey)  SSH_PUBKEY="$2"; shift 2 ;;
    --template-id) TEMPLATE_ID="$2"; shift 2 ;;
    --dc-id)       DC_ID="$2"; shift 2 ;;
    --vps-id)      VPS_ID="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -z "${HOSTINGER_TOKEN:-}" ]] && { echo "❌ HOSTINGER_TOKEN env required"; exit 1; }
[[ -z "$HOSTNAME" ]] && { echo "❌ --hostname required (must be FQDN like client-vps.theirdomain.com)"; exit 1; }
[[ -z "$SLUG"     ]] && { echo "❌ --slug required"; exit 1; }
[[ ! -f "$SSH_PUBKEY" ]] && { echo "❌ SSH pubkey not found at $SSH_PUBKEY"; exit 1; }

# Slug validator (codex hi#4)
if ! [[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]{0,30}$ ]]; then
  echo "❌ Invalid slug '$SLUG' — must be lowercase alphanumeric + hyphens"; exit 1
fi
# Hostname validator (FQDN format)
if ! [[ "$HOSTNAME" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$ ]]; then
  echo "❌ Hostname '$HOSTNAME' isn't a valid FQDN format"; exit 1
fi

# Portable ISO timestamp helper (codex hi#3 — date -Iseconds is GNU-only)
iso_now() { date +"%Y-%m-%dT%H:%M:%S%z"; }

# Move Hostinger token from curl argv to a header file (codex medium#1 — token visible in `ps`)
TOKEN_HEADER=$(mktemp)
chmod 600 "$TOKEN_HEADER"
echo "Authorization: Bearer $HOSTINGER_TOKEN" > "$TOKEN_HEADER"
trap 'rm -f "$TOKEN_HEADER"' EXIT

# ──────────── find VPS to provision ────────────
if [[ -z "$VPS_ID" ]]; then
  echo "═══ Discovering Hostinger VPS list ═══"
  curl -s -H @"$TOKEN_HEADER" \
    "https://developers.hostinger.com/api/vps/v1/virtual-machines" \
    -o /tmp/hostinger-vps-list.json
  VPS_ID=$(python3 -c "
import json
d = json.load(open('/tmp/hostinger-vps-list.json'))
items = d if isinstance(d, list) else d.get('data', d.get('items', []))
initial = [vm for vm in items if vm.get('state') == 'initial']
if not initial:
    print('NO_INITIAL_VPS')
else:
    print(initial[0].get('id'))
")
  if [[ "$VPS_ID" == "NO_INITIAL_VPS" ]]; then
    echo "❌ No VPS in 'initial' state. Available VPS:"
    python3 -c "
import json
d = json.load(open('/tmp/hostinger-vps-list.json'))
items = d if isinstance(d, list) else d.get('data', d.get('items', []))
for vm in items:
    print(f\"  id={vm.get('id')} state={vm.get('state')} hostname={vm.get('hostname')}\")
"
    echo ""
    echo "Provision a new VPS in hPanel first, OR pass --vps-id to use a specific one."
    exit 1
  fi
  echo "Using VPS id=$VPS_ID (state=initial)"
fi

# ──────────── generate passwords ────────────
# Allowed specials:  root → -().&@?#;,+   |   panel → #%+:?@
# Intersection (safe for both):  # + ? @
ROOT_PWD=$(python3 -c "
import secrets, string
chars = string.ascii_letters + string.digits + '#+?@'
while True:
    pwd = ''.join(secrets.choice(chars) for _ in range(32))
    if (any(c.isupper() for c in pwd) and any(c.islower() for c in pwd)
        and any(c.isdigit() for c in pwd) and any(c in '#+?@' for c in pwd)):
        print(pwd); break
")
PANEL_PWD=$(python3 -c "
import secrets, string
chars = string.ascii_letters + string.digits + '#+?@'
while True:
    pwd = ''.join(secrets.choice(chars) for _ in range(28))
    if (any(c.isupper() for c in pwd) and any(c.islower() for c in pwd)
        and any(c.isdigit() for c in pwd) and any(c in '#+?@' for c in pwd)):
        print(pwd); break
")
SSH_PUB=$(head -1 "$SSH_PUBKEY")

# ──────────── fire setup ────────────
echo ""
echo "═══ Provisioning VPS $VPS_ID ═══"
echo "  Hostname:     $HOSTNAME"
echo "  Template:     $TEMPLATE_ID"
echo "  Data center:  $DC_ID"
echo "  SSH key:      ${SSH_PUBKEY##*/} (only public key, never private)"
echo ""

# Build setup JSON via env vars (codex crit#3 — no shell interpolation into Python source)
HOSTINGER_TEMPLATE_ID="$TEMPLATE_ID" \
HOSTINGER_DC_ID="$DC_ID" \
HOSTINGER_ROOT_PWD="$ROOT_PWD" \
HOSTINGER_PANEL_PWD="$PANEL_PWD" \
HOSTINGER_HOSTNAME="$HOSTNAME" \
HOSTINGER_SSH_PUB="$SSH_PUB" \
HOSTINGER_KEY_NAME="biznomad-onboarding-$(date +%s)" \
python3 - > /tmp/hostinger-setup.json <<'PY'
import os, json
print(json.dumps({
  "template_id": int(os.environ["HOSTINGER_TEMPLATE_ID"]),
  "data_center_id": int(os.environ["HOSTINGER_DC_ID"]),
  "password": os.environ["HOSTINGER_ROOT_PWD"],
  "panel_password": os.environ["HOSTINGER_PANEL_PWD"],
  "hostname": os.environ["HOSTINGER_HOSTNAME"],
  "public_key": {
    "name": os.environ["HOSTINGER_KEY_NAME"],
    "key": os.environ["HOSTINGER_SSH_PUB"],
  }
}))
PY
chmod 600 /tmp/hostinger-setup.json

HTTP=$(curl -s -X POST \
  -H @"$TOKEN_HEADER" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d @/tmp/hostinger-setup.json \
  "https://developers.hostinger.com/api/vps/v1/virtual-machines/$VPS_ID/setup" \
  -o /tmp/hostinger-setup-resp.json -w "%{http_code}")

if [[ "$HTTP" != "200" ]]; then
  echo "❌ Provisioning request rejected (HTTP $HTTP):"
  python3 -c "import json; print(json.dumps(json.load(open('/tmp/hostinger-setup-resp.json')), indent=2))" 2>/dev/null || cat /tmp/hostinger-setup-resp.json
  rm /tmp/hostinger-setup.json
  exit 1
fi
rm /tmp/hostinger-setup.json
echo "✓ Provisioning request accepted (HTTP 200)"

# ──────────── save creds ────────────
mkdir -p "$HOME/.$SLUG"
chmod 700 "$HOME/.$SLUG"
cat > "$HOME/.$SLUG/vps-credentials.txt" <<EOF
$SLUG VPS — credentials (provisioned $(iso_now))
─────────────────────────────────────────
VPS ID:           $VPS_ID
Hostname:         $HOSTNAME
Template:         id=$TEMPLATE_ID (Ubuntu 24.04 with Claude Code)
Data center:      id=$DC_ID (Boston 2 by default)

Root password:    $ROOT_PWD
Panel password:   $PANEL_PWD
SSH key:          $SSH_PUBKEY

➡ Move both passwords to Bitwarden ("$SLUG VPS")
➡ Delete this file after move: rm $HOME/.$SLUG/vps-credentials.txt
EOF
chmod 600 "$HOME/.$SLUG/vps-credentials.txt"
echo "✓ Credentials saved to $HOME/.$SLUG/vps-credentials.txt (chmod 600)"

# ──────────── poll until running with IPv4 ────────────
echo ""
echo "═══ Waiting for state=running + IPv4 (max 3 min) ═══"
IPV4=""
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  sleep 15
  curl -s -H @"$TOKEN_HEADER" \
    "https://developers.hostinger.com/api/vps/v1/virtual-machines/$VPS_ID" \
    -o /tmp/hostinger-poll.json
  read -r STATE IPV4 < <(python3 -c "
import json
d = json.load(open('/tmp/hostinger-poll.json'))
state = d.get('state', '-')
ip = d.get('ipv4')
if isinstance(ip, list) and ip:
    ip = ip[0].get('address') if isinstance(ip[0], dict) else ip[0]
ip = ip or '-'
print(state, ip)
")
  printf "  poll #%-2d  state=%-12s ipv4=%s\n" "$i" "$STATE" "$IPV4"
  if [[ "$STATE" == "running" && "$IPV4" != "-" && "$IPV4" != "None" ]]; then
    echo ""
    echo "✓ VPS is running at $IPV4"
    break
  fi
done

if [[ -z "$IPV4" || "$IPV4" == "-" ]]; then
  echo "⚠ Timed out waiting. Check hPanel manually. VPS_ID=$VPS_ID"
  exit 2
fi

# ──────────── add SSH alias ────────────
if ! grep -q "^Host $SLUG$" "$HOME/.ssh/config" 2>/dev/null; then
  printf "\nHost %s\n  HostName %s\n  User root\n  IdentityFile %s\n  StrictHostKeyChecking accept-new\n" \
    "$SLUG" "$IPV4" "${SSH_PUBKEY%.pub}" >> "$HOME/.ssh/config"
  echo "✓ Added '$SLUG' SSH alias (now: ssh $SLUG)"
fi

# ──────────── output for caller ────────────
echo ""
echo "═══ PROVISIONED ══════════════════════════════════════"
echo "  VPS_ID=$VPS_ID"
echo "  IPV4=$IPV4"
echo "  SSH_ALIAS=$SLUG"
echo "  CRED_FILE=$HOME/.$SLUG/vps-credentials.txt"
echo "═════════════════════════════════════════════════════"

# Write machine-readable summary the wizard can consume
cat > "$HOME/.$SLUG/vps-info.json" <<EOF
{
  "vps_id": $VPS_ID,
  "ipv4": "$IPV4",
  "hostname": "$HOSTNAME",
  "ssh_alias": "$SLUG",
  "ssh_target": "root@$IPV4",
  "cred_file": "$HOME/.$SLUG/vps-credentials.txt",
  "provisioned_at": "$(iso_now)"
}
EOF
chmod 600 "$HOME/.$SLUG/vps-info.json"
