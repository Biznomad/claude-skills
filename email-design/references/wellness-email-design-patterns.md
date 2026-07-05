# Premium Wellness Email Design Patterns (8/9-figure DTC teardown)

_Compiled 2026-07-03 from live email archives (milled.com, reallygoodemails, emaillove, emailinspire) across AG1, Ritual, Seed, Olipop, Bloom, Liquid I.V., Vital Proteins, Hims & Hers, Cymbiotika, Moon Juice. Use as the design-grounding for `/email-design` (esp. health & wellness brands)._

## Universal patterns (do these)
1. **Single-column, modular, mobile-first.** Stack of self-contained blocks: hero → benefit → product → social proof → CTA → footer. Never multi-column.
2. **Locked branded header** — centered wordmark (± thin nav or a promo strip) so the email feels like the site.
3. **ONE dominant hero** carrying the message, backed by **real product/lifestyle photography** (or photo-real composited). Graphics/illustration are accents, never the foundation.
4. **Tight ownable color system** — cream/white or brand-tinted ground + **one flexing accent reserved for CTAs**. Palette discipline is the clearest "premium" tell.
5. **Rounded/pill or crisp solid CTA**, ONE primary per block, short imperative ("Shop Now", "Get 20% Off", "Build Your Trio").
6. **Oversized display type with real hierarchy.** Two camps: sans-modern (AG1/Ritual/Liquid IV/Vital Proteins/Moon Juice) vs **serif-editorial (Cymbiotika)**. Each brand owns a distinctive headline treatment. NEVER Arial/Inter as the display face.
7. **A recurring signature device** = instant recognizability: AG1 "free-from" checklist + expert quote; Ritual editorial-letter + traceability; Seed inline arrow/snake glyphs; Cymbiotika serif-italic + highlighter emphasis + pull-quote testimonials; Moon Juice die-cut stickers + lowercase voice; Vital Proteins "New Product Drop" ticker; Liquid IV colored eyebrow labels.
8. **Distinctive preview-text voice** paired to the subject line (a consistent 8-fig tell).

## Two lanes — pick one per brand
- **Clinical-premium / luxury-editorial** (AG1, Ritual, Seed, **Cymbiotika**): restrained cream/sage/muted palette, science/transparency/expert-authority devices, serif-italic or refined sans, calm whitespace, pull-quote testimonials, dark editorial footer. → **This is HV's lane.**
- **Playful-poster** (Olipop, Bloom, Moon Juice, Liquid IV): saturated color-blocking, oversized/script or lowercase type, emoji-heavy subjects, nostalgia/culture voice, promo urgency.

## What separates 8-fig from templated (the anti-slop checklist)
- Real art-directed photography with lighting discipline — NOT colored blocks, NOT AI-garbled product labels.
- Named/custom typefaces (Cymbiotika = Ivy Journal serif + Neue Haas sans; Hims = custom web font, all live text).
- Restrained palette + single accent, generous negative space.
- Editorial devices (eyebrow labels, pull-quote reviews, benefit taglines, hairline rules) instead of a "SALE" banner.
- Live HTML text, not text baked into images.

## HV application (locked)
Lane: luxury-editorial (Cymbiotika-adjacent). Serif display (Fraunces/Georgia fallback) + clean sans body (Jost). Cream ground `#FBF8F1`/`#E9E0CE`, deep green `#243B27`, gold `#C9A94E` reserved for eyebrow + rules, warm-brown body ink. Real product photography as hero + 3×2 flavor grid (see brand-profile `hero_products[].image_url`). Elegant hairline-bordered code card (NOT a dashed coupon box). One CTA. Star + pull-quote + "200,000+ / 10,000+ reviews". Dark green editorial footer. NEVER the mix-match "3 FOR $60" promo graphic. Reference build: `Clients/Holistic-Vitalis/email-brand/samples/july4-bogo-premium.html`.
