# Growth Hacker Engine — Reference

**Loaded when:** the empire-builder loop rotation lands on track (a) for Inevitably Hers.
**Parallels:** `growth-loop-engine.md` (the general loop engine).

Read this reference, then run the 12-step GH cycle below.

---

## When this fires

Track (a) "Reach / Acquisition" runs in Growth-Hacker mode. Instead of generating another
standalone reach asset, the GH wraps the run as a **measured experiment** — same deliverable
quality, but with a hypothesis, a metric, a target, and a result logged in the ledger.

The rotation stays `a → b → c`. The run-number increments normally. SESSION_STATE format
stays the same. Only the *content* of the track-(a) run changes.

---

## Pre-flight (always read these first)

1. `clients/inevitably-hers/growth-hacker/README.md` — the GH persona, funnel, ICE rules,
   asset library, brand voice, safety rules.
2. `clients/inevitably-hers/growth-hacker/experiments.json` — the live ledger.
3. `clients/inevitably-hers/growth-hacker/metrics-history.json` — funnel time series.
4. `clients/inevitably-hers/SESSION_STATE.md` — top entry for current run # and next track.
5. `clients/inevitably-hers/metrics.json` — current north-star value (member_count).
6. `clients/inevitably-hers/DECISIONS_LOG.md` — check for any publish/measured/won/killed
   decisions Ashley logged via Telegram buttons since the last cycle.

---

## The 12-Step GH Cycle

### Step 1 — Read state (non-negotiable)
Read all 6 pre-flight files above. Extract:
- Current run number from SESSION_STATE top entry.
- Any experiments with `status: running` + their `measure_after` dates.
- Any `won` experiments not yet `scaled`.
- Any decisions in DECISIONS_LOG logged since the last GH entry in SESSION_STATE.
- Current `member_count` from metrics.json.

### Step 2 — Triage the ledger (pick the cycle's job)
Evaluate in priority order:

**2a. MEASURE** (highest priority): is there a `status: running` experiment whose
`measure_after` date has passed AND a result has been entered in DECISIONS_LOG or reported?
→ If yes, this cycle measures it. Skip to Step 6.

**2b. SCALE-UP**: is there a `status: won` experiment not yet `scaled`?
→ If yes, this cycle designs the scale-up (a new experiment that amplifies the winner,
  one step up the ICE score or to the next funnel stage).

**2c. PROPOSE NEW**: no running experiment, no unscaled winner.
→ Identify the bottleneck funnel stage (lowest-converting stage with data, or earliest
  stage without data).
→ Enumerate 2–3 levers from the README asset library that address that stage.
→ ICE-score each (Impact × Confidence × Ease, 1–5 each; score = product).
→ Pick the highest-scoring lever as the next experiment.

### Step 3 — Idempotency guard
Compute the signature: `<funnel_stage>|<channel>|<lever_slug>`.
Check `experiments.json` for any non-killed entry with the same signature.
If found: skip to the next highest-ICE candidate. Re-running is safe.

### Step 4 — One-line approach statement (write-the-loop discipline)
State the approach in one sentence before building. Example:
`"Testing whether the Run 64 bio hook lifts profile→opt-in rate; staging an A/B bio variant."`

### Step 5 — Build the staged creative
Write the outbox asset to `outbox/<YYYY-MM-DD>/GH-<id>-<slug>.md`.

**What the outbox file must contain:**
1. **The experiment brief** (for Ashley): hypothesis in plain language, what you're testing,
   why this funnel stage, why this lever, the ICE score rationale.
2. **The exact creative to publish** — the actual copy, scripts, bio text, caption text,
   hashtag set, DM script, whatever the lever is. A/B variants where it's a head-to-head
   test. Publish-ready. Brand-voice compliant.
3. **What to measure and where to find the number** — e.g. "Instagram Insights → External
   link taps for the next 7 days" or "Skool member list → count new paid members in 7 days."
   Be specific: tell Ashley exactly which screen to look at and what number to note.
4. **The `measure_after` date** — how many days post-publish before reporting a result.
   Short tests: 7 days. Longer build assets (bio changes): 14 days.
5. **The target** — what counts as a win.

**Never auto-post. Staged only.**

### Step 6 — (If measuring) Record the result
If this cycle is a measurement run:
- Read the result from DECISIONS_LOG or prompt the next Telegram card to request it.
- If result available: compute win/kill vs target.
  - **Won**: set `status: won`, log `result`, `decision`, `learnings`.
  - **Killed**: set `status: killed`, log `result`, `decision`, `learnings` (one sentence
    on what the data says and what to try next).
- Append a row to `metrics-history.json`:
  ```json
  { "date": "YYYY-MM-DD", "paying_members": N, "optins": X, "follows": Y,
    "impressions": Z, "experiments_running": N, "experiments_won": N }
  ```
- Set `updated` timestamp on the experiment.
- If result not yet available: leave `status: running`, note in SESSION_STATE.

### Step 7 — Update the ledger
Write the new or updated experiment entry to `experiments.json`:
- New entry: append to `experiments[]`, increment `next_experiment_id`.
- Updated entry: find by `id`, update the fields.
- Verify `experiments.json` parses as valid JSON before continuing.

### Step 8 — Independent verification
Before updating state and pushing:
- Re-read the outbox file — confirm it exists and is non-empty.
- Confirm `experiments.json` parses (no JSON errors).
- Confirm the experiment id is present in the ledger.
- Brand-keyword check on Ashley-facing copy: no "hustle", "grind", "woo".
- If any URLs referenced in the asset: use `/browse` to confirm they resolve.
- If this is a measurement run: confirm the math (result vs target comparison) is correct.

### Step 9 — Check stop conditions
(Reuse the conditions from `loop-spec.md`, plus one GH-specific condition.)

**GH no-progress:** if 3 consecutive experiments have `status: killed` with no movement
in `paying_members` between them → pause and surface a pivot card via Telegram:
```
🧪 Growth Hacker — Pivot Needed
3 experiments killed, no member movement.
The current funnel stage may not be the bottleneck.
[✅ Switch funnel stage] [📝 Reframe approach] [⏸ Pause GH mode]
```

### Step 10 — Update SESSION_STATE.md
Prepend a dated H2 in the existing format. Use a distinctive prefix so GH cycles are
scannable:
```
## 2026-06-27 GH-cycle (track a) — GH-001 Bio Hook Opt-in Test [staged]

**Experiment:** GH-001
**Funnel stage:** opt-ins · **Channel:** Instagram
**Hypothesis:** Bio Version A hook → profile→opt-in rate ≥ 8%
**Asset:** outbox/2026-06-27/GH-001-bio-hook-test.md
**Measure after:** 2026-07-04

Next loop track: (b)
```

The `Next loop track:` line must be the last line and must correctly advance the rotation
(a → b). This preserves the rotation invariant that the OS and push scripts depend on.

### Step 11 — Push to OS state.json
Run `bash inevitably-hers-affiliate/scripts/push-gh-state.sh` with the updated experiment
data. This script does the read-then-append (GET → merge → POST) — never call the state
API directly with a bare POST that would replace the `experiments` array.

The push updates:
- `growthHacker.experiments[]` (append or update the experiment)
- `growthHacker.funnelTrend[]` (append if a measurement was recorded)
- `growthHacker.summary` (recomputed: running count, won count, kill count, win rate)
- `loop` scalars (totalRuns, nextTrack, lastRun, lastAsset)
- `assets[]` (append this run's asset, read-then-append)

### Step 12 — Post the Telegram card
Send the Telegram changelog card (see `templates/telegram-changelog.md` for the base format).
The GH card uses this caption structure:

```
🧪 Inevitably Hers — Growth Hacker
GH Cycle <N> · Experiment <id> · [STATUS]

Funnel stage: <stage>  ·  Channel: <channel>
Hypothesis: <one sentence>

Lever: <what to publish>
Metric: <what to measure>  ·  Target: <target>
Measure after: <date>

📂 Ready in outbox:
<outbox path>

What to do: <one sentence plain-language instruction>

North star: <member_count> / 100 paying members  ·  Win rate: <N>%
Next track: (<b|c>) <track name>
```

**InlineKeyboardMarkup (all handler-backed):**
```
Row 1: [✅ Publish outbox]  →  publish_ih_GH<id>
       [📝 Edit draft]      →  edit_ih_GH<id>
Row 2: [🏆 Mark won]        →  ghwon_ih_GH<id>
       [🪦 Mark killed]     →  ghkill_ih_GH<id>
Row 3: [⏭ Skip]            →  skip_ih_GH<id>
       [📊 Dashboard]       →  dash_ih
```

Handler behaviors (Hermes appends to DECISIONS_LOG.md):
- `publish_*` → log "published GH-<id>" → experiment status becomes `running` next cycle
- `ghwon_*` → log won decision + prompt for result number → next cycle records it
- `ghkill_*` → log killed decision + prompt for result number → next cycle records it
- `dash_*` → reply with `/os` URL deep-linked to Growth Hacker tab
- `skip_*` → log skip; experiment stays `staged`
- `edit_*` → reply with the outbox asset path for Ashley to edit locally

**Fallback:** if `telegram.dm_chat_id` is null, write the card content to
`outbox/<YYYY-MM-DD>/telegram-card.md` instead.

**Wrap-up:** 6–10 lines. Experiment id + hypothesis, outbox path, what Ashley publishes,
what metric to report and when, next track.

---

## Example: first GH cycle (Run 66)

```
GH mode: track (a) Reach — Run 66

Pre-flight: experiments.json empty, member_count=0, SESSION_STATE next track=(a).
Triage: no running experiments → propose new.
Bottleneck: earliest stage with no data → impressions.
Candidates:
  - Short-form video hook test (Run 40 scripts + hashtag rotation) | I=4 C=3 E=4 → 48
  - TikTok bio Version A publish (Run 64) | I=3 C=4 E=5 → 60
  - Instagram Reel repurposing (Run 40 script 1) | I=4 C=2 E=3 → 24
Pick: TikTok bio Version A (score 60, easiest to deploy immediately from Run 64 asset).
Approach: "Stage Run 64 TikTok bio Version A as GH-001; measure profile→opt-in rate over 7 days."
Build: outbox/2026-06-27/GH-001-tiktok-bio-version-a.md
```

---

## Hard rules (never skip)

1. Always read the ledger before proposing anything.
2. Never propose an experiment with the same signature as a non-killed entry.
3. Never auto-post. Staged only.
4. Never request or store social media credentials.
5. Never hardcode secrets.
6. The SESSION_STATE `Next loop track:` line must be the last line of the H2 entry.
