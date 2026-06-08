#!/usr/bin/env python3
"""
Safe template renderer for Biznomad client provisioning.

Replaces sed-based {{PLACEHOLDER}} substitution that was vulnerable to:
  - special chars in client name (&, |, /, \\, newlines)
  - secret values with sed delimiters corrupting .env files
  - inline-python heredoc injection from bash variables

Usage:
    cat config.json | render.py <template.md> > output.md

Or:
    render.py --template <path> --config <json-file> --output <out-path>

JSON config is the SOURCE OF TRUTH. Bash never interpolates into Python.
All placeholders are {{KEY}} pulled directly from the JSON dict (no eval).

Supports nested access via {{platforms.shopify_domain}} dot-notation.

Unknown placeholders are left in place (with a warning to stderr) instead
of silently producing empty strings — that way template bugs are visible.
"""
import sys
import json
import argparse
import re
from pathlib import Path


PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][\w.]*)\s*\}\}")


def get_nested(d: dict, key: str):
    """Walk dot-notation key into nested dict. Returns None if not found."""
    cur = d
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


_MISSING = []  # accumulator for --strict mode


def render(text: str, ctx: dict, strict: bool = False) -> str:
    """Substitute {{KEY}} placeholders with values from ctx. Safe — never evals."""
    def sub(match):
        key = match.group(1)
        val = get_nested(ctx, key)
        # Distinguish missing-key vs present-null (codex round-2 med#5)
        if key not in _flatten_keys(ctx) and val is None:
            _MISSING.append(key)
            if not strict:
                print(f"⚠ render: unknown placeholder {{{{{key}}}}} — left in place",
                      file=sys.stderr)
            return match.group(0)
        if isinstance(val, bool):
            return "true" if val else "false"
        if val is None:
            return ""
        return str(val)
    return PLACEHOLDER.sub(sub, text)


def _flatten_keys(d, prefix=""):
    """Set of all dot-notation keys present (including null values)."""
    out = set()
    if isinstance(d, dict):
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            out.add(full)
            if isinstance(v, dict):
                out |= _flatten_keys(v, full)
    return out


def main():
    p = argparse.ArgumentParser(description="Safe template renderer (no eval, no shell)")
    p.add_argument("--template", "-t", help="Template file path", required=False)
    p.add_argument("--config", "-c", help="JSON config file (else stdin)", required=False)
    p.add_argument("--output", "-o", help="Output file (else stdout)", required=False)
    p.add_argument("--strict", action="store_true",
                   help="Exit non-zero if any placeholder is unresolved")
    p.add_argument("template_positional", nargs="?", help="Template path (positional)")
    args = p.parse_args()

    template_path = args.template or args.template_positional
    if not template_path:
        print("❌ template path required (--template or positional)", file=sys.stderr)
        sys.exit(2)

    if args.config:
        ctx = json.loads(Path(args.config).read_text())
    else:
        ctx = json.load(sys.stdin)

    if not isinstance(ctx, dict):
        print("❌ config must be a JSON object", file=sys.stderr)
        sys.exit(2)

    text = Path(template_path).read_text()
    _MISSING.clear()
    out = render(text, ctx, strict=args.strict)

    if args.output:
        Path(args.output).write_text(out)
    else:
        sys.stdout.write(out)

    if args.strict and _MISSING:
        unique = sorted(set(_MISSING))
        print(f"❌ render --strict: {len(unique)} unresolved placeholders: {', '.join(unique)}",
              file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
