# Loop Backlog — <business>

Ranked candidate tasks. The loop READS this at cycle start, REPLENISHES it (adds new
candidates from the product audit), SCORES + re-ranks, builds the top eligible task, and
updates status. Idempotent: dedupe on `id` (slug). Never delete — set status `rejected`.

**Scoring:** `value = round((impact + buyer_value + reach) / effort, 1)` — each factor 1–5
(value range ~0.6–15). Eligible to build when `value ≥ value_threshold` (from loop-budget)
and `status: idea`.

**Status:** idea | building | verifying | shipped | rejected
**Track:** a (growth) | b (product/UX) | c (showcase/authority)

| id | title | track | impact | buyer | reach | effort | value | status | notes |
|----|-------|-------|--------|-------|-------|--------|-------|--------|-------|
| _example-add-pricing-faq_ | Add objection-handling FAQ to offer page | a | 4 | 4 | 3 | 1 | 11.0 | idea | from CRO audit |

<!-- Loop appends/updates rows above. Keep newest-built at bottom of shipped. -->

## Replenish sources (where the opportunity-finder looks each cycle)
- The product/service itself: audit the live asset for gaps, friction, weak spots.
- The human handoff / unlocks cleared (a cleared unlock often spawns 2–3 buildable tasks).
- The 3 value tracks (a/b/c) — ensure all three keep progressing.
- Verifier rejections (re-scoped, not dropped).
- Real signals if available (analytics, CRO audit, reviews, ad data).
