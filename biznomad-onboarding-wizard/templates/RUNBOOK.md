# {{CLIENT_NAME}} — AI Team Runbook

The technical reference guide. Bookmark this. You won't need it often, but when you do, you'll be grateful it's here.

---

## Your infrastructure at a glance

| Component | Where | What it does |
|---|---|---|
| Your VPS | `{{SSH_TARGET}}` | The server that runs your bots 24/7 |
| Hermes | `/root/.hermes/` | The AI agent framework powering your bots |
| Your bot profiles | `/root/.hermes/profiles/{{SLUG}}-*` | One folder per bot — persona, memory, sessions |
| Shared team memory | `/root/.hermes/shared/{{SLUG}}/` | Where bots write notes for each other |
| Kanban board | `/root/.hermes/kanban/boards/{{SLUG}}/` | Task board the team uses to coordinate |
| 183 specialist agents | `/root/.claude/agents/` | The deep bench |
| Monitoring scaffold | `/opt/{{SLUG}}-monitors/` | Tier-1 ad health monitors (timers off until configured) |
| Tier-1 config | `/etc/{{SLUG}}-monitors.env` | Where API tokens go to enable monitoring |

---

## Common operations

### 🔁 Restart a bot that's not responding

```bash
ssh {{SSH_TARGET}}
systemctl restart hermes-gateway-{{SLUG}}-ops.service
# Same pattern: -social, -marketing, -intel
```

Then check status:
```bash
systemctl status hermes-gateway-{{SLUG}}-ops.service
journalctl -u hermes-gateway-{{SLUG}}-ops.service -n 50 --no-pager
```

### 👀 See what a bot has been doing

```bash
# Last 50 actions of any bot:
journalctl -u hermes-gateway-{{SLUG}}-social.service -n 50 --no-pager

# What's in the bot's shared notes:
cat /root/.hermes/shared/{{SLUG}}/social.md
```

### 🧠 Reset a bot's conversation memory (start fresh)

In Telegram, DM the bot: `/reset`

(This is intentional — you can reset any bot anytime without losing the team's shared memory or kanban tasks. Only that bot's recent conversation context clears.)

### 🔑 Rotate API keys

When you change your Kimi API key (or any API key):

```bash
ssh {{SSH_TARGET}}
nano /root/.hermes/.env
# Edit the KIMI_API_KEY line, save
systemctl restart hermes-gateway-{{SLUG}}-ops.service hermes-gateway-{{SLUG}}-social.service \
                  hermes-gateway-{{SLUG}}-marketing.service hermes-gateway-{{SLUG}}-intel.service
```

### 👥 Add a teammate to your bot commands

By default, only the owner ({{OWNER_NAME}}) can issue commands. To add a teammate:

```bash
ssh {{SSH_TARGET}}
# Edit each bot's .env to include another Telegram user ID:
nano /root/.hermes/profiles/{{SLUG}}-ops/.env
# Change TELEGRAM_ALLOWED_USERS={{OWNER_TG_ID}} to TELEGRAM_ALLOWED_USERS={{OWNER_TG_ID}},NEW_USER_ID
# Repeat for the other 3 profiles
# Then restart that bot's service
```

To find a teammate's Telegram user ID: have them DM `@userinfobot` from their phone, copy the ID.

### 🎯 Enable Tier-1 monitoring (ad spend protection)

This is the killer feature for businesses running paid ads. By default the scaffold is in place but disabled until you provide credentials.

```bash
ssh {{SSH_TARGET}}
nano /etc/{{SLUG}}-monitors.env
# Fill in the 6 __FILL_IN__ placeholders:
#   {{SLUG_UPPER}}_SHOPIFY_ADMIN_TOKEN
#   {{SLUG_UPPER}}_META_ACT_ID
#   {{SLUG_UPPER}}_META_PIXEL_ID
#   {{SLUG_UPPER}}_META_ACCESS_TOKEN
#   {{SLUG_UPPER}}_OPS_BOT_TOKEN  (already in /root/.hermes/profiles/{{SLUG}}-ops/.env)
#   {{SLUG_UPPER}}_TEAM_CHAT_ID

# Then enable the timers:
systemctl enable --now {{SLUG}}-pixel-watcher.timer \
                       {{SLUG}}-meta-monitor.timer \
                       {{SLUG}}-checkout-monitor.timer \
                       {{SLUG}}-attribution.timer
```

Now your team gets a Telegram alert within 30 minutes if your Meta Pixel breaks, your ad spend spikes, or your checkout funnel drops.

### 🗄 Back up your bots

The bot state lives in `/root/.hermes/profiles/`. To back up:

```bash
ssh {{SSH_TARGET}}
tar czf /root/{{SLUG}}-backup-$(date +%Y%m%d).tgz /root/.hermes/profiles/{{SLUG}}-* /root/.hermes/shared/{{SLUG}} /root/.hermes/kanban/boards/{{SLUG}}
# Move to your local machine:
scp {{SSH_TARGET}}:/root/{{SLUG}}-backup-*.tgz ~/backups/
```

Do this monthly. Or set up an automated rsync to a backup VPS.

---

## Troubleshooting

### "My bot isn't responding in Telegram"

1. Check service is running: `systemctl is-active hermes-gateway-{{SLUG}}-ops.service`
2. Check token still valid: `journalctl -u hermes-gateway-{{SLUG}}-ops.service -n 20 | grep -i "unauthorized\|invalid\|conflict"`
3. Restart: `systemctl restart hermes-gateway-{{SLUG}}-ops.service`
4. If still nothing, the bot's Telegram token may have been revoked. Get a new one from @BotFather and update the .env.

### "My bot is saying weird things / drifting from voice"

1. Open the bot's SOUL.md: `cat /root/.hermes/profiles/{{SLUG}}-social/SOUL.md`
2. The "Personality" or "Brand voice" section is the source of truth
3. Edit any line that's no longer accurate
4. Restart that bot
5. Send the bot `/reset` in Telegram to start a fresh conversation

### "A bot tried to do something I didn't approve"

Find what happened:
```bash
journalctl -u hermes-gateway-{{SLUG}}-{ops,social,marketing,intel}.service --since "1 hour ago" | grep -iE "approval|tool|action"
```

Then add to that bot's SOUL.md under "Boundaries":
```
- DO NOT [the thing it did wrong] without explicit owner approval
```

Restart. The bot will respect the new rule.

### "The whole VPS is down"

1. Check Hostinger panel — VPS state should be "running"
2. If down, restart it from the panel
3. After it comes back up, your services will auto-start (they're set to start on boot)

If the VPS is up but you can't SSH in, you may have changed the SSH config wrong. Use Hostinger's panel VNC console.

---

## Cost expectations

Your monthly costs roughly break down:

| Item | Approx cost | Why |
|---|---|---|
| Hostinger VPS (KVM 4) | ~$15/mo | The server |
| Kimi API tokens | $30–80/mo | Bot conversations + agent calls |
| Telegram bots | $0 | Free forever |
| Domain (optional) | $10–15/yr | If you point a hostname to the VPS |
| Backups | $0–5/mo | If you use rsync to a second VPS |

Compare to a part-time agency: $2K–10K/mo. Your team is significantly cheaper AND doesn't take vacation.

---

## When to call Biznomad for help

✅ **Call us when:**
- You want to add a new specialist agent type we don't have yet
- You want a new integration (Slack, Discord, custom API)
- Your business needs are evolving and you want to upgrade your team's personas
- Something genuinely broken that you can't fix from this runbook

🚫 **Don't call us for:**
- Bot says something off-brand → just edit SOUL.md
- Want to add a teammate → see "Add a teammate" above
- Daily ops decisions → that's literally what your bots are for

---

## What's next on your roadmap

After ~30 days of using the team, you'll start to see:
- Patterns in what specialists get called most → those become "core team members"
- Patterns in what you wish your team could do → tell us, we'll build it
- Specific workflows your business needs → we'll codify them as recurring scheduled actions

Schedule a 30-day check-in with Biznomad. We'll review the team's first month and tune the personas based on what worked.

---

*Generated {{GENERATED_AT}}. Lives at `/root/.hermes/shared/{{SLUG}}/RUNBOOK.md`. Bookmark a local copy: `scp {{SSH_TARGET}}:/root/.hermes/shared/{{SLUG}}/RUNBOOK.md ~/Desktop/`*
