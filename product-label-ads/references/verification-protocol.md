# Verification Protocol

Never approve a generated ad creative from a thumbnail. ~50% of Nano Banana Pro generations contain typos that thumbnails hide. This protocol catches them.

## The 4-step verification

For every generated asset:

### 1. Download full-resolution
```bash
curl -sL "$URL" -o sample-N.png
```

### 2. Make a label-band crop
```bash
W=$(sips -g pixelWidth sample-N.png | tail -1 | awk '{print $2}')
H=$(sips -g pixelHeight sample-N.png | tail -1 | awk '{print $2}')
sips -c $((H*55/100)) $((W*55/100)) sample-N.png \
  --out sample-N-label-crop.jpg \
  --setProperty format jpeg --setProperty formatOptions 90 > /dev/null 2>&1
sips -Z 900 sample-N-label-crop.jpg --out sample-N-label-crop.jpg \
  --setProperty format jpeg --setProperty formatOptions 90 > /dev/null 2>&1
```

The crop should give you ~900px of label area — enough to read every word.

### 3. Read via the Read tool
```
Read /full/path/to/sample-N-label-crop.jpg
```

The image arrives as visual input. Read **every word** on the label out loud in your reasoning. Do not skim.

### 4. Compare against the visual specs file
For each text element in the visual specs file, ask:
- Is this exact word on the generated label?
- Is it spelled identically?
- Is the layout correct (left vs right column, top vs bottom)?

Mark deviations:

| Deviation type | Example | Action |
|---|---|---|
| Misspelled ingredient | TURMEKIIT instead of TURMERIC | Regenerate with character-level guard |
| Invented ingredient | "Cosmed", "Koerohentz", "Durozov" | Regenerate or composite-fallback |
| Brand wordmark misspelled | "HOLISTIC VIRALYS" | **Hard fail — never ship**. Regenerate |
| Wrong cap color | gold cap when product is black cap | Regenerate with explicit cap-color callout |
| Wrong jar transparency | opaque when product is see-through | Regenerate with "see-through tinted plastic" |
| Wrong logo geometry | rectangular badge when product has round badge | Regenerate with explicit "round green circle badge, NOT rectangular" |
| Wrong content color | yellow when product is teal | Regenerate with "liquid color is BLUE-CYAN/TEAL, never yellow" |
| Garbled bottom badges | merged into one | Regenerate with explicit "TWO SEPARATE badges, not merged" |
| Cropped/clipped label | side ingredients cut off | Reframe — tighter crop or reduce overlay text size |

## Two-pass policy

If the first generation has 1–3 minor typos: **regenerate once** with the failed words explicitly listed in a "never spell as" guard.

If the second generation still fails or has different typos: **switch to composite workflow** (see `composite-workflow.md`). Don't burn a third generation on the same scene — Nano Banana Pro is non-deterministic and you may roll the same dice forever.

## When the asset is clean

1. `open <full-resolution.png>` — preview in macOS Preview
2. Show the user the file path + use-case + CDN URL + a one-line summary
3. Wait for explicit approval before scaling to other variants

## What to NEVER do

- ❌ Approve from a 600px thumbnail
- ❌ Skip the label crop because "the thumbnail looks good"
- ❌ Tell the user "this is publication-ready" without reading every label word at full res
- ❌ Generate at 1k resolution — always 2k for label-fidelity work (cost is identical on Ultra plan)
- ❌ Regenerate more than twice with the same approach — switch to composite if pattern repeats

## Logging the failure modes

When you hit a misspelling that wasn't in the existing guard list, **add it to the visual specs file** under "Per-product spelling guards" so future generations include it. The skill gets smarter over time as the guard list grows.
