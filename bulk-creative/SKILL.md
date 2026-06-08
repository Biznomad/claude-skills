---
name: bulk-creative
description: >
  Generate 20 on-brand ad copy variations in ~10 minutes from brand
  guidelines + tone of voice. Mapped to messaging pillars from
  brand-profile.json. Replaces briefing copywriters for ad copy. Alias
  chain for /ads-create → /ads-generate. Use when user says
  "/bulk-creative", "20 ad variations", "bulk ad copy", "write 20 ads",
  "generate ad copy variants", or is starting Phase 2 of
  /biznomad-meta-ads-team.
---

# /bulk-creative — 20 On-Brand Copy Variations

Thin alias that chains `/ads-create` → `/ads-generate` to produce 20
on-brand Meta ad copy variations from the client's brand DNA.

## What this skill does

Reads `brand-profile.json` (or runs `/ads-dna` first if missing) →
generates 20 on-brand copy variations across primary text + headlines,
mapped to the brand's messaging pillars.

Each variation includes:
- Primary text (≤125 chars sweet spot, hard cap 280)
- Headline (≤40 chars sweet spot, hard cap 60)
- CTA from {SHOP NOW, GET OFFER, ORDER NOW, LEARN MORE}
- Messaging pillar tag

## Inputs needed (ask the user)

- Client (must be `cd`-ed into the client project root)
- Target offer / promo angle if applicable (BOGO, geo, evergreen, etc.)
- Audience segment if non-default

## How to invoke

1. **Pre-flight memory grep** for `feedback_{client}_*` and
   `playbook_{client}_*` files — read them in full BEFORE generating
   any copy. The Apr 2026 HV run violated [[feedback_hv_copy_minerals]]
   ("90+ minerals" not "92 of 102") because this step was skipped.
2. Verify `brand-profile.json` exists in current directory. If not,
   invoke `/ads-dna` first.
3. Invoke `/ads-create` to build campaign concepts.
4. Invoke `/ads-generate` to produce the 20 variations.
5. If inside `/biznomad-meta-ads-team`, save to
   `./meta-ads-team/02-creative/copy-deck.md`.

## Compliance hardening

Honor any platform-specific compliance memories before output:
- `[[feedback_hv_brand_compliance]]` — banned language for HV
- `[[feedback_hv_copy_minerals]]` — "90+ minerals" wording
- `[[feedback_hv_free_shipping_threshold]]` — $65+ for HV
- `[[feedback_meta_clean_creative]]` — OPT_OUT spec for HV API calls

Meta-rejection history to avoid:
- No "$X/month" dollar savings claims (rejected in HV Apr 29 V3)
- No medical claims (cure / treat / prevent / heal)
- No before/after health transformations

## Inspired by

cindie.zhu's "Meta x Claude skills" reel — the `/bulk creative` command.
See [[reference_biznomad_meta_ads_team_skill]] for the orchestrator.
