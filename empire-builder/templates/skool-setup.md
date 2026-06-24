# Skool Community Setup — {{community_name}}

> Step-by-step guide to setting up {{slug}} on Skool.com.
> Follow in order. Don't skip steps.

---

## 1. Create the Skool group

1. Go to https://www.skool.com → "Create a group"
2. Group name: **{{community_name}}**
3. URL: `skool.com/{{handles.skool}}`
4. Privacy: **Paid** (price: ${{offer.price_per_month}}/mo)
   OR **Public Free** (if starting free — see skool-playbook.md for decision guidance)
5. Category: [choose closest match — usually "Entrepreneurship" or "Self Development"]
6. Description: [use the brand bible's one-sentence pitch + 3-4 bullet promises]

---

## 2. Community about page

**Paste this into the Skool group "About" section:**

---
**Who this is for:**
{{community.audience}}

**What you'll get:**
- [Promise 1 — specific and outcome-focused]
- [Promise 2]
- [Promise 3]
- Access to the full [Community Name] classroom ({{skool_config.classroom_modules | length}} modules)
- Monthly live calls with {{founder.name}}

**The community promise:**
{{community.promise}}

**Join {{community_name}}: ${{offer.price_per_month}}/month**
---

---

## 3. Feed categories

Set up in Skool → Community → Settings → Categories.

**Create these (in this order):**

| Category | Description | Who can post |
|----------|-------------|-------------|
| 📢 Announcements | Official updates from {{founder.name}} | Admin only |
| 👋 Introductions | Where new members say hello | Everyone |
| ✨ Wins & Gratitude | Share your results — big or small | Everyone |
| ❓ Questions & Support | Ask the community anything | Everyone |
| 📚 Resources | Tools, books, links worth sharing | Everyone |

---

## 4. Classroom structure

Build modules in order. Each module should have 3-5 lessons max 15 minutes each.

{{#each skool_config.classroom_modules}}
### {{this}}
Lessons:
- [Lesson 1 title]
- [Lesson 2 title]
- [Lesson 3 title]
{{/each}}

**Format for each lesson:**
- Short intro (why this lesson matters — 30 seconds)
- Core teaching (the how — 8-12 minutes)
- Action step (one specific thing to do this week)
- Optional: resource download (PDF, worksheet, checklist)

---

## 5. Gamification (points and levels)

Set up in Skool → Settings → Gamification.

**Points per action:**
| Action | Points |
|--------|--------|
| New post | 2 |
| Comment on post | 1 |
| Reaction received | 0.5 |
| Lesson completed | 5 |

**Level unlocks:**
| Level | Points needed | What unlocks |
|-------|--------------|-------------|
| Level 1 | 0 | Feed access + Module 1 |
| Level 2 | 25 | Modules 2-3 |
| Level 3 | 75 | Modules 4-5 |
| Level 4 | 150 | Bonus content + early access to new modules |

---

## 6. Welcome DM (auto-sent to every new member)

Set up in Skool → Settings → Welcome Message.

**Paste this:**

> Hey [first_name]! 🙏 Welcome to {{community_name}} — I'm so glad you're here.
>
> A few things to get you started:
>
> 1️⃣ **Introduce yourself** in the community — pop over to Introductions and tell us who you are and what brought you here. Everyone wants to meet you!
>
> 2️⃣ **Head to the Classroom** and start with Module 1. It's short and will give you a quick win right away.
>
> 3️⃣ **Share your first win** in the Wins & Gratitude section. This community celebrates everything — big or small.
>
> If you ever have questions, reply to this message and I'll get back to you personally.
>
> So happy you're here. Let's build something amazing together.
> — {{founder.name}} {{brand.emoji_rule | first_emoji}}

---

## 7. Founder pinned intro post

**Post in the Introduction category (pin it):**

> 👋 Hey {{community_name}} — I'm {{founder.name}}, your host.
>
> Here's my quick story: [2-3 sentences from founder_story — authentic, specific]
>
> This community exists because [reason — specific, real, emotional].
>
> Here's my promise to you: [community.promise in 1-2 sentences].
>
> I show up here [cadence — e.g. "every weekday"], I answer questions personally, and I run a live call every [frequency].
>
> Now it's your turn: **go to the Introductions section and say hi!** Tell me your name, where you're from, and one thing you're manifesting right now. I read every single one. 🙏

---

## 8. First-week posts (founder posts daily)

Before the community has members, the founder needs to "fill the room" with content.
Schedule these for the first 7 days post-launch:

**Day 1:** Pinned intro post (see above)
**Day 2:** A teaching post — share a piece of the framework
**Day 3:** A personal story — vulnerable, real, relates to the community topic
**Day 4:** An engagement prompt — "What's the one thing you want to manifest this month?"
**Day 5:** A resource drop — tool, book, or PDF that's genuinely useful
**Day 6:** A win or result — your own recent win, or a testimonial
**Day 7:** Community update — "We've been live 1 week. Here's what's happening..."

---

## 9. Skool SEO optimization

- Group name: include your main keyword (e.g. "Manifestation," "Law of Attraction," "Entrepreneur")
- Description: use 3-5 keywords naturally
- Category: choose the most searchable category for your niche
- Cover image: include your community name as text — not just a graphic

---

## 10. Pre-launch checklist

- [ ] Group created with correct name and URL
- [ ] Privacy/price set correctly
- [ ] About page filled in (copy from section 2)
- [ ] All 5 feed categories created
- [ ] At least Module 1 and Module 2 uploaded to classroom
- [ ] Gamification levels configured
- [ ] Welcome DM saved
- [ ] Founder pinned intro post written (save as draft)
- [ ] First 7 posts written and scheduled
- [ ] Profile photo uploaded
- [ ] Group cover image uploaded

When all boxes are checked → you're ready for the funnel (see `funnel.md`).

---

*Generated by empire-builder for {{slug}}*
