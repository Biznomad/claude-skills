// Turbo-mode fan-out for the growth-loop (opusplan pattern).
// Run via the Workflow tool. The MAIN loop (Opus) does stages 1-3 inline (read state,
// replenish, rank) then invokes this to fan out build+verify across the top tasks.
// Pass the ranked eligible tasks + paths via `args`.
//
//   args = { business, tasks:[{id,title,track,value,brief}], budgetTokens, valueThreshold }
//
// Tier map: makers = Sonnet, verifier = Sonnet, scouts/QA = Haiku. Orchestration = this
// script (driven by the Opus main loop). Adjust model strings if tiers change.

export const meta = {
  name: 'growth-loop-turbo',
  description: 'Turbo growth-loop: parallel Sonnet makers + Sonnet verifier + Haiku QA per task',
  phases: [
    { title: 'Build',  detail: 'one Sonnet maker per eligible task', model: 'sonnet' },
    { title: 'Verify', detail: 'independent Sonnet checker, default-reject', model: 'sonnet' },
  ],
}

const tasks = (args && args.tasks) || []
const biz = (args && args.business) || 'business'
log(`turbo: ${tasks.length} eligible task(s) for ${biz}`)

const VERDICT = {
  type: 'object',
  properties: {
    isRealValue: { type: 'boolean' },
    zeroErrors:  { type: 'boolean' },
    reasons:     { type: 'string' },
    fixesNeeded: { type: 'string' },
  },
  required: ['isRealValue', 'zeroErrors', 'reasons'],
}

// Pipeline: each task is built by a Sonnet maker, then verified by an INDEPENDENT Sonnet
// checker whose default stance is reject. No barrier — a task verifies as soon as its
// build finishes while others are still building. (Empty tasks → empty pipeline → no-op.)
const results = await pipeline(
  tasks,
  (t) => agent(
    `You are a MAKER sub-agent for the "${biz}" growth-loop. Build exactly ONE increment:\n` +
    `Task ${t.id} (track ${t.track}, value ${t.value}): ${t.title}\n${t.brief || ''}\n\n` +
    `Build it idempotently and reversibly. Self-QA (no tofu, no overflow, correct numbers). ` +
    `Commit to the repo. Return: what you built, the file path(s), the commit sha, and a ` +
    `one-line proof it works. Do NOT do any hard-denied action (money/secrets/infra/sends/public posts).`,
    { label: `make:${t.id}`, phase: 'Build', model: 'sonnet' }
  ).then((built) => agent(
    `You are an INDEPENDENT VERIFIER for the "${biz}" growth-loop. DEFAULT STANCE: REJECT.\n` +
    `Task: ${t.title}\nMaker reported:\n${built}\n\n` +
    `Confirm ONLY if the increment delivers REAL buyer/operator value AND has zero errors ` +
    `(broken render, console errors, wrong numbers, tofu, filler). If it's padding or ` +
    `unverifiable, reject. Be specific in reasons.`,
    { label: `verify:${t.id}`, phase: 'Verify', model: 'sonnet', schema: VERDICT }
  ).then((v) => ({ task: t, built, verdict: v })))
)

const ok = results.filter(Boolean)
const shipped  = ok.filter((r) => r.verdict && r.verdict.isRealValue && r.verdict.zeroErrors)
const rejected = ok.filter((r) => !(r.verdict && r.verdict.isRealValue && r.verdict.zeroErrors))
log(`turbo: ${shipped.length} shipped, ${rejected.length} rejected`)

// The Opus main loop consumes this: writes run-log lines, posts the changelog, updates the
// backlog (shipped→shipped, rejected→idea with verdict.fixesNeeded), and evaluates the stop
// condition (value-dry × N or budget cap). Cheap QA/formatting/log-writes run as Haiku
// Agent calls from the main loop, not here.
return {
  shipped:  shipped.map((r) => ({ id: r.task.id, built: r.built, verdict: r.verdict })),
  rejected: rejected.map((r) => ({ id: r.task.id, verdict: r.verdict })),
}
