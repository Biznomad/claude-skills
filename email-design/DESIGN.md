# Email Design Agent — Design Doc

_Date: 2026-07-03 · Status: approved, Phase 1 in progress_

## Purpose
A reusable Claude Code skill (`/email-design`) that builds conversion-focused ecommerce
marketing emails for the agency's ~8–9 client brands. Each email is designed in Figma
(reviewable artifact), built as email-safe responsive HTML, and loaded into the correct
Klaviyo account ready to schedule. Output is on-brand per client and grounded in CRO
best practice.

## Three decisions locked (2026-07-03 brainstorm)
1. **Deliverable:** Figma design → responsive email-safe HTML → Klaviyo template (ready to
   attach to a campaign). Not Figma-only; not straight-to-Klaviyo.
2. **Per-brand training:** each brand has a `brand-profile.json` (rules/voice/offer/catalog)
   **plus** a Figma component library **plus** `samples/` of past winners. Three grounding
   layers: profile (hard rules) + samples (few-shot, brand-specific) + `email-marketing-bible`
   skill (universal best practice).
3. **Form factor:** a skill (`/email-design <brand> "<brief>"`), human-in-the-loop with two
   review gates. Not a subagent, not a workflow.

## Pipeline (one run)
1. Load brand context (`brand-profile.json` + `figma.json`).
2. Strategy pass — detect email type, pull proven structure from `email-marketing-bible`.
3. Copy pass — subject/preview/body in brand voice, checked vs. brand do/don'ts.
4. Design in Figma via Figma MCP → reviewable frame.
5. **Review gate #1** — user approves/redlines Figma.
6. Build email-safe HTML from the brand's HTML partials (NOT a raw Figma export — Figma
   export is bloated/non-responsive/breaks in email clients). Figma = design/approval artifact;
   HTML = built from a parallel, hand-tuned partial library kept in sync with the Figma components.
7. Load to Klaviyo template on the correct account.
8. **Review gate #2** — render preview; user approves before it touches a send.

**Key consequence:** each brand's "library" is two synced halves — Figma components (design)
+ HTML partials (build).

## Per-brand structure (lives in each client project — respects project-isolation rule)
```
Projects/Clients/<Client>/email-brand/
  brand-profile.json   # identity, voice, offer rules, catalog, klaviyo acct, CRO defaults
  figma.json           # Figma file key + component node map
  partials/            # email-safe HTML partials mirroring the Figma components
  samples/             # 2-3 past winning emails (few-shot training) + content specs
```
Global registry: `~/.claude/skills/email-design/brands.json` maps slug → project path +
Klaviyo account slug.

## Token system
Partials use `[[brand.*]]` and `[[content.*]]` delimiters (square brackets) so Klaviyo's own
`{{ ... }}` merge tags pass through the build untouched. `build_email.py` fills brand tokens
from `brand-profile.json` and content tokens from a per-email content spec, assembling ordered
blocks into the shell.

## Rollout
- **Phase 1 (now):** Pilot on Holistic Vitalis. Skill skeleton + HV brand-profile + HTML
  partial library (seeded from the July-4 BOGO email) + build script. Prove Figma→HTML→Klaviyo.
- **Phase 2:** Templatize — extract HV setup into a scaffold + `/email-design init <brand>`
  bootstrapper that pulls colors/logo/fonts from a brand's site (ads-dna style).
- **Phase 3:** Onboard remaining brands (Vicelle, D'Lluxe, Liquid Wizdom, …) one at a time.

## Non-goals (YAGNI)
- No fully-automatic Figma→HTML export (unreliable for email).
- No autonomous sending — sends stay behind explicit human approval (existing rule).
- No mass batch generation in Phase 1 — one great email at a time.
