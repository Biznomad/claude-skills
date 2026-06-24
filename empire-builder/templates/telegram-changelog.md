# Telegram Changelog — Empire Builder Loop Update

Reference format for every Stage 3 Telegram notification.
Every post MUST include InlineKeyboardMarkup with working callbacks.

---

## Card format (sent via sendPhoto)

**Caption (max 1024 chars):**
```
✨ {{community_name}} — Loop Update

Track: [a/b/c] — [Track name]
Built: [One-line description of what was staged]

📊 Stats:
• Members: [N] [▲+N from last run if increased]
• Content this month: [N] pieces
• Run #[N] of [max_iterations]

📂 Ready in outbox:
`outbox/YYYY-MM-DD/[filename]`

[What to do]: [Specific 1-line instruction, e.g. "Post the IG Reel — script is ready"]

Next track: [a/b/c] ([Track name])
```

**Photo:** branded card PNG (or fallback: text-only if PIL not available)
Card elements:
- Community name (top, primary color)
- Track badge: "(a) Reach" / "(b) Community" / "(c) Proof"
- What was built (middle, large)
- Key metric (member count, content count)
- Biznomad/Empire Builder logo (bottom right, small)

---

## InlineKeyboardMarkup (MANDATORY — every post)

### Default set (when increment is staged and ready):
```python
reply_markup = {
    "inline_keyboard": [
        [
            {"text": "✅ Publish outbox", "callback_data": "publish_{{slug}}_YYYYMMDD"},
            {"text": "📝 Edit draft", "callback_data": "edit_{{slug}}_YYYYMMDD"}
        ],
        [
            {"text": "⏭ Skip this one", "callback_data": "skip_{{slug}}_YYYYMMDD"},
            {"text": "📊 See stats", "callback_data": "stats_{{slug}}"}
        ]
    ]
}
```

### Decision-required set (when founder approval needed before proceeding):
```python
reply_markup = {
    "inline_keyboard": [
        [
            {"text": "✅ Approve & continue", "callback_data": "approve_{{slug}}_YYYYMMDD"},
            {"text": "❌ Reject this one", "callback_data": "reject_{{slug}}_YYYYMMDD"}
        ],
        [
            {"text": "📝 Edit first", "callback_data": "edit_{{slug}}_YYYYMMDD"}
        ]
    ]
}
```

### Stop-condition hit (no-progress alert):
```python
reply_markup = {
    "inline_keyboard": [
        [
            {"text": "✅ Change direction", "callback_data": "pivot_{{slug}}"},
            {"text": "⏸ Pause loop", "callback_data": "pause_{{slug}}"}
        ],
        [
            {"text": "📊 Full stats", "callback_data": "stats_{{slug}}"}
        ]
    ]
}
```

---

## Send method

```python
# Always use sendPhoto (not sendMessage) for branded card
bot.send_photo(
    chat_id=dm_chat_id,
    photo=open("card.png", "rb"),  # or BytesIO
    caption=caption,
    reply_markup=reply_markup,
    parse_mode="Markdown"
)
```

If PIL/Pillow not available on this machine, fallback to sendMessage:
```python
bot.send_message(
    chat_id=dm_chat_id,
    text=caption,
    reply_markup=reply_markup,
    parse_mode="Markdown"
)
```

---

## Fallback: outbox card (when Telegram not configured)

Write to `clients/<slug>/outbox/YYYY-MM-DD/telegram-card.md`:

```markdown
# Loop Update — [YYYY-MM-DD]

**Track:** [a/b/c] — [Track name]
**Built:** [Description]
**Staged to:** `outbox/YYYY-MM-DD/[filename]`
**What to do:** [Specific instruction]

**Stats:**
- Members: [N]
- Content this month: [N] pieces
- Run #[N]

**Next track:** [a/b/c]
```

---

## Callback handler setup (if Hermes or loop bot is running on VPS)

Register handlers in your Telegram bot:

```python
@bot.callback_query_handler(func=lambda c: c.data.startswith("publish_"))
def handle_publish(call):
    slug, date = call.data.replace("publish_", "").split("_")
    # Mark outbox/date as "to publish" — notify founder in next message
    bot.answer_callback_query(call.id, "📋 Outbox marked for publishing!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("stats_"))
def handle_stats(call):
    slug = call.data.replace("stats_", "")
    metrics = load_metrics(slug)  # read clients/<slug>/metrics.json
    bot.send_message(call.message.chat.id, format_stats(metrics))
```

If no Hermes/bot running: skip callbacks. Buttons are informational only.

---

*Part of empire-builder for {{slug}}*
