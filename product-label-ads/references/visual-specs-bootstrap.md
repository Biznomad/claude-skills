# Visual Specs Bootstrap

When a client doesn't have a `project_<client>_product_visual_specs.md` in memory, gather one with the user before generating any creative. Garbage-in = brand-violating-out.

## Where the file lives

`/Users/biznomad/.claude/projects/-Users-biznomad/memory/project_<client_slug>_product_visual_specs.md`

Slug examples: `hv` (Holistic Vitalis), `vicelle`, `dlluxe`, `liquid_wizdom`.

After writing it, add a one-line pointer in `MEMORY.md` under the relevant client section.

## Required fields per product

For **each SKU** the client may want in ad creative:

### Container
- Shape (jar, bottle, pouch, tube, box)
- Material (HDPE, PET, glass, amber plastic, Mason jar, etc.)
- Transparency (opaque, see-through tinted, clear)
- Color of the container itself
- Cap/lid color and material (do not assume gold or matching — verify)

### Label
- Background color
- Border pattern (greek-key, solid frame, none)
- Text color (white, black, gold) — distinct from any accent metallic
- Headline text (exact)
- Subtitle text (exact)
- **Ingredient or content list** — exact, in column order. **Every word matters** because the model will hallucinate if you guess.
- Brand wordmark/logo geometry (round badge, rectangular badge, on-product mark, color of the badge)
- Bottom badges (count, layout — separated or combined, exact text)
- Any small icon row (benefit icons, certification marks)
- Distinguishing illustration if any (fruit graphic, flower, abstract)

### Color palette
- Primary brand colors (hex if available)
- Accent metallic (gold tone, silver tone, copper, none)

### Liquid / contents color (if visible)
For products where the contents show through (gel jars, syrup bottles, oils): **state the actual color** so the model doesn't invert it. e.g. "Pineapple Skies gel — BLUE-CYAN/TEAL liquid, NOT yellow."

## Interview script (for the user)

If specs are missing, walk the user through:

1. "Send me 2–3 product photos per SKU you want in ad creative — front of label, label crop close-up, and a side angle if possible."
2. "What's the cap color? Same on every SKU?"
3. "What does the brand wordmark look like — round badge, rectangular, on-label only?"
4. "Are there any badges at the bottom? Tell me the exact text."
5. "Are the ingredients listed on the label? If yes, give me the exact list in column order."
6. "Is the container transparent or opaque? Can you see the contents through it?"
7. "Any color on the contents that shows through? (For gel/liquid/oil products.)"

Save answers to the visual specs file. If the user can't answer a field, write `UNKNOWN — verify before generating` rather than guessing.

## Template

Use this skeleton when writing the file:

```markdown
---
name: <Client> product visual specs (for AI generation)
description: Exact visual specs for <Client> products — required for any AI-generated ad creative to maintain brand fidelity
type: project
---

When generating AI ad creative for <Client> products, the model MUST preserve these exact details. Skipping these leads to off-brand creative that the client rejects.

## <Product Name>

- **Container:** <shape, material, transparency, color>
- **Cap:** <color, material — call out if NOT matching obvious assumption>
- **Label background:** <color>
- **Label text color:** <color>
- **Headline:** "<exact text>"
- **Subtitle:** "<exact text>"
- **Ingredient list (exact, no inventions):**
  - LEFT: <ingredient 1>, <ingredient 2>, ...
  - RIGHT: <ingredient 7>, <ingredient 8>, ...
- **Brand logo:** <geometry — e.g. round green circle badge with white wordmark, NOT a heart icon>
- **Bottom badges:** <count, layout, exact text>
- **Border:** <pattern>
- **Distinguishing illustration:** <description, or none>
- **Liquid/contents color (if visible):** <color>

## <Next Product>

...

## Workflow notes

- Models tested: <which models worked best for this brand>
- Per-product spelling guards: <list of words historically misspelled and the guard format>
- Compositing required for: <SKUs that AI cannot reliably reproduce>
- Real product photos for reference live at: <path>
```

## Worked example: Holistic Vitalis

Already exists at `project_hv_product_visual_specs.md`. Use it as the template when writing for a new client. Captures both gummies (AI-friendly) and gel jars (composite-required).
