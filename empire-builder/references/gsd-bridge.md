# GSD Bridge — How to Invoke GSD from Empire Builder

Reference for Stage 1 (Plan) and Stage 2 (Build) of SKILL.md.
This file prevents you from guessing how GSD works — follow these exact patterns.

---

## Stage 1 — Bootstrap the project

### Set working directory
All GSD commands run with `clients/<slug>/` as the working directory. GSD creates
`.planning/` relative to where it's invoked. Create the dir first via `new-client.sh`.

### Render the PRD
Before invoking GSD, render `templates/prd.md` with the client config and write to
`clients/<slug>/prd.md`. This is the `--auto` input document.

### Bootstrap command
```
/gsd-new-project --auto @clients/<slug>/prd.md
```

Working directory must be `clients/<slug>/`. GSD will:
1. Read the PRD
2. Create `clients/<slug>/.planning/PROJECT.md`
3. Create `clients/<slug>/.planning/REQUIREMENTS.md`
4. Create `clients/<slug>/.planning/ROADMAP.md`
5. Create `clients/<slug>/.planning/STATE.md`

### Reconcile the roadmap
After GSD generates the roadmap, compare to `templates/roadmap.md`. The canonical
phase sequence is: Foundation → Social presence → Content engine → Skool setup →
Funnels → Launch. If GSD named phases differently, patch ROADMAP.md to match.

### Check state via CLI
```bash
node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" state json
```
Returns: `current_phase`, `plans_total`, `progress`, `status`. Use this to determine
where to pick up in the router (SKILL.md §2).

---

## Stage 2 — Execute the build

### Autonomous execution (founder says "start building")
```
/gsd-autonomous
```
GSD will run all phases from current state: discuss → plan → execute → verify for each.
This is the "hands-off" path. Stop-and-surface is still required between phases (override
`gsd-autonomous` behavior by telling it to pause between phases for founder review).

### Step-by-step execution (founder wants control)
```
/gsd-next
```
GSD reads STATE.md and ROADMAP.md, picks the next action, invokes it automatically.
Call `/gsd-next` repeatedly to advance one step at a time. Each call invokes one of:
- `/gsd-discuss-phase N` — clarifies assumptions for phase N
- `/gsd-plan-phase N` — creates PLAN.md for phase N
- `/gsd-execute-phase N` — executes phase N (spawns subagents)
- `/gsd-verify-work` — verifies phase N completion

### Per-phase manual control
```
/gsd-discuss-phase 1
/gsd-plan-phase 1
/gsd-execute-phase 1
/gsd-verify-work
```
Repeat for phases 2-6. Use this if you want maximum control or if a phase needs
special handling (e.g. Phase 3 content generation needs the content system doc).

### Check phase status
```bash
node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" phase json <N>
```
Returns per-phase status: has CONTEXT.md, has PLAN.md(s), has SUMMARY.md(s),
has VERIFICATION.md. Use to determine if a phase is complete before advancing.

### Check full roadmap status
```bash
node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" roadmap analyze
```
Returns all phases with `disk_status` (not_started / in_progress / complete).
Use to determine overall build progress.

---

## Content generation phases (Phase 3 — Content engine)

Phase 3 requires content skill delegation. Before GSD executes Phase 3:
1. Read `references/content-system.md` into context.
2. Read the client config for `brand.voice`, `community.topic`, `community.audience`,
   `community.promise`, `channels[]`.
3. Invoke `/create-viral-content` with the client config as context for each content
   piece type (Reel, TikTok, Thread, YouTube outline).
4. Alternatively invoke `/biznomad-social-engine` for a full social content package.
5. Stage all output to `clients/<slug>/outbox/` via `scripts/stage-content.sh`.

---

## Stage artifact flow (what each phase produces in outbox/)

| Phase | GSD creates | Empire-builder stages to |
|-------|------------|--------------------------|
| 1 Foundation | `.planning/phases/1-*/` | `outbox/brand-bible.md` |
| 2 Social presence | `.planning/phases/2-*/` | `outbox/social-profiles.md` |
| 3 Content engine | `.planning/phases/3-*/` | `outbox/content-calendar.md` + `outbox/content-pieces/` |
| 4 Skool setup | `.planning/phases/4-*/` | `outbox/skool-setup.md` |
| 5 Funnels | `.planning/phases/5-*/` | `outbox/funnel.md` |
| 6 Launch | `.planning/phases/6-*/` | `outbox/launch-checklist.md` |

The `stage-content.sh` script reads GSD's SUMMARY.md files and renders artifacts
using the corresponding templates/*.md as wrappers.

---

## Router logic (how empire-builder determines where GSD is)

```bash
# Is project bootstrapped?
[ -f "clients/<slug>/.planning/ROADMAP.md" ] && echo "yes" || echo "no"

# What phase are we on?
node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" state json | grep current_phase

# Is there a checkpoint to resume?
[ -f "clients/<slug>/.planning/.continue-here.md" ] && echo "checkpoint exists"

# Is the roadmap complete?
node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" roadmap analyze | grep "roadmap_complete"
```

---

## GSD config for this skill

Set in `clients/<slug>/.planning/config.json` after bootstrap:
```json
{
  "workflow": {
    "granularity": "standard",
    "git": false,
    "agents": true,
    "discuss_mode": "assumptions",
    "text_mode": false,
    "YOLO": false
  }
}
```

`discuss_mode: "assumptions"` means GSD auto-fills phase assumptions without asking
the founder (we already gathered everything in the interview). Use `"discuss"` only
if the founder wants to be consulted on every technical decision.

`git: false` because the outbox artifacts aren't code — no need to commit each piece.
The empire-builder skill manages its own state in SESSION_STATE.md.

---

## Gotchas

- `gsd-autonomous` requires ROADMAP.md and STATE.md to exist — always bootstrap first.
- The working directory must be `clients/<slug>/` for `.planning/` to land in the right place.
- `gsd-execute-phase` spawns subagents and uses ~15% orchestrator context — safe.
- If `.planning/.continue-here.md` exists, GSD has a checkpoint — read it before running `/gsd-next`.
- Phase execution is parallel and subagent-heavy; this is expected. Don't interrupt.
