---
name: product-label-ads
description: |
  Generate brand-faithful paid-ad creative for client products where the
  product label carries critical detail (ingredients, dose, claims, brand
  wordmark, certification badges). Pulls real product photos from the
  client's storefront, builds a 3-image reference stack including a
  label-tight crop, generates via Higgsfield Nano Banana Pro with
  character-level spelling locks, and verifies label fidelity at full
  resolution before approval.
  Use when: "make an ad", "ad creative", "Meta creative", "product hero",
  "lifestyle shot", "BOGO promo", "X for $Y promo", "Stories asset",
  "Reels creative", "client brand ad", "supplement ad", "skincare ad",
  "wellness brand ad", "label-perfect product photo".
  Required upfront: a client product visual specs memory file
  (`project_<client>_product_visual_specs.md`). If none exists,
  invoke the bootstrap step to create one before generating.
  Built from the May 2026 Holistic Vitalis BOGO + Mix-and-Match build,
  where Nano Banana Pro hit ~50% label fidelity on first try until the
  master prompt template + tight-crop reference + character-level spelling
  lock landed sample 14 (every ingredient correct).
  NOT for: brand identity / logo design (use brand-designer), text-free
  product photos (use higgsfield-product-photoshoot directly), animated
  video (use higgsfield-generate Marketing Studio Video).
argument-hint: "[client] [promo] — e.g. 'holistic-vitalis bogo-gummies'"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Product Label Ads

Generate paid-ad creatives where the product label must read **exactly correct** at full resolution. Wraps the Higgsfield CLI with a verified workflow that catches the failure modes generic image generation skills miss.

## Why this skill exists

Generic image generators hallucinate label text. Stock prompts get you "TURMEKIIT", "BLADBERWHICK", "EXTRA RIRREMNEWA", or worse — invented brand wordmarks that misspell the client's name. Thumbnails hide the damage. Paying clients reject the ads.

This skill enforces a 6-step workflow that turned 50% pass-rate on Holistic Vitalis BOGO into ship-ready creative.

## Bootstrap — required before generation

1. **Higgsfield CLI authed.** Run `higgsfield account status`. If it errors, ask the user to run `higgsfield auth login` and wait. CLI lives at `/opt/homebrew/bin/higgsfield`.
2. **Client visual specs file exists.** Look for `~/.claude/projects/-Users-biznomad/memory/project_<client>_product_visual_specs.md` (e.g. `project_hv_product_visual_specs.md`). It must contain: jar shape, cap color, label colors, exact ingredient list (no inventions), brand badge geometry, bottom badge layout, border pattern, and color palette. **If missing, do not proceed** — invoke the bootstrap-visual-specs flow (see `references/visual-specs-bootstrap.md`) to interview the user and write one.
3. **Client `CLAUDE.md` checked.** `Clients/<Client-Name>/CLAUDE.md` confirms which Shopify store, brand colors, and ad accounts to target. Project-isolation rules apply — never mix accounts/keys/data.

## The 6-step workflow

### Step 1 — Asset prep
- Get real product photos. From Shopify storefront: `curl -sL "https://<store>/products/<handle>.json" -o /tmp/p.json` then read `images[].src`. Save 2–3 angles to `Clients/<Client>/higgsfield-assets/<YYYY-MM>/<promo>/`.
- Build a label-tight crop reference. Crop the source product photo to ~70% width × 60% height (the label band). Use `sips --cropToHeightWidth $((H*60/100)) $((W*70/100)) source.png --out label-only-ref.png`. This gives Nano Banana Pro more pixels per ingredient word.

### Step 2 — Master prompt assembly
Use `references/master-prompt-template.md`. Required slots:
- **Composition**: where the product sits, scale (≥45% frame height), camera angle, lighting.
- **Hand/avatar**: skin tone explicit if applicable ("warm medium-deep brown skin tone", "Black woman's hand"), accessories.
- **Props**: same plane as product, listed concretely.
- **Background**: bokeh-blurred environment with named objects.
- **Jar physical specs**: from the visual specs memory file, copy verbatim (cap color, transparency, shape).
- **Label specs**: copy the entire ingredient list with character-level spelling for any word that has historically failed (`TURMERIC` → `T-U-R-M-E-R-I-C, never TURMEKIIT or any variant`). Maintain LEFT/RIGHT column layout.
- **Headline overlay**: promo copy, position, color, weight.

### Step 3 — Generation
Always use `nano_banana_2` (Nano Banana Pro). Pass three reference images: full product photo + label-tight crop + secondary angle. 2k resolution.

```bash
higgsfield generate create nano_banana_2 \
  --prompt "$PROMPT" \
  --image ./<product>.png \
  --image ./label-only-ref.png \
  --image ./<product>-angle-2.jpg \
  --aspect_ratio <1:1|9:16|4:5> \
  --resolution 2k \
  --wait --wait-timeout 5m
```

Multiple variants? Use `--run_in_background` and parallelize. ~2 credits per Nano Banana Pro generation on Ultra plan (`higgsfield account status` to check).

### Step 4 — Full-resolution verification (NEVER SKIP)
Thumbnails lie. Always:
1. `curl -sL "$URL" -o sample-N.png`
2. Make a label-band crop: `sips -c $((H*55/100)) $((W*55/100)) sample-N.png --out sample-N-label-crop.jpg && sips -Z 900 sample-N-label-crop.jpg --out sample-N-label-crop.jpg`
3. `Read` the label crop via the Read tool (image input).
4. Read every word on the label out loud (in your reasoning) and compare to the visual specs file. Flag any deviation:
   - Misspelled ingredient (TURMEKIIT, GARDELION, MANM4A, BLADBERWHICK, COLOROPPYLL, etc.)
   - Invented ingredient (Cosmed, Koerohentz, Durozov, etc.)
   - Wrong brand wordmark spelling (HOLISTIC VIRALYS instead of HOLISTIC VITALIS, etc.)
   - Wrong cap color, jar transparency, label background color
   - Wrong badge geometry (rectangular vs round)

### Step 5 — Pass / regenerate / fallback
- **Clean**: open in Preview (`open <file>`), report the asset path + URL + a one-line summary, ask for approval.
- **Typos present, rerunable**: regenerate once with even tighter spelling lock — list the failed words explicitly in the "never spell as" guard. Nano Banana Pro is non-deterministic; second pass often clears.
- **Persistent failure across 2 passes**: switch to **composite workflow** (`references/composite-workflow.md`) — generate the scene with no product, then drop the real product photo in via Pillow. 100% guaranteed label fidelity.

### Step 6 — Deliver
Approved assets live in the client's `higgsfield-assets/<YYYY-MM>/<promo>/` directory. Provide the user a table with: file path, use-case (1:1 feed / 9:16 stories / 4:5 carousel), credit cost, and CDN URL for sharing.

## Failure modes — what NOT to do

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Approving from a 600px thumbnail | Thumbnails hide ingredient typos and brand-wordmark errors | Always crop the label band and read at ≥800px |
| Bottle <40% of frame height | Not enough label pixels — model invents text | Reframe to ≥45% bottle, lean wider angle on environment |
| Single reference image | Insufficient label data for OCR-fidelity | Pass 3 refs: full + tight label crop + angle-2 |
| Generic "preserve label" prompt | Model still hallucinates text it can't read | Spell problem words letter-by-letter with "never spell as" guards |
| Trying gel/complex labels with multiple illustrations + benefit icons | Single-pass AI cannot reproduce reliably | Skip Nano Banana, use composite workflow |
| Mixing client product specs across generations | Brand contamination — wrong wordmark, wrong colors | One generation = one client = one specs file loaded |

## Cost awareness (Higgsfield Ultra plan, May 2026)

- Nano Banana Pro (`nano_banana_2`): ~**2 credits** per image on Ultra plan (200 list price, 100× discount)
- Marketing Studio Video: ~40 credits
- Seedance 2.0: ~135 credits per video
- Z Image: free (use for cheap ideation)

Do `higgsfield account status` before any large batch.

## When to NOT use this skill

- Logo design / brand identity → `brand-designer`
- Text-free product photos (clean studio shot, no label legibility needs) → `higgsfield-product-photoshoot` directly
- Brand video ads → `higgsfield-generate` with Marketing Studio Video
- AI bottle/label that doesn't yet exist → that's product packaging design, different problem
- Static graphic ad with stock typography over a logo (no product photo) → social-media-designer

## References

- `references/master-prompt-template.md` — fill-in-the-blanks prompt for any client product
- `references/visual-specs-bootstrap.md` — how to interview the user and write a `project_<client>_product_visual_specs.md`
- `references/composite-workflow.md` — Pillow-based fallback when AI label fidelity fails
- `references/verification-protocol.md` — full-resolution QA checklist
