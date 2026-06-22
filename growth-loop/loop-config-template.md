# Growth Loop config — <BUSINESS>

Copy this to `<memory-dir>/loop-config-<business>.md` and fill it in. The skill reads it
at the start of every run.

## Identity
- **Business:** <name + one line on what it does>
- **Asset goal:** <e.g. "$25–50k sellable asset" / "$X MRR" / "turnkey ops">
- **Owner / who reads the changelog:** <name + Telegram chat-id>

## Deploy target
- **How it runs:** <SSH alias + host / local repo path / hosting platform>
- **Interpreter / runtime:** <e.g. /opt/venv/bin/python, node, n8n sandbox>
- **Live vs dev:** <which is production; what must be confirmed before pushing>

## The three rotation tracks
Map a/b/c to this business's real value levers. Examples:
- **(a) Growth engine:** <demand in / conversion — sourcing, outreach, closing tools>
- **(b) Product / UX:** <the operator console / customer experience / dashboards>
- **(c) Showcase reporting:** <visual proof-of-value to the owner/buyer>

## Memory
- **Project memory file:** <path to the durable project notes>
- **State scratchpad:** <path to SESSION_STATE (prepend newest H2 each run)>
- **Capability registry:** <optional — a SOUL.md / tools list to keep current>

## Telegram changelog
- **Bot token source:** <env file path + key, e.g. grep TELEGRAM_BOT_TOKEN .env>
- **DM chat-id:** <numeric chat id>
- **Buttons:** every post needs InlineKeyboardMarkup w/ working callbacks. Default set:
  `[🏠 Open the app] [📊 <metric>] [🔍 <top items>]`. Callback handler service: <where>

## Brand / visual
- **Voice:** <direct/playful/premium…>
- **Card style:** <bg/accent colors, fonts available on the deploy host>
- **UI icon rule:** <e.g. "no emoji in product UIs — premium SVG/Lucide" vs "emoji ok">

## Safety / gotchas
- <which account/server is live; what needs explicit confirmation>
- <secrets to never touch; auth/auto-mode gates not to bypass>
- <data sources, API limits, sandbox constraints, known quirks>
