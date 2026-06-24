# Empire Builder — Interview Script

10 questions, asked one at a time. Each answer maps to a specific config field.
Resume from `interview_progress.last_question` if interrupted.

## Tone rules (mandatory)

- One question at a time. Period.
- Use "you" and "your community." Never "the client" or technical terms.
- Before each question: one warm sentence explaining WHY you're asking.
- After each answer: one warm acknowledgment sentence before moving on.
- Zero jargon (no "API," "VPS," "slug," "tier," "MCP," "provision," "config").
- Sound like a smart, successful friend helping her build her dream — not a consultant.
- If she's vague, ask one gentle follow-up to get specificity. Then move on.

---

## Question 1 — Community identity

**Why to give (say this first):** "First, I want to understand the heart of what you're building so everything we create is perfectly aligned with your vision."

**Ask:** "What do you want to call your community, and what's it really about? Tell me the story — what are you building and who are you building it for?"

**Capture:** `community_name`, `slug` (auto-derived, lowercase-kebab), `slug_init` (initials), `community.topic`

**Follow-up if vague:** "Love that! Just so I can get really specific — what's the one thing someone would tell their friend after joining?"

---

## Question 2 — Ideal member

**Why:** "So everything we create speaks directly to the right people — the ones who light up when they find you."

**Ask:** "Who is your ideal member? Paint me a picture — who is she (or he), what's going on in her life right now, and what's she desperately wishing she had?"

**Capture:** `community.audience`

**Follow-up if vague:** "And how old is she roughly? What keeps her up at night?"

---

## Question 3 — The transformation

**Why:** "This is the most important thing we'll put on every piece of content you create — the promise that makes someone pull out their wallet."

**Ask:** "What transformation does your community deliver? Complete this sentence: 'After joining and doing the work, members will go from _________ to _________.' Be as specific as possible."

**Capture:** `community.promise`

---

## Question 4 — Your story

**Why:** "People don't join communities — they join people. Your story is the most powerful content asset you have, and we're going to use it everywhere."

**Ask:** "Tell me YOUR story with this topic. Why are you the right person to build this? What happened that made you go 'I have to share this with other people'?"

**Capture:** `community.founder_story`

---

## Question 5 — Offer structure

**Why:** "So we design the community to be something people gladly pay for — and build in the right stepping stones for bigger investment later."

**Ask (using AskUserQuestion, single-select):** "How do you want to structure access?"

Options:
- "Free to join — I'll monetize through courses or coaching later"
- "Paid membership — monthly fee to be part of the community"
- "Hybrid — free access plus a paid inner circle or premium tier"

Then ask (free text): "And if it's paid, what feels like the right starting price? Don't overthink it — what feels fair for what members get?"

Then ask (free text): "Do you have a vision for the bigger journey — like a free thing that leads to the community, which leads to something higher-end like coaching?"

**Capture:** `offer.model`, `offer.price_per_month`, `offer.offer_ladder[]`

---

## Question 6 — Channels

**Why:** "So we don't try to be everywhere at once — just where your ideal members actually hang out."

**Ask (using AskUserQuestion, multiSelect):** "Which platforms do you want to show up on? Pick the ones where you can actually see yourself creating content."

Options:
- "Instagram — I love visuals and short video (Reels)"
- "TikTok — I'm comfortable in front of a camera"
- "YouTube — I want to do longer, more in-depth content"
- "X or Threads — I like writing and sharing thoughts"

**Capture:** `channels[]`

---

## Question 7 — Time/capacity

**Why:** "So we create a content plan that's actually realistic for your life — not one that burns you out in week 2."

**Ask:** "Honestly, how many hours a week can you dedicate to creating content and showing up in the community? And what day works best for batching your content — like sitting down for a few hours and cranking it out?"

**Capture:** `cadence.hours_per_week`, `cadence.content_batch_days`

**Derive:** `cadence.posts_per_week` (1-2hr/week = 2 posts/wk; 3-5hr = 3-4 posts/wk; 5hr+ = 5 posts/wk)

---

## Question 8 — Brand voice and visuals

**Why:** "So everything we create looks and feels unmistakably like you — your colors, your energy, your style."

**Ask:** "Describe how you want to FEEL to people who come across your content. What's the vibe? And do you have any colors in mind — colors you already love or that feel like your brand?"

**Capture:** `brand.voice` (pull 3-5 adjectives from her answer), `brand.palette` (convert color descriptions to hex if possible, otherwise note descriptors)

**Follow-up if no colors:** "Think about a brand or creator you love the look of — what feels right? Minimalist and clean? Warm and earthy? Bold and vibrant?"

---

## Question 9 — What's already live

**Why:** "So we build on what you already have instead of starting from absolute zero — and I know exactly what to create first."

**Ask:** "What do you already have in place? Any social media accounts (even personal ones we could convert), a website, an email list, anything like that? And have you already set up your community on Skool, or are we starting fresh?"

**Capture:** `handles.*` (fill in any existing), `existing_assets`, `skool_config.is_live`, `skool_config.community_url`

---

## Question 10 — Safety and constraints

**Why:** "One last thing — just so I never do something that could cause a headache."

**Ask:** "Is there anything I should know about how you want to work? Like, are there topics that are off-limits for your content, industries you don't want to associate with, or things you'd want to approve before they go anywhere? Also — do you have a Telegram account? It's the best way for me to send you updates and finished content as we go."

**Capture:** `safety.notes`, `telegram.dm_chat_id` (if provided), `safety.secrets_never_touch`

---

## After all 10 questions

1. Summarize what you heard in 5-7 sentences: "Here's what I'm going to build for you..."
2. Confirm: "Does that sound right? Anything to adjust?"
3. If confirmed: set `interview_complete: true`, write the config, proceed to Stage 1.
4. If corrections needed: update the relevant fields, re-confirm, then proceed.

---

## Config field quick-reference

| Question | Config fields |
|----------|--------------|
| 1 | `community_name`, `slug`, `slug_init`, `community.topic` |
| 2 | `community.audience` |
| 3 | `community.promise` |
| 4 | `community.founder_story` |
| 5 | `offer.model`, `offer.price_per_month`, `offer.offer_ladder` |
| 6 | `channels[]` |
| 7 | `cadence.hours_per_week`, `cadence.posts_per_week`, `cadence.content_batch_days` |
| 8 | `brand.voice`, `brand.palette` |
| 9 | `handles.*`, `existing_assets`, `skool_config.*` |
| 10 | `safety.notes`, `telegram.dm_chat_id` |
