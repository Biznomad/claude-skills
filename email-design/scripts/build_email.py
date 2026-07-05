#!/usr/bin/env python3
"""
build_email.py — assemble an email-safe HTML email from a brand's partial library.

Usage:
  build_email.py --brand <slug> --content <spec.json> --out <out.html>
  build_email.py --profile <brand-profile.json> --partials <dir> --content <spec.json> --out <out.html>

Design:
- Partials use [[brand.<dot.path>]] and [[content.<field>]] tokens (square brackets) so that
  Klaviyo merge tags written as {{ ... }} pass through the build UNTOUCHED.
- brand tokens resolve from brand-profile.json (flattened to dot paths).
- content tokens resolve per-block from the content spec.
- Structural blocks header/hero/footer are emitted as-is; every other block is wrapped in a
  single <div class="body"> ... </div> region (mirrors the brand shell structure).
- Unresolved [[...]] tokens are blanked and reported so nothing broken ships silently.

Content spec JSON:
  {
    "title": "...",              # <title> / used by [[content.title]] in _shell
    "preheader": "...",          # hidden inbox preview
    "blocks": [
      {"type": "header"},
      {"type": "hero", "headline": "...", "subhead": "..."},
      {"type": "text", "html": "Hey {{ first_name|default:\"friend\" }},"},
      {"type": "code_box", "label": "...", "code": "...", "expiry": "..."},
      {"type": "product_grid", "heading": "...", "products": [{"name":"..","price":".."}, ...]},
      {"type": "cta", "text": "...", "href": "..."},
      {"type": "signoff"},
      {"type": "fine_print", "html": "..."},
      {"type": "footer"}
    ]
  }
"""
import argparse, json, os, re, sys

TOKEN_RE = re.compile(r"\[\[([a-zA-Z0-9_.]+)\]\]")
STRUCTURAL = {"header", "hero", "footer"}


def die(msg):
    sys.stderr.write("ERROR: " + msg + "\n")
    sys.exit(1)


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, prefix + k + "."))
    elif isinstance(obj, (str, int, float)) and not isinstance(obj, bool):
        out[prefix[:-1]] = str(obj)
    # lists are intentionally not flattened into brand tokens
    return out


def resolve_brand(slug):
    reg_path = os.path.join(os.path.dirname(__file__), "..", "brands.json")
    with open(reg_path) as f:
        reg = json.load(f)
    b = reg.get("brands", {}).get(slug)
    if not b:
        die("brand slug '%s' not in brands.json" % slug)
    proj = b["project_path"]
    return (os.path.join(proj, "email-brand", "brand-profile.json"),
            os.path.join(proj, "email-brand", "partials"))


def load_partial(partials_dir, name):
    p = os.path.join(partials_dir, name + ".html")
    if not os.path.exists(p):
        die("missing partial: %s" % p)
    with open(p) as f:
        return f.read()


def fill_content(html, fields):
    """Replace [[content.<key>]] for keys present in this block's fields."""
    def repl(m):
        tok = m.group(1)
        if tok.startswith("content."):
            key = tok[len("content."):]
            if key in fields:
                return str(fields[key])
        return m.group(0)  # leave brand.* and unknown content.* for later passes
    return TOKEN_RE.sub(repl, html)


def render_block(block, partials_dir):
    btype = block.get("type")
    if not btype:
        die("a block is missing 'type'")
    fields = {k: v for k, v in block.items() if k != "type"}

    if btype == "product_grid":
        products = fields.get("products", [])
        cell_tpl = load_partial(partials_dir, "product_cell")
        cells_html = [fill_content(cell_tpl, p).strip() for p in products]
        rows = []
        for i in range(0, len(cells_html), 2):
            rows.append("<tr>\n" + "\n".join(cells_html[i:i + 2]) + "\n</tr>")
        fields = {"heading": fields.get("heading", ""), "cells": "\n".join(rows)}

    tpl = load_partial(partials_dir, btype)
    return fill_content(tpl, fields)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand")
    ap.add_argument("--profile")
    ap.add_argument("--partials")
    ap.add_argument("--content", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.brand:
        profile_path, partials_dir = resolve_brand(args.brand)
    elif args.profile and args.partials:
        profile_path, partials_dir = args.profile, args.partials
    else:
        die("provide --brand OR (--profile AND --partials)")

    with open(profile_path) as f:
        profile = json.load(f)
    with open(args.content) as f:
        spec = json.load(f)

    brand_tokens = {"brand." + k: v for k, v in flatten(profile).items()}
    brand_tokens["brand.name"] = profile.get("name", "")

    # assemble blocks with the .body wrapper around the middle region
    parts, body_open = [], False
    for block in spec.get("blocks", []):
        rendered = render_block(block, partials_dir)
        if block["type"] in STRUCTURAL:
            if block["type"] == "footer" and body_open:
                parts.append("</div>"); body_open = False
            parts.append(rendered)
        else:
            if not body_open:
                parts.append('<div class="body">'); body_open = True
            parts.append(rendered)
    if body_open:
        parts.append("</div>")
    body_html = "\n".join(parts)

    shell = load_partial(partials_dir, "_shell")
    shell = shell.replace("[[BODY]]", body_html)
    shell = fill_content(shell, {"title": spec.get("title", ""),
                                 "preheader": spec.get("preheader", "")})

    # brand token pass across the whole document
    def brand_repl(m):
        tok = m.group(1)
        if tok.startswith("brand."):
            return brand_tokens.get(tok, m.group(0))
        return m.group(0)
    shell = TOKEN_RE.sub(brand_repl, shell)

    # report + blank any leftover tokens so nothing broken ships silently
    leftover = sorted(set(TOKEN_RE.findall(shell)))
    if leftover:
        sys.stderr.write("WARN unresolved tokens (blanked): " + ", ".join(leftover) + "\n")
        shell = TOKEN_RE.sub("", shell)

    with open(args.out, "w") as f:
        f.write(shell)
    print("OK wrote %s (%d bytes)" % (args.out, len(shell)))
    if leftover:
        sys.exit(3)


if __name__ == "__main__":
    main()
