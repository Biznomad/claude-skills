# Loop Spec — {{community_name}} Growth Loop

> Generated from empire-builder client config for {{slug}}.
> Governs Stage 3 (growth loop) stop conditions, verification, and supervision.
> Based on write-the-loop's 7 mandatory components.

---

## 1. Goal

One sentence, outcome-shaped:

"{{community_name}} reaches {{goal.member_count}} paying members at ${{offer.price_per_month}}/mo
({{goal.mrr}} MRR) with {{goal.content_per_week}} pieces of content shipped per week,
while maintaining a <5% monthly churn rate."

Fill in from config:
- `goal.member_count` = (ask founder at end of Stage 1, or default to 50 for month 3)
- `goal.mrr` = member_count × price
- `goal.content_per_week` = from `cadence.posts_per_week`

---

## 2. Done-check (machine-verifiable)

The loop is done when ALL of these are true simultaneously:

- [ ] `metrics.json` shows `member_count >= {{goal.member_count}}`
- [ ] `metrics.json` shows 3 consecutive weeks of `content_pieces_shipped >= {{goal.content_per_week}}`
- [ ] `metrics.json` shows `churn_rate_last_month < 0.05`
- [ ] Founder has confirmed success via Telegram `[✅ Goal reached]` button

Machine-verifiable means: read the file, check the number. Do not ask the loop
worker (that's you) whether it's done — check the actual data.

---

## 3. Step prompt (what one loop iteration does)

Each run of Stage 3 does exactly ONE of:
- (a) Reach: Generate one batch of {{cadence.posts_per_week}} content pieces for the week,
  stage to `outbox/YYYY-MM-DD/`, verify hooks match content-system.md formulas
- (b) Community: Build one Skool improvement (module, DM sequence, gamification level,
  live call agenda), stage to `outbox/`, verify it's ready to publish
- (c) Showcase: Collect or format one piece of social proof (win, testimonial, metrics
  card), stage to `outbox/`, verify the story is concrete and specific

Fresh context each time: re-read `clients/<slug>/loop-config.md` and `SESSION_STATE.md`
at the start of every run. State lives in files, not in this prompt's memory.

---

## 4. Verifier (independent of the worker)

The verifier is SEPARATE from the content generator. After building:

**Content verification (every run):**
- Re-read the staged file from `outbox/` — confirm it exists and is non-empty
- Check hook against content-system.md formulas — does it match a real formula?
- Check voice against `brand.keywords_use` and `brand.keywords_avoid`
- If content references a URL: use `/browse` to confirm the URL resolves

**Metric verification (every run):**
- Read `clients/<slug>/metrics.json` — compare member_count to last run
- If no movement in 3 runs → trigger no-progress stop condition

The orchestrator (empire-builder) runs the verification check, not the content
generation subagent. Never trust "I believe this is correct." Check the actual output.

---

## 5. Stop conditions (all four required)

### SUCCESS
- `metrics.json` member_count >= goal AND 3 consecutive weeks content >= goal
- Action: Post a celebration Telegram card. Surface to founder: "Goal reached!
  Let's set the next milestone." Suggest: double member count, add coaching tier,
  or start a new community vertical.

### MAX ITERATIONS
- Cap: 52 loop runs (approx. 1 year at weekly cadence)
- Action: Stop, write a full SESSION_STATE summary, surface to founder via Telegram:
  "We've completed 52 growth loop iterations. Here's where things stand: [summary].
  Ready to define the next chapter?"

### BUDGET
- Context/cost cap: if 80%+ of session token budget consumed without completing the
  increment, stop, save position in STATE.md, and tell the founder to restart
  `/empire-builder <slug>` in a fresh session.

### NO PROGRESS
- Trigger: same track produces no measurable output change for 3 consecutive runs
  (member count flat, content staged but metrics unchanged, or same content type
  generated repeatedly)
- Action: surface to founder via Telegram: "The [track] track may be saturated.
  Suggested pivot: [specific alternative increment]. Approve?" + `[✅ Yes] [📝 Edit]`

---

## 6. State

State is persisted in two files so the loop can resume after any kill/crash:

**`clients/<slug>/SESSION_STATE.md`** — running journal (newest H2 entry at top)
Format: `## YYYY-MM-DD Track (a|b|c) — [what was built]`
Ends with: `Next loop track: ([a|b|c])`

**`clients/<slug>/metrics.json`** — machine-readable progress tracker
Fields: `last_run`, `member_count`, `content_pieces_shipped`, `track_last_run`, `run_count`

Both files are read at Step 1 of every loop run. If either file is missing, the loop
starts fresh (safe — idempotent by track rotation).

---

## 7. Supervision surface

The founder supervises via two channels:

**Telegram DM** (if `telegram.dm_chat_id` is configured):
- Every loop run posts a branded card (see `templates/telegram-changelog.md`)
- Cards arrive as `sendPhoto` with `InlineKeyboardMarkup`
- Default button set: `[✅ Publish outbox] [📝 Edit draft] [⏭ Skip this one] [📊 Stats]`
- Decision-required variants: `[✅ Approve] [❌ Reject] [📝 Edit]`
- Callback handlers live in Hermes or the growth-loop bot (if configured)

**Outbox review** (always available, even without Telegram):
- All staged artifacts live in `clients/<slug>/outbox/YYYY-MM-DD/`
- Founder can review, edit, and publish at her own pace
- Nothing is posted automatically

**How the founder intervenes:**
- Edit a staged file before publishing: open `outbox/YYYY-MM-DD/[file]`, edit, publish
- Skip an increment: tap `[⏭ Skip]` in Telegram or just don't publish the outbox folder
- Change direction: run `/empire-builder <slug>` and tell the skill what to adjust
