---
name: spy
description: >
  Pull every competitor's active Meta ads with hooks, CTAs, offers, format,
  and how long each has been running. Saves a ranked swipe file. Replaces
  manually scrolling Meta Ads Library. Alias for /ads-competitor scoped to
  Meta. Use when user says "/spy", "spy on competitors", "competitor ad
  swipe", "what ads are competitors running", "pull competitor ads", or
  is starting Phase 1 of /biznomad-meta-ads-team.
---

# /spy — Competitor Meta Ads Swipe

Thin alias that routes the request to the more-capable installed
`/ads-competitor` skill, scoped to Meta only, with output landing in the
standard Biznomad workflow path.

## What this skill does

Pulls every actively-running Meta ad from 3–5 named competitors:
- Verbatim hooks (first line / headline)
- CTAs
- Offers (lead promo, bundle, BOGO, discount %)
- Creative format (static / video / carousel)
- Days-running on standout ads (>30 days = likely winners)
- Pricing snapshot from competitor website

## Inputs needed (ask the user)

- 3–5 competitor brand names or Facebook page URLs
- Geo scope (default: US)
- Client name (if running inside `/biznomad-meta-ads-team` — sets output path)

## How to invoke

1. Invoke `/ads-competitor` with `platform: meta` and the named competitors.
2. If running inside `/biznomad-meta-ads-team`, save output to
   `./meta-ads-team/01-spy/swipe-file.md`. Otherwise prompt for output location.
3. Cross-reference any prior swipe file in the same directory for delta
   ("what changed since last scan").

## Inspired by

cindie.zhu's "Meta x Claude skills" reel — the `/spy` command in her
5-skill stack. Built as an alias since her version is gated behind her
DM install guide. See [[reference_biznomad_meta_ads_team_skill]] for the
full orchestrator that chains this with the other 4.

## Related

- `/ads-competitor` — the underlying skill
- `/competitive-ads-extractor` — alternate scraper (ComposioHQ)
- `/biznomad-meta-ads-team` — runs this as Phase 1 automatically
- `[[feedback_security_scan]]` — already satisfied for the underlying skill
