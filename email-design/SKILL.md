---
name: email-design
description: Design and build conversion-focused ecommerce marketing emails for the agency's client brands (Holistic Vitalis, Vicelle, D'Lluxe, Liquid Wizdom, Biznomad, etc.). Designs in Figma, builds email-safe responsive HTML, and loads it into the correct Klaviyo account ready to schedule. Use when the user says "design an email", "build an email", "make a campaign email", "email for <brand>", "/email-design", or wants an on-brand marketing/promo/welcome/abandoned-cart email.
---

# Email Design Agent

Builds on-brand, conversion-focused emails per client brand. Human-in-the-loop with two review
gates. See `DESIGN.md` in this folder for full architecture.

## Invocation
`/email-design <brand-slug> "<brief>"` — e.g. `/email-design holistic-vitalis "July 4th BOGO, buy 2 get 1 free, ends July 4"`

If brand or brief is missing, ask (use AskUserQuestion for the brand — list known slugs from `brands.json`).

## Step 0 — Resolve brand
Read `~/.claude/skills/email-design/brands.json`. Map the slug → `project_path` + `klaviyo_account`.
If the slug isn't registered, tell the user to run Phase 2 `init` for that brand first (not yet built) —
do NOT guess a brand's colors/voice.

## Step 1 — Load brand context
Read `<project_path>/email-brand/brand-profile.json` (the brain) and `figma.json`.
Load 1–2 files from `<project_path>/email-brand/samples/` as few-shot examples of what wins for this brand.

## Step 2 — Strategy pass
Detect the email type from the brief (promo / welcome / launch / abandoned-cart / back-in-stock).
Invoke the `email-marketing-bible` skill for the proven structure + benchmarks for that type.
Decide the block sequence (typical promo: hero → intro text → offer block → product grid → single CTA → fine print).
Respect `brand-profile.json` `offer_rules` and `compliance` (e.g. HV: no cure/treat claims).

## Step 3 — Copy pass
Write subject, preview text, and body copy in the brand's voice (`voice` block in the profile).
Lean on the `copywriting` and `marketing-psychology` skills. One dominant CTA. Validate against
`voice.donts` and `compliance` before proceeding.

## Step 4 — Design in Figma
Using the Figma MCP and `figma.json` (file key + component node map), assemble the email from the
brand's Figma component library into a new frame. This is the reviewable design artifact.
(If the brand has no Figma library yet, say so and offer to create one — see DESIGN.md Phase notes.)

## Step 5 — REVIEW GATE #1
Show the Figma frame (screenshot/link). Ask the user to approve or redline. Do not proceed until approved.

## Step 6 — Build email-safe HTML
Write a content spec JSON (ordered blocks + fields) to `<project_path>/email-brand/samples/<campaign>.json`.
Run: `python3 ~/.claude/skills/email-design/scripts/build_email.py --brand <slug> --content <spec.json> --out <out.html>`.
This assembles the brand's `partials/` (email-safe, table-based, dark-mode-aware) filling `[[brand.*]]`
and `[[content.*]]` tokens. Klaviyo `{{ ... }}` merge tags pass through untouched.
NEVER raw-export Figma to HTML — always build from partials.

## Step 7 — Load to Klaviyo
Push the built HTML as a template on the brand's Klaviyo account (`klaviyo_account` slug from the
profile — HV=WXuDSN, Vicelle=V8fsvS; NEVER mix accounts). Prefer the clone-then-`update_email_template`-then-
`assign_template_to_campaign_message` flow (a message-linked template can 404 on direct PATCH).

## Step 8 — REVIEW GATE #2
Render the template (Klaviyo `render_email_template`) and show the user. Get explicit approval BEFORE
attaching to any campaign or creating a send job. Follow `reference_klaviyo_schedule_guard` for scheduling.

## Rules
- Respect project isolation: only ever touch one brand's project + Klaviyo account per run.
- Sends stay behind explicit human approval — this skill never fires a send on its own.
- Keep Figma components and HTML partials in sync; if you change one, note the other needs updating.
