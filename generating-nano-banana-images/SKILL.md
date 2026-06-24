---
name: generating-nano-banana-images
description: Automates bulk image generation via Google AI Studio using Nano Banana (Gemini 2.5 Flash Image) or Nano Banana Pro (Gemini 3 Pro Image). Handles Google account authentication, prompt batching, aspect ratio configuration, and image downloading. Use when the user wants to generate AI images through Google AI Studio, Nano Banana, or Gemini image models.
allowed-tools: Read, Grep, Bash(python3 *), Bash(pip3 *), Bash(ls *), Bash(mv *), Bash(cp *), Bash(mkdir *)
---

# Generating Nano Banana Images

Automate bulk image generation through Google AI Studio using Playwright browser automation. Supports both Nano Banana (free) and Nano Banana Pro (paid/Ultra) models.

## Prerequisites

- Python 3.12+ with `playwright` package installed
- Google account logged into Chrome (for AI Studio access)
- Google Ultra subscription for Nano Banana Pro access (optional)

## Quick Start

Generate all images from a prompts JSON file:

```bash
python3 scripts/generate_images.py --prompts <prompts.json> --output <output_dir> --model nano-banana
```

For Nano Banana Pro (requires Google Ultra or paid API key):

```bash
python3 scripts/generate_images.py --prompts <prompts.json> --output <output_dir> --model nano-banana-pro
```

## Prompts JSON Format

Each prompt entry requires:

```json
{
  "id": "UNIQUE-ID",
  "product": "Product Name",
  "format": "square|portrait|story",
  "prompt": "The image generation prompt text"
}
```

Format-to-aspect-ratio mapping:
- `square` → 1:1
- `portrait` → 3:4
- `story` → 9:16

## Label & product fidelity (critical for product ads)

For product / jar / packaging ads, the model drifts to **plain, minimalist, or solid-color labels** that do NOT match the real product — the user rejects these ("this is not my product"). A generation is correct only if the label matches the real product's actual design.

**Proven fix (flipped consistency from ~1/4 → 4/4):**
1. **Reference = a SHARP per-flavor close-up, not a wide lineup.** In a wide group shot the labels are tiny and illegible, so the model invents simplified labels. Build a high-res (3–4k px) reference sheet where every label is fully legible.
2. **Hard-lock the label color in the prompt.** Add a line like:
   `ABSOLUTE REQUIREMENT: every label is a BLACK/dark-charcoal label — NEVER white, NEVER a solid flavor color. ALL labels MUST be black — if any is white or solid-colored it is wrong.`
   Without this the model drifts to white or solid-color label backgrounds.
3. **Spell out the required label elements** (border style, fruit illustration, brand wordmark, benefit bar, icon row) and add `copy exactly from the reference, do not simplify`.
4. **Self-review bar = REJECT** any output with a plain / minimalist / white / solid-color label. "Says the right flavor name" is not enough — it must carry the full real label design.

**Guaranteed 100% fidelity fallbacks:** composite real product cutouts into AI-generated backgrounds (PIL, $0) — or, via Higgsfield GPT Image 2, pass the real product photo as `--image` every time with `keep each jar IDENTICAL — do not redesign labels`.

## Workflow

1. **Kill existing Chrome processes** to avoid Playwright conflicts
2. **Launch Chrome** with persistent profile for Google auth
3. **Navigate to AI Studio** and select model
4. **For each prompt:**
   - Set correct aspect ratio
   - Enter prompt text
   - Submit and wait for generation
   - Download generated image
   - Rename and move to output directory
5. **Report results** with success/failure counts

## Script Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--prompts` | Required | Path to prompts JSON file |
| `--output` | `./out` | Output directory for images |
| `--model` | `nano-banana` | Model: `nano-banana` or `nano-banana-pro` |
| `--start-from` | `0` | Resume from specific prompt index |
| `--chrome-profile` | Auto | Chrome user data directory |

## Troubleshooting

- **"Opening in existing browser session"**: Kill all Chrome processes first with `pkill -9 "Google Chrome"`
- **Nano Banana Pro requires paid key**: Switch to `--model nano-banana` or link a paid API key in AI Studio
- **Download fails**: Check `~/Downloads/` for generated images with timestamps
- **Rate limiting**: Script includes automatic delays between generations

## Product Reference

See [references/vicelle_prompts.json](references/vicelle_prompts.json) for pre-built Vicelle Naturals sea moss gel prompts.
