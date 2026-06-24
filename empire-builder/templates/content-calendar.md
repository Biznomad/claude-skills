# 30-Day Content Calendar — {{community_name}}

> Pre-launch content plan. {{cadence.posts_per_week}} posts/week.
> Batch on {{cadence.content_batch_days}}. All content staged to `outbox/content-pieces/`.

## The month at a glance

| Week | Theme | Pillar | Goal |
|------|-------|--------|------|
| Week 1 | Brand introduction + founder story | Attract | New eyeballs, first followers |
| Week 2 | Framework + teaching | Nurture | Trust building, saves, shares |
| Week 3 | Proof + community teaser | Attract + Convert | Social proof, community buzz |
| Week 4 | Launch push | Convert | Drive Skool sign-ups |

---

## Week 1 — Brand Introduction

> "Who am I and why should you care?"

**Monday — Reel/TikTok (Attract)**
Hook: "POV: You've been doing manifestation for years and your bank account still
hasn't gotten the memo."
Content: Relatable struggle → your story → "here's what changed"
CTA: "Follow for the bridge between manifestation and real business results"

**Wednesday — Carousel/Thread (Nurture)**
Hook: "3 reasons your vision board isn't working (it's not your fault)"
Content: 3-slide breakdown of the most common mistakes + 1 reframe
CTA: "Save this for the next time you feel like manifestation isn't working"

**Friday — Story/Short (Convert)**
Behind-the-scenes: "I'm building something for you..."
Tease the community. Show the classroom screenshot (blurred faces).
CTA: "Want early access? Comment [WORD] or DM me."

---

## Week 2 — Framework + Teaching

> "Here's the system. Here's how it works."

**Monday — Reel/TikTok (Attract)**
Hook: [choose from content-system.md hook formulas — 'Uncomfortable Truth' works well here]
Content: The core tension of your niche (woo vs. practical — you bridge both)
CTA: "If this hit home, follow — I post this every week"

**Wednesday — Carousel/Thread (Nurture)**
Hook: "The [X]-step process I used to [specific result]"
Content: Your framework in [N] steps. One step per slide/tweet.
CTA: "Which step are you on? Comment below"

**Friday — Live or Story Q&A (Nurture/Convert)**
Go live on IG or TikTok: "Ask me anything about [topic]"
Record it → clip best 60 seconds → post as Reel
CTA: "We do this every [day] inside [Community Name]. Join us: [link in bio]"

---

## Week 3 — Proof + Community Teaser

> "Look at what's happening. You should be here."

**Monday — Reel/TikTok (Attract)**
Hook: "She went from [specific before] to [specific after] in [timeframe]"
[Use founder's own story OR beta member testimonial if available]
CTA: "Join us — link in bio"

**Wednesday — Carousel/Thread (Nurture)**
Hook: "What [specific audience] gets wrong about [topic] (and how to fix it)"
Content: Myth-busting + reframe
CTA: "DM me 'READY' if you want to go deeper on this"

**Friday — Community Invite (Convert)**
Direct, warm pitch: "I opened up {{community_name}} this week. Here's what's inside..."
Show the community structure, module list, what the weekly call looks like.
Clear CTA with price: "${{offer.price_per_month}}/month. Link in bio."

---

## Week 4 — Launch Push

> "Now or never. This is the moment."

**Monday — Reel/TikTok (Convert)**
Hook: "The decision that changed everything for me was [decision related to your community topic]"
Content: Your transformation → invitation → time-bound offer if applicable
CTA: "[Community Name] is open. Link in bio. Come join us."

**Wednesday — Thread/Carousel (Convert)**
"Everything you'll get when you join {{community_name}}..."
List format: classroom modules, live calls, community support, transformation promise
Last slide: price + link

**Friday — Last call + start Week 5 cycle**
"One more thing before I shift focus..." — final soft pitch
Begin Week 5 with Week 1's pattern (Attract) — the cycle restarts

---

## Content pieces to produce (in outbox/ before launch)

Each piece needs files in `outbox/content-pieces/YYYY-MM-DD/`:

### IG Reel #1 (Week 1 Monday)
- `hook.txt` — first 3 seconds of script
- `script.md` — full 60-second word-for-word script
- `caption.md` — caption + 3-5 hashtags
- `thumbnail-brief.md` — what the cover frame should show

### TikTok #1 (same content, adapted)
- `hook.txt` — TikTok hook (slightly shorter/punchier)
- `script.md` — same core, TikTok pacing
- `caption.md` — TikTok caption (shorter, first 150 chars matter)

### Carousel/Thread #1 (Week 1 Wednesday)
- For IG: `slides.md` — slide-by-slide content (Slide 1 = hook, Slides 2-8 = content, Last = CTA)
- For X: `thread.md` — tweet-by-tweet, numbered, last tweet = CTA

### YouTube Outline #1 (Week 2 or whenever YT is priority)
- `title.txt` — searchable title with keyword first
- `thumbnail-brief.md` — 3 words max on thumbnail
- `outline.md` — intro, 3-4 sections with timestamps, CTA, end screen

---

## Content production instructions (for batch day)

On {{cadence.content_batch_days}}, produce 3 pieces for the coming week:

1. Read `references/content-system.md` for current platform specs
2. Read the client config for voice and keywords
3. Write all pieces — hook last (after you know the full piece)
4. Run `scripts/stage-content.sh {{slug}} content` to place in outbox
5. Review: check hooks, voice, CTAs, character limits
6. If founder has Telegram configured: send the weekly content card

---

*Generated by empire-builder for {{slug}}*
