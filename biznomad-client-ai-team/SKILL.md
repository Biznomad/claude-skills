---
name: biznomad-client-ai-team
description: Deploy a 4-bot AI Team (ops, social, marketing, intel) on Hermes for any Biznomad client. Each agent gets a distinct Telegram bot, locked-down permissions, shared memory, and a kanban coordination board. Reusable across Vicelle, Holistic Vitalis, D'Lluxe, Liquid Wizdom, and future clients. Triggered by "deploy AI team", "set up agency bots", "onboard client to AI team", or "spin up multi-agent for {client}".
---

# biznomad-client-ai-team

Deploys a productized **4-bot AI Team** for any Biznomad client on the Biznomad VPS (187.77.10.20).
Codifies the Vicelle Naturals reference deployment as a repeatable onboarding flow.

## What you ship per client

| Agent | Role | Bot username pattern | Default model |
|---|---|---|---|
| `{slug}-ops` | Server + Shopify + GHL + revenue ops (the operator) | `@{ClientInit}_Ops_Bot` | kimi-for-coding |
| `{slug}-social` | Klaviyo + IG + brand voice (the writer) | `@{ClientInit}_Social_Bot` | kimi-for-coding |
| `{slug}-marketing` | Paid ads + performance creative (the closer) | `@{ClientInit}_Marketing_Bot` | kimi-for-coding |
| `{slug}-intel` | Competitor + market signals (the analyst) | `@{ClientInit}_Intel_Bot` | kimi-for-coding |

Plus the supporting stack:

- **Telegram team room** group with all 4 bots + owner
- **Hermes kanban** board (one per client) with the 4 profiles as assignees
- **Shared memory** dir at `/root/.hermes/shared/{slug}/` symlinked into each profile
- **Lock-down** envs on all 4 profiles (require @mention, observe off, allowed_users gate)
- **systemd units** patched to load `/root/.hermes/.env` so Kimi auth is shared

## Right-sizing by client tier

| Tier | Client size | Bots | Notes |
|---|---|---|---|
| solo | < $5K/mo | 2 — ops + marketing | Owner handles social manually |
| standard | $5K–$50K | 3 — ops + social + intel | Common starting point |
| **full** (default) | $50K+ | **4 — ops + social + marketing + intel** | Vicelle reference |
| enterprise | $250K+ | 5–6 — add compliance + retention | Custom personas |

Pass `--tier solo|standard|full|enterprise` to scale the deploy.

## Inputs you need before running

Collect these into a client config file at `clients/{slug}.json`:

```json
{
  "slug": "dlluxe",
  "client_name": "D'Lluxe Scrubs",
  "client_init": "DLS",
  "owner_name": "Owner Name",
  "owner_telegram_id": 5165464044,
  "owner_timezone": "America/New_York",
  "tier": "full",
  "brand_color_hex": "#000000",
  "brand_emoji": "👩‍⚕️",
  "vertical": "medical scrubs / apparel",
  "audience": "nurses, dental staff, medical professionals",
  "platforms": {
    "shopify_domain": "dlluxe.myshopify.com",
    "klaviyo_account_id": "xxx",
    "ghl_location": "xxx",
    "manychat": null
  },
  "fda_compliance": false,
  "telegram_bot_tokens": {
    "ops":       "<from BotFather>",
    "social":    "<from BotFather>",
    "marketing": "<from BotFather>",
    "intel":     "<from BotFather>"
  }
}
```

The Telegram tokens come from **@BotFather** — see "BotFather pre-flight" below.

## The flow (15-step playbook)

### Phase 1 — BotFather pre-flight (~10 min, manual in Telegram)

Owner does this once per bot. Skill cannot do it (BotFather has no API for creation).

1. Open `@BotFather`, send `/newbot`
2. For each role (`ops`, `social`, `marketing`, `intel`):
   - Name: `{Client} {Role} Agent` (e.g. "D'Lluxe Ops Agent")
   - Username: `{ClientInit}_{Role}_Bot` (e.g. `DLS_Ops_Bot`)
   - Save the token into the config file
3. Privacy mode (for each bot): `/mybots → {bot} → Bot Settings → Group Privacy → ENABLE`
4. Description (for each bot): `/mybots → {bot} → Edit Bot → Edit Description` → paste role-appropriate 1-liner
5. Commands list (for each bot): `/mybots → {bot} → Edit Bot → Edit Commands` → paste:
   ```
   whoami - Show bot identity + scope
   status - Current state + recent activity
   brief - Daily briefing
   shared - Show shared memory snapshot
   reset - Clear conversation context
   ```

### Phase 2 — Run provisioner (~3 min, automated)

```bash
# Local: copy your client config + run the skill
cp ~/.claude/skills/biznomad-client-ai-team/templates/client.example.json \
   ~/.claude/skills/biznomad-client-ai-team/clients/{slug}.json
# edit clients/{slug}.json with real values + 4 Telegram tokens

# Then run the provisioner over SSH on the Biznomad VPS
bash ~/.claude/skills/biznomad-client-ai-team/scripts/provision.sh {slug}
```

The script will:

- Refuse to start if token fingerprints aren't unique (Vicelle taught us — duplicate tokens = polling collision)
- Create 4 Hermes profiles via `hermes profile create {slug}-{role} --clone-from {sibling-or-default}`
- Render SOUL.md for each role from `templates/{role}.SOUL.md` with client variables substituted
- Write `.env` for each profile with the role's Telegram token + 7 lockdown env vars
- Install systemd units via `hermes -p {slug}-{role} gateway install --system --run-as-user root`
- **Patch each unit** with `EnvironmentFile=/root/.hermes/.env` (Kimi auth) — this is the bug Hermes' auto-installer doesn't handle
- Initialize the `{slug}` kanban board with brand color + emoji
- Create `/root/.hermes/shared/{slug}/` dir with brand.md + per-role files + README
- Symlink the shared dir into each profile's `memories/shared/`
- Start all 4 systemd services
- Run `verify.sh` and report

### Phase 3 — Team room setup (~5 min, manual in Telegram)

Owner creates the Telegram group:

1. New Group → name it `{Client} AI Team` (e.g. "D'Lluxe Scrubs AI Team")
2. Add: owner + 4 bots (search by username `@{ClientInit}_*_Bot`)
3. Make all 4 bots admin (optional but recommended — lets them pin messages / get full message metadata)
4. Send `/whoami` in the group — capture the chat_id from the bot's response or from journalctl

### Phase 4 — Lock the group chat (~30 sec, automated)

Once you have the chat_id:

```bash
bash ~/.claude/skills/biznomad-client-ai-team/scripts/lock-group.sh {slug} {chat_id}
```

This adds `TELEGRAM_GROUP_ALLOWED_CHATS={chat_id}` to each profile's .env and restarts them. After this, the bots will literally ignore messages from any group except the official team room.

### Phase 5 — Smoke test

In the team room, send each of these and verify the correct bot responds:

```
@{ClientInit}_Ops_Bot /whoami            → only ops responds, terse operator voice
@{ClientInit}_Social_Bot /brief          → only social responds, brand-voice tone
@{ClientInit}_Marketing_Bot /brief       → only marketing responds, performance-talk
@{ClientInit}_Intel_Bot /brief           → only intel responds, analyst tone
```

No bot should respond when a message is sent without an @-mention (privacy + REQUIRE_MENTION combined).

## Default lockdown env vars (every profile gets these)

```bash
# Per-bot
TELEGRAM_BOT_TOKEN=<unique-per-bot>

# User gate (only owner can command in DMs OR groups)
TG_ALLOWED_USER_IDS=<owner-id>
TELEGRAM_ALLOWED_USERS=<owner-id>
GATEWAY_ALLOW_ALL_USERS=false

# Group behavior
TELEGRAM_REQUIRE_MENTION=true
TELEGRAM_OBSERVE_UNMENTIONED_GROUP_MESSAGES=false
TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true

# Set in phase 4 after team room is created
TELEGRAM_GROUP_ALLOWED_CHATS=<group-chat-id>
```

## Failure modes already designed out

These are the gotchas from the Vicelle reference deployment — the scripts prevent each:

| Failure | Prevention |
|---|---|
| Two bots polling the same Telegram token | `provision.sh` SHA256-fingerprints all 4 tokens, refuses to proceed if any pair matches |
| Old systemd bot keeps respawning | Scripts use `systemctl mask` (not `disable`) when retiring old bridges |
| Auth fails with "Could not resolve authentication method" | Auto-generated systemd unit gets patched to `EnvironmentFile=/root/.hermes/.env` |
| `--dangerously-skip-permissions` error at runtime | Pure Hermes architecture — no claude-tg-bridge → no flag → no error |
| Persona drift (ops bot talks like social bot) | Strict SOUL.md template per role with "you are NOT" sections + sister-agent list |
| Bot-to-bot echo loops in the group | BotFather privacy ON + REQUIRE_MENTION=true + EXCLUSIVE_BOT_MENTIONS=true (triple gate) |

## Where things live (filesystem map for the Biznomad VPS)

```
/root/.hermes/
├── .env                                  shared keys (KIMI_API_KEY, OPENAI fallback, etc.)
├── profiles/
│   ├── {slug}-ops/                       per-bot profile + memories + SOUL + state.db
│   ├── {slug}-social/
│   ├── {slug}-marketing/
│   └── {slug}-intel/
├── shared/
│   └── {slug}/                           shared memory namespace
│       ├── README.md
│       ├── brand.md                      canonical brand facts (read-mostly)
│       ├── ops.md
│       ├── social.md
│       ├── marketing.md
│       ├── intel.md
│       └── decisions.md                  human-written strategy log
└── kanban/boards/{slug}/kanban.db        team task board

/etc/systemd/system/hermes-gateway-{slug}-{role}.service
```

## Onboarding checklist (printable)

```
☐ Verify client has CLAUDE.md project file under Projects/Clients/{ClientName}
☐ Create clients/{slug}.json from template, fill in everything except tokens
☐ Owner does Phase 1 (BotFather) — paste 4 tokens into config
☐ Run scripts/provision.sh {slug}
☐ Owner does Phase 3 (Telegram group) — share chat_id back
☐ Run scripts/lock-group.sh {slug} {chat_id}
☐ Run Phase 5 smoke tests in team room
☐ Document tokens in Bitwarden under "{Client} AI Team"
☐ Add row to ~/.claude/projects/-Users-biznomad/memory/MEMORY.md client table
☐ Commit clients/{slug}.json to a secrets vault (don't commit Telegram tokens to git)
```

## When NOT to use this skill

- Single-bot deployments → use `biznomad-ops-manager` (the older single-bot skill) instead
- Service businesses with one operator (e.g. junk removal) → `biznomad-ops-manager` is right-sized
- Internal Biznomad bots (not client-facing) → use `master-gateway` profile or build directly

## Reference deployments

| Client | Slug | Status | Notes |
|---|---|---|---|
| Vicelle Naturals | vicelle | LIVE (2026-05-27) | First deployment; reference template |
| Holistic Vitalis | hv | PLANNED | Already has Atlas + social concierge — migration, not greenfield |
| D'Lluxe Scrubs | dlluxe | NOT STARTED | Next candidate |
| Liquid Wizdom | liquidwizdom | NOT STARTED | After D'Lluxe |
