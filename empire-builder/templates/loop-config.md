# Empire Builder loop config — {{community_name}}

Auto-generated from client config for {{slug}}.
Written to `clients/<slug>/loop-config.md` at the start of Stage 3.

## Identity
- **Community:** {{community_name}} — {{community.topic}}
- **Founder:** {{founder.name}}
- **Goal:** {{goal.member_count}} paying members at ${{offer.price_per_month}}/mo

## The platform
- **Where it lives:** https://www.skool.com/{{handles.skool}}
- **Is live:** {{skool_config.is_live}}
- **Outbox path:** clients/{{slug}}/outbox/

## The three rotation tracks
- **(a) Reach / acquisition:** Create {{cadence.posts_per_week}} content pieces for the week
  targeting {{community.audience}} on {{channels}}
- **(b) Community / product:** Improve the Skool experience — classroom, welcome DM,
  gamification, live calls, retention
- **(c) Proof / showcase:** Member wins, testimonials, metrics card, shareable results

## Memory
- **Session state:** clients/{{slug}}/SESSION_STATE.md
- **Metrics:** clients/{{slug}}/metrics.json
- **Loop spec:** clients/{{slug}}/loop-spec.md

## Telegram changelog
- **Bot token source:** {{telegram.bot_token_env_path}}
- **DM chat-id:** {{telegram.dm_chat_id}}
- **Buttons:** Every post needs InlineKeyboardMarkup.
  Default: `[✅ Publish outbox] [📝 Edit draft] [⏭ Skip this one] [📊 Stats]`
  Decision-required: `[✅ Approve] [❌ Reject] [📝 Edit]`

## Brand
- **Voice:** {{brand.voice}}
- **Card style:** Primary {{brand.palette.primary}}, Accent {{brand.palette.accent}}
- **Emoji rule:** {{brand.emoji_rule}}
- **Keywords use:** {{brand.keywords_use}}
- **Keywords avoid:** {{brand.keywords_avoid}}

## Safety
- All content staged to outbox/ — never posted automatically
- No passwords or credentials — outbox only
- {{safety.notes}}
- Confirm Skool URL is live before referencing in any content: {{skool_config.community_url}}
