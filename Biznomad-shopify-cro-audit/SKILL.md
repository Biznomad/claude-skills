---
name: Biznomad-shopify-cro-audit
description: Full-site CRO + UX + messaging + functionality audit for any Shopify or Shopify Plus store. Runs four parallel waves (static Admin-API audits, live browser walkthrough, CRO scoring, opus synthesis), produces prioritized P1/P2/P3 punch list, auto-fixes P1 (revenue/compliance/data correctness) issues with backups + rollback commands. Use when the user asks to "audit the site", "audit the store", "find conversion blockers", "CRO audit", "full Shopify audit", "site inconsistencies", "messaging audit", or names a specific Shopify store + asks for any health check. Reusable across HV, Vicelle, D'Lluxe, Liquid Wizdom, and other Biznomad client Shopify stores.
argument-hint: "<shopify-store-domain> [--tier1 url1,url2,...] [--no-fix] [--depth tiered|deep|everything]"
license: MIT
---

# Biznomad — Shopify CRO + UX + Messaging Audit

Single-command full-site audit. Catches conflicting messaging, broken functionality, conversion blockers, CRO gaps, and compliance violations across the customer-facing surface. Auto-fixes P1 (revenue / data correctness / compliance) issues in the same pass with explicit user approval and rollback commands.

Built from the HV audit on 2026-05-21 that found and fixed: a missing product template (lost $60 bundle UX), fashion placeholder testimonials on the cart page, Lorem ipsum reviews on a top PDP, "Boosts Immunity" FTC violations in 24 places, "Boosts energy" in 15 places, a stale shipping policy page, undisclosed subscription auto-enrollment, a 404'd product URL with active ad traffic, and a Christmas promo still running in May (with a typo). All in one pass.

## When to use

Invoke when the user asks any of:
- "audit the [store / website / Shopify]"
- "full site audit"
- "CRO audit"
- "find conversion blockers"
- "test the entire website for inconsistencies"
- "check for [messaging / UI / functionality] issues sitewide"
- "is anything broken on [store domain]"
- Names a Biznomad client store + asks for any sitewide review

Do NOT use for: single-page reviews (use `/design-review`), ad-account audits (use `/ads audit`), email-flow audits (use `/klaviyo-*`).

## Per-client setup

This skill is fully reusable. Each client requires a one-time config that is stored in
`<client-project-root>/shopify-audit-config/` (never inside this skill directory).

### Required inputs
| Env var | Where to get it |
|---------|-----------------|
| `SHOPIFY_STORE` | e.g. `mystore.myshopify.com` |
| `SHOPIFY_TOKEN` | Shopify Admin → Apps → private app token (read_products + read_themes + read_content + write_themes) |
| `THEME_ID` | Admin API `GET /themes.json`, `role: main` |

### Config-file convention

Each client has a `compliance-profile.json` at `<client-project-root>/shopify-audit-config/compliance-profile.json`.
Set `COMPLIANCE_PROFILE=<client-project-root>/shopify-audit-config/compliance-profile.json` before running scripts.

**Schema:**
```json
{
  "client": "Client Name",
  "store": "mystore.myshopify.com",
  "canonical_summary": [
    { "item": "Subscribe price", "price": "$60.00", "status": "CANONICAL" }
  ],
  "price_patterns": {
    "$60": { "regex": "\\$\\s*60(?:\\.00)?\\b", "tier": "EXPECTED", "note": "Subscribe price — correct" },
    "$65": { "regex": "\\$\\s*65(?:\\.00)?\\b", "tier": "SUSPICIOUS", "note": "STALE — old threshold" }
  },
  "banned_phrases": {
    "boosts immunity": {
      "regex": "boost(?:s|ing|ed)?\\s+immunit(?:y|ies)",
      "tier": "CRITICAL",
      "why": "FTC/FDA health claim",
      "fix": "Replace with 'supports immune function'"
    }
  },
  "required_vocab": {
    "90+ minerals": { "regex": "90\\+\\s*minerals", "tier": "BRAND-REQUIRED", "note": "Preferred mineral claim" }
  },
  "allowlists": {
    "fda_disclaimer": true,
    "css_properties": true
  }
}
```

Non-supplement clients carry their own rules. For example:
- **Apparel store**: `banned_phrases` might flag misleading sizing claims; no supplement allowlists needed.
- **Healthcare brand**: `banned_phrases` flags HIPAA-adjacent copy; `allowlists.fda_disclaimer` stays `true`.
- **Legal/SaaS**: completely different forbidden-language set, `allowlists` both `false`.

### Script portability
Wave 1 Subagents A + B reference audit scripts. For each new client either:
- **(a) Copy** the scripts from an existing client's `audit-v2/` into `<client-project-root>/audit-v2/` and update env vars, **or**
- **(b) Use** the bundled `scripts/` wrappers in this skill (pricing + messaging + fetch_theme_assets) — they are fully self-contained and require no client-specific files beyond the config above.

## Required context

Before running, collect:
- Shopify store domain (e.g. `store.myshopify.com`)
- Shopify Admin API token (Admin API read + write_themes scopes)
- Live theme ID (Admin API → themes list, `role: main`)
- Path to `compliance-profile.json` for this client (see Per-client setup above)

If any are missing, ask via `AskUserQuestion`. Don't guess token values.

## The four waves

### Wave 1 — Static audits (parallel sonnet subagents, Admin API only, no bot challenge)

Six checks in three subagents (group 2-2-2 for shared context):

| Subagent | Reuses / writes | Output |
|---|---|---|
| **A — content + feed** | `audit_v2_content.py` + `audit_v2_mc_feed.py` | `content.md`, `mc-feed.md` |
| **B — links + theme** | `audit_v2_broken_pages.py` + `theme_checker.py` | `links.md`, `theme-scripts.md` |
| **C — pricing + messaging** | Bundled `pricing-consistency.py` + `messaging-consistency.py` (in `scripts/` of this skill) | `pricing.md`, `messaging.md` |

Scripts for Subagents A + B must be present in `<client-project-root>/audit-v2/`. Either copy from a
prior audit client or implement inline. The bundled `scripts/` wrappers (Subagent C) are self-contained
and need only env vars + a `compliance-profile.json` — see "Per-client setup" above.

### Wave 2 — Live browser audit (sequential sonnet subagent)

For each Tier 1 page (default top 7: homepage, top 2 LPs, top 2 PDPs, cart, one random spot-check PDP):
- Desktop screenshot @ 1400×900 (full page)
- Mobile screenshot @ 390×844 (full page)
- Functional E2E: every CTA click → expected destination; cart-add → drawer opens
- WCAG quick-pass via axe-core (`page.evaluate(() => axe.run())`)
- Core Web Vitals: TTFB + LCP + CLS sampled 3x, median reported
- Mobile-specific: horizontal scroll, sticky bar coverage, tap targets

Bot challenge bypass: real-browser Playwright with stealth UA + accept-language usually passes Shopify's challenge. Failing that, use `/setup-browser-cookies` to import a real session.

If the client has a tracking-blocker boilerplate (HV has one in `CLAUDE.md`), inject it via `browser_evaluate` before navigation to avoid polluting analytics.

### Wave 3 — CRO scoring + cross-funnel divergence (sonnet subagent)

Per Tier 1 page, score 1-10 across:
- Hero clarity (what / who is this for / why care in 5 seconds)
- Value clarity (anchoring, savings highlighting, comparison framing)
- Social proof depth (count + recency + UGC + names + aggregate)
- Risk reversal (guarantee, return policy, free-ship, cancel-anytime)
- Urgency / scarcity (real, not crying wolf)
- Friction count (explicit list of clicks/scrolls/decisions to place-order)
- Mobile parity

Cross-funnel divergence check: do LP claims (price, perks, ship, guarantee, subscribe terms, social proof) survive into the next funnel step? Flag every divergence. This is where the most damaging bugs hide.

### Wave 4 — Opus synthesis + P1 auto-fix

1. Aggregate findings from waves 1-3.
2. Triage:
   - **P1**: revenue impact / data correctness / fraud risk / overcharge / broken cart-checkout / live test products / conflicting prices / 4xx CTAs / FTC violations / placeholder content live
   - **P2**: UX gaps, mobile issues, slow load, missing trust signals, weak CRO patterns
   - **P3**: polish, typography, micro-copy, minor inconsistencies
3. Build the P1 catalogue. Split items into two buckets:
   - **Auto-approvable:** Lorem ipsum, demo content, placeholder testimonials, stale seasonal promos with typos, test products. These are safe to fix without business input.
   - **Needs client decision:** dosage claims, review counts, canonical prices, guarantee wording, subscription terms. These require explicit per-item approval.
4. `AskUserQuestion` with the P1 catalogue grouped into ≤4 questions:
   - One question for bulk approval of all auto-approvable fixes (present as a list, ask "approve all?").
   - One question per item needing client decision (dosage, review count, canonical number, etc.).
5. Apply approved fixes via auto-fix script with backups to `<client-dir>/audit-YYYY-MM-DD/backups/<P-id>__<asset-key>.bak`.
6. Verify each fix via live HEAD-check or content re-fetch.
7. Append rollback commands to `PUNCH-LIST.md` under each `[x]` line.

## Deliverables

```
<client-dir>/audit-YYYY-MM-DD/
├── REPORT.md                  # executive summary, scoring, all findings P1/P2/P3
├── PUNCH-LIST.md              # actionable list, [x] for done, rollback per fix
├── CRO-SCORECARD.md           # Wave 3 per-page scoring
├── P1-EXECUTION.md            # what auto-fixed, what skipped, all rollbacks
├── content.md, mc-feed.md, links.md, theme-scripts.md, pricing.md, messaging.md
├── wave1ac-summary.md, wave1bd-summary.md, wave1ef-summary.md
├── wave2-summary.md, wave3-summary.md
├── live/<page-slug>/{desktop.png, mobile.png, notes.md}
└── scripts/
    ├── pricing-consistency.py
    ├── messaging-consistency.py
    ├── fetch_theme_assets.py
    └── p1-auto-fix.py
```

## P1 catalogue patterns (what to look for, what to fix)

This is the playbook — every audit should check for these.

### Live placeholder / demo content
- `Lorem ipsum` anywhere in templates/sections
- Default theme demo testimonials with names like "Robert Smith", "Allen Lyn", "Peter Rope", "Hellen Ase", "Mike Johnson"
- Demo product titles like "Frosted Cake"
- Generic "this web fashion site" / "stylish and affordable" demo text

### Missing live template files
For every product, GET `templates/product.<template_suffix>.json` from the live theme. If 404, that PDP is broken. Either upload from dev theme or remove the suffix.

### Stale promotional content
- Holiday/seasonal announcements still live past their date (Christmas in May, etc.)
- Typos in promo copy ("Christimas" was a real find)
- Free-ship threshold that contradicts the actual shipping rule
- Pricing that contradicts the variant base price + selling plan adjustments

### FTC / compliance (vertical-specific — loaded from compliance-profile.json)
Banned phrases and required vocabulary are **not** hardcoded in this skill. They are loaded
from each client's `compliance-profile.json` (see Per-client setup above). The default shipped
with `messaging-consistency.py` covers supplement/health brands. Non-supplement clients must
supply their own profile.

Example compliance-profile.json excerpt for a supplement brand (illustrative):
```json
{
  "banned_phrases": {
    "boosts immunity":   { "tier": "CRITICAL", ... },
    "cure":              { "tier": "CRITICAL", ... },
    "clinically proven": { "tier": "HIGH",     ... }
  },
  "required_vocab": {
    "supports healthy":  { "tier": "BRAND-PREFERRED", ... }
  },
  "allowlists": { "fda_disclaimer": true, "css_properties": true }
}
```

Run `messaging-consistency.py --strict` to disable all allowlists for a full FTC scan.

### Subscription auto-enrollment without disclosure
Any LP that defaults `SP_MODE = 'subscribe'` (or equivalent) MUST disclose in the subheading or above the CTA. Otherwise ROSCA / FTC risk.

### Review-count / rating consistency
Customer count, review count, star rating must match across every page. Common drift: 200,000+ vs 22,500+ vs 10,000+ vs actual ~3,700.

### Dead product URLs
- HEAD-check every URL in the sitemap.
- HEAD-check every URL referenced in active ad campaigns.
- 4xx → 301-redirect to closest active product/collection, or restore product.

### Test products in catalog
Any product with handle containing `test-product`, `first-test`, `untitled-`, or status that should be `archived` but is `active`. Archive them.

### Missing GTIN / images
Required for Google Shopping eligibility. Service SKUs (shipping protection, processing upgrade) can be excluded from feed.

## Reusable scripts

Bundled with this skill in `scripts/` — fully self-contained, no HV-specific paths:
- `pricing-consistency.py` — sitewide grep for prices that contradict the canonical model
  - Config: `SHOPIFY_STORE`, `THEME_ID`, `OUTPUT_DIR`, `CACHE_DIR`, `CANONICAL_PRICING_JSON`
- `messaging-consistency.py` — banned-phrase scan + review-count + star-rating divergence
  - Config: `SHOPIFY_STORE`, `THEME_ID`, `OUTPUT_DIR`, `CACHE_DIR`, `COMPLIANCE_PROFILE`
  - Flags: `--strict` disables FDA/CSS false-positive allowlists
- `fetch_theme_assets.py` — pull all live theme assets to a per-client/per-run cache dir
  - Config: `SHOPIFY_STORE`, `SHOPIFY_TOKEN`, `THEME_ID`, `CACHE_DIR`, `OUTPUT_DIR`
  - Flags: `--refresh` / `--no-cache` force a fresh pull (ignores cached files)

Client-side scripts (must exist in `<client-project-root>/audit-v2/`):
- `audit_v2_content.py` — Admin API content scan (A1-A13)
- `audit_v2_broken_pages.py` — sitemap + asset HEAD-checks (B14-B20)
- `audit_v2_mc_feed.py` — merchant feed audit
- `theme_checker.py` — CRO script integrity check

## Cache propagation note

Shopify has a URL-keyed page_cache that distributes across multiple origins. After theme edits:
- Body_html bump on the page record forces invalidation
- Manually saving the theme in Shopify admin is the most reliable hammer
- Otherwise expect 5-30 min for all origins to refresh
- Test pages with `?_cb=<timestamp>` to bypass page cache during verification

Cache stickiness will produce inconsistent results across multi-trial sampling. Multi-origin variants (`servedBy` in response header) each have their own TTL. Verify source-side via Admin API GET, then trust cache will catch up.

## Anti-patterns (do not do)

- **Don't auto-fix without explicit approval.** Use bulk approval for obviously safe fixes (Lorem ipsum, demo content, stale promos, placeholder testimonials). Require per-item approval only for findings that need business input (dosage, review count, canonical price, subscription terms). See Wave 4 step 3 for the exact split.
- **Don't push to live theme without backup.** Every mutation gets a `/tmp/<audit-dir>-backup/<P-id>__<asset-key>.bak` copy and a rollback command in the punch list.
- **Don't use regex with `[^<]{0,N}` for HTML content scans.** Today's session learned this: matches break at any `<` tag and miss multi-line context. Use explicit literal find/replace for known strings, or parse HTML properly.
- **Don't trust headless Playwright against Shopify storefront unaided.** Bot challenge will 403. Use real-browser cookies or accept the limitation and use Admin API + static theme analysis instead.
- **Don't conflate Cloudflare cache with Shopify page_cache.** `cf-cache-status: DYNAMIC` means CF didn't cache. Shopify's own per-URL cache (`etag: W/"page_cache:..."`) is the one that thrashes.

## Sequencing (single-message reference)

1. Verify scripts + theme source present (Bash).
2. Create `<client>/audit-YYYY-MM-DD/` and `/tmp/<audit-dir>-backup/`.
3. `TaskCreate` × 12 (one per wave step + auto-fix + verify + skill-package follow-up).
4. Wave 1 (3 parallel sonnet subagents).
5. Wave 2 + Wave 3 (2 parallel sonnet subagents, after Wave 1).
6. Opus synthesis: read 5 summary files, write REPORT + PUNCH-LIST + CRO-SCORECARD.
7. `AskUserQuestion` × ≤4: bulk approve + per-item decisions.
8. Auto-fix sonnet subagent with full P1 spec + backups.
9. Verification HEAD-checks (Bash).
10. Mark all tasks complete.

## Companion / chained skills

- `/setup-browser-cookies` — bypass Shopify bot challenge for Wave 2
- `/browse` — visual + functional checks in Wave 2
- `/accessibility-testing` — deeper WCAG pass on flagged pages
- `/landing-page-optimization` — applied during Wave 3 scoring
- `/ui-ux-pro-max` — applied during Wave 3 scoring
- `/marketing-psychology` — applied during Wave 3 scoring
- `/copywriting` — for messaging rewrites in P1-F / P1-G / P1-K
- `/investigate` — root-cause specific findings from the punch list
- `/codex` — independent second-opinion review of P1 catalogue before applying

## Reference audits

- HV (2026-05-21): `<client-project-root>/audit-2026-05-21/` — first audit, 11 P1s applied, ~$110 in overcharges already prevented earlier in the day, missing template restored, FTC violations fixed. (HV project root: `Projects/Clients/Holistic-Vitalis/`)
