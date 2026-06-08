---
name: biznomad-meta-ads-team
description: >
  Biznomad's end-to-end Meta Ads team workflow — runs the 5-phase pipeline
  (spy → bulk creative → pre-launch scoring → competitor angle extraction →
  full health audit) across any Biznomad client account (HV, Vicelle, D'Lluxe,
  Liquid Wizdom, Biznomad internal). Chains the existing /ads-* skills into a
  single productized agency workflow. Use when user says "run the ads team",
  "full Meta Ads workflow", "Meta Ads team", "5-phase ads", "agency ads
  workflow", "Biznomad ads stack", or asks to "go through the full Meta Ads
  pipeline" for a specific client. Inspired by cindie.zhu's Meta x Claude
  skills reel.
---

# Biznomad Meta Ads Team

Productized agency workflow that replaces a $10k/mo agency retainer with a
5-phase pipeline of Claude Code skills. Reusable across every Biznomad client
running Meta Ads.

## Before starting (pre-flight checklist — do not skip)

1. **Confirm the target client.** Never mix client data (MEMORY.md project
   isolation rule). Ask: "Which client account — HV (act_…), Vicelle,
   D'Lluxe, Liquid Wizdom, or Biznomad internal?"

2. **`cd` into the client's project root.** All sub-skills depend on the
   right `CLAUDE.md`, `brand-profile.json`, and `.mcp.json` being in scope.

3. **Grep memory for client-specific rules** — MANDATORY before any
   creative or audit work. Run:

   ```bash
   ls ~/.claude/projects/-Users-biznomad/memory/ | \
     grep -iE "^(feedback|playbook|finding|project)_(hv|holistic|vitalis|vicelle|dlluxe|liquid.wizdom|biznomad)_"
   ```

   Read every match in full. These memories override defaults — copy
   conventions, banned phrases, known-broken assets, attribution quirks,
   approval rules. The Apr/May 2026 HV run violated 3 such memories
   (mineral copy, pixel walkthrough, attribution framing) by not doing
   this step. See [[feedback_triple_check_against_memory]].

   Also read the always-on rules: [[feedback_meta_ads_72h_blackout]],
   [[feedback_approve_before_posting]], [[feedback_no_live_push]],
   [[feedback_image_quality]], [[feedback_product_reference_images]].

4. **Apply 72h blackout.** If any account change happened in the last 72h,
   only run read-only phases (1, 3, 5). Phases 2 and 4 produce local
   assets — they do not push to Meta — so they are always safe. Phase 5
   is read-only audit.

5. **Verify infrastructure state with live checks, not docs.** Before
   citing "the token is 403'd" / "the pixel is firing" / "CAPI is down,"
   SSH and curl/check yourself. Inherited diagnoses are often stale. See
   [[finding_hv_overattribution_two_problems]] for the canonical example.

## The 5 phases

Run sequentially. Each phase's output feeds the next. Stop and surface
findings to the user between phases — do NOT auto-launch ads.

### Phase 1 — SPY (competitor active ads)

Invoke `/ads-competitor` scoped to Meta only. Pull every active ad from 3–5
named competitors with hooks, CTAs, offers, format, and "days running"
(a proxy for what's working). Save the swipe file to
`./meta-ads-team/01-spy/swipe-file.md`.

Inputs needed:
- 3–5 competitor brand names or Facebook page URLs
- Geo (default: US)

Output: ranked swipe file with hook patterns, offer patterns, and any
long-running ads (>30 days = likely winners).

### Phase 2 — BULK CREATIVE (20 copy variations)

Invoke `/ads-create` for campaign concepts, then `/ads-generate` for the
actual copy. Requires `brand-profile.json` in the client root — if missing,
run `/ads-dna` first to build it.

Target: 20 on-brand copy variations across primary text + headlines, mapped
to messaging pillars from the brand DNA. Save to
`./meta-ads-team/02-creative/copy-deck.md`.

If visual assets are also needed, follow with `/ads-photoshoot` or
`/higgsfield-product-photoshoot` (preferred for HV / Vicelle / D'Lluxe
products — see [[reference_higgsfield_mcp]] and the relevant client product
visual specs, e.g. [[project_hv_product_visual_specs]]).

### Phase 3 — ADSCORES (pre-launch quality gate)

Score every creative from Phase 2 BEFORE any spend. Invoke `/ads-creative`
with the Phase 2 outputs as input. The skill grades each ad on:

- Hook strength (first 3 seconds / first line)
- Copy clarity and CTA
- Emotional resonance vs. brand DNA
- Offer specificity
- Visual / copy fit
- Platform-native compliance (1:1, 4:5, 9:16 safe zones)

Output: `./meta-ads-team/03-scores/scorecard.md` with PASS / WARN / FAIL per
creative. Only PASS-tier creatives proceed to launch.

### Phase 4 — COMPETITOR ANGLE EXTRACTION

Re-run `/ads-competitor` in "angle extraction" mode against the Phase 1 swipe
file. Outputs: ranked hook categories (pain, status, curiosity, social
proof, mechanism), offer categories, and a gap list of angles competitors
are NOT running.

Use the gap list to brief one additional creative batch — these are the
highest-leverage tests because nobody else has tried them.

Save to `./meta-ads-team/04-angles/gap-analysis.md`.

### Phase 5 — ADS-META FULL AUDIT (186-check health score)

Invoke `/ads-meta` on the live account. Runs the full audit covering:

- Pixel + CAPI health, EMQ scores
- Creative fatigue and frequency
- Audience overlap and saturation
- Account structure (Advantage+ vs. manual)
- Bidding strategy and learning phase health

Output: `./meta-ads-team/05-audit/health-score.md` with overall score 0–100
and prioritized fix list (P1 revenue / compliance / data, P2 efficiency,
P3 polish).

For HV specifically, cross-reference [[project_hv_audit_2026-04-26]] for
known issues (Klaviyo tracking gap, declining ROAS context).

## Deliverable

After all 5 phases, produce one consolidated brief at
`./meta-ads-team/SUMMARY.md` with:

1. Top 3 competitor patterns worth stealing (from Phase 1)
2. Top 5 scored creatives ready to launch (from Phase 3)
3. Top 3 untapped angles to test (from Phase 4)
4. Top 3 P1 fixes on the live account (from Phase 5)
5. Recommended 7-day test budget split (winners + gap angles)

Surface this to the user and STOP. Do not push to Meta. Per
[[feedback_approve_before_posting]] and [[feedback_meta_ads_72h_blackout]],
every launch and budget change requires explicit approval.

## Client-specific notes

- **HV** (`Clients/Holistic-Vitalis/`) — pixel/CAPI was broken Apr 21; verify
  in Phase 5 before trusting any historical metrics.
- **Vicelle** (`Clients/Vicelle-Naturals/`) — $25/day Mushroom Gummies ASC
  baseline; DM ecosystem should improve ROAS from 1.29x to 2–3x.
- **D'Lluxe** (`Clients/DLluxe-Scrubs/`) — new account, no historical data;
  Phase 5 audit will mostly find learning-phase issues.
- **Biznomad internal** (`Clients/Biznomad/`) — dental AGaaS pilot live at
  $300/day CBO ([[project_dental_ads_launch]]); high-stakes account.
