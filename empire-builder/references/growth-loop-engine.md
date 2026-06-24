# Growth Loop Engine — Stage 3 Reference

Adapted from `growth-loop/SKILL.md` §1-4, hardened with `write-the-loop` discipline.
Read before every Stage 3 increment run.

This is the execution engine for SKILL.md §5. All loop mechanics live here so SKILL.md
stays navigable.

---

## The Ten-Step Loop (every run, no skipping)

### Step 1 — Read state (non-negotiable)
Read in this order:
1. `clients/<slug>/loop-config.md` — the community identity, tracks, safety rules
2. `clients/<slug>/SESSION_STATE.md` — the running journal (newest entry at top)
3. `clients/<slug>/.json` — the full client config

Look for: last track run, last increment built, member count, open issues.
**Never start an increment without reading state. This prevents duplicating work.**

### Step 2 — Pick the track
Three tracks rotate a → b → c. STATE.md ends with "Next loop track: (x)".

| Track | What it builds |
|-------|---------------|
| **(a) Reach / acquisition** | Content batch, outreach scripts, lead magnet updates, social bios, challenge promos |
| **(b) Community / product** | Skool modules, welcome DM, gamification, feed categories, member experience improvements |
| **(c) Proof / showcase** | Member wins format, testimonial collection, metrics card, shareable results post |

Default rotation: a → b → c → a. If a track is saturated (nothing left to build),
skip to next and note it in STATE.md.

### Step 3 — Pick the single highest-value increment
One thing per run. Bias toward:
- What directly moves the member counter (acquisition track)
- What keeps existing members active (community track)
- What generates social proof for content (showcase track)

Ask: "If I do only one thing this run, what will matter most in 30 days?"

### Step 4 — Think before heavy work
For any non-trivial increment: state your approach in one sentence before executing.
Example: "I'm going to write a 5-day email sequence for the free challenge that ends
with a pitch to the paid community."

### Step 5 — Build it
Create the content/copy/template. Rules:
- Read `references/content-system.md` for platform specs before generating any content.
- Read `references/skool-playbook.md` for community mechanics before building Skool assets.
- Write all output to `clients/<slug>/outbox/<YYYY-MM-DD>/`.
- Name files clearly: `instagram-reel-hook.txt`, `skool-welcome-dm.md`, etc.
- Content must match `brand.voice` from the config — check keywords_use and keywords_avoid.

### Step 6 — Verify independently (the write-the-loop hardening)
This is what separates a real loop from "unattended AI slop."

**Content verification checklist:**
- [ ] Does the hook fit the formula in `content-system.md`? (not just generic)
- [ ] Does the voice match `brand.voice` from the config?
- [ ] Is the CTA pointing to the right destination (Skool URL, linktree, etc.)?
- [ ] Are character/duration limits respected for the platform?
- [ ] Did the file actually get written to outbox/? (read it back — don't assume)

**Link verification:**
- Any URL in the content → use `/browse` to confirm it resolves.
- Skool community URL → use `/browse` to confirm the group exists and is accessible.
- Bio links → confirm they're not 404.

**Metrics verification (if measurable):**
- Read `clients/<slug>/metrics.json` to get last-run member count.
- Compare to current (if Skool dashboard is accessible).
- If count hasn't moved in 3 consecutive runs → trigger no-progress stop condition.

**The rule: never trust self-report.** "I believe I generated this correctly" is not
verification. The independent check is what catches the gap between what you intended
and what actually landed in the outbox.

### Step 7 — Check stop conditions (from loop-spec.md)
Read `clients/<slug>/loop-spec.md`. Check all four every run:

| Condition | How to check |
|-----------|-------------|
| **SUCCESS** | member_count ≥ goal OR MRR ≥ goal. If yes: celebrate, suggest new milestone. |
| **MAX ITERATIONS** | count runs in STATE.md. If ≥ max_iterations: pause, surface summary to founder. |
| **BUDGET** | token/cost cap. If nearing: log position, stop, tell founder to resume next session. |
| **NO PROGRESS** | Same track output 3+ consecutive runs with no member/content movement: surface to founder, adjust. |

### Step 8 — Update state
Prepend to `clients/<slug>/SESSION_STATE.md`:

```markdown
## [YYYY-MM-DD] Track (a|b|c) — [Increment title]

**Built:** [one-line description]
**Staged to:** `outbox/YYYY-MM-DD/[filename]`
**Verified:** [yes/no + method]
**Member count:** [N] (was [N-1])
**Content pieces shipped this month:** [N]
**Open issues:** [any blockers]

Next loop track: ([a|b|c])
```

Also update `clients/<slug>/metrics.json`:
```json
{
  "last_run": "YYYY-MM-DD",
  "member_count": N,
  "content_pieces_shipped": N,
  "track_last_run": "a",
  "run_count": N
}
```

### Step 9 — Post the Telegram changelog
See `templates/telegram-changelog.md` for the exact format.

Required elements every post:
- Branded card: community name + track letter + what shipped + 1 key metric
- Caption: 2-3 lines max. What was built. What to do now. What's next.
- InlineKeyboardMarkup (MANDATORY): every post needs buttons.
  Default set: `[✅ Publish outbox] [📝 Edit draft] [⏭ Skip this one] [📊 Stats]`
  Use `sendPhoto` with `reply_markup` — never send a photo without the keyboard.

If no Telegram bot is configured (token is null):
- Write the changelog to `clients/<slug>/outbox/YYYY-MM-DD/telegram-card.md` instead.
- Note: "Telegram not configured. Card saved to outbox for manual review."

### Step 10 — Wrap up
6-10 lines max:
- What was built (one sentence)
- Where it is (outbox path)
- What the founder needs to do (publish it, and how)
- What track is next
- When to re-run ("Call me again with `/empire-builder <slug>` to run the next increment")

---

## The Three Tracks — Detailed

### Track (a) — Reach / Acquisition

Goal: pull more of the right people toward the community.

High-value increments (pick the best one per run):
- **Content batch** — 3 pieces for the week: one Attract, one Nurture, one Convert
- **Outreach script** — DM template for reaching out to potential members personally
- **Free lead magnet update** — improve the freebie that funnels people to the community
- **Challenge campaign** — 5-day challenge landing page copy + email sequence
- **Social bio update** — optimize one platform bio to improve CTR to community
- **Collaboration script** — pitch for guest podcast, IG live, or collab post
- **Hashtag/SEO audit** — update hashtag strategy based on what's working
- **Referral mechanic** — draft referral offer for existing members to share

### Track (b) — Community / Product

Goal: make the Skool community so good members can't imagine leaving.

High-value increments (pick the best one per run):
- **New classroom module** — draft one module (3-5 lessons) with outlines
- **Welcome sequence** — improve the welcome DM, intro post prompt, first-week checklist
- **Live call agenda** — plan the next weekly/monthly call with talking points
- **Gamification level** — design a new level unlock reward
- **Resource drop** — create a high-value free resource for the community feed
- **Member spotlight** — interview template + how to feature a member win
- **Community challenge** — internal (for members only) challenge to boost engagement
- **FAQ document** — answer the top 5 questions new members always ask

### Track (c) — Proof / Showcase

Goal: make results visible so existing members feel proud and prospects feel safe.

High-value increments (pick the best one per run):
- **Member win post** — format a real member story for social (with permission)
- **Metrics card** — create a visual "community report" (members, content pieces, wins)
- **Testimonial collection** — write outreach to 3 members asking for a quote/video
- **Before/after story** — format founder's own transformation as a 10-slide carousel
- **Case study** — deep-dive on one member's journey (blog post / long caption)
- **Social proof reel** — script for a "here's what our members are saying" video

---

## Hard-won lessons for this niche

**Manifestation + entrepreneur content:**
- Concrete beats abstract every time. "I made $2,000 from a community of 23 people"
  outperforms "I manifested abundance" — even in the spiritual niche.
- Specificity is credibility. Vague transformation claims get ignored. Specific ones
  (30 days, 10 clients, $47/mo) build trust.
- The "woo + practical" tension is the niche. The content that works: "Here's the
  spiritual practice AND here's the business strategy." Don't separate them.

**Skool-specific:**
- Communities with active founders (posting daily) retain 2x better than silent ones.
  Build the habit before building the classroom.
- The welcome DM response rate is the single best predictor of community stickiness.
  Invest disproportionately in the welcome experience.
- Live calls create community identity. Record them and put the replay in the classroom.

**Content:**
- The best content comes from real conversations with real members. Mine the DMs.
- Reuse aggressively: one YouTube video → 3 IG carousels → 5 TikToks → 10 tweets.
- Batch creation is the only way a solo founder can show up consistently. Sunday batch,
  weekly scheduled posts.
