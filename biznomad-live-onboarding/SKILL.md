---
name: biznomad-live-onboarding
description: Arms a Biznomad client's Ops bot for live in-Telegram-group onboarding of their business owner. Patches the Ops profile + playbook with a group-only handoff protocol, widens permission gates so the owner's user_id auto-captures on first message, and generates a copy-paste WhatsApp message + in-group trigger prompt for the operator (Naeem) to ship. Re-runnable per client. Use when handing over a freshly-provisioned client AI team to the actual business owner (e.g. "arm onboarding for vicelle", "michelle is ready for her bots", "fire client onboarding for dlluxe").
---

# biznomad-live-onboarding

The handoff layer between provisioning a client's AI team and the moment their business owner actually meets the bots live in a Telegram group room. Designed to let the operator (Naeem) **watch the entire onboarding play out in the room** rather than the bot DMing the owner separately.

This skill is the last mile of the Biznomad onboarding chain:

```
1. biznomad-onboarding-wizard      → collects client config, creates VPS
2. biznomad-client-ai-team         → installs Hermes profiles, agents, kanban, vault
3. biznomad-live-onboarding (THIS) → arms Ops + delivers WhatsApp + trigger to operator
                                     ↓
                                     Naeem sends WhatsApp, adds owner to Telegram group,
                                     fires trigger message → Ops introduces herself live,
                                     onboarding plays out in the room over 4 days
```

## What the skill does on each run

For a given client slug (e.g. `vicelle`, `dlluxe`):

1. **Reads** the client config at `~/.claude/skills/biznomad-client-ai-team/clients/{slug}.json` to get owner first name, client name, SSH alias, bot usernames
2. **Patches** the Ops bot's `SOUL.md` on the client VPS with an owner-handoff protocol that:
   - Tells Ops to expect Naeem's `@-mention` introduction in the team room
   - Captures the next new user's `user_id` and records it as the owner
   - Stays in the group room throughout onboarding (no DM escalation)
3. **Patches** the Ops onboarding playbook in the client's Obsidian vault with a group-only directive at the top
4. **Widens** Ops's permission gate temporarily (`GATEWAY_ALLOW_ALL_USERS=true`) so the owner can interact before her `user_id` is on the allowlist
5. **Restarts** the Ops gateway service
6. **Prints** two ready-to-ship messages to stdout:
   - **WhatsApp text** the operator copy-pastes to the owner
   - **Telegram trigger prompt** the operator pastes in the team room to launch onboarding

All patches are idempotent — re-running the skill on the same client is safe.

## When to invoke

User says any of:
- "Arm onboarding for {slug}"
- "Fire client onboarding for {client name}"
- "{Owner first name} is ready"
- "Send the welcome to {client}"
- "Let's go live with {client}"
- "/biznomad-live-onboarding {slug}"

## Inputs

The skill reads everything it needs from the client config file. Optional overrides:

```bash
bash ~/.claude/skills/biznomad-live-onboarding/scripts/arm.sh <slug> [options]

Options:
  --owner-name "Michelle"         Override owner first name (else from config)
  --operator-name "Naeem"         Override operator first name (else "Naeem")
  --whatsapp-number "16783299051" Operator's WhatsApp (else hardcoded default)
  --group-name "Custom Group"     Override Telegram group name (else "{Client} AI Team")
```

For `slug=vicelle` with defaults, the skill knows:

- Client name → from `clients/vicelle.json`'s `client_name`
- Owner name → from `clients/vicelle.json`'s `owner_name` (currently "Michelle")
- SSH alias → from `clients/vicelle.json`'s `vps.ssh_alias` or `vps.ssh_target`
- Bot usernames → from `clients/vicelle.json`'s `telegram_bot_usernames`

## Output

Stdout prints two clearly-formatted blocks, copy-paste ready:

```
═══ WHATSAPP MESSAGE FOR {OWNER NAME} ═══
{personalized message text}

═══ TELEGRAM IN-GROUP TRIGGER ═══
@{ops_bot_username} meet {owner name}, the owner of {client name}.
Please run her through onboarding.
```

The operator copies the WhatsApp message to the owner, then on Telegram adds the owner to the existing team group and pastes the trigger message. Done.

## What's already running afterward

After running this skill:

- Ops bot has the owner-handoff protocol baked into its persistent identity
- The playbook explicitly forbids DM escalation
- The permission gate is wide enough for the first contact
- The bot listens in the team room and will only respond when @-mentioned (TELEGRAM_REQUIRE_MENTION=true stays on)

After the owner's first message arrives:

- Ops captures her `user_id` and writes it to `{vault}/70-Onboarding/{owner-name-lowercase}-profile.md` under Identity
- Ops sends a warm in-room welcome addressed to her by name
- Ops walks her through the standard onboarding playbook (Shopify token, email platform key, etc.)
- Tokens she pastes get processed silently — never echoed back as raw text in the room
- When onboarding completes, the kanban handoff fires Intel for day 2

## Locking down after onboarding

Once the owner's user_id is captured, run the companion lockdown:

```bash
bash ~/.claude/skills/biznomad-live-onboarding/scripts/lock-down.sh <slug> <owner-user-id>
```

This tightens `TELEGRAM_ALLOWED_USERS` back to just the operator + the owner, and sets `GATEWAY_ALLOW_ALL_USERS=false`. Run it after Ops confirms day-1 onboarding is complete.

You can get the owner's user_id from the bot's journal:

```bash
ssh <client-ssh-alias> 'journalctl -u hermes-gateway-{slug}-ops.service --since "1 hour ago" | grep -oE "user_id[\":= ]+[0-9]+" | sort -u'
```

## Idempotency markers

The skill uses two HTML comment markers to guarantee idempotency:

- `<!-- OWNER-HANDOFF -->` in SOUL.md
- `<!-- GROUP-ONLY-MODE -->` in the playbook

If either marker is already present, the skill skips that patch. Safe to re-run.

## Per-client memory

Each invocation appends a row to `~/.claude/skills/biznomad-live-onboarding/clients/{slug}.onboarding-log.txt`:

```
2026-05-29T18:42:00-04:00  armed for live onboarding · operator=Naeem · owner=Michelle
```

So you can see when each client was armed without spelunking through transcripts.

## Failure modes designed out

| Issue | Mitigation |
|---|---|
| Owner DMs the bot instead of using the group | Playbook explicitly tells Ops to redirect: "Let's keep this in the team room" |
| Owner's user_id not on allowlist → bot ignores her | Gate widened temporarily; locked down after capture |
| Sensitive tokens visible in room | Operator is the agency owner — she/he must see them anyway. Bot processes silently, never echoes raw token values |
| Re-running breaks state | Idempotency markers prevent double-patching |
| Wrong owner name in config | `--owner-name` flag overrides the JSON value |
| Ops crashes mid-onboarding | systemctl restarts; SOUL.md persistence means the protocol stays loaded |

## Reference deployments

| Client | Owner | Group room | Status |
|---|---|---|---|
| Vicelle Naturals | Michelle | "Vicelle Naturals AI Team" | LIVE (2026-05-29) — first deployment |
| D'Lluxe Scrubs | TBD | "D'Lluxe Scrubs AI Team" | Pending |
| Liquid Wizdom | TBD | "Liquid Wizdom AI Team" | Pending |
