---
name: manychat-template-installer
description: Use to deploy a pre-built ManyChat Template to a client account and customize per-brand text via YAML. Triggers on "install manychat template", "deploy DM ecosystem", "manychat onboarding", "wellness concierge install".
when_to_trigger:
  - "install manychat template"
  - "deploy DM ecosystem"
  - "manychat onboarding"
  - "wellness concierge install"
  - "clone manychat flows to client"
  - "manychat template install"
  - "set up manychat for new client"
inputs:
  - config: path to client YAML config (required, e.g. configs/vicelle.yaml)
  - client_slug: optional override for browser-data directory name
outputs:
  - installed flows in target ManyChat account
  - placeholder-overridden text in every message block
  - renamed tags/fields per YAML
  - verification report (exit 0 PASS / 1 FAIL)
---

# /manychat-template-installer

Deploys a pre-built ManyChat **Template** (created in a master account) onto a fresh client account, then patches every brand-specific text token via a per-client YAML config.

## Why this exists

ManyChat's public API does **not** support flow creation — flows must be built in the UI. ManyChat's **Templates** feature lets us save a master ecosystem (e.g. the "Vicelle Wellness Concierge" 6-flow + 7-sequence build) and share it via a permanent install URL. A new client account can install that URL through a 4-step wizard. After install, every reference to the source brand still says `{{brand_name}}`, `{{product_1_name}}`, etc., and must be patched per-client.

This skill drives both halves via Playwright:
1. **Install pass** — log into the target account, hit the template URL, click through the wizard, wait for flows to land.
2. **Override pass** — walk every flow and replace `{{placeholders}}` with the YAML values inside message blocks, button labels, and quick-reply text.
3. **Rename pass** — convert `PLACEHOLDER_VIP` → `<BRAND>_VIP` for tags and custom fields.
4. **Verify pass** — re-scan and fail loud if any placeholder survives.

## Prerequisites

- Master template URL (built once in the Biznomad ManyChat master account, see `docs/v1-wellness-build-spec.md`)
- Target client ManyChat Pro account (free tier cannot install Templates)
- Client credentials stored **outside the repo** — either in a `.env` referenced by the YAML or in macOS Keychain. Never inline.
- Playwright + Chromium installed (`pip install playwright pyyaml && playwright install chromium`)
- A YAML config in `configs/<client>.yaml` — see `schema.example.yaml`

## Project Isolation (CRITICAL)

Per `/Users/biznomad/CLAUDE.md`, this skill maintains **strict per-client isolation**:
- Browser data dir is `~/.manychat-installer-browser-data/<client_slug>/` (NOT shared)
- Cookies, tokens, sessions never cross client accounts
- Each client requires its own YAML; the skill refuses to run without `--config`
- The `client_slug` in YAML must match the filename to prevent foot-guns

## How to invoke

First-time setup (per client, interactive login):
```bash
python ~/.claude/skills/manychat-template-installer/install.py \
  --config ~/.claude/skills/manychat-template-installer/configs/vicelle.yaml \
  --interactive-login
```

Subsequent runs (re-use saved session):
```bash
python ~/.claude/skills/manychat-template-installer/install.py \
  --config configs/vicelle.yaml
```

Dry run (no UI mutations, just walk + report):
```bash
python install.py --config configs/vicelle.yaml --dry-run
```

## What it does (step by step)

1. **Load + validate YAML** — fails fast if required keys are missing.
2. **Launch Chromium** with persistent context at the per-client data dir.
3. **Login gate** — if no session cookie, halt and prompt the human operator to log in. Skill does not handle/store passwords directly (HUMAN-IN-LOOP).
4. **Install wizard** — navigate to `template_url`, click through page-select → permissions → install. Polls for the "Install complete" toast.
5. **Override loop** — for each flow name in YAML `flows`, open it, scan message blocks, run text-replace for every `{{placeholder}}`.
6. **Rename loop** — Tags & Fields panels: rename anything starting with `PLACEHOLDER_`.
7. **Post-install actions** — e.g. subscribe owner to admin notifications, set default reply, enable Auto Backup.
8. **Verify** — export flow JSON via UI, regex-scan for any remaining `{{` token; exit 1 if found.
9. **Report** — print summary table: flows touched / placeholders replaced / tags renamed / fields renamed / verify status.

## Expected outputs

- `~/.claude/skills/manychat-template-installer/logs/<client_slug>-<ts>.log` — full run log
- `~/.claude/skills/manychat-template-installer/logs/<client_slug>-<ts>-screenshots/` — error captures
- stdout: human-readable summary

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Template not found" on wizard step 1 | URL revoked / wrong account scope | Re-publish template in master account |
| Login loop never completes | 2FA challenge | Run with `--interactive-login`, complete manually |
| Placeholder survives verify pass | New block type the override pass doesn't visit | Add selector to `lib/playwright_helpers.text_replace_in_visible_blocks` |
| Wizard "Install" button greyed | Target account is free tier | Upgrade target to Pro |
| Browser data clash with sibling skill | Two skills sharing dir | Confirm `~/.manychat-installer-browser-data/<slug>/` is unique |

## Reading order for the agent
1. Read the client YAML (path from `--config`).
2. Confirm the operator has the right account selected. Per CLAUDE.md: **always ask "which account?" before mutating**.
3. Run `install.py`. Do not skip the verify pass.
4. If verify FAILS, surface the surviving placeholders and STOP — do not "fix it up" silently.
5. Commit the YAML (not credentials) to the client repo for future re-runs.
