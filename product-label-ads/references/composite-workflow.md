# Composite Workflow — when AI label fidelity fails

When two passes of Nano Banana Pro can't render the label correctly (typical for products with multi-element labels: illustrations + benefit icons + multiple text tiers, like the HV Sea Moss gels), drop AI bottle generation entirely. Instead:

1. Generate the **environmental scene only** (no product) via AI.
2. **Composite the real product photo** in via Pillow.

100% guaranteed label fidelity. The product photo IS the product photo.

## Step 1 — Generate the empty scene

Same prompt structure as a normal generation, but:
- Remove all jar/bottle/label specs from the prompt
- Replace with: "An empty space on the [SURFACE] where a product would sit. Same scene, same lighting, same props clustered around the empty area. Camera framed for a centered product shot."
- Use `nano_banana_2` for consistency with the rest of the workflow

```bash
PROMPT='Premium wellness lifestyle scene, square 1:1 composition, magazine-quality photorealistic.

A warm honey-toned wooden kitchen counter with empty space at center-left where a product will sit. The empty area is approximately 30% of frame height — clean countertop with no objects in this center-left zone. Soft golden hour light from upper left creates a slight shadow on the right side of the empty zone.

Around the empty space at the same plane: fresh turmeric root with sliced pieces, sprig of rosemary, two yellow dandelion flowers, scattered black peppercorns, halved lemon, dried elderberries.

Background: bright airy kitchen with sunlit window, white shaker cabinets, hanging copper pan, herb plants — softly defocused warm bokeh. Golden hour lighting.

A Black woman'\''s hand with warm medium-deep brown skin tone reaches in from upper right, fingertips hovering at the level the product will be (do not include the product itself). Small gold ring on her finger.

Bold metallic gold typography overlay lower-third reading "BUY 2 GET 1 FREE".

No bottle, no jar, no product visible — just the prepared empty scene.'

higgsfield generate create nano_banana_2 \
  --prompt "$PROMPT" \
  --aspect_ratio 1:1 \
  --resolution 2k \
  --wait --wait-timeout 5m
```

## Step 2 — Composite the product photo

Use Pillow. The product photo should be a transparent-background PNG (cut out via `rembg`, Photoshop, or Preview's instant alpha if it's not already isolated).

```python
#!/usr/bin/env python3
"""Composite a real product photo into an AI-generated empty scene."""
from PIL import Image
import sys

scene_path = sys.argv[1]    # AI-generated empty scene
product_path = sys.argv[2]  # Real product photo, transparent BG, RGBA PNG
output_path = sys.argv[3]

# Tunables
scale_pct = 0.45      # product height as % of scene height
center_x_pct = 0.42   # horizontal center (0=left, 1=right)
center_y_pct = 0.55   # vertical center (0=top, 1=bottom)
shadow_opacity = 110  # 0-255

scene = Image.open(scene_path).convert("RGBA")
product = Image.open(product_path).convert("RGBA")

W, H = scene.size
target_h = int(H * scale_pct)
ratio = target_h / product.size[1]
target_w = int(product.size[0] * ratio)
product = product.resize((target_w, target_h), Image.LANCZOS)

# Drop a soft shadow underneath
shadow = Image.new("RGBA", (target_w + 60, 30), (0, 0, 0, 0))
from PIL import ImageDraw, ImageFilter
draw = ImageDraw.Draw(shadow)
draw.ellipse([(0, 0), (target_w + 60, 30)], fill=(0, 0, 0, shadow_opacity))
shadow = shadow.filter(ImageFilter.GaussianBlur(15))

cx = int(W * center_x_pct)
cy = int(H * center_y_pct)
sx = cx - (target_w + 60) // 2
sy = cy + target_h // 2 - 5
scene.paste(shadow, (sx, sy), shadow)

px = cx - target_w // 2
py = cy - target_h // 2
scene.paste(product, (px, py), product)

scene.save(output_path, "PNG")
print(f"Wrote {output_path}")
```

Save as `~/.claude/skills/product-label-ads/scripts/composite.py` and call:

```bash
python3 ~/.claude/skills/product-label-ads/scripts/composite.py \
  scene.png \
  /path/to/real-product-cutout.png \
  composited-final.png
```

## Step 3 — Get a transparent-cutout product photo

If you only have the product on a styled background, isolate it first:

```bash
# Install rembg once: pip install rembg
rembg i source-product.jpg cutout.png
```

`rembg` uses an ML model to remove backgrounds. Output is RGBA PNG with the product on transparent.

For Holistic Vitalis gummies, the original Shopify CDN photo at `https://cdn.shopify.com/s/files/1/0681/3106/1955/files/hf_20260116_220952_21f0c20c-c75c-4d7d-ae03-e6882d125dbe.png?v=1768602532` is already on a soft styled background — pass it through `rembg` once, save the cutout for reuse.

Cache cutouts in: `Clients/<Client>/higgsfield-assets/cutouts/<product-slug>.png`

## When to use composite over AI bottle

| Situation | AI bottle | Composite |
|---|---|---|
| Single-color label, ≤6 ingredient list | ✅ | overkill |
| Black/dark label, ≤12 ingredients | ✅ (with master prompt) | optional |
| Label has illustration / benefit icons / multi-tier text | ❌ unreliable | ✅ required |
| Product has photographic illustration on label | ❌ AI invents it | ✅ required |
| Product is in clear glass with visible contents requiring exact color | ⚠️ flips colors often | ✅ required |
| Multiple different SKUs in same shot (e.g. 3-for-$60 mix) | ❌ very unreliable | ✅ required |

For the May 2026 Holistic Vitalis BOGO build:
- **Gummies** (single-element label) → AI bottle worked after the master prompt
- **Sea Moss Gels** (illustration + flavor name + tagline + benefit icons + greek-key border) → composite required

## Cost comparison

- AI bottle: ~2 credits per generation, 50% pass rate → ~4 effective credits per usable asset
- Composite: 2 credits for empty scene + free Pillow run → 2 credits per usable asset, 100% pass rate

For batch-of-10+ runs, composite is cheaper and faster.
