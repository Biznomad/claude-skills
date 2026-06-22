---
name: growth-loop
description: >
  Autonomous build-loop that compounds a client business into a high-grade,
  sellable ASSET — one concrete, verified increment per run. Rotates across three
  business-specific value tracks, self-QAs every change, updates persistent memory,
  and posts a visual changelog to the business's Telegram DM with inline buttons.
  Use when the user says "run the loop", "ship an increment", "continue the <business>
  buildout", "/growth-loop <business>", or sets it up as a repeating /loop or cron.
---

# Growth Loop — autonomous asset-builder

Turn any client business into a $25–50k-grade (or higher) sellable asset by shipping
**one concrete, valuable, verified increment per run**, rotating across the business's
three value tracks so all three progress over time. Battle-tested on a real-estate deal
engine (~30+ increments); the methodology below is what makes it actually compound
instead of thrash.

## 0. Load the business config (always first)

Each business has a config at `<memory-dir>/loop-config-<business>.md` (see
`loop-config-template.md`). If the user names a business, load its config. If no config
exists, ask the 8 config questions (below) once, write the config, then proceed.

The config defines: **name · asset goal · deploy target · the 3 rotation tracks ·
memory file + state file paths · Telegram bot-token source + DM chat-id · brand/voice ·
safety constraints.**

## 1. The loop (every single run)

1. **Read state.** Read the project memory file and the `SESSION_STATE` scratchpad
   (newest entries at top). This is non-negotiable — it prevents re-doing work and tells
   you the last track shipped.
2. **Pick the track.** Rotate a → b → c. The last state entry ends with
   "Next loop track: (x)" — do that one.
3. **Pick the single highest-value increment** in that track. One thing. Not three.
   Bias to what a buyer of this asset would pay more for, or what removes real operator
   friction.
4. **Think before heavy work.** For a new tool/migration/non-trivial feature, state the
   approach in one line first.
5. **Build it** — idempotent, reversible, safe (see Lessons).
6. **Deploy** — confirm account/server/live-vs-dev before any prod push; deploy code via
   scp'd files, not ssh heredocs.
7. **VERIFY** — this is half the job:
   - Self-QA every generated image/render against spec, and state pass/fail *before*
     showing the user. Check for tofu (missing glyphs), overflow, wrong numbers.
   - Browser-verify any UI change live (cache-bust with `?v=<ts>`), confirm **0 console
     errors**, and read back the actual DOM/state — don't trust timing.
   - Hit new backend routes with real calls; check edge cases degrade gracefully.
8. **Update memory** — prepend a dated H2 to `SESSION_STATE`, append a detail block to
   the project file, end with "Next loop track: (next)". Update any tool/capability
   registry (e.g. the bot's SOUL.md). Convert relative dates to absolute.
9. **Post the visual changelog** to the Telegram DM — a branded card image + a caption
   + **InlineKeyboardMarkup buttons with working callbacks** (mandatory; see §3).
10. **Wrap up in ~6–10 lines.** Detail lives in memory + the changelog, not the chat.

## 2. Hard-won lessons (apply every run — these are why it works)

**Rendering (PIL/Pillow cards):**
- DejaVu (and most server fonts) can't render color emoji → they come out as tofu boxes
  (⌘ 🔥 ⬇ ✓ 💵 📬 etc.). In *generated images*, draw shapes (`d.ellipse`, `d.line`) or use
  plain text; emoji are fine in **HTML and Telegram captions**, not in PIL.
- `·` (U+00B7), `—` (em dash), `→` `★` render fine in DejaVu; smart quotes too. Verify by
  eye anyway.
- Auto-size canvases to content and crop; always re-view a render after a numbers change.
- Watch source-string escaping: a Python tool that needs a literal `\uXXXX` in its output
  vs an actual unicode char — get it backwards and you ship tofu-text or a SyntaxError.

**Deploying code to a server:**
- Write the patch/tool as a local file → `scp` it → run with the remote interpreter.
  Do **not** pipe Python via `ssh '... python -c "..."'` or heredocs — backticks, `$`, and
  quotes get bash-substituted and silently corrupt the code.
- Patch files in place with a small scp'd Python script that does exact `str.replace`
  with `assert old in s` guards + `ast.parse(s)` before writing + a `.bak.<ts>` copy.
- Injecting into HTML: insert before the **LAST** `</body>` via `s.rfind("</body>")` —
  inline `<script>` strings often contain `</body>` literally (count tags after).
- Editing the same string that appears twice: know whether you want one or all
  occurrences; globs that match a sibling dir (`campaign-*` also matching `campaign-blind-*`)
  are a classic latent bug — exclude explicitly.

**Data tools (sourcing/enrichment/mutation):**
- Idempotent: dedupe on a stable key (e.g. parcel/record id); re-running must not double-insert.
- Conservative + reversible: **mark, don't delete**; soft-flag for review rather than
  auto-purge. Use a unique note/marker so a run is fully revertible.
- QA the output before trusting it: sample rows, check for noise (gov/institutional owners,
  duplicates, wrong-side entities like buyers-as-sellers, condo/HOA artifacts). When you
  find junk, add the filter, **revert the bad run via its marker, re-run clean.**
- If a field looks too good/weird (a count that equals the all-time total, an age field
  that's 0 at "75+"), probe it before building on it.
- Re-verify accumulated data against the live source periodically — stale = the difference
  between a lead list and an asset.

**UI verification:**
- A headless browser blocks `window.open` popups → intercept it to capture output, or
  render via a blob URL to screenshot.
- `let`-scoped vars aren't on `window` — read the bare identifier, not `window.X`.
- Wait for async loads (dossier/detail fetches) before asserting; re-check, don't assume.

**Telemetry of your own progress:** keep wrap-ups short; the user reads the changelog +
memory, not a wall of text.

## 3. Telegram changelog (mandatory format)

Every changelog post — and every cron/notification this loop creates — MUST include
`reply_markup: InlineKeyboardMarkup` with action buttons backed by a real callback handler
(a button with no handler is a bug). **Put UP TO 10 decision cards (buttons) on every
update** (Naeem runs ops from his phone — each update must be one-tap actionable; "up to"
is a ceiling, use as many *meaningful* handler-backed buttons as exist, don't pad). Wire any
missing handlers before posting. Standard set: an `[🌐 Open the app]` URL row + showcase
actions (primary metric / top items / snapshot) + the decision row
`[✅ Acknowledge] [💾 Save] [⏭ Skip] [🔍 Investigate]` (ack/save/skip → toast + log a
decision; investigate → post the key report). Decision-required updates swap in
`[✅ Approve] [❌ Reject] [📝 Edit]` etc. — still all handler-backed. Applies to EVERY
business's loop. See memory `feedback_changelog_decision_cards`.
Build the card as a branded PNG (header eyebrow + headline + the proof/stat + a footer
line naming the increment + track), caption in the brand voice, then `sendPhoto` with the
keyboard. Verify the callback_data values have handlers before relying on them.

## 4. Picking the increment (quality bar)

- **Track (a) "growth engine":** a new way to bring in or convert demand (sourcing,
  outreach, a response/closing tool). When the obvious veins are mined, build the tool
  that makes existing volume convert better, or a data-hygiene tool that protects spend.
- **Track (b) "the product/UX":** make the operator's daily job faster + the asset feel
  premium (dashboards, focused workflows, one-click actions, wiring CLI tools into the UI).
- **Track (c) "showcase reporting":** make the automation's value legible to the owner/buyer
  (visual cards). When saturated, **refresh a stale flagship** (accuracy matters for a
  sellable asset) instead of adding fatigue.
- Each increment should be demonstrable *now* (real numbers, a working screenshot), not
  theoretical.

## 5. Config questions (ask once if no config exists)

1. Business name + what it does, and the asset goal (e.g. "$25–50k sellable").
2. Where does it run / deploy? (SSH alias, VPS path, local repo, hosting.)
3. What are its **three value tracks**? (the a/b/c — map to the business's real levers.)
4. Memory file path + state-scratchpad path.
5. Telegram: bot-token location (env file path) + the DM chat-id to post to.
6. Brand voice + any visual style (colors, "no emoji in product UI", logo path).
7. Safety constraints (which account/server is live, what needs confirmation, secrets to
   never touch).
8. Any domain gotchas (data sources, APIs, sandbox limits).

Write the answers to `loop-config-<business>.md` so future runs are turnkey.

## 6. Safety (always)

- Confirm account / server / live-vs-dev before any production or outward-facing push;
  approval in one context doesn't carry to the next.
- Never exfiltrate cookies, tokens, or secrets; never bypass auth or an auto-mode gate;
  no destructive/mass actions without explicit confirmation.
- Sending to an external service publishes it — confirm before posting anything public.

---
*This skill is the generalized form of the REI deal-engine loop. See
`examples/rei-config.md` for a fully-worked configuration.*
