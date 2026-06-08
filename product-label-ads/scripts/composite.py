#!/usr/bin/env python3
"""Composite a real product photo onto an AI-generated empty scene.

Usage:
  python3 composite.py SCENE.png PRODUCT_CUTOUT.png OUTPUT.png \
    [--scale 0.45] [--cx 0.42] [--cy 0.55] [--shadow 110]

PRODUCT_CUTOUT.png must be RGBA with the product on a transparent background.
Use `rembg i source.jpg cutout.png` to isolate first if needed.
"""
import argparse
from PIL import Image, ImageDraw, ImageFilter


def composite(scene_path, product_path, output_path,
              scale_pct=0.45, center_x_pct=0.42, center_y_pct=0.55,
              shadow_opacity=110):
    scene = Image.open(scene_path).convert("RGBA")
    product = Image.open(product_path).convert("RGBA")

    W, H = scene.size
    target_h = int(H * scale_pct)
    ratio = target_h / product.size[1]
    target_w = int(product.size[0] * ratio)
    product = product.resize((target_w, target_h), Image.LANCZOS)

    shadow = Image.new("RGBA", (target_w + 60, 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse([(0, 0), (target_w + 60, 30)],
                 fill=(0, 0, 0, shadow_opacity))
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


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("scene")
    p.add_argument("product")
    p.add_argument("output")
    p.add_argument("--scale", type=float, default=0.45)
    p.add_argument("--cx", type=float, default=0.42)
    p.add_argument("--cy", type=float, default=0.55)
    p.add_argument("--shadow", type=int, default=110)
    args = p.parse_args()

    composite(args.scene, args.product, args.output,
              scale_pct=args.scale,
              center_x_pct=args.cx,
              center_y_pct=args.cy,
              shadow_opacity=args.shadow)
