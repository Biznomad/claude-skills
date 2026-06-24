---
name: Biznomad-shopify-cro-audit
description: Full-site CRO + UX + messaging + functionality audit for any Shopify or Shopify Plus store. Runs four parallel waves (static Admin-API audits, live browser walkthrough, CRO scoring, opus synthesis), produces prioritized P1/P2/P3 punch list, auto-fixes P1 (revenue/compliance/data correctness) issues with backups + rollback commands. Use when the user asks to "audit the site", "audit the store", "find conversion blockers", "CRO audit", "full Shopify audit", "site inconsistencies", "messaging audit", or names a specific Shopify store + asks for any health check. Reusable across HV, Vicelle, D'Lluxe, Liquid Wizdom, and other Biznomad client Shopify stores.
argument-hint: "<shopify-store-domain> [--tier1 url1,url2,...] [--no-fix] [--depth tiered|deep|everything]"
license: MIT
---

# Biznomad — Shopify CRO + UX + Messaging Audit

Single-command full-site audit. Catches conflicting messaging, broken functionality, conversion blockers, CRO gaps, and compliance violations across the customer-facing surface. Auto-fixes P1 (revenue / data correctness / compliance) issues in the same pass with explicit user approval and rollback commands.

Coverage now also includes the **live functional buy-path** (2026-06-08 hardening): cart-type/drawer friction, custom add-to-cart handlers that hard-redirect to `/cart` and bypass the drawer, JS console/exception errors on PDP/cart/checkout, archived/unpublished variants wired into live add-to-cart UI, promo↔active-discount mechanism mismatches, duplicate internal products with reachable standalone PDPs, destructive cart-clear urgency timers, and false subscription free-shipping claims. An optional Wave 0 pulls PostHog signal (funnel leaks, rageclicks, exceptions, deploy-regression detection) to aim the audit at the real leaks.

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
- Functional E2E: every CTA click → expected destination; **cart-add → the slide-out drawer opens and does NOT forward to `/cart`** (test the real ATC AND any custom bundle/BOGO/mix-match "add" button — those have their own handlers that often redirect). Confirm the drawer shows the just-added item, not a stale/empty state.
- **JS console + page errors:** attach `page.on('console')` (filter `type==='error'`) + `page.on('pageerror')` and record any exception fired on this page. Treat errors on a product/cart/checkout/money page as P1 (silent conversion breakers). Ignore benign noise: `_AutofillCallbackHandler`, `Load failed`/`NetworkError`, `Script error.` (cross-origin/extension chatter).
- WCAG quick-pass via axe-core (`page.evaluate(() => axe.run())`)
- Core Web Vitals: TTFB + LCP + CLS sampled 3x, median reported
- Mobile-specific: horizontal scroll, sticky bar coverage, tap targets
- **Headless reality check:** Shopify aggressively 429s cart-write POSTs (`/cart/add.js`, `/cart/clear.js`) from automated sessions — even real-UA Playwright. If you can't complete an add E2E, verify the *mechanism* statically (the drawer-open code path exists + no `/cart` redirect) and note the env limitation; don't report a false "drawer broken." Server-side `curl` adds (HTTP 200) confirm endpoints are fine.

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

### Cart behavior + custom add-to-cart redirects (added 2026-06-08)
The single biggest cart→checkout leak hides here. Check three things:
1. **Cart type.** `config/settings_data.json` → `cart_type`. `"page"` or `"notification"` means add-to-cart routes shoppers to the full `/cart` page (a navigation away from the product = friction). A slide-out **`"drawer"`** keeps them in flow and converts better. Flag `page`/`notification` as a P2 CRO finding (P1 if it was recently *changed* from drawer — that's a regression).
2. **Custom add-to-cart handlers that hard-redirect.** Grep all `sections/*.liquid`, `snippets/*.liquid`, `assets/*.js` (esp. GemPages/bundle-builder/B2G1/mix-match sections) for `window.location.href = '/cart'` / `location.assign`/`location.replace` inside an add-to-cart success path. These bypass the drawer and force a page nav. **The fragile anti-pattern:** dispatching a `cart:update` CustomEvent then falling back to `/cart` after a short `setTimeout` — the event usually doesn't open the theme drawer, so the timeout *always* redirects. **The fix:** call the drawer custom element's `.open()` directly (e.g. `document.querySelector('hdt-cart-drawer').open()`), with `[aria-controls="CartDrawer"]` click + `dialog#CartDrawer.showModal()` fallbacks, and `/cart` only as a true last resort.
3. **Destructive urgency timers.** A `<cart-countdown>`/urgency timer whose expiry runs `fetch('/cart/clear.js')` + `window.location.href='/cart'` will wipe carts of long-session shoppers (and on this store the replays that abandoned were 19–58 min long). Flag any cart-clear-on-expiry as P1.

### JS runtime errors on the buy path (added 2026-06-08)
Console exceptions on PDP/cart/checkout silently break conversion. In Wave 2, capture `page.on('console')` errors + `page.on('pageerror')` per page; flag any error firing on a product, cart, or money page. **Real example:** a cart fix removed a `[name=minus]` button the theme's quantity web-component required → `null is not an object (this.buttonMinus.classList)` thrown ~225×/day. **Lesson baked in:** never delete a DOM element a theme web-component queries in its init. If the client has PostHog with `capture_exceptions`, pull `$exception` events grouped by `$exception_values[1]` + `$current_url` — far faster than browser sampling. Note `_AutofillCallbackHandler` and `Load failed`/`Script error.` are benign browser/network noise — don't flag them.

### Archived / unpublished variants referenced in live add-to-cart UI (added 2026-06-08)
A product card / bundle card / upsell that adds an **archived or unpublished** variant returns 422 "Cannot find variant" → the button is dead. Cross-check: for every variant ID hardcoded in theme JS (`spAddUpsell(...)`, bundle card configs, B2G1 `BUNDLES` arrays), GET the product and confirm `status:active` + `published_at != null`. Flag any pointing at archived/draft variants as P1 (broken purchase control).

### Promo / discount mechanism mismatch (added 2026-06-08)
Promotional UI must match the *actual active discount*. Pull `automaticDiscountNodes` (GraphQL) and reconcile: a "Buy 2 Get 1 Free" card priced as a pre-discounted bundle product while a separate **automatic Bxgy** also runs = double-discount risk or a dead card. Verify the discount's `customerBuys`/`customerGets` **target the same product** the promo UI sits on (a real find: the Bxgy targeted "16 in 1 …" but the BOGO cards lived on a different "Black Gold …" product). Check `usesPerOrderLimit` to know if "Buy 4 Get 2" works via repeated application of a "Buy 2 Get 1" discount.

### Duplicate / internal-only products with reachable standalone PDPs (added 2026-06-08)
Detect near-duplicate products (same title stem, identical variant structure + prices). One is usually canonical/public; the other is an **internal cart-only / bundle-addon** SKU (tags like `_hidden-from-collections, bundle-addon-only`, product_type `Internal — Cart-Only`). The internal one's **standalone PDP should not be a destination** (it renders cluttered/broken bundle UI). Confirm whether its variants are load-bearing (grep theme for the *exact variant IDs* — see substring gotcha below — e.g. used by `spAddUpsell`). If load-bearing it MUST stay published, so a Shopify 301 won't fire (see gotcha); use a **handle-gated theme-level JS redirect** (`if product.handle == '<internal>' { window.location.replace('/products/<canonical>') }`) that only runs on that PDP. If NOT load-bearing, archive it (then the 301 fires).

### Free-shipping claims vs the actual rule (added 2026-06-08; supplement/ecom)
Verify every "free shipping" claim against the *real* rule (usually a single `$X+` auto-discount, e.g. `$75`). Mode-specific claims are the trap: **"free shipping on every subscription" / "free shipping always (subscribe)" / "your subscription ships FREE"** are FALSE when the subscribe price ($60) is under the threshold. Free-ship progress meters must compute distance to the threshold from the **actual cart total, identically for subscribe and one-time** — never branch `subscribe → free`. Confirm which cart total actually crosses the threshold (e.g. a 4-pack at $80 ships free *because* $80 > $75, not via a special perk). This is an FTC/trust P1.

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
- **Don't assume a Shopify 301 URL Redirect fixes a "looking crazy"/duplicate PDP.** URL Redirects only fire on paths that **404**. If the product is still published, its page resolves and the redirect is *silently ignored*. Either archive/unpublish the product (only if nothing depends on its variants), or use a handle-gated theme-level JS redirect. (2026-06-08)
- **Don't grep for a product handle as a bare substring.** `black-gold-sea-moss-gummies` is a substring of `16-in-1-black-gold-sea-moss-gummies`, so a naive grep reports the wrong product as referenced. Match on **exact variant IDs** (unambiguous) or word-boundaried handles. This false-positive nearly led to "B is load-bearing" when the refs were all Product A. (2026-06-08)
- **Don't verify a fix against the live rendered HTML alone.** This store's page_cache served stale HTML for minutes after every PUT. Verify the **asset source** via Admin API `GET` (that's the source of truth); the cache catches up. A browser hard-refresh does NOT bust a server-side page cache. (2026-06-08)
- **Don't ship a "fix" that deletes a DOM node a theme web-component depends on.** Theme quantity/cart custom elements query for specific nodes (`[name=minus]`) in their init and throw if absent. Keep the element; change its behavior via a capture-phase listener instead. (2026-06-08)
- **Don't edit a stale local copy of an asset and push it — you'll silently revert an earlier fix.** A later "drawer fix" pushed a pre-shipping-fix copy of `sale-mix-match-toggle.liquid` and reverted that day's approved shipping-claim correction. ALWAYS re-pull the live asset (`GET .../assets.json`) immediately before editing, or merge onto the current live source. When two fixes touch the same file in one session, the second push must include the first. (Caught only because the audit re-scanned the live source.) (2026-06-08)
- **Don't trust a single-pass static scan's exact match counts blindly.** The FTC scan flagged ~7 blog articles; the actual fix pass found 17 (e.g. "hormonal balance" 9× in one article). Re-scan EVERY article's body for the banned set during the fix pass, not just the flagged handles. (2026-06-08)

## Optional Wave 0 — PostHog signal pull (when the client has PostHog)

If the store runs PostHog (check theme.liquid for `posthog.init`), pull real behavioral signal *before* the static waves — it points the audit straight at the live leaks:
- **Funnel** (visitor → product_viewed → add_to_cart → checkout_started → purchase): find the worst-converting step. A low ATC→checkout step = a cart/offer problem to chase in Waves 2-3.
- **Rageclicks** (`$rageclick`): group by `$el_text` + `$current_url`. Dead/broken controls surface here instantly (a dead `−` stepper, a non-responsive toggle, a broken bundle card).
- **Exceptions** (`$exception`, if `capture_exceptions` on): group by `$exception_values[1]` + page; real JS breakers, minus the benign noise.
- **Deploy-regression signature:** if conversion fell off a cliff on a specific date with **CTR/CPM/frequency flat** (pull from Meta if available) but click→buy CVR down, the cause is a **site deploy**, not ads. Cross-check theme asset `updated_at` clustering around that date (a dated theme name like `HV-Live-2026-05-27` + a batch of cart/PDP/CSS files stamped that day = the smoking gun). HogQL query host is `https://us.posthog.com` (NOT the ingest host `us.i.posthog.com`).

After fixes ship, the same signals are the *bulletproofing* layer: alerts on funnel-CVR/revenue/error breach (a watchdog that pings the client's ops channel) would catch the next regression in hours, not weeks. Offer it as a follow-up.

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
- HV (2026-06-08): live functionality/CRO sweep that produced the new patterns above. Found+fixed: dead `/cart` minus stepper (the #1 cart-abandon rageclick) → JS regression caught by error tracking within hours; cart was on `notification` mode (routed to `/cart` page) → switched to slide-out drawer; **two** custom add-to-cart handlers hard-redirecting to `/cart` (B2G1 snippet + mix-match bundle builder's fragile `cart:update`+1.2s fallback) → drawer.open(); false "free shipping on every subscription" claims (15+ instances + a meter) → corrected to the real $75 rule; a duplicate internal "Black Gold" gummy with a crazy standalone PDP (broken BOGO cards pointing at archived bundle products) → handle-gated redirect to the canonical "16 in 1" product while keeping it published for mix-match upsells; BOGO confirmed running via an automatic Bxgy discount (don't un-archive the bundle products). Root cause of a −40% revenue period was a **May 27 theme deploy** (CTR/CPM flat, click→buy CVR −60%), not the ads. Spawned a PostHog funnel guardian (deploy/error/CVR tripwire). Key files: `finding_hv_cart_stepper_rage.md`, `finding_hv_ads_decline_siteside.md`, `reference_hv_shipping_rule.md`, `reference_hv_gummies_and_drawer.md`, `project_hv_posthog.md`.
