---
name: ads-compliance-check
description: Pre-flight gate that blocks ad publish until brand-compliance, Meta 72-hour blackout, and platform policy red-flag checks pass. Triggers on "compliance check", "ads compliance", "compliance gate", "blackout check", "creative QA", "pre-flight ad check", "can I push this ad", "is it safe to launch", "check ad before publish", "verify ad creative", "ad QA gate".
when_to_trigger:
  - "compliance check"
  - "ads compliance"
  - "compliance gate"
  - "blackout check"
  - "creative QA"
  - "pre-flight ad check"
  - "can I push this ad"
  - "is it safe to launch"
  - "check ad before publish"
  - "verify ad creative"
  - "ad QA gate"
  - "review this ad for compliance"
inputs:
  - manifest: path to ads-manifest.json (default ./ads-manifest.json)
outputs:
  - per-check PASS/FAIL verdicts
  - actionable fix list when FAIL
  - exit non-zero on FAIL
---

# /ads-compliance-check

A pre-flight gate that **blocks** ad publishing until three categories of checks pass:

## (A) Brand-Compliance
Per memory feedback files:
- `feedback_hv_brand_compliance.md` — Mason jar specs, gel colors, banned medical language, 36-grid naming
- `feedback_ad_creative_rules.md` — logo must be real composite, no AI-generated brand text in video
- `feedback_image_quality.md` — no generic Canva-level images, one-at-a-time approval gate
- `feedback_hv_copy_minerals.md` — "90+ minerals" not "92 of 102"
- `feedback_product_reference_images.md` — real product photos as ingredients, no sample jars, blur competitor logos

## (B) Meta 72-Hour Blackout
Per `feedback_meta_ads_72h_blackout.md`:
- Zero edits within 72h of any prior change
- Max 20% single budget adjustment
- New campaigns frozen 3 full days post-launch
- Exception: ROAS < 0.5x AND spend > 2x daily target → emergency pause only

## (C) Per-Platform Policy Red-Flags
- **Meta:** health claims, before/after, "cure/treat/prevent/diagnose"
- **Google:** YMYL (Your-Money-Your-Life) restrictions, financial-product guarantees
- **TikTok:** medical/health claim restrictions, weight loss language

## How to invoke

```bash
python ~/.claude/skills/ads-compliance-check/compliance-check.py [path/to/ads-manifest.json]
```

Default manifest path: `./ads-manifest.json`

## Exit codes
- `0` — All checks PASS, safe to publish
- `1` — One or more FAIL, do NOT publish; see fix list
- `2` — Manifest invalid / missing

## State file
Tracks last-change timestamps per `{platform}:{account_id}:{campaign_id}` at:
`~/.claude/skills/ads-compliance-check/.state/last-changes.json`

After a successful publish, callers should update this file (or pass `--record` flag) so the next 72h blackout check works.

## Reading order for the agent
1. Read manifest file (path from $1 or default).
2. Run `compliance-check.py` end-to-end; do not skip any check.
3. Print structured report; DO NOT auto-fix unless explicitly asked.
4. If FAIL, surface the fix list verbatim to the user before any publish attempt.
