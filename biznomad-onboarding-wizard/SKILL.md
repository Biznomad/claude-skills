---
name: biznomad-onboarding-wizard
description: Interactive client onboarding wizard for Biznomad's AGaaS offer. Walks a non-technical small business owner through 8 questions, generates their personalized AI team configuration (right-sized to revenue + headaches), provisions a Hostinger VPS, installs Hermes + 4 client bots + 183 agency-agents, and produces the client's first-week sample schedule + runbook. Reuses biznomad-client-ai-team for the actual provisioning. Use when user says "onboard new client", "run the wizard for {client}", "start client onboarding", or "/biznomad-onboarding-wizard".
---

# biznomad-onboarding-wizard

End-to-end AGaaS onboarding for a new Biznomad client. Walks the user through an 8-question interview written in beginner-friendly language, picks the right tier + bots + specialist agents for their business, and either provisions a fresh Hostinger VPS or installs onto an existing one.

**This skill orchestrates `biznomad-client-ai-team`** (which does the actual provisioning). Run this when starting a NEW client. Don't reach for `biznomad-client-ai-team` directly — this wizard ensures the config is complete and correct before provisioning.

## What you ship per client

By the end of the wizard, the client has:

1. **Their own VPS** (Hostinger KVM 4 in Boston 2 by default, or an existing one if they have one)
2. **2/3/4 Hermes Telegram bots** depending on their tier
3. **50/100/183 specialist agents** loaded into Claude Code on their VPS
4. **Tier-1 monitoring scaffold** (timers disabled until they provide API tokens)
5. **Shared memory namespace** for the bot team
6. **A YOUR-AI-TEAM.md runbook** in their shared memory dir
7. **A first-week sample schedule** showing what each bot does on days 1, 3, 7, 14, 30
8. **A BotFather setup checklist** for the bots they need to create

## When to invoke this skill

- User says: "onboard {client}", "/biznomad-onboarding-wizard", "run the wizard", "set up new client AI team"
- User mentions a client name + wants the full Biznomad agency stack deployed
- User asks how to spin up the AGaaS offer for a real customer

When you receive any of those triggers, IMMEDIATELY start at Step 1 below. Do NOT use AskUserQuestion to confirm — the user already triggered the wizard, that's the confirmation.

## Tier matrix (the wizard maps revenue → tier automatically)

| Tier | Revenue band | Bots | Specialist agents | Setup | Monthly |
|---|---|---|---|---|---|
| Solo / Sidekick | $0–$5K/mo | 2 (ops + marketing) | ~50 curated | $1,497 | $497 |
| Standard / Squad | $5K–$50K/mo | 3 (ops + social + intel) | ~100 curated | $2,997 | $1,497 |
| Full / Agency | $50K+/mo | 4 (ops + social + marketing + intel) | All 183 | $4,997 | $2,997 |
| Enterprise / In-House | $250K+/mo | 4 + custom domain specialists | All 183 + niche curated | $10K+ | $5K+ |

Beta testers (the user will name them explicitly) get **Enterprise tier at $0** until graduation.

## The 8-question flow — RUN THIS LITERALLY

Conduct the interview as a friendly conversation. Speak like a small-business consultant, not a tech person. For each question, use the AskUserQuestion tool (for choices) or wait for free-text (for open answers). Track answers as you go in a local mental model. Don't dump all 8 questions at once — flow them one at a time so the user feels seen.

**Tone rules:**
- Use "you" and "your business," never "the client"
- Explain WHY you're asking each question (1 line of context)
- After each answer, say one warm sentence acknowledging what you heard before moving on
- Never use jargon (no "API", "VPS", "MCP", "tier", "provisioning", "endpoint") in user-facing text. Internal notes can use those words.

### Q1 — Business name (free text)
"Hi! I'm going to ask you 8 quick questions about your business — about 4 minutes total. By the end you'll have a personalized AI team ready to work. First: **what's your business called?**"

Capture as `client_name`. Derive `slug` (lowercase, kebab-case, no special chars) and `client_init` (first letter of each word, max 3 chars, uppercase).

### Q2 — One-sentence description (free text)
"Great. In one sentence, **what does {client_name} do?** Think: what you'd say at a dinner party."

Capture as `description`. From this, infer:
- `vertical` (e.g. "sea moss + supplements", "medical scrubs", "B2B SaaS")
- `audience` (e.g. "women 28-55 wellness curious", "nurses + healthcare staff")

### Q3 — Revenue stage (AskUserQuestion, single)
Use AskUserQuestion:
```
question: "Where are you in your business journey right now?"
header: "Stage"
options:
- "Just starting — no sales yet" → tier=solo
- "Side hustle — under $5K/month" → tier=solo
- "Growing — $5K to $50K/month" → tier=standard
- "Established — $50K to $250K/month" → tier=full
- "Scaling — $250K+/month" → tier=enterprise
```

Capture as `tier`. (If the user has flagged this client as a beta tester, OVERRIDE to `enterprise` regardless of revenue answer.)

### Q4 — Biggest headaches (AskUserQuestion, multiSelect)
"What's keeping you up at night? Pick up to 3 — we'll prioritize these."
```
options:
- "Not enough customers coming in" → adds: marketing-content-creator, marketing-growth-hacker
- "Customers come but don't buy" → adds: marketing-landing-page-optimizer, design-ux-researcher
- "I can't keep up with social media" → adds: marketing-content-creator, marketing-tiktok-strategist
- "My ads aren't working" → adds: paid-media-ppc-strategist, paid-media-creative-strategist
- "Operations are chaos" → adds: project-management-sprint-prioritizer, engineering-devops
- "I'm losing customers I won" → adds: marketing-email-strategist, support-customer-success
- "I have no idea what competitors are doing" → adds: intel category, marketing-trend-researcher
- "I can't tell if I'm making money" → adds: finance-financial-analyst, support-finance-tracker
```

Capture as `headaches[]`. Map to `priority_agents[]` for SOUL.md personalization.

### Q5 — Sales channels (AskUserQuestion, multiSelect)
"Where do customers buy from you today?"
```
options:
- "My own website (Shopify, WooCommerce, etc.)" → asks follow-up: which platform + domain
- "Amazon"
- "Etsy"
- "In person / at events"
- "Direct messages on social media"
- "B2B / direct contracts"
- "Don't sell yet"
```

If "My own website" → free-text follow-up: "What's your store URL?" Capture as `platforms.site` and `platforms.shopify_domain` if shopify-like.

### Q6 — Marketing channels (AskUserQuestion, multiSelect)
"How do customers find you now?"
```
options:
- "Email newsletter" → follow-up: which tool?
- "Instagram"
- "TikTok"
- "Facebook"
- "Google search"
- "Word of mouth"
- "Paid ads" → follow-up: which platforms?
```

Capture as `marketing_channels[]`. If email tool mentioned, set `platforms.klaviyo` or similar.

### Q7 — Team size (AskUserQuestion, single)
"Who else helps you run things?"
```
options:
- "Just me — I do everything" → solo_operator=true
- "Me + one helper (VA, partner, family)"
- "Small team (2 to 5 people)"
- "Bigger team (6+ people)"
```

Solo operators get an Ops bot configured to DO more (handle tasks itself). Bigger teams get an Ops bot configured to DELEGATE more (assign to humans by name).

### Q8 — Industry regulation (AskUserQuestion, multiSelect)
"Are you in a regulated industry? Pick all that apply:"
```
options:
- "Health / supplements / wellness (FDA rules)" → compliance.fda_supplement_rules=true
- "Financial services" → compliance.sec_rules=true
- "Cannabis / hemp" → compliance.cannabis_rules=true
- "Legal services" → compliance.legal_rules=true
- "Healthcare / medical" → compliance.hipaa_rules=true
- "Real estate" → compliance.real_estate_rules=true
- "Children's products" → compliance.children_rules=true
- "None of these"
```

This sets the compliance language baked into the brand SOUL.md so the bots never say something that gets the client fined.

## Step 2 — After Q8, generate the config

Combine all answers into a clients/{slug}.json file matching the schema in `biznomad-client-ai-team/templates/client.example.json`. Place at `~/.claude/skills/biznomad-client-ai-team/clients/{slug}.json`. Do NOT fill telegram_bot_tokens yet — those come from BotFather in Step 4.

Add these wizard-derived fields:
- `priority_agents`: array from Q4 mapping — these get featured in SOUL.md
- `tone`: derived from Q1+Q2 (e.g. "warm, personal, grandma-with-degree")
- `solo_operator`: bool from Q7
- `compliance.*`: bools from Q8

## Step 3 — VPS provisioning

Ask: "Does {client_name} already have a VPS we're installing onto, or do we need a new one?"

Two paths:

### Path A — New Hostinger VPS (recommended for client_init !=biz)
Ask: "Do you have access to {client_name}'s Hostinger account? I'll need an API token to provision their VPS."

If yes, get the token (paste once, never log). Use scripts/provision-hostinger-vps.sh to:
- List their VPSes, pick one with state=initial OR offer to skip if all are provisioned
- Provision with template_id=1189 (Ubuntu 24.04 with Claude Code), data_center=24 (Boston 2)
- Generate strong root_password + panel_password using allowed character sets
- Wait for state=running + IPv4 assignment
- Save credentials to ~/.{slug}/vps-credentials.txt (chmod 600)
- Add SSH alias to ~/.ssh/config

### Path B — Existing VPS
Ask: "What's the SSH endpoint? (e.g. root@1.2.3.4 or an alias from your ssh config)"

Capture as `ssh_target`. Verify connectivity. Make sure it's Ubuntu 22+ or 24+.

## Step 4 — BotFather instructions

Print a clear checklist for the user. The bots they create depend on the tier:

```
You'll need to create {N} Telegram bots in @BotFather.
Open Telegram on your phone → search @BotFather → /newbot

For each bot below:
1. Send /newbot
2. Name: "{Client Name} {Role} Agent"
3. Username: "{ClientInit}_{Role}_Bot" (must end in _Bot)
4. Save the token I'll ask for next.

Bots to create:
- {ClientInit}_Ops_Bot          (your operations manager)
- {ClientInit}_Marketing_Bot    (your paid ads specialist) [tier ≥ solo]
- {ClientInit}_Social_Bot       (your brand voice + email) [tier ≥ standard]
- {ClientInit}_Intel_Bot        (your competitor watcher) [tier ≥ standard]
```

Then for EACH bot, prompt:
- "Paste the token for {ClientInit}_Ops_Bot:"
- (Token gets saved to `clients/{slug}.json` under telegram_bot_tokens.ops)
- "Now in BotFather: /mybots → {ClientInit}_Ops_Bot → Bot Settings → Group Privacy → ENABLE"
- (User confirms "done" before moving to next)

## Step 5 — Install agency-agents on client VPS

```bash
ssh {ssh_target} '
mkdir -p /opt/agency-agents
git clone --depth 1 https://github.com/msitarzewski/agency-agents.git /opt/agency-agents 2>/dev/null || git -C /opt/agency-agents pull --ff-only
mv /opt/agency-agents/specialized/agents-orchestrator.md /opt/agency-agents/specialized/agents-orchestrator.md.quarantined-by-biznomad 2>/dev/null || true
cd /opt/agency-agents
bash scripts/install.sh --tool claude-code
'
```

## Step 6 — Run biznomad-client-ai-team provisioner

```bash
# Set BIZNOMAD_SSH env so provision.sh targets the client's VPS
BIZNOMAD_SSH="{ssh_target}" bash ~/.claude/skills/biznomad-client-ai-team/scripts/provision.sh {slug}
```

That handles: 4 Hermes profiles, 4 systemd units, EnvironmentFile patches, shared memory, kanban board, smoke test.

## Step 7 — Configure Vicelle Kimi key (or client's own Kimi key)

If the user is a beta tester or has their own Kimi Coding plan, ask for the key. Otherwise, ask "should we use your existing Biznomad Kimi key for now?" (cheap, simple).

Apply with the same rotate script pattern we developed for Vicelle: writes /root/.hermes/.env on the client VPS, locks model.default=kimi-for-coding + model.provider=kimi-coding in all 4 profile config.yaml files, configures /root/.claude/settings.json for the agency-agents to inherit via Claude Code.

## Step 8 — Telegram team room

Print: "On your phone in Telegram, create a new group called '{Client Name} AI Team'. Add the owner + the {N} bots you just created. Send /whoami in the group from the owner. Tell me what the group chat_id is (you'll see it in the bot's reply)."

When user provides chat_id, run:
```bash
BIZNOMAD_SSH="{ssh_target}" bash ~/.claude/skills/biznomad-client-ai-team/scripts/lock-group.sh {slug} {chat_id}
```

## Step 9 — Generate client deliverables

Run scripts/generate-deliverables.sh which produces THREE markdown docs on the client VPS at /root/.hermes/shared/{slug}/:

1. `YOUR-AI-TEAM.md` — one-page reference card with each bot's role, Telegram username, top 5 things to ask, escalation rules. Beginner-friendly.

2. `SAMPLE-WEEK.md` — what to expect day 1, day 3, day 7, day 14, day 30. Concrete sentences like "Friday morning your Ops bot sends you a one-pager showing revenue vs last week."

3. `RUNBOOK.md` — operator's guide: how to /reset a bot, how to add a teammate, how to rotate the Kimi key, what to do if a bot stops responding. Plain English.

These three docs are the "you got something tangible" moment for the client.

## Step 10 — Final verification + handoff

Run scripts/verify.sh from biznomad-client-ai-team. Confirm all 4 bots active, Kimi auth loaded, MCP enabled. Then deliver the handoff message:

```
🎉 {Client Name}'s AI team is live!

Your 4 bots are ready to talk to you in Telegram:
- @{ClientInit}_Ops_Bot
- @{ClientInit}_Social_Bot
- @{ClientInit}_Marketing_Bot
- @{ClientInit}_Intel_Bot

Find your team room: "{Client Name} AI Team"

Your AI team has access to 183 specialist consultants ready to be
called in whenever needed. You don't manage them — your 4 bots do.

Your reference docs are on your VPS at:
  /root/.hermes/shared/{slug}/
  - YOUR-AI-TEAM.md   ← start here, 1 page
  - SAMPLE-WEEK.md    ← what to expect this week
  - RUNBOOK.md        ← operator's guide for later

Investment: {tier_setup} setup + {tier_monthly}/month
{if beta_tester: "Beta tester perk: full Enterprise tier at $0 until graduation."}

Next step: open Telegram and send 'hi' to @{ClientInit}_Ops_Bot in
the team room. Your Ops bot will introduce itself.

Got it? Let me know if you want me to set up anything else.
```

## Beta-tester mode

When invoked with `--beta-tester` flag OR when the user says "Vicelle is our beta tester" / "make this a beta", do:

1. Set tier=enterprise regardless of Q3 answer
2. Set `beta_tester=true` in config
3. Skip the pricing in the handoff message
4. Add a note to MEMORY.md: "{Client} is a beta tester, charge later"
5. Generate a `BETA-AGREEMENT.md` deliverable: "We're treating you as our beta tester. You get full Enterprise access at $0 while we refine the product. Once it's polished (~30 days) we'll discuss pricing — fair-priced based on what value you've gotten."

## Output files map

After completion:

```
LOCAL (Naeem's Mac):
  ~/.claude/skills/biznomad-client-ai-team/clients/{slug}.json   (with tokens)
  ~/.{slug}/vps-credentials.txt                                 (chmod 600)
  ~/.ssh/config                                                  (alias added)

CLIENT VPS:
  /root/.hermes/                                                 (Hermes installed)
  /root/.hermes/profiles/{slug}-{role}/                          (per-bot profile)
  /root/.hermes/shared/{slug}/                                   (team brain)
    ├── YOUR-AI-TEAM.md
    ├── SAMPLE-WEEK.md
    ├── RUNBOOK.md
    ├── brand.md
    ├── ops.md / social.md / marketing.md / intel.md
    └── decisions.md
  /root/.hermes/kanban/boards/{slug}/                            (task board)
  /root/.claude/agents/                                          (183 specialist agents)
  /opt/agency-agents/                                            (source clone)
  /opt/vicelle-monitors/ (if tier ≥ standard)                    (Tier-1 monitoring scaffold)
  /etc/vicelle-monitors.env                                       (config template)
```

## Failure modes (designed out)

| Risk | Mitigation |
|---|---|
| User pastes token in DM and it leaks to logs | Tokens read once, written to chmod-600 files, NEVER echoed in logs or commits |
| Wrong tier picked (revenue lies) | If user-provided revenue feels off from their answers, gently confirm before tier lock |
| BotFather privacy mode skipped | Step 4 requires explicit "done" before moving to next bot |
| Telegram polling conflict | Same as biznomad-client-ai-team — token fingerprint check refuses duplicates |
| Compliance language missed | Q8 is mandatory; if "None of these" picked, default conservative compliance is still applied |
| Beta tester forgot to charge later | `MEMORY.md` updated + `BETA-AGREEMENT.md` deliverable serves as durable reminder |
| Wizard interrupted mid-flow | Each step is idempotent; user can re-run wizard with same slug to resume from where they left off |
