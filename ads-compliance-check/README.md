# /ads-compliance-check

Pre-flight gate that blocks ad publishing until brand, blackout, and platform-policy checks pass.

## Quick start

```bash
# 1. Drop an ads-manifest.json in your working directory describing the change.
#    See ./ads-manifest.json in this skill dir for the canonical shape.

# 2. Run the gate.
python ~/.claude/skills/ads-compliance-check/compliance-check.py ./ads-manifest.json

# 3. On PASS, record the publish so the 72h blackout starts ticking.
python ~/.claude/skills/ads-compliance-check/compliance-check.py ./ads-manifest.json --record

# 4. Machine-readable output for n8n / scripts.
python ~/.claude/skills/ads-compliance-check/compliance-check.py ./ads-manifest.json --json
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0`  | All checks PASS — safe to publish |
| `1`  | One or more FAIL — fix list printed |
| `2`  | Manifest missing or unparseable |

## Files in this skill

| File | Purpose |
|------|---------|
| `SKILL.md` | Trigger phrases + when-to-invoke |
| `compliance-check.py` | Reference implementation (stdlib only, optional Pillow) |
| `BANNED_PHRASES.json` | Per-niche banned regex (`common`, `health`, `finance`, `real_estate`, `tiktok_extra`, `hv_brand_specific`) |
| `ads-manifest.json` | Example manifest input |
| `.state/last-changes.json` | Auto-created on `--record`. Tracks last-change UTC per `{platform}:{account_id}:{campaign_id}` |

## Checks performed

1. **Manifest schema** — required fields, valid platform/change_type
2. **Blackout window** — Meta 72h / Google 24h / TikTok 48h / LinkedIn 48h / Microsoft 24h since last change on the same campaign
3. **Budget delta cap** — Meta 20% / Google 30% / TikTok 25% (asymmetric increase OR decrease)
4. **Banned phrases** — niche-aware regex scan over every string in `change.copy`
5. **Required disclaimers** — health → FDA disclaimer, finance → "terms apply", real estate → "equal housing opportunity"
6. **Image / aspect-ratio** — per-platform spec; uses Pillow if available, falls back to declared `image_spec`
7. **Brand-fidelity vision** *(stub)* — TODO, wire to Gemini or Claude vision via `GOOGLE_API_KEY` or `ANTHROPIC_API_KEY`

## Manifest shape (minimum viable)

```json
{
  "brand": "Holistic Vitalis",
  "niche": ["health", "hv_brand_specific"],
  "changes": [
    {
      "id": "MM-71-A1",
      "platform": "meta",
      "account_id": "act_930457189958096",
      "campaign_id": "120214000000000001",
      "change_type": "edit",
      "creative_paths": ["/abs/path/to/creative.mp4"],
      "copy": { "primary_text": "...", "headline": "..." },
      "budget": { "previous_daily_usd": 150, "new_daily_usd": 175 },
      "image_spec": { "width": 1080, "height": 1350, "aspect_ratio": "4:5" },
      "disclaimers_present": ["These statements have not been evaluated by the FDA."]
    }
  ]
}
```

## Supported `platform` values

`meta`, `google`, `tiktok`, `linkedin`, `microsoft`

## Supported `change_type` values

`new`, `edit`, `pause`, `resume`

- `new` skips the blackout check (no prior change exists) and the budget-delta check.
- `edit` runs both.

## Niche selection

Set `manifest.niche` to any subset of:
- `health` — supplements, wellness, sea moss, gummies
- `finance` — loans, credit, crypto
- `real_estate` — Fair Housing Act category
- `hv_brand_specific` — Holistic Vitalis specific (banned "92 of 102 minerals" + sample-size jar refs)

`common` is always applied. `tiktok_extra` is auto-applied when `platform == "tiktok"`.

## Wiring into a publish workflow

```bash
set -e
python ~/.claude/skills/ads-compliance-check/compliance-check.py ./ads-manifest.json
# ...publish step here (Meta API / Google Ads API / etc.)...
python ~/.claude/skills/ads-compliance-check/compliance-check.py ./ads-manifest.json --record
```

If the first command returns non-zero, the publish step never runs.

## TODO

- Replace `check_brand_fidelity_vision` stub with a real Gemini 2.5 Pro / Claude Sonnet vision call. Rubric must cover Mason jar shape, gel liquid colors per SKU, black cap on Black Gold Gummies, two-separate-badge layout, Greek-key border, HV logo legibility, disclaimer overlay readability.
- Add live platform-API lookup of true `last_change` timestamp (Meta Insights API + Google Ads API change_history) so the gate is authoritative even when the state file is stale.
- Add a `--policy-feed` flag to refresh banned phrases from a remote URL (so the agent team can ship updates without code changes).
- Expand `PLATFORM_IMAGE_SPECS` with carousel/collection ad sizes per platform.
- Add a `--soft` mode that prints warnings but exits 0 for advisory-only runs.
