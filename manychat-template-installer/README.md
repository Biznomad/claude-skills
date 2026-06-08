# manychat-template-installer

## Why this exists

ManyChat's public API does **not** support creating flows. Templates (UI feature) let us save an entire ecosystem in a master account and share a permanent install URL. This skill drives the install wizard for a new client account via Playwright, then patches every `{{placeholder}}` token (brand name, product names, URLs, discount codes) per a per-client YAML — turning a 6-flow / 7-sequence build into a 5-minute deploy instead of a 6-hour manual clone.

## Install

```bash
pip install playwright pyyaml
playwright install chromium
```

## First-time: build the master template

Build the canonical flow ecosystem in the Biznomad master ManyChat account using `{{placeholder}}` tokens wherever brand-specific text appears (see `docs/v1-wellness-build-spec.md` in the Vicelle repo for the reference build). Save it as a Template and copy the install URL. Drop it into the client YAML's `template_url`.

Use the literal tokens — they must round-trip through the install wizard intact:

- `{{brand_name}}`, `{{owner_first_name}}`, `{{shop_url}}`, `{{support_email}}`
- `{{product_1_name}}`, `{{product_1_url}}`, etc.
- `{{discount_code_welcome}}`, `{{free_shipping_threshold}}`

Tags & fields in the master should be prefixed `PLACEHOLDER_` so the rename pass can target them.

## Per-client run

```bash
cd ~/.claude/skills/manychat-template-installer

# Copy the example, fill in client values, save as configs/<slug>.yaml
cp schema.example.yaml configs/vicelle.yaml
$EDITOR configs/vicelle.yaml

# First run for a new client: interactive login
python install.py --config configs/vicelle.yaml --interactive-login

# Subsequent runs reuse the saved browser session
python install.py --config configs/vicelle.yaml

# Walk without mutating
python install.py --config configs/vicelle.yaml --dry-run
```

The script always asks: which account? Confirm in the opened Chromium window before pressing Enter.

## YAML schema (reference)

| Key | Type | Required | Notes |
|---|---|---|---|
| `client_slug` | string | yes | must match filename stem |
| `template_url` | https URL | yes | from master ManyChat account |
| `target_page_name` | string | yes | the FB/IG page in the target account |
| `placeholders` | mapping | yes | nested dicts are flattened: `product_1.name` → `product_1_name` |
| `placeholders.brand_name` | string | yes | enforced |
| `placeholders.owner_first_name` | string | yes | enforced |
| `placeholders.shop_url` | string | yes | enforced |
| `placeholders.support_email` | string | yes | enforced |
| `flows` | list of strings | yes | flow display names expected post-install |
| `tag_renames` | mapping | optional | `PLACEHOLDER_X: BRAND_X` |
| `field_renames` | mapping | optional | renames in Settings > Custom Fields |
| `post_install_actions` | list of dicts | optional | e.g. `{type: set_default_reply, text: "..."}` |

Full example: [`schema.example.yaml`](./schema.example.yaml)

## File layout

```
manychat-template-installer/
  SKILL.md                  # frontmatter + agent invocation guide
  README.md                 # this file
  install.py                # main entrypoint
  schema.example.yaml       # canonical example
  lib/
    playwright_helpers.py   # wait_for_text, click_when_visible, text replace, screenshots
    yaml_loader.py          # validating loader
  configs/                  # per-client YAMLs (gitignore credentials!)
  logs/                     # auto-created at run time
```

## Browser data isolation

Each client gets `~/.manychat-installer-browser-data/<client_slug>/`. Cookies, tokens, and saved sessions never cross client boundaries. Per `/Users/biznomad/CLAUDE.md` — strict project isolation, no exceptions.

## Known limitations & TODOs

- ManyChat UI selectors are unknown until first proving run. ~10 `# TODO: confirm selector` markers in `install.py` and `lib/playwright_helpers.py` need filling in via `playwright codegen` during the Vicelle prove-out session.
- No diff-style "what would change" preview — `--dry-run` only logs intent.
- The verify pass relies on scraping canvas inner text; an export-JSON path would be more robust (TODO: investigate ManyChat's flow JSON export endpoint).
- No retry / partial-resume — a mid-run failure requires re-running from scratch (template install is idempotent only if the wizard supports re-installation).
- Free ManyChat accounts cannot install Templates; target must be Pro.
- 2FA flows force `--interactive-login` mode.

## Smoke test

```bash
cd ~/.claude/skills/manychat-template-installer && python -c "import install"
```

Should return cleanly with no exceptions.
