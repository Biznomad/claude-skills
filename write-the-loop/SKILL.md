---
name: write-the-loop
description: Use when the user wants Claude to keep working autonomously until something is done — "stop babysitting", "keep going until", "run overnight", "work on its own", "loop until tests pass / all images approved / queue empty", or any request to set up an autonomous AI loop, agent loop, or self-driving workflow instead of one-off prompts.
---

# Write the Loop

## Overview

Your job is to design the loop, not type the prompts. An autonomous loop is:
**prompt → execute → verify → decide → repeat**, with a human supervision surface on top.
(Source pattern: Boris Cherny's Claude Code workflow — the human writes the loop, the loop drives Claude.)

A loop without an independent verifier and hard stop conditions is not autonomous — it's unattended.

## The Loop Spec (write this BEFORE any code)

Every loop needs all 7. Missing one = redesign.

| Component | Requirement |
|-----------|-------------|
| **Goal** | One sentence, outcome-shaped ("all tests stable", not "fix tests") |
| **Done-check** | Machine-verifiable AND matches goal *semantics*. "Stable" = N consecutive green runs, not 1. "Approved" = passes rubric, not "generated". |
| **Step prompt** | What one iteration does, fresh context each time, smallest useful unit of work |
| **Verifier** | Independent of the worker. The orchestrator re-runs the test / re-checks the artifact itself. NEVER trust the worker's self-report ("RESULT: FIXED" means nothing until re-verified). |
| **Stop conditions** | ALL of: success (done-check), max iterations, budget (tokens/$/wall-clock), and no-progress (K iterations with no state change → halt + escalate, don't spin) |
| **State** | Persisted queue/checkpoint file so the loop resumes after kill/crash |
| **Supervision surface** | Where progress lands (Telegram card, log, dashboard) + how the human intervenes (pause/skip/approve). Telegram = inline buttons, per CLAUDE.md. |

## Pick a runner — don't build one

| Situation | Runner |
|-----------|--------|
| Loop within this Claude session | `/loop` skill (self-paced or interval) |
| Recurring on schedule, cloud | `/schedule` (Claude Code routines) |
| Headless on a server/VPS | `claude -p "$(cat step-prompt.md)"` in a `while` loop or systemd timer — NOT ad-hoc `at`/crontab fallback chains |
| Fan-out / multi-agent single run | Workflow tool (loop-until-dry, budget patterns built in) |
| Non-Claude steps (APIs, approvals) | n8n on the relevant VPS |

## Safety rails (required for unattended runs)

- Scope permissions: allowlist the commands the step needs; never blanket `--dangerously-skip-permissions` on a repo with push access. If you must, sandbox: separate branch, no push, human merges.
- Worker commits to a work branch; verifier gates promotion.
- Anti-reward-hacking line in the step prompt ("never skip/weaken the check to make it pass") — AND the independent verifier, because the line alone doesn't hold.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Exit on first green run when goal is stability/quality | Done-check = N consecutive passes / rubric score, matched to goal wording |
| Orchestrator parses worker's "FIXED" claim as truth | Orchestrator re-runs the check itself before marking done |
| Only `MAX_PASSES` as stop condition | Add budget + no-progress halt; a rescheduling loop with pending items runs forever |
| One giant session that degrades | Fresh `claude -p` context per iteration; state lives in files, not context |
| Silent loop | Report each batch to the supervision surface; only-on-issue alerts + daily heartbeat |

## Red flags — stop and fix the spec

- You can't state the done-check as a command that exits 0/1
- The verifier and the worker are the same agent/process
- "It'll just stop when it's done" (no budget, no no-progress halt)
- You're writing cron/`at` plumbing instead of using `/loop`, `/schedule`, systemd, or n8n
