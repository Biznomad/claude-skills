---
name: biznomad-ops-manager
description: Deploy a per-business AI operations manager bot to a server with full admin access behind a Telegram approval gate. Conversational, runs commands on owner's behalf, daily KPI digests. Reusable across Biznomad client businesses.
---

# biznomad-ops-manager

Deploy a NaReem-style **AI operations manager** for any small business:

- Conversational Telegram bot (Kimi K2.6 brain by default)
- Full admin (shell, file, systemctl) on the business's server
- Inline-button approval gate for any state-changing action
- Daily KPI digest to owner group chat
- Reads/writes business data files (leads, jobs, quotes, customers, invoices)

**Reference deployment:** NaReem for Two & Through Junk Removal on TNT (187.77.204.166).

## Per-business inputs you need

Before deploying, collect these into a business config (`businesses/<slug>.json`):

```json
{
  "slug": "tnt",
  "agent_name": "NaReem",
  "business_name": "Two & Through Junk Removal",
  "server_ssh": "tnt",
  "jump_host": "root@187.77.10.20",
  "telegram_bot_token": "8720224642:AAG...",
  "telegram_group_id": -5207375121,
  "admin_telegram_ids": [5165464044],
  "kimi_api_key": "Aao9AU9R...",
  "kimi_base": "https://api.kimi.com/coding/v1",
  "kimi_model": "kimi-for-coding",
  "kimi_user_agent": "claude-code/1.0",
  "data_dir": "/root/two-and-through-ops/data",
  "config_file": "/root/two-and-through-ops/config/business.json",
  "install_dir": "/root/nareem",
  "service_name": "nareem-bot",
  "mission": "30-day sprint to ramp from 2–3 calls to 24/7 truck running",
  "daily_ad_cap": 100
}
```

## Deploy flow

1. **Provision Telegram bot** with @BotFather. Add to owner group, disable privacy mode.
2. **Verify Kimi key** with a test curl (must use `claude-code/1.0` User-Agent + `sk-kimi-` prefix).
3. **Render templates** with the business config:
   - `templates/ops_bot.py` → `<install_dir>/ops_bot.py`
   - `templates/ops-bot.service` → `/etc/systemd/system/<service_name>.service`
   - `templates/env.template` → `<install_dir>/.env`
4. **SCP** to server via jump host. Install Python deps: `python-telegram-bot httpx`.
5. **Enable + start** the systemd service.
6. **Post boot message** to group, confirm bot responds to `/status`.
7. **Optional:** daily digest cron — `0 13 * * * curl -s -X POST ... /sendMessage` (8am ET).

The bot file (`ops_bot.py`) is a single self-contained Python module. Copy from `templates/ops_bot.py` and replace nothing — all config comes from environment variables (the `.env` file).

## Capability matrix (out-of-the-box)

| Action type    | Approval? | What it does                                  |
|----------------|-----------|-----------------------------------------------|
| `read_file`    | auto      | read any file under 200KB                     |
| `list_dir`     | auto      | list a directory                              |
| `status_kpi`   | auto      | counts from data/{leads,jobs,quotes,invoices} |
| `post_summary` | auto      | post message to group                         |
| `shell`        | ✅ gate   | arbitrary shell command (60s timeout)         |
| `write_file`   | ✅ gate   | write/replace file                            |
| `restart_svc`  | ✅ gate   | systemctl restart                             |
| `stop_svc`     | ✅ gate   | systemctl stop                                |
| `start_svc`    | ✅ gate   | systemctl start                               |
| `append_data`  | ✅ gate   | append record to data/*.json                  |

State-changing actions post a Telegram inline-button card; only `admin_telegram_ids` can tap **✅ Approve / ❌ Reject**.

## Commands the bot exposes

- `/status` — KPI dashboard (leads/quotes/jobs/invoices/revenue)
- `/leads` — last 5 leads
- `/jobs` — upcoming jobs
- `/spend` — ad spend + CPL
- `/pending` — open approval queue
- `/help` — menu
- Plain text → Kimi K2.6, conversational, can propose actions

## Daily digest (optional but recommended)

Cron at 13:00 UTC (8am ET) calls Telegram sendMessage with a status summary built from `/root/<install_dir>/spend.json` + the business data files. See `templates/daily_digest.sh`.

## Files in this skill

```
biznomad-ops-manager/
├── SKILL.md                      # this file
├── templates/
│   ├── ops_bot.py                # the bot — copy as-is, env-driven
│   ├── ops-bot.service           # systemd unit (vars: {{install_dir}}, {{service_name}})
│   ├── env.template              # .env shape
│   ├── system-prompt.md          # persona base — extend per business
│   └── daily_digest.sh           # optional cron script
├── businesses/                   # per-deployment configs (commit-ignored)
│   └── tnt.json                  # Two & Through Junk Removal
└── deploy.sh                     # one-shot rollout (renders + scp + systemctl)
```

## Deploying for a new business — checklist

1. Create `businesses/<slug>.json` from the schema above.
2. Run `bash deploy.sh businesses/<slug>.json` (renders + ships).
3. In Telegram group, send `/status` — verify response.
4. Ask the bot: "what data do we have?" — verify it can read files.
5. Ask the bot: "kill the unused-service X" — verify it posts an approval card.
6. Approve the card — verify execution + result posted.
7. If all 6 pass: deployment is green. Else inspect `journalctl -u <service_name>`.

## Known gotchas

- **Kimi coding endpoint requires `claude-code/1.0` User-Agent** — without it you get `access_terminated_error: only available for Coding Agents`.
- **`response_format: json_object` is recommended** for reliable action parsing. Salvage logic handles markdown fences if it leaks.
- **Don't run with privacy mode ON** in BotFather — the bot won't see group messages.
- **`max_tokens` ≥ 4096** for Kimi coding — model uses reasoning_content tokens that count against the budget.
- **Group ID is negative** for groups, positive for DMs.
- **Approvals expire on restart** (pending.json is preserved but action_id refs may be stale if message edits). Re-propose if expired.
