---
name: system-stress-test
description: "Stress test all systems — spawns parallel agents to find bugs across n8n, Telegram, Shopify, Meta Ads, websites, VPS health, Netlify sites, and API tokens. Use when user says 'stress test', 'find bugs', 'health check', 'system audit', 'check all systems', 'is everything working', 'run diagnostics', or 'status report'."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, TaskCreate, TaskGet, TaskList, TaskUpdate
---

# System Stress Test

You are a systems reliability engineer for Biznomad. Your job is to run non-destructive health checks across every active system and produce a clear, actionable health report.

## Before Starting

1. Read the project-level `CLAUDE.md` if running from a client directory — respect project isolation.
2. Determine which systems to test based on the current scope (see System Registry below).
3. If the user says "all systems" or just "stress test", run every check in the registry.
4. If the user names specific systems, run only those.

## Execution Strategy

Run checks in parallel using the `TaskCreate` tool with `subagent_type`. Each system gets its own subagent so failures in one do not block others. After all subagents complete, aggregate results into the health report.

**Parallelism pattern:**
- Create one task per system category (VPS, n8n, Telegram, Shopify, Meta Ads, Websites, Netlify, API Tokens)
- Each task runs independently
- Poll tasks until all complete
- Aggregate into final report

If the `TaskCreate` tool is unavailable or subagents are not supported in the current session, fall back to running each check sequentially via Bash. The checks themselves are just shell commands — they work either way.

## System Registry

Each system has a set of checks. All checks are **read-only** and **non-destructive** unless explicitly noted.

---

### 1. VPS Health (187.77.10.20 — Biznomad Main VPS)

**SSH command prefix:** `ssh root@187.77.10.20`

| Check | Command | OK | WARN | FAIL |
|-------|---------|-----|------|------|
| Disk usage | `df -h / \| tail -1` | <70% | 70-90% | >90% |
| Memory usage | `free -m \| grep Mem` | <80% used | 80-95% | >95% |
| CPU load (1m) | `cat /proc/loadavg` | <2.0 | 2.0-4.0 | >4.0 |
| Uptime | `uptime -p` | >1 day | <1 day | down |
| Docker containers | `docker ps --format '{{.Names}}\t{{.Status}}'` | All Up | Any restarting | Any exited |
| Zombie processes | `ps aux \| grep -c defunct` | 0 | 1-5 | >5 |
| Open files | `cat /proc/sys/fs/file-nr` | <50% max | 50-80% | >80% |
| Swap usage | `free -m \| grep Swap` | <20% | 20-50% | >50% |

**Additional VPS services to check:**
```bash
# Systemd services
for svc in n8n ghl-webhook dental-guardrails hv-telegram-bot nicole-bridge; do
  systemctl is-active "$svc" 2>/dev/null || echo "MISSING: $svc"
done

# Docker containers expected
docker ps --format '{{.Names}}' | sort
# Expected: openclaw-wu3j-openclaw-1 (and any client containers)

# Disk breakdown (top consumers)
du -sh /root/* /opt/* /data/* 2>/dev/null | sort -rh | head -10

# Check for stale PID files or lock files
find /tmp /var/run -name '*.lock' -mmin +1440 2>/dev/null
```

---

### 2. VPS Health (76.13.111.134 — Vitalis/Nicole VPS)

**SSH command prefix:** `ssh root@76.13.111.134`

| Check | Command | OK | WARN | FAIL |
|-------|---------|-----|------|------|
| Disk usage | `df -h / \| tail -1` | <70% | 70-90% | >90% |
| Memory usage | `free -m \| grep Mem` | <80% used | 80-95% | >95% |
| CPU load (1m) | `cat /proc/loadavg` | <2.0 | 2.0-4.0 | >4.0 |
| Docker containers | `docker ps --format '{{.Names}}\t{{.Status}}'` | All Up | Any restarting | Any exited |
| n8n service | `systemctl is-active n8n` | active | — | inactive/failed |
| Telegram bot | `systemctl is-active hv-telegram-bot` | active | — | inactive/failed |
| Nicole bridge | `systemctl is-active nicole-bridge` | active | — | inactive/failed |
| Google Flow session | `ls -la /opt/n8n/chrome-profile/Default/Cookies 2>/dev/null` | <24h old | 24-72h | >72h or missing |
| noVNC | `curl -s -o /dev/null -w '%{http_code}' http://localhost:6080/vnc.html` | 200 | — | not 200 |

---

### 3. n8n Workflows

**n8n API base:** `http://76.13.111.134:5678/api/v1`
**API key:** Read from VPS env or use stored key: `n8n_api_7e3660044d8f8c3b8a42c0224640911234755d6c9dddf362`

```bash
# Check n8n is responding
ssh root@76.13.111.134 'curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/healthz'

# List active workflows
ssh root@76.13.111.134 'curl -s -H "X-N8N-API-KEY: n8n_api_7e3660044d8f8c3b8a42c0224640911234755d6c9dddf362" http://localhost:5678/api/v1/workflows | python3 -c "
import sys, json
data = json.load(sys.stdin)
workflows = data.get(\"data\", [])
for w in workflows:
    status = \"ACTIVE\" if w.get(\"active\") else \"INACTIVE\"
    print(f\"  {status}: {w.get(\"name\", \"unnamed\")} (ID: {w.get(\"id\", \"?\")})\"  )
print(f\"Total: {len(workflows)} workflows\")
"'

# Check recent executions for errors (last 20)
ssh root@76.13.111.134 'curl -s -H "X-N8N-API-KEY: n8n_api_7e3660044d8f8c3b8a42c0224640911234755d6c9dddf362" "http://localhost:5678/api/v1/executions?limit=20" | python3 -c "
import sys, json
data = json.load(sys.stdin)
execs = data.get(\"data\", [])
errors = [e for e in execs if e.get(\"status\") == \"error\" or e.get(\"finished\") == False]
successes = [e for e in execs if e.get(\"status\") == \"success\"]
print(f\"Last 20 executions: {len(successes)} success, {len(errors)} errors\")
for e in errors[:5]:
    print(f\"  ERROR: {e.get(\"workflowData\", {}).get(\"name\", \"?\")} at {e.get(\"startedAt\", \"?\")}\")
"'
```

| Check | OK | WARN | FAIL |
|-------|-----|------|------|
| n8n responding | HTTP 200 | slow (>2s) | not responding |
| Active workflows | >0 active | 0 active | API error |
| Recent errors | 0 errors in last 20 | 1-3 errors | >3 errors |

---

### 4. Telegram Bots

#### @hv_content_engine_bot (Holistic Vitalis)
**Token:** `8755194695:AAEZ_E-c6tUQcWOkq3LBQZf6DiBlPOPL6C8`

```bash
# Check bot info
curl -s "https://api.telegram.org/bot8755194695:AAEZ_E-c6tUQcWOkq3LBQZf6DiBlPOPL6C8/getMe" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if r.get('ok'):
    bot = r['result']
    print(f\"Bot: @{bot.get('username')} ({bot.get('first_name')})\")
else:
    print(f\"FAIL: {r.get('description', 'unknown error')}\")
"

# Check webhook status
curl -s "https://api.telegram.org/bot8755194695:AAEZ_E-c6tUQcWOkq3LBQZf6DiBlPOPL6C8/getWebhookInfo" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if r.get('ok'):
    info = r['result']
    url = info.get('url', '')
    pending = info.get('pending_update_count', 0)
    last_err = info.get('last_error_message', '')
    if url:
        print(f\"Webhook: {url}\")
    else:
        print(f\"Webhook: NOT SET (using polling)\")
    print(f\"Pending updates: {pending}\")
    if last_err:
        print(f\"Last error: {last_err}\")
"

# Check for pending updates (only if polling mode)
curl -s "https://api.telegram.org/bot8755194695:AAEZ_E-c6tUQcWOkq3LBQZf6DiBlPOPL6C8/getUpdates?limit=1&offset=-1" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if r.get('ok'):
    updates = r.get('result', [])
    print(f\"Recent updates: {len(updates)}\")
"
```

| Check | OK | WARN | FAIL |
|-------|-----|------|------|
| Bot reachable | getMe succeeds | — | getMe fails |
| Webhook/Polling | Configured and no errors | Pending >10 | Last error present |
| Service running | systemctl active | — | inactive/failed |

---

### 5. Shopify Stores

Test each store's Storefront API and admin access. Use `curl` with the store domain.

```bash
# For each store, check if the storefront is responding
for store in "zrwwbj-jq.myshopify.com" "biznomad.myshopify.com"; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "https://$store")
  echo "$store: HTTP $status"
done

# Check Vicelle Shopify via local MCP (if available)
# The MCP tool vicelle-klaviyo should be able to verify connectivity
```

| Check | OK | WARN | FAIL |
|-------|-----|------|------|
| Storefront HTTP | 200/301 | 403 | 5xx/timeout |
| Admin API | Authenticated | Rate limited | 401/403 |
| Theme status | Published theme exists | — | No published theme |
| Products live | >0 active products | 0 products | API error |

**Note:** Admin API checks require store-specific access tokens. If tokens are not available in the current session, skip admin checks and report storefront HTTP status only.

---

### 6. Meta Ads

#### Dental Campaign (act_930457189958096)
#### Biznomad Account (act_327886216331270)

```bash
# Test Meta API token validity
# Token is session-dependent — check if META_ACCESS_TOKEN is set
if [ -n "$META_ACCESS_TOKEN" ]; then
  curl -s "https://graph.facebook.com/v21.0/me?access_token=$META_ACCESS_TOKEN" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if 'error' in r:
    print(f\"FAIL: {r['error'].get('message', 'unknown')}\")
else:
    print(f\"Token valid: {r.get('name', 'unknown user')}\")
"
else
  echo "SKIP: META_ACCESS_TOKEN not set in environment"
fi

# If token available, check campaign status
# curl -s "https://graph.facebook.com/v21.0/act_930457189958096/campaigns?fields=name,status,daily_budget&access_token=$META_ACCESS_TOKEN"

# If token available, pull today's spend
# curl -s "https://graph.facebook.com/v21.0/act_930457189958096/insights?date_preset=today&fields=spend,impressions,clicks,cpc&access_token=$META_ACCESS_TOKEN"
```

| Check | OK | WARN | FAIL |
|-------|-----|------|------|
| Token validity | Valid | Expires <7 days | Expired/invalid |
| Campaign status | ACTIVE | PAUSED | ERROR/disabled |
| Today's spend | Within budget | >120% budget | $0 (if should be active) |
| Anomalies | Normal CPC/CTR | CPC >2x avg | No impressions |

**Note:** Meta tokens are often short-lived. If the token is expired, report it as FAIL with instructions to generate a new one via Business Settings > System Users.

---

### 7. Websites & Netlify Sites

Check HTTP status, response time, and SSL for all known sites.

```bash
check_site() {
  local url="$1"
  local label="$2"
  local start=$(python3 -c "import time; print(time.time())")
  local status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url")
  local end=$(python3 -c "import time; print(time.time())")
  local elapsed=$(python3 -c "print(f'{$end - $start:.2f}')")
  echo "$label|$url|$status|${elapsed}s"
}

# Biznomad properties
check_site "https://biznomad.io" "Biznomad Homepage"
check_site "https://dentist.biznomad.io" "Dental Landing Page"
check_site "https://dentist.biznomad.io/privacy" "Dental Privacy Policy"

# Client sites (Netlify)
check_site "https://vicelle-dashboard.netlify.app" "Vicelle Dashboard"
check_site "https://dlluxe-scrubs.netlify.app" "DLluxe Scrubs Website"
check_site "https://dlluxe-dashboard.netlify.app" "DLluxe Dashboard"

# Vitalis
check_site "https://holisticvitalis.com" "Holistic Vitalis Storefront"
```

| Check | OK | WARN | FAIL |
|-------|-----|------|------|
| HTTP status | 200 | 301/302 (redirect) | 4xx/5xx/timeout |
| Response time | <1s | 1-3s | >3s |
| SSL valid | Valid >30d | Expires <30d | Expired/invalid |

**SSL check command:**
```bash
check_ssl() {
  local domain="$1"
  local expiry=$(echo | openssl s_client -servername "$domain" -connect "$domain":443 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
  if [ -n "$expiry" ]; then
    local expiry_epoch=$(date -j -f "%b %d %H:%M:%S %Y %Z" "$expiry" "+%s" 2>/dev/null || date -d "$expiry" "+%s" 2>/dev/null)
    local now_epoch=$(date "+%s")
    local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
    echo "$domain: SSL expires in ${days_left} days ($expiry)"
  else
    echo "$domain: SSL check failed"
  fi
}

check_ssl "biznomad.io"
check_ssl "dentist.biznomad.io"
check_ssl "holisticvitalis.com"
check_ssl "vicelle-dashboard.netlify.app"
```

---

### 8. API Token & Credential Validity

Quick validation of stored API tokens and credentials.

```bash
# Google API Key (free tier, text-gen only)
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=AIzaSyBifKna_6ZFmxwAp0WLKG8FKYAtxlxHGB0" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if 'error' in r:
    print(f\"Google API Key: FAIL — {r['error'].get('message', '')}\")
elif 'models' in r:
    print(f\"Google API Key: OK — {len(r['models'])} models available\")
"

# ManyChat API (Vicelle)
curl -s -H "Authorization: Bearer 3854938:$(cat /Users/biznomad/Projects/Clients/Vicelle-Naturals/.env 2>/dev/null | grep MANYCHAT | cut -d= -f2 || echo 'TOKEN_NOT_FOUND')" "https://api.manychat.com/fb/page/getInfo" | python3 -c "
import sys, json
try:
    r = json.load(sys.stdin)
    if r.get('status') == 'success':
        print(f\"ManyChat: OK — {r.get('data', {}).get('name', 'connected')}\")
    else:
        print(f\"ManyChat: FAIL — {r.get('message', 'unknown')}\")
except:
    print('ManyChat: SKIP — token not available')
"

# Klaviyo (Vicelle — V8fsvS) — check via local MCP if available, otherwise skip
# Note: Do NOT use the cloud MCP Klaviyo (WXuDSN) — that's the wrong account (Holistic Vitalis)
```

| Check | OK | WARN | FAIL |
|-------|-----|------|------|
| Google API Key | Models returned | Rate limited | Invalid/revoked |
| ManyChat Token | Page info returned | Rate limited | 401/invalid |
| Klaviyo API | Account info returned | — | 401/invalid |
| Meta Token | User info returned | Expires soon | Expired |

---

### 9. Local Mac Health

Checks for the local development environment.

```bash
# Disk space
df -h / | tail -1

# Docker Desktop (if running)
docker info --format '{{.ContainersRunning}} running, {{.ContainersStopped}} stopped' 2>/dev/null || echo "Docker: not running"

# Node.js / npm
node -v 2>/dev/null && npm -v 2>/dev/null

# Python
python3 --version 2>/dev/null

# FFmpeg
ffmpeg -version 2>/dev/null | head -1

# Homebrew outdated (quick check)
brew outdated --quiet 2>/dev/null | wc -l | xargs -I{} echo "{} outdated Homebrew packages"

# Check if any dev servers are running
lsof -i :3000 -i :5173 -i :8000 -i :8080 -i :4321 -t 2>/dev/null | wc -l | xargs -I{} echo "{} dev server processes detected"
```

---

## Output Format

After all checks complete, compile the report in this exact format:

```
==========================================================
  SYSTEM HEALTH REPORT — YYYY-MM-DD HH:MM
  Tested: X systems | Duration: Xs
==========================================================

VPS 187.77.10.20 (Biznomad)
  [OK]   Disk: 45% used (18.2G/40G)
  [OK]   Memory: 2.1G/3.8G (55%)
  [OK]   Load: 0.82 (1m avg)
  [OK]   Docker: 2 containers running (openclaw, ghl-webhook)
  [WARN] Swap: 42% used
  [FAIL] Service dental-guardrails: inactive

VPS 76.13.111.134 (Vitalis/Nicole)
  [OK]   Disk: 62% used
  [OK]   Memory: 1.8G/4G (45%)
  [OK]   n8n service: active
  [WARN] Google Flow session: 3 days old — may need re-auth via noVNC
  [OK]   Telegram bot service: active
  [OK]   Nicole bridge: active

n8n Workflows
  [OK]   Server: responding (HTTP 200)
  [OK]   Workflows: 3 active, 1 inactive
  [OK]   Executions: 18/20 success, 2 errors
  [WARN] Error: "Social | Content Engine" failed at 2026-04-09 03:00

Telegram Bots
  [OK]   @hv_content_engine_bot: reachable, polling mode
  [OK]   Pending updates: 0
  [OK]   Service: active on VPS

Shopify Stores
  [OK]   zrwwbj-jq.myshopify.com (Vicelle): HTTP 200
  [OK]   biznomad.myshopify.com: HTTP 200

Meta Ads
  [FAIL] Token: expired — regenerate via Business Settings > System Users
  [SKIP] Campaign status: skipped (no valid token)
  [SKIP] Today's spend: skipped (no valid token)

Websites
  [OK]   biznomad.io: HTTP 200 (0.34s) | SSL: 89 days
  [OK]   dentist.biznomad.io: HTTP 200 (0.41s) | SSL: 89 days
  [OK]   vicelle-dashboard.netlify.app: HTTP 200 (0.22s) | SSL: auto
  [OK]   dlluxe-scrubs.netlify.app: HTTP 200 (0.18s) | SSL: auto
  [OK]   dlluxe-dashboard.netlify.app: HTTP 200 (0.19s) | SSL: auto
  [OK]   holisticvitalis.com: HTTP 200 (0.55s) | SSL: 45 days

API Tokens
  [OK]   Google API Key (Gemini): valid, 42 models
  [SKIP] ManyChat: token not in env
  [SKIP] Klaviyo: check via local MCP

Local Mac
  [OK]   Disk: 52% used (480G/1TB)
  [OK]   Node: v22.x | npm: 10.x | Python: 3.14
  [OK]   FFmpeg: 8.0.1
  [OK]   Docker Desktop: running

==========================================================
  SUMMARY: 22 OK | 3 WARN | 2 FAIL | 4 SKIP
==========================================================

ACTION ITEMS:
  1. [FAIL] Regenerate Meta Ads access token (expired)
  2. [FAIL] Restart dental-guardrails service on 187.77.10.20
  3. [WARN] Re-auth Google Flow session via noVNC (76.13.111.134:6080)
  4. [WARN] Investigate n8n workflow error in "Social | Content Engine"
  5. [WARN] VPS swap usage at 42% — consider adding memory or clearing cache
```

## Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| `[OK]` | Healthy, within normal parameters | None |
| `[WARN]` | Degraded but functional — needs attention soon | Monitor or fix within 24h |
| `[FAIL]` | Broken or critical — needs immediate fix | Fix now |
| `[SKIP]` | Could not test (missing credentials, service unavailable) | Note why and move on |

## Adding New Systems

To add a new system to the stress test, append a new section to the System Registry above with:

1. **Section header** with the system name
2. **Connection details** (SSH host, API base URL, auth method)
3. **Check table** with Command, OK/WARN/FAIL thresholds
4. **Shell commands** ready to copy-paste
5. **Update the output format** section with example entries for the new system

### Example: Adding a new Netlify site
```
# In the Websites section, add:
check_site "https://newsite.netlify.app" "New Site Name"
check_ssl "newsite.netlify.app"
```

### Example: Adding a new VPS service
```
# In the VPS section, add to the service loop:
for svc in ... new-service-name; do
  systemctl is-active "$svc" 2>/dev/null || echo "MISSING: $svc"
done
```

## Timing

Wrap the entire test in a timer:

```bash
START_TIME=$(date +%s)
# ... run all checks ...
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Total duration: ${DURATION}s"
```

Each individual check should also be timed. If any single check takes more than 15 seconds, report it as slow.

## Safety Rules

1. **Read-only** — never modify data, restart services, or change configurations during the test. Report problems; do not fix them.
2. **No secrets in output** — redact API keys, tokens, and passwords from the report. Show only the last 4 characters (e.g., `...6C8`).
3. **Timeouts** — set `--max-time 10` on all curl commands. If SSH hangs, skip after 15 seconds.
4. **Respect rate limits** — do not hammer APIs. One request per endpoint is enough.
5. **No test messages** — do not send messages to Telegram bots or post to any platform. Only read status.
6. **Project isolation** — do not mix credentials between clients. Each check uses only the credentials belonging to that system.

## Quick Reference: SSH Hosts

| Host | IP | User | Key |
|------|-----|------|-----|
| Biznomad VPS | 187.77.10.20 | root | default |
| Vitalis VPS | 76.13.111.134 | root | default |

## Quick Reference: Known Sites

| Site | URL | Platform |
|------|-----|----------|
| Biznomad Homepage | biznomad.io | Netlify + Cloudflare |
| Dental Landing | dentist.biznomad.io | Netlify + Cloudflare |
| Vicelle Dashboard | vicelle-dashboard.netlify.app | Netlify |
| DLluxe Website | dlluxe-scrubs.netlify.app | Netlify |
| DLluxe Dashboard | dlluxe-dashboard.netlify.app | Netlify |
| Holistic Vitalis | holisticvitalis.com | Shopify |
| Vicelle Shopify | zrwwbj-jq.myshopify.com | Shopify |
| Biznomad Shopify | biznomad.myshopify.com | Shopify (Plus) |
| n8n | 76.13.111.134:5678 | Self-hosted |
| noVNC | 76.13.111.134:6080 | Self-hosted |
