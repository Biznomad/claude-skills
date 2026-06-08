---
name: adscores
description: >
  Grade every ad creative on hook strength, copy clarity, CTA, emotional
  resonance vs brand DNA, offer specificity, visual/copy fit, and
  platform-native compliance — BEFORE spending a dollar. Outputs
  PASS/WARN/FAIL scorecard. Alias for /ads-creative. Use when user says
  "/adscores", "score my ads", "grade my creatives", "pre-launch ad
  check", "creative quality check", or is starting Phase 3 of
  /biznomad-meta-ads-team.
---

# /adscores — Pre-Launch Creative Quality Gate

Thin alias for `/ads-creative` — scores every ad creative against brand
DNA before any spend.

## What this skill does

Grades each creative (image / video / copy combo) on 6 dimensions:
- **Hook strength** — first 3 seconds (video) / first line (copy)
- **Copy clarity** — scannability, length, CTA fit
- **Emotional resonance** — alignment with brand voice + pillars
- **Offer specificity** — concrete price + scarcity
- **Visual / copy fit** — image supports headline; headline supports image
- **Platform-native compliance** — 1:1 / 4:5 / 9:16 safe zones, text-on-image rule

Output: scorecard with PASS / WARN / FAIL per creative. Only PASS-tier
creatives proceed to launch.

## Inputs needed (ask the user)

- Path to the copy deck and/or visual assets to score
- Client (for brand-profile.json context)
- Whether running inside `/biznomad-meta-ads-team` (sets output path)

## How to invoke

1. **Pre-flight memory grep** for `feedback_{client}_*` rules that affect
   scoring (banned language, exact phrasings, kill-rule triggers).
2. Invoke `/ads-creative` with the input deck.
3. For each creative, score 0–3 per dimension (max 18).
   Verdict thresholds: PASS ≥14, WARN 10–13, FAIL <10. Compliance 0 = auto-FAIL.
4. Surface top 5 per batch + recommended launch list.
5. If inside `/biznomad-meta-ads-team`, save to
   `./meta-ads-team/03-scores/scorecard.md`.

## Kill rules (HV-specific)

When scoring HV ads, also cross-reference [[feedback_hv_meta_kill_rules]]
for the exact triggers that should pause a creative or revert a budget
bump after launch.

## Inspired by

cindie.zhu's "Meta x Claude skills" reel — the `/adscores` command.
See [[reference_biznomad_meta_ads_team_skill]] for the orchestrator.
