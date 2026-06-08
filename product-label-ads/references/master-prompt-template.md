# Master Prompt Template

Fill in the bracketed slots from the client's `project_<client>_product_visual_specs.md` and the brief.

```
Premium [BRAND_AESTHETIC e.g. wellness lifestyle, clean luxury, vibrant Caribbean] hero advertisement, [ASPECT_RATIO e.g. square 1:1, vertical 9:16] composition, magazine-quality photorealistic.

[COMPOSITION — describe the framing.]
A [SUBJECT — e.g. single jar of <product>, three jars in a row, etc.] sits/stands on a [SURFACE — e.g. warm honey-toned wooden kitchen counter, white marble vanity]. The [SUBJECT] occupies [SCALE — must be ≥45% frame height for label fidelity] of the frame.

[OPTIONAL HAND/AVATAR]
A [SKIN_TONE — e.g. Black woman's hand with warm medium-deep brown skin tone, fair Mediterranean hand, brown hand] reaches in from the [DIRECTION — upper right, upper left]. [DETAILS — fingertips hover above cap / fingers grip the body / two fingers pinching a gummy / etc.]. [ACCESSORY — small gold ring catching light / no jewelry / brass-toned watch].

[PROPS — same plane as product]
At the same plane around the product: [LIST 4–7 CONCRETE OBJECTS — e.g. fresh turmeric root with sliced pieces, sprig of rosemary, two yellow dandelion flowers, scattered black peppercorns, halved lemon, dried elderberries].

[BACKGROUND]
Bright [BACKGROUND_TYPE e.g. airy modern kitchen / spa-like bathroom / sunlit living room] with [3–4 BACKGROUND OBJECTS softly defocused into warm bokeh — e.g. white shaker cabinets, hanging copper pan, herb plants, sunlit window]. [LIGHTING — e.g. golden hour from back-left, soft side-light, overhead studio softbox].

[JAR/BOTTLE PHYSICAL SPECS — copy verbatim from visual-specs file]
- [Container: see-through tinted dark-amber plastic / clear Mason jar / opaque white HDPE / etc.]
- [Cap: solid BLACK plastic — NEVER gold / etc.]
- [Shape: tall cylindrical supplement bottle / wide-mouth Mason jar / etc.]

[LABEL SPECS — preserve EXACTLY, every word spelled correctly:]
- HEADLINE: [exact text] (large white text)
- SUBTITLE: [exact text] (white)
- LEFT COLUMN INGREDIENTS — exactly these, no inventions, character-level spelling:
   1. [INGREDIENT 1]
   2. [INGREDIENT 2 with letter-by-letter spelling for any historically failed word, e.g. TURMERIC (T-U-R-M-E-R-I-C, never TURMEKIIT)]
   ...
- RIGHT COLUMN INGREDIENTS — exactly these:
   1. [INGREDIENT 7]
   2. [INGREDIENT 8 with letter-by-letter spelling, e.g. BLADDERWRACK (B-L-A-D-D-E-R-W-R-A-C-K, never BLADBERWHICK)]
   ...
- LOGO: [exact geometry — e.g. round green circle badge with white wordmark inside, NOT a heart icon]
- [BOTTOM BADGES — TWO SEPARATE: e.g. "60 VEGAN GUMMIES" left + "EXTRA STRENGTH" right (separate, not merged)]
- [BORDER PATTERN — e.g. gold greek-key border at top and bottom of label]
- All label text [COLOR — e.g. WHITE, never gold (only the border is gold)]

[PROMO OVERLAY]
Bold [STYLE — e.g. metallic gold] typography overlay [POSITION — at TOP of frame / lower-third]: "[PROMO_COPY — e.g. BUY 2 GET 1 FREE / 3 FOR $60]".

Photorealistic, sharp focus on the label, every ingredient correctly spelled and clearly readable.
```

## Character-level spelling lock — when to add it

Add the letter-by-letter spelling guard for any word the model has previously misspelled OR any word with unusual spelling for English speakers. Common offenders from real generations:

| Correct | Failure modes seen | Guard |
|---|---|---|
| TURMERIC | TURMEKIIT, TUNNERUT, TURMERIIT | `TURMERIC (T-U-R-M-E-R-I-C, never TURMEKIIT or any variant)` |
| DANDELION | GARDELION, BARDLLGRY, DARDELION | `DANDELION (D-A-N-D-E-L-I-O-N, never GARDELION)` |
| MANUKA HONEY | MANM4A, MANIKA, MANNIA | `MANUKA HONEY (M-A-N-U-K-A, never MANM4A or MANMA)` |
| BLADDERWRACK | BLADBERWHICK, BLADKEDVRIAGK | `BLADDERWRACK (B-L-A-D-D-E-R-W-R-A-C-K, never BLADBERWHICK)` |
| CHLOROPHYLL | COLOROPPYLL, COLOBOPPYLL | `CHLOROPHYLL (C-H-L-O-R-O-P-H-Y-L-L, never COLOROPPYLL)` |
| ELDERBERRY | ELOERBERRY | `ELDERBERRY (E-L-D-E-R-B-E-R-R-Y)` |
| ASHWAGANDHA | (so far solid) | usually fine without guard |

When generating for a new client, run two test generations and harvest any new misspellings into a per-client guard list.

## Aspect ratio rules

- **1:1** — Meta feed, default. ≥45% bottle scale works comfortably.
- **9:16** — Stories/Reels. Bottle should be center-vertical, headline copy at top in open dark space, props clustered low. Bottle ≥40% frame height (vertical aspect compensates).
- **4:5** — Meta feed alt (taller), Pinterest. Bottle ≥45%, slight more vertical breathing room.
- **16:9** — banner. Bottle off-center (left or right thirds), copy in negative space. Lower label-fidelity priority, pictorial.

## Required negative space for promo overlay

Always reserve a band of dark/uncluttered area for the promo headline. Examples:
- Top 15% of 9:16 frame
- Lower-third (~25% bottom) of 1:1 frame
- Top-left third of 16:9 frame

Without reserved space, the model overlays text on top of the bottle and the headline becomes illegible.
