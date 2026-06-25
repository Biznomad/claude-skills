# Growth Loop — Versions + Self-Replenishing Engine (Design)

**Date:** 2026-06-25 · **Status:** approved, building.
**Goal:** loops that run *longer* and *autonomously decide the next value-adding task*
to enhance a product/service — instead of dry-stopping the moment the obvious backlog
empties (the 2026-06-25 overnight run stopped for exactly this reason).

Grounded in the `loop-engineering` discipline (Greyling/Osmani/Cherny): the leverage is
designing the control system, not prompting each step. Adds the two gaps our loop-audit
found — a **maker/checker verifier** and **budget/run-log discipline** — plus a
**self-replenishing, value-ranked backlog** and **selectable autonomy modes**.

---

## 1. Selectable modes (the "versions")

Chosen at launch: `/growth-loop <business> --mode <mode>`. All modes share one engine;
they differ in how far the loop acts before it needs the human.

| Mode | Acts | Stops when | Models |
|------|------|-----------|--------|
| `advisor` (L1) | Audits product, generates + ranks next-best tasks to the backlog. **Builds nothing.** | one pass | single |
| `copilot` (L2) | Builds + commits each increment, self-QAs. Outward actions (deploy/public post/send) wait for a tap. | backlog value-dry **or** budget cap | single |
| `autonomous` (L3) | Self-replenishes, builds, **verifier confirms real value**, ships all but hard-denied. Unattended. | N value-dry cycles **or** token cap | single |
| `turbo` (L3+) | Same as autonomous, **parallel** + model-tiered fan-out. | same | Opus→Sonnet→Haiku |

**Default:** `copilot`. **Hard-denied in ALL modes** (never autonomous): money movement,
secrets, infra/DNS, live customer sends w/o approval, destructive ops.

## 2. The 6-stage engine (every mode)

1. **Read state** — backlog + run-log + memory (anti-redo).
2. **Replenish** — opportunity-finder audits the product/service → candidate tasks.
3. **Score** — each candidate: `value = (impact × buyer_value × reach) ÷ effort`, 1–5
   each; rank desc. Below `value_threshold` → not built.
4. **Build** — top task(s) above threshold (one; turbo = several in parallel).
5. **Verify** — independent checker, **default stance REJECT**, confirms real value +
   0 errors before the increment counts. Reject → back to backlog with notes, not shipped.
6. **Log + ship + budget-check** — append run-log line, post changelog, then evaluate the
   stop condition.

## 3. Stop condition (value-threshold + budget cap)

Stop (and post the dry-stop/handoff card) when **either**:
- **value-dry:** `N` consecutive cycles produce no candidate ≥ `value_threshold`
  (default N=2) — *value-defined dry, not "obvious-list empty"*; or
- **budget cap:** cumulative `tokens_estimate` ≥ `token_budget` for the run.

This is why it runs longer: replenish+score keeps surfacing real work until the product
is genuinely well-served, then it stops on quality — not on running out of the first ideas.

## 4. Turbo model tiering (opusplan pattern)

| Tier | Model | Role |
|------|-------|------|
| Orchestrator | **Opus** | read state, replenish, rank, plan, assign, stop-call. Plans, doesn't build. |
| Makers (parallel) | **Sonnet** | one implementer sub-agent per top task. |
| Verifier | **Sonnet** | independent checker per increment, default-reject. |
| Scouts / QA (high-volume) | **Haiku** | score candidates, tofu/console-error/link scans, run-log writes, formatting. |

Implemented via the `Workflow` tool (pipeline: score → build → verify) or `Agent` calls
with `model:` overrides. `advisor`/`copilot`/`autonomous` are single-stream; only `turbo`
fans out.

## 5. New artifacts (per business, in the memory dir / repo)

- `backlog-<business>.md` — ranked candidate tasks (id, title, track, value score, status:
  `idea|building|verifying|shipped|rejected`). Idempotent: dedupe on task id.
- `loop-run-log-<business>.md` — append-only JSON line per cycle (run_id, mode, task,
  value, tokens_estimate, verifier_verdict, outcome).
- `loop-budget-<business>.md` — `token_budget`, `value_threshold`, `dry_cycles_N`,
  `max_parallel` (turbo), kill-switch state, hard-denylist.
- Config gains: `mode` default, budget/threshold, backlog + run-log paths.

## 6. Safety / lessons carried forward

- Verifier is a **separate** sub-agent/instructions — the maker can't pass its own work
  (loop-audit anti-pattern #1).
- Denylist hard-blocks money/secrets/infra/sends in every mode (anti-pattern #6/#9).
- Kill switch in `loop-budget-<business>.md`; honored at start of every cycle.
- Run-log makes long unattended runs auditable; budget cap makes them bounded.
- Backlog/run-log are co-located so a future `loop-audit` literal scan scores L3 too.

## 7. Build steps

1. This design doc (committed).
2. Extend `SKILL.md`: modes, 6-stage engine, scoring rubric, verifier, stop condition,
   turbo tiering.
3. Templates: `backlog.md`, `loop-run-log.md`, `loop-budget.md`, `value-rubric.md`,
   `turbo-workflow.js`.
4. Update `loop-config-template.md` + `loop-config-biznomad.md` with the new fields.
5. Seed Biznomad's `backlog-biznomad.md` from the 12 handoff items + product audit (so the
   next run has a ranked queue).
