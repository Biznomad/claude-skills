# Loop Budget — <business>

Read at the START of every cycle. The loop must honor this file.

## Mode
- **default_mode:** copilot        # advisor | copilot | autonomous | turbo

## Caps
- **token_budget:** 500000         # cumulative output-token target for one run; stop at/above
- **value_threshold:** 3.0         # 1–5; candidates below this are NOT built
- **dry_cycles_N:** 2              # stop after N consecutive cycles with no candidate ≥ threshold
- **max_parallel:** 3              # turbo only: max concurrent maker sub-agents
- **max_cycles:** 40               # hard backstop on cycle count

## Kill switch
- **state:** RUNNING               # RUNNING | PAUSED — if PAUSED, do nothing but post a "paused" note
- To pause: set state: PAUSED (or tap the Telegram Pause button if wired).

## Hard denylist (NEVER autonomous, every mode)
- Money movement / payments / refunds / budget changes
- Secrets, tokens, API keys (never print, commit, or exfiltrate)
- Infra / DNS / server destructive ops
- Live customer sends (email/SMS/DM) without explicit approval
- Publishing to public channels without approval (Skool Public flip, social posts)
- Deleting/overwriting anything the loop did not create

## On budget exceed or kill
1. Stop building. 2. Append a final run-log line (outcome: "budget-stop" | "killed").
3. Post the dry-stop / handoff card. 4. Do NOT schedule the next cycle.
