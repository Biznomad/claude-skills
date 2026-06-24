---
name: gstack-browse-reference
description: Hard-won working patterns for the gstack `browse` CLI (headed-Chromium automation used for logged-in verification and scraping). Load when driving gstack browse — correct binary path, the `js` vs `eval` gotcha, key names, and `@e##` element refs over CSS. Saves ~1,200 tokens/session of re-discovery.
allowed-tools: Bash, Read
---

# gstack `browse` CLI — working reference

The gstack `browse` binary drives a headed Chromium with a persistent profile (used for logged-in automation and verification). These are the patterns that actually work; the obvious alternatives fail.

## Binary path is fixed — call it directly

```bash
B="$HOME/.claude/skills/gstack/browse/dist/browse"
"$B" snapshot -i
```

Skip the `git rev-parse` discovery dance — the path never moves.

## Use `js`, never `eval`

```bash
"$B" js "document.querySelector('#price').textContent"
```

`$B eval "..."` fails with "File not found". For any in-page DOM script, use the `js` subcommand.

## Key names

- Press Enter with `$B press "Enter"` — **not** `"Return"` (fails).

## Prefer `@e##` element refs over CSS selectors

Run `$B snapshot -i` to get an interactive snapshot with stable refs like `@e42`, then act on them:

```bash
"$B" snapshot -i      # read the @e## refs
"$B" click @e42
```

CSS selectors often match multiple elements or time out. `@e##` refs are unambiguous.

## Heavy-use stability

Headed Chromium drops its session / navigates to `about:blank` after ~150s of heavy use. Keep in-page loops under ~120s and reconnect (`browse connect`) on crash — the persistent-profile login is restored on reconnect.
