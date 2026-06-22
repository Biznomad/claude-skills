# Growth Loop config — REI deal engine (the original, fully worked)

This is the config that produced ~30+ increments on @Biz_RealEstate_Wholesaler_bot.
Copy its shape for a new business.

## Identity
- **Business:** Ohio (Cuyahoga) real-estate wholesaling deal engine — sources distressed
  owners from county records, prices them, mails them, matches deals to cash buyers.
- **Asset goal:** a $25–50k-grade sellable asset (turnkey, runs itself).
- **Owner / changelog reader:** Naeem · Telegram DM chat-id `5165464044`.

## Deploy target
- **Runs on:** Biznomad VPS, SSH alias `biznomad` (187.77.10.20). Hermes profile
  `growth-rei-bot`. Public app behind Cloudflare at `deals.biznomad.io`.
- **Interpreter:** `/opt/hermes-agent/venv/bin/python` (NOT venv/bin/pip — use `python -m pip`).
  API service `rei-operator-api` (FastAPI :8090); console at `/opt/dealroom/ops/index.html`.
- **Live vs dev:** the VPS is live; confirm before restarting services / pushing console.

## The three rotation tracks
- **(a) Sourcing / outreach tool:** new county channel, mail format, cadence, dispo, or
  data-hygiene tool (`/root/.local/bin/rei-*`, extensionless Python).
- **(b) Deal Room UI/UX:** the operator console (`/opt/dealroom/ops/index.html`) — views,
  dossier, triage, command palette, wiring CLI tools into the UI.
- **(c) Telegram reporting:** visual PNG cards (PIL) posted to the DM; refresh stale
  flagships when saturated.

## Memory
- **Project file:** `/Users/biznomad/.claude/projects/-Users-biznomad/memory/project_growth_rei_browser.md`
- **State scratchpad:** `.../memory/SESSION_STATE.md` (prepend newest H2 each run).
- **Capability registry:** `/root/.hermes/profiles/growth-rei-bot/SOUL.md` (the bot's tool list).

## Telegram changelog
- **Bot token:** `grep "^TELEGRAM_BOT_TOKEN=" /root/.hermes/profiles/growth-rei-bot/.env | cut -d= -f2`
- **DM chat-id:** `5165464044`
- **Buttons:** `[🏠 Open the Deal Room (url)] [🔍 Top 3 deals (rei:top)] [📊 Pipeline (rei:pipe)]`
  — callbacks handled by `patch_rei_buttons.py` in the profile (verify handlers exist).

## Brand / visual
- **Voice:** direct, builder, sharp; short wrap-ups (~6–10 lines).
- **Card style:** near-black bg `(8,11,18)`, panels `(18,22,33)`, acid green `(204,255,61)`,
  fonts DejaVuSans / DejaVuSans-Bold on the VPS. Header eyebrow + headline + proof stat +
  footer line naming the increment + track.
- **UI icon rule:** emoji OK in this internal console + Telegram; NO emoji in PIL cards
  (tofu) — draw shapes/plain text.

## Safety / gotchas
- ArcGIS source: `Parcel_Analytics_(PUBLIC_DRAFT_)/FeatureServer/0/query` (210 fields).
  Date filters need `timestamp 'YYYY-MM-DD HH:MM:SS'`; some "owner" fields need NOISE
  regex (gov/land-bank/funds/LPs); two code-violation sources coexist (old "Code Violation"
  + new "Code Violations (County)").
- Shared `/etc/rei-mail.env` holds SECRETS (OPS_PASSWORD, API keys) alongside MAIL_* —
  only ever read/write the MAIL_* lines, preserve the rest.
- Console deploys: inject before the LAST `</body>` (genOffer/genAssignment have `</body>`
  in JS strings); patch via scp'd .py, restart `rei-operator-api` after API changes.
- Tools are idempotent (dedupe on parcelpin) + conservative (mark, don't delete; rei-verify
  soft-flags owner-changed/recheck, never purges).
