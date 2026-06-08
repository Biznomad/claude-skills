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
