# Wellness DM Ecosystem v1 — ManyChat Template Build Spec

**Template Name:** `Wellness DM Ecosystem v1`
**Tier:** AGaaS Tier-2 (DM Concierge add-on)
**Source of Truth:** Distilled from Vicelle Naturals "Wellness Concierge" (live build, validated Feb 25 2026)
**Build Target:** Biznomad master ManyChat account (PRO)
**Estimated Build Time:** 2 hours focused (1 builder, no interruptions)
**Document Version:** 1.0
**Last Updated:** 2026-05-13

---

## A. Architecture Overview

The **Wellness DM Ecosystem** is a conversational, value-first DM funnel for any wellness/supplement/beauty/CPG brand. It converts paid social (Meta/IG ads), organic comments, story replies, and cold DMs into engaged leads via a 5-question quiz, then nurtures non-buyers and post-purchase customers with timed sequences. The system loops everything back to a central "Welcome Hub" — there are no dead ends.

### The 6 Flows

| # | Flow Name | Trigger | Purpose | End State |
|---|-----------|---------|---------|-----------|
| 1 | **Welcome Hub** | Ad JSON, comment keywords, story reply, DM keyword | Greet + route to one of 5 paths | Tag `new_follower` + `{channel}_entry`, set `entryPoint` |
| 2 | **Wellness Quiz** | QR `🧪 Take the Wellness Quiz` from Hub | 5-question diagnostic → personalized product rec | Tag `quiz_completed`, `quiz_result_{slug}`, `goal_{x}`, `lead_hot` |
| 3 | **Product Guide** | QR `🛒 Browse Products` from Hub | Browsable catalog (3-4 categories) | Tag `browsed_products` |
| 4 | **Education** | QR `📚 Learn About {Hero Ingredient}` from Hub | Value-first content, 4 articles | Tag `browsed_education` |
| 5 | **Social Proof** | QR `⭐ See Reviews` from Hub | 5 star testimonials in one message | Tag `browsed_reviews` |
| 6 | **FAQ Support** | QR `💬 Ask a Question` from Hub | Shipping, ingredients, usage, subs, human handoff | Tag `needs_human_support` (only on escalation) |

### The 7 Follow-Up Sequences

| # | Sequence | Trigger Condition | Delay | End Tag |
|---|----------|-------------------|-------|---------|
| 1 | 24h Quiz Offer | `quiz_completed` AND NOT `purchased` | 24h | `followup_24h` |
| 2 | 3-Day Review Nudge | (`browsed_products` OR `browsed_education`) AND NOT `purchased` | 3d | `followup_3d` |
| 3 | 7-Day Check-In | Any engagement AND NOT `purchased` | 7d | `followup_7d` |
| 4 | 14-Day Education | NOT `purchased` | 14d | `followup_14d` |
| 5 | 1-Day Post-Purchase | `purchased` | 1d | `post_purchase_1d` |
| 6 | 7-Day Review Request | `purchased` | 7d | `post_purchase_7d` |
| 7 | 21-Day Reorder | `purchased` AND NOT `subscribed` | 21d | `post_purchase_21d` |

**Expected outcomes (benchmarks from Vicelle pilot):**
- DM opt-in rate: 8–15% of ad clicks
- Quiz completion: 45–60% of Hub visitors
- Quiz → purchase (7d): 15–20%
- ROAS lift from baseline ads: +0.5–1.0x

---

## B. Build Prerequisites — Tags & Custom Fields

These must exist in the master Biznomad account BEFORE building any flow. Create via `manychat_create_tag()` and `manychat_create_custom_field()` MCP calls.

### 35 Tags (8 categories)

**Quiz Result Tags (11)** — tracks which product the quiz recommended.
- `quiz_completed`, `quiz_result_p1`, `quiz_result_p2`, `quiz_result_p3`, `quiz_result_p4`, `quiz_result_p5`, `quiz_result_p6`, `quiz_result_p7`, `quiz_result_p8`, `quiz_result_p9`, `quiz_result_bundle`

> **Template note:** Generic `_p1`...`_p9` slots (not product names) so installer can rebind to any client's catalog.

**Goal Tags (5)** — wellness goal segmentation for targeted follow-ups.
- `goal_energy`, `goal_immunity`, `goal_gut`, `goal_skin`, `goal_general`

**Follow-up Tags (4)** — prevents duplicate sequence sends.
- `followup_24h`, `followup_3d`, `followup_7d`, `followup_14d`

**Purchase Lifecycle Tags (4)** — drives post-purchase sequences.
- `purchased`, `post_purchase_1d`, `post_purchase_7d`, `post_purchase_21d`

**Engagement Tags (3)** — tracks browsing depth.
- `browsed_products`, `browsed_education`, `browsed_reviews`

**Lead Temperature Tags (3)** — prioritizes outreach.
- `lead_hot` (quiz done), `lead_warm` (browsed), `lead_cold` (Hub only)

**Entry Source Tags (4)** — acquisition channel.
- `ad_entry`, `comment_entry`, `story_entry`, `dm_entry`

**Operational Tags (2)** — system flags.
- `needs_human_support`, `new_follower`

### 8 Custom Fields

| Field | Type | Purpose |
|-------|------|---------|
| `wellnessGoal` | text | Stores Q1 answer (energy, immunity, gut, skin, general) |
| `supplementFormat` | text | Q2 answer (gel, gummies, open, new) |
| `healthConcern` | text | Q3 answer (brain fog, joints, energy, thyroid, optimizing) |
| `flavorPref` | text | Q4 answer (simple, tropical, surprise) |
| `seaMossExp` | text | Q5 answer — rename to `productExp` if non-sea-moss brand |
| `quizResult` | text | Stores recommended product name (used in follow-up merge fields) |
| `lastInteraction` | datetime | Updated by every flow entry; powers re-engagement |
| `entryPoint` | text | "ad", "comment", "story", "dm" |

---

## C. Per-Flow Build Spec

All flows live in folder `{{brand_name}} DM Operating System`. Every message uses casual, conversational tone — "like texting a knowledgeable friend." Placeholders in `{{...}}` are filled by the installer YAML at deploy time.

---

### Flow 1: Welcome Hub

**Trigger:** Multi-source (configured in Phase D Growth Tools, not in flow itself).

**Block 1 — Actions (run before message):**
- Set Field: `lastInteraction` = current datetime
- Add Tag: `new_follower`
- Add Tag: `lead_cold` (upgraded later if they take quiz)

**Block 2 — Message:**
```
Hey! 👋 Welcome to {{brand_name}}. I'm here to help you find the right {{category}} products — no pressure, just good info.

What sounds good?
```

**Block 3 — Quick Replies (5):**
1. `🧪 Take the Wellness Quiz` → Flow 2
2. `🛒 Browse Products` → Flow 3 (Action: Add Tag `browsed_products`)
3. `📚 Learn About {{hero_ingredient}}` → Flow 4 (Action: Add Tag `browsed_education`)
4. `⭐ See Reviews` → Flow 5 (Action: Add Tag `browsed_reviews`)
5. `💬 Ask a Question` → Flow 6

**End-state:** subscriber routed to chosen flow; tags applied per choice.

---

### Flow 2: Wellness Quiz

**Trigger:** From Hub QR `🧪 Take the Wellness Quiz`.

**Q1 — Wellness Goal**
- Message: `What's your biggest wellness goal right now?`
- QRs (5): `More energy` / `Stronger immunity` / `Better digestion` / `Skin & hair` / `General wellness`
- Per-QR Actions:
  - Set Field `wellnessGoal` = button label
  - Add Tag: `goal_energy` / `goal_immunity` / `goal_gut` / `goal_skin` / `goal_general` (1:1 map)
- All paths → Q2

**Q2 — Supplement Format**
- Message: `How do you like taking {{category_singular}}?`
- QRs (4): `Smoothie or gel` / `Gummies` / `I'm open to anything` / `Haven't tried supplements yet`
- Action: Set Field `supplementFormat` = button label
- All paths → Q3

**Q3 — Health Concerns**
- Message: `Anything specific you're dealing with?`
- QRs (5): `Brain fog` / `Joint discomfort` / `Low energy` / `{{concern_4}}` / `Nah, just optimizing`
- Action: Set Field `healthConcern` = button label
- All paths → Q4

**Q4 — Flavor Preference**
- Message: `How adventurous are you with flavors?`
- QRs (3): `Keep it simple` / `Love tropical flavors` / `Surprise me`
- Action: Set Field `flavorPref` = button label
- All paths → Q5

**Q5 — Product Experience**
- Message: `Have you tried {{hero_ingredient}} before?`
- QRs (3): `Yes, love it` / `Tried it once` / `Never — I'm curious`
- Action: Set Field `seaMossExp` = button label
- All paths → Condition router

**Condition Router (in order, first match wins):**
1. IF `wellnessGoal` = "More energy" AND `supplementFormat` contains "Gummies" → Result_P1 ({{product_1_name}})
2. IF `wellnessGoal` = "Stronger immunity" AND `supplementFormat` contains "gel" → Result_P2 ({{product_2_name}})
3. IF `wellnessGoal` = "Better digestion" → Result_P3 ({{product_3_name}})
4. IF `wellnessGoal` = "Skin & hair" → Result_P4 ({{product_4_name}})
5. IF `flavorPref` = "Love tropical flavors" → Result_P5 ({{product_5_name}})
6. IF `healthConcern` contains "{{mens_keyword}}" → Result_P6 ({{product_6_name}})
7. ELSE → Result_Default ({{product_default_name}})

**Result Block (1 per product, ~9 blocks total + 1 bundle):**
- Actions BEFORE message:
  - Add Tag: `quiz_completed`
  - Add Tag: `quiz_result_p{n}` (matches condition slot)
  - Add Tag: `lead_hot`
  - Remove Tag: `lead_cold`
  - Set Field `quizResult` = `{{product_n_name}}`
- Message:
  ```
  Based on what you told me, I'd recommend **{{product_n_name}}** — here's why:

  {{product_n_pitch}}

  🛒 {{product_n_url}}

  Want to know more about what's in it, or explore other options?
  ```
- QRs (3): `Tell me more` (→ deeper detail message, loop back) / `See other products` (→ Flow 3) / `Back to menu` (→ Flow 1)

**End-state:** `quiz_completed` + 1 of 10 `quiz_result_*` + 1 of 5 `goal_*` + `lead_hot`; 5 fields populated.

---

### Flow 3: Product Guide

**Trigger:** Hub QR or "See other products" from Quiz.

**Entry actions:** Add Tag `browsed_products` (idempotent), update `lastInteraction`.

**Entry message:** `What are you interested in?`
**QRs (4):** `{{category_1_name}}` / `{{category_2_name}}` / `{{category_3_name}}` / `Bundles & Deals`

**Per-category sub-menu (4 sub-flows):**
- Message: 1-sentence category framing + product QRs (1 QR per SKU in category)
- Product card (1 message per SKU):
  ```
  **{{product_n_name}}**
  {{product_n_hook}}
  💰 ${{product_n_price}}
  🛒 {{product_n_url}}
  ```
- Footer message: `Want help choosing?` with QRs: `Take the quiz` (→ Flow 2) / `Tell me about something else` (→ category sub-menu) / `Back to menu` (→ Flow 1)

**Bundle sub-menu special block:**
```
**{{bundle_name}}**
{{bundle_pitch}}
💰 ${{bundle_price}} (save ${{bundle_savings}})
🛒 {{bundle_url}}

**Subscribe & Save {{sub_discount_pct}}%**
{{sub_pitch}}
🛒 {{subscription_url}}
```

---

### Flow 4: Education

**Trigger:** Hub QR `📚 Learn About {{hero_ingredient}}`.

**Entry actions:** Add Tag `browsed_education`, update `lastInteraction`.

**Entry message:** `What are you curious about?`
**QRs (4):** `What is {{hero_ingredient}}?` / `{{ingredient_2}} Benefits` / `{{ingredient_3}} Power` / `How We Source`

**4 article messages** (~150 words each) using template:
```
{{article_n_hook_line}}

{{article_n_body}}

People use it for:
• {{benefit_1}}
• {{benefit_2}}
• {{benefit_3}}
• {{benefit_4}}

{{article_n_close}}
```

Each article ends with QRs: `Which {{category_singular}} is right for me?` (→ Flow 2) / `Shop {{category}}` (→ Flow 3) / `Tell me about something else` (→ Education menu) / `Back to menu` (→ Flow 1)

---

### Flow 5: Social Proof

**Trigger:** Hub QR `⭐ See Reviews`.

**Entry actions:** Add Tag `browsed_reviews`, update `lastInteraction`.

**Single message (5 stacked reviews):**
```
Here's what real customers are saying:

⭐⭐⭐⭐⭐ {{review_1_name}}
"{{review_1_quote}}"

⭐⭐⭐⭐⭐ {{review_2_name}}
"{{review_2_quote}}"

⭐⭐⭐⭐⭐ {{review_3_name}}
"{{review_3_quote}}"

⭐⭐⭐⭐⭐ {{review_4_name}}
"{{review_4_quote}}"

⭐⭐⭐⭐⭐ {{review_5_name}}
"{{review_5_quote}}"
```

**QRs (4):** `Ready to try it` (→ Flow 2) / `Browse products` (→ Flow 3) / `More reviews` (URL → `{{reviews_page_url}}`) / `Back to menu` (→ Flow 1)

---

### Flow 6: FAQ Support

**Trigger:** Hub QR `💬 Ask a Question`.

**Entry actions:** Update `lastInteraction`.

**Entry message:** `What can I help with?`
**QRs (5):** `Shipping & Delivery` / `Ingredients & Quality` / `How to Use` / `Subscriptions` / `Talk to a Person`

**4 self-serve sub-messages** + 1 human-handoff sub-message. Each self-serve uses:
```
**{{topic}}**

{{4_bullet_facts}}

{{soft_close_line}}
```

**Talk to a Person sub-flow:**
- Add Tag: `needs_human_support`
- Message: `No problem! I'm connecting you with our team — someone will get back to you shortly. Feel free to ask anything while you wait.`
- QR: `Back to menu` → Flow 1
- (Installer should wire a Zap/webhook to Slack or email here.)

---

### Sequences 1–7

All sequences are built in **Automation → New Automation** (not inside a flow). Each = 1 trigger + 1 delay + 1 message + 1 tag action.

**Sequence 1 — 24h Quiz Offer**
- Trigger: tag added `quiz_completed`; condition NOT has tag `purchased`
- Delay: 24h
- Message:
  ```
  Hey! Your quiz matched you with **{{cuf:quizResult}}**.

  Here's {{discount_pct}}% off to try it:

  Code: {{discount_code}}
  🛒 {{shop_url}}

  Good for the next 48 hours.
  ```
- Action: Add Tag `followup_24h`

**Sequence 2 — 3-Day Review Nudge**
- Trigger: tag added `browsed_products` OR `browsed_education`; NOT `purchased`
- Delay: 3d
- Message:
  ```
  Still thinking about {{cuf:quizResult}}?

  Here's what {{review_featured_name}} said:

  "{{review_featured_quote}}" ⭐⭐⭐⭐⭐

  Questions? Just reply — I'm here to help.
  ```
- Action: Add Tag `followup_3d`

**Sequence 3 — 7-Day Check-In**
- Trigger: any engagement tag; NOT `purchased`; NOT `followup_7d`
- Delay: 7d
- Message:
  ```
  Quick question — was anything holding you back?

  I'm happy to answer questions or help you find the right product. No pressure, just here if you need me.
  ```
- Action: Add Tag `followup_7d`

**Sequence 4 — 14-Day Education**
- Trigger: NOT `purchased`; NOT `followup_14d`
- Delay: 14d
- Message: 3-tip educational content keyed off `wellnessGoal` (use one default tip set in v1; v1.1 can branch by goal field)
- Action: Add Tag `followup_14d`. No CTA.

**Sequence 5 — 1-Day Post-Purchase**
- Trigger: tag added `purchased`
- Delay: 1d
- Message:
  ```
  Your **{{cuf:quizResult}}** is on its way! 📦

  How to get the most from it:
  {{usage_tip}}

  Track your order: {{tracking_url}}
  Questions? Just reply.
  ```
- Action: Add Tag `post_purchase_1d`

**Sequence 6 — 7-Day Review Request**
- Trigger: tag `purchased`; NOT `post_purchase_7d`
- Delay: 7d
- Message:
  ```
  How are you liking your **{{cuf:quizResult}}**?

  We'd love to hear! Leave a review: {{review_form_url}}
  ⭐⭐⭐⭐⭐
  ```
- Action: Add Tag `post_purchase_7d`

**Sequence 7 — 21-Day Reorder**
- Trigger: tag `purchased`; NOT has tag `subscribed`; NOT `post_purchase_21d`
- Delay: 21d
- Message:
  ```
  Running low on **{{cuf:quizResult}}**?

  Subscribe & save {{sub_discount_pct}}% on every order — skip or cancel anytime.
  🛒 {{subscription_url}}

  Or grab a one-time refill: {{shop_url}}
  ```
- Action: Add Tag `post_purchase_21d`

---

## D. Placeholder Convention (Installer YAML Schema)

The installer's deploy YAML must supply these variables. Keys use snake_case to mirror ManyChat field conventions.

```yaml
brand:
  brand_name: "Vicelle Naturals"
  category: "wellness"            # plural noun used in Hub
  category_singular: "supplements" # singular noun used in Q2
  hero_ingredient: "Sea Moss"     # primary education hook
  ingredient_2: "Shilajit"
  ingredient_3: "Mushroom"
  mens_keyword: "testosterone"    # condition keyword for product 6 routing
  owner_first_name: "Naeem"
  shop_url: "https://vicellenaturals.com"
  subscription_url: "https://vicellenaturals.com/subscriptions"
  reviews_page_url: "https://vicellenaturals.com/reviews"
  discount_code: "WELCOME10"
  discount_pct: 10
  sub_discount_pct: 30

products:
  product_1: { name, slug, url, pitch, hook, price }   # energy + gummies
  product_2: { ... }                                    # immunity + gel
  product_3: { ... }                                    # digestion
  product_4: { ... }                                    # skin
  product_5: { ... }                                    # tropical
  product_6: { ... }                                    # men's
  product_7: { ... }                                    # extra slot
  product_8: { ... }
  product_9: { ... }
  product_default: { ... }
  bundle: { name, url, pitch, price, savings }

categories:
  category_1_name: "Sea Moss Gels"
  category_2_name: "Shilajit"
  category_3_name: "Mushroom Gummies"

reviews:
  review_1: { name, quote }
  ... (5 total)
  review_featured: { name, quote }  # used in Sequence 2

faq:
  shipping_block, ingredients_block, usage_block, subscriptions_block

education:
  article_1, article_2, article_3, article_4   # each: hook, body, benefits[4], close

assets:
  tracking_url, review_form_url
```

---

## E. Build Checklist (Naeem — 2-Hour Session)

Do this in the **Biznomad master ManyChat account** (separate from any client account).

**Pre-flight (10 min)**
1. Confirm master ManyChat account exists, PRO plan active, dummy IG/FB page connected.
2. Open Claude Code in this directory; verify `manychat_page_info()` returns master account.
3. Create folder: Automation → Flows → New Folder → `Wellness DM Ecosystem v1`.

**Tags & Fields (15 min)**
4. Run all 35 `manychat_create_tag` calls (script: paste from Section B).
5. Run all 8 `manychat_create_custom_field` calls.
6. Verify with `manychat_list_tags()` and `manychat_list_custom_fields()`.

**Flow Build (75 min)**
7. Build Flow 1 — Welcome Hub. Save as draft, do not wire QRs yet.
8. Build Flow 2 — Wellness Quiz (Q1-Q5 + condition router + 10 result blocks). 25 min.
9. Build Flow 3 — Product Guide (main menu + 4 sub-menus). 15 min.
10. Build Flow 4 — Education (4 articles). 10 min.
11. Build Flow 5 — Social Proof (1 message). 5 min.
12. Build Flow 6 — FAQ Support (5 sub-messages). 10 min.
13. Return to Flow 1; wire all 5 Hub QRs to flows 2–6.
14. Verify every flow has a "Back to menu" QR that routes to Flow 1.

**Sequences (15 min)**
15. Build all 7 sequences in Automation → New Automation. Use the trigger/delay/message/tag spec from Section C.

**Final pass (5 min)**
16. Mark every flow + sequence **Draft** (NOT Live — clients will activate after install).
17. Run `manychat_list_flows()` and screenshot the output; save flow `ns` values to `manychat-template-installer/v1-flow-namespace-map.json`.

**Quality gates:**
- Every QR has a destination (no dead buttons).
- All placeholders use the `{{snake_case}}` convention.
- No real product names, URLs, or brand strings — only `{{...}}`.

---

## F. Save-as-Template Instructions

ManyChat templates are exported via the **Templates** feature (PRO only).

1. In the master account, navigate to **Automation → Flows**.
2. Click the `Wellness DM Ecosystem v1` folder.
3. Top-right ⋯ menu → **"Create Template"** (or "Save as Template" depending on UI version).
4. Template name: `Wellness DM Ecosystem v1`
5. Description: `Conversational DM funnel for wellness/CPG brands. 6 flows + 7 sequences. Requires 35 tags + 8 custom fields. v1 — May 2026.`
6. Cover image: upload `template-cover.png` (1200x630, Biznomad-branded).
7. Sharing: **Private link** (unlisted, share-by-URL). DO NOT publish to public marketplace.
8. Click **Generate share link**. Copy the URL.
9. Save the share link to `manychat-template-installer/v1-share-link.txt`.

**Verify install works:** create a throwaway test account, open the share link, accept template → confirm all flows + sequences import. Note: ManyChat templates do NOT carry tags/fields — installer must recreate those via MCP on each client account.

---

**End of v1 build spec.**
