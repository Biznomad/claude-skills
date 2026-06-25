# Loop Run Log — <business>

Append ONE JSON line per cycle (newest at bottom). Prune entries older than 30 days.
Makes long unattended runs auditable + lets `loop-audit` detect real activity.

## Format
```json
{"run_id":"<ISO8601>","cycle":1,"mode":"autonomous","task_id":"add-pricing-faq","track":"a","value":14.0,"tokens_estimate":48000,"verifier":"pass","outcome":"shipped","commit":"abc1234"}
```
`outcome`: shipped | proposed (advisor) | rejected (verifier) | no-op | budget-stop | value-dry-stop | killed
`verifier`: pass | reject | n/a (advisor/copilot-self)

## Runs
<!-- Loop appends below this line -->
