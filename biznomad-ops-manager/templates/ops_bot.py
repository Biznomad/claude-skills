#!/usr/bin/env python3
"""
NaReem v2 — Two & Through Junk Removal ops manager bot.

Conversational Telegram bot powered by Kimi K2.6 (coding plan) with
full server-admin tool access behind an inline-button approval gate.

Protocol: Kimi responds with JSON
  {
    "say":  "<conversational reply to user>",
    "do":   [ { "type": ..., ...args..., "description": "..." }, ... ]
  }

Action types:
  read_file     {path}                    auto-execute (read-only)
  list_dir      {path}                    auto-execute
  status_kpi    {}                        auto-execute (reads data files)
  shell         {cmd}                     REQUIRES APPROVAL
  write_file    {path, content}           REQUIRES APPROVAL
  restart_svc   {service}                 REQUIRES APPROVAL
  stop_svc      {service}                 REQUIRES APPROVAL
  start_svc     {service}                 REQUIRES APPROVAL
  append_data   {file, record}            REQUIRES APPROVAL (data/*.json)
  post_summary  {text}                    auto-execute (posts to group)
"""
from __future__ import annotations

import os, sys, json, uuid, asyncio, logging, subprocess, shlex
from datetime import datetime, timezone
from pathlib import Path
from collections import deque

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

ROOT = Path("/root/nareem")
DATA = Path("/root/two-and-through-ops/data")
CONFIG = Path("/root/two-and-through-ops/config/business.json")
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
PENDING_FILE = ROOT / "pending.json"
APPROVAL_LOG = ROOT / "approvals.jsonl"
SHELL_TIMEOUT = 60  # seconds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "nareem.log"),
        logging.StreamHandler(),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("nareem")

TOKEN = os.environ["TELEGRAM_TOKEN"]
GROUP_ID = int(os.environ.get("GROUP_ID", "-5207375121"))
ADMIN_IDS = {int(x) for x in os.environ.get("ADMIN_IDS", "5165464044").split(",") if x.strip()}
_raw_key = os.environ["KIMI_API_KEY"]
KIMI_KEY = _raw_key if _raw_key.startswith("sk-") else f"sk-kimi-{_raw_key}"
KIMI_BASE = os.environ.get("KIMI_API_BASE", "https://api.kimi.com/coding/v1")
KIMI_MODEL = os.environ.get("KIMI_MODEL", "kimi-for-coding")
KIMI_UA = os.environ.get("KIMI_USER_AGENT", "claude-code/1.0")

async def _is_authorized_approver(ctx, user_id: int) -> bool:
    """True if user is in ADMIN_IDS, or is a member of the ops group."""
    if user_id in ADMIN_IDS:
        return True
    try:
        m = await ctx.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        return m.status in ("creator", "administrator", "member")
    except Exception:
        return False

HISTORY: dict[int, deque] = {}   # chat_id -> rolling turns

# ─── persistence helpers ─────────────────────────────────────────────────────

def _load_json(p: Path, default):
    try: return json.loads(p.read_text())
    except Exception: return default

def _save_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, default=str))

def _append_jsonl(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(obj, default=str) + "\n")

# ─── system prompt ───────────────────────────────────────────────────────────

ACTION_SPEC = """
You can take actions on the TNT server. When you want to do something, include
a "do" array in your JSON response. Each action is an object with a "type"
field plus type-specific args plus a "description" field (human-readable).

Always respond as STRICT JSON ONLY, no preamble:
{ "say": "<short conversational reply>", "do": [ ... optional actions ... ] }

Action catalog:

  AUTO-EXECUTE (no approval needed):
  - {"type":"read_file","path":"<abs path>","description":"..."}
  - {"type":"list_dir","path":"<abs path>","description":"..."}
  - {"type":"status_kpi","description":"refresh KPI snapshot"}
  - {"type":"post_summary","text":"<text>","description":"post to group"}

  REQUIRES APPROVAL (Naeem or Karriem must tap ✅ in the group):
  - {"type":"shell","cmd":"<command>","description":"..."}
  - {"type":"write_file","path":"<abs path>","content":"<text>","description":"..."}
  - {"type":"restart_svc","service":"<name>","description":"..."}
  - {"type":"stop_svc","service":"<name>","description":"..."}
  - {"type":"start_svc","service":"<name>","description":"..."}
  - {"type":"append_data","file":"<leads|jobs|quotes|invoices|customers>","record":{...},"description":"..."}

Rules:
- Keep "say" SHORT (1–4 lines). Decision-ready.
- Only propose actions that are clearly needed; don't fish for approvals.
- Group destructive actions together when sensible; one approval can ship multiple commands.
- If you need data first, propose a read_file/list_dir first, then continue next turn.
- Never propose: rm -rf /, mkfs, dd to disk, passwd, useradd, anything irreversible without naming it explicitly in description.
- Approved spend caps: ads $100/day, no new domains, no new SaaS subs without asking.
""".strip()

def _system_prompt() -> str:
    biz = _load_json(CONFIG, {})
    company = biz.get("company", {})
    services = biz.get("services", [])
    svc_str = "\n".join(f"  • {s.get('name')}: ${s.get('base_price')} ({s.get('price_unit')})" for s in services[:8])
    return f"""You are NaReem, AI operations manager for {company.get('name','Two & Through Junk Removal')}.
You report to Naeem and Karriem (owner) in Telegram group TNT_OPS_GROUP.
You have FULL admin access to the TNT server (187.77.204.166) behind an approval gate.

Mission: 30-day sprint to ramp from 2–3 calls to a truck-running-24/7 lead engine.
We have a $50–100/day ad budget approved. Every reply should move toward booking a job.

Company: {company.get('name','')} — {company.get('tagline','')}
Service area: {', '.join(company.get('service_area',[])[:6])}
Phone: {company.get('phone','(unset)')}  Web: {company.get('website','(unset)')}

Services & starting prices:
{svc_str}

Files you can rely on (read freely):
- /root/two-and-through-ops/data/{{leads,jobs,quotes,customers,invoices}}.json
- /root/two-and-through-ops/config/business.json
- /root/nareem/spend.json

{ACTION_SPEC}
""".strip()

# ─── kimi call ───────────────────────────────────────────────────────────────

async def kimi_chat(chat_id: int, user_msg: str, tool_result: str | None = None) -> dict:
    """Returns parsed JSON: {say: str, do: [actions]}"""
    hist = HISTORY.setdefault(chat_id, deque(maxlen=24))
    msgs = [{"role": "system", "content": _system_prompt()}]
    msgs.extend(hist)
    if tool_result is not None:
        msgs.append({"role": "user", "content": f"[tool_result]\n{tool_result}"})
    else:
        msgs.append({"role": "user", "content": user_msg})
    payload = {
        "model": KIMI_MODEL,
        "messages": msgs,
        "temperature": 0.4,
        "max_tokens": 6000,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=120) as cli:
        r = await cli.post(
            f"{KIMI_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {KIMI_KEY}",
                "Content-Type": "application/json",
                "User-Agent": KIMI_UA,
            },
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
    raw = (data["choices"][0]["message"].get("content") or "").strip()
    if not raw:
        return {"say": "(empty Kimi response — try again)", "do": []}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # try to salvage by stripping markdown fences
        cleaned = raw.strip("` \n")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        try:
            parsed = json.loads(cleaned)
        except Exception:
            log.warning("Kimi returned non-JSON: %r", raw[:300])
            return {"say": raw[:1500], "do": []}
    if not isinstance(parsed, dict):
        return {"say": str(parsed)[:1500], "do": []}
    parsed.setdefault("say", "")
    parsed.setdefault("do", [])
    hist.append({"role": "user", "content": user_msg if tool_result is None else f"[tool_result]\n{tool_result}"})
    hist.append({"role": "assistant", "content": raw})
    return parsed

# ─── action execution ────────────────────────────────────────────────────────

AUTO_TYPES = {"read_file", "list_dir", "status_kpi", "post_summary"}
APPROVAL_TYPES = {"shell", "write_file", "restart_svc", "stop_svc", "start_svc", "append_data"}

def _exec_read_file(args: dict) -> str:
    p = Path(args["path"])
    if not p.exists(): return f"ERR: not found: {p}"
    if p.stat().st_size > 200_000: return f"ERR: too large ({p.stat().st_size} bytes); use shell head/tail"
    try:
        return p.read_text()[:50_000]
    except Exception as e:
        return f"ERR: {type(e).__name__}: {e}"

def _exec_list_dir(args: dict) -> str:
    p = Path(args["path"])
    if not p.is_dir(): return f"ERR: not a dir: {p}"
    items = sorted(p.iterdir(), key=lambda x: x.name)[:80]
    return "\n".join(f"{'d' if i.is_dir() else 'f'} {i.name}" for i in items)

def _exec_status_kpi(_args: dict) -> str:
    leads = _load_json(DATA / "leads.json", [])
    jobs = _load_json(DATA / "jobs.json", [])
    quotes = _load_json(DATA / "quotes.json", [])
    invoices = _load_json(DATA / "invoices.json", [])
    return json.dumps({
        "leads": len(leads) if isinstance(leads, list) else 0,
        "jobs": len(jobs) if isinstance(jobs, list) else 0,
        "quotes": len(quotes) if isinstance(quotes, list) else 0,
        "invoices": len(invoices) if isinstance(invoices, list) else 0,
    })

def _exec_shell(args: dict) -> str:
    cmd = args["cmd"]
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=SHELL_TIMEOUT)
        out = (r.stdout + ("\n[stderr]\n" + r.stderr if r.stderr else "")).strip()
        return f"exit={r.returncode}\n{out[:5000]}"
    except subprocess.TimeoutExpired:
        return f"ERR: timeout after {SHELL_TIMEOUT}s"
    except Exception as e:
        return f"ERR: {type(e).__name__}: {e}"

def _exec_write_file(args: dict) -> str:
    p = Path(args["path"])
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(args["content"])
        return f"wrote {len(args['content'])} bytes -> {p}"
    except Exception as e:
        return f"ERR: {type(e).__name__}: {e}"

def _exec_svc(action: str, args: dict) -> str:
    svc = args["service"]
    op = {"restart_svc": "restart", "stop_svc": "stop", "start_svc": "start"}[action]
    return _exec_shell({"cmd": f"systemctl {op} {shlex.quote(svc)} && systemctl is-active {shlex.quote(svc)}"})

def _exec_append_data(args: dict) -> str:
    file_key = args["file"]
    allowed = {"leads", "jobs", "quotes", "invoices", "customers"}
    if file_key not in allowed: return f"ERR: file must be one of {allowed}"
    p = DATA / f"{file_key}.json"
    cur = _load_json(p, [])
    if not isinstance(cur, list): cur = []
    rec = dict(args["record"])
    rec.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    rec.setdefault("id", str(uuid.uuid4())[:8])
    cur.append(rec)
    _save_json(p, cur)
    return f"appended to {file_key} (total {len(cur)})"

def execute_action(action: dict) -> str:
    t = action.get("type")
    try:
        if t == "read_file":    return _exec_read_file(action)
        if t == "list_dir":     return _exec_list_dir(action)
        if t == "status_kpi":   return _exec_status_kpi(action)
        if t == "shell":        return _exec_shell(action)
        if t == "write_file":   return _exec_write_file(action)
        if t in ("restart_svc","stop_svc","start_svc"): return _exec_svc(t, action)
        if t == "append_data":  return _exec_append_data(action)
        if t == "post_summary": return "(handled by caller)"
        return f"ERR: unknown action type: {t}"
    except Exception as e:
        log.exception("execute_action failed")
        return f"ERR: {type(e).__name__}: {e}"

# ─── pending approvals ───────────────────────────────────────────────────────

def _load_pending() -> dict:
    return _load_json(PENDING_FILE, {})

def _save_pending(d: dict):
    _save_json(PENDING_FILE, d)

def _stash_action(action: dict, orig_chat_id: int) -> str:
    aid = uuid.uuid4().hex[:10]
    pending = _load_pending()
    pending[aid] = {
        "action": action,
        "chat_id": orig_chat_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_pending(pending)
    return aid

def _approval_card_text(action: dict) -> str:
    t = action.get("type")
    desc = action.get("description", "(no description)")
    detail = ""
    if t == "shell":        detail = f"<code>{(action.get('cmd','')[:400])}</code>"
    elif t == "write_file": detail = f"path: <code>{action.get('path','')}</code>\nbytes: {len(action.get('content','') or '')}"
    elif t in ("restart_svc","stop_svc","start_svc"): detail = f"service: <code>{action.get('service','')}</code>"
    elif t == "append_data": detail = f"file: {action.get('file')}\nrecord: <code>{json.dumps(action.get('record',{}))[:300]}</code>"
    return f"⚠️ <b>Approval needed</b> — <code>{t}</code>\n{desc}\n\n{detail}"

# ─── Telegram handlers ───────────────────────────────────────────────────────

async def _send_action_results_back(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int, results: list[str]):
    """Feed tool results back to Kimi for a follow-up natural reply."""
    summary = "\n\n".join(results)
    parsed = await kimi_chat(chat_id, "", tool_result=summary)
    say = parsed.get("say", "").strip()
    if say:
        await ctx.bot.send_message(chat_id=chat_id, text=say[:3800])
    # if kimi proposes more actions in the follow-up, process them too (1 hop)
    actions = parsed.get("do", []) or []
    for action in actions:
        await _handle_proposed_action(ctx, chat_id, action)

async def _handle_proposed_action(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int, action: dict):
    t = action.get("type")
    if t in AUTO_TYPES:
        if t == "post_summary":
            await ctx.bot.send_message(chat_id=chat_id, text=action.get("text","")[:3800])
            return
        result = execute_action(action)
        await _send_action_results_back(ctx, chat_id, [f"[{t}] result:\n{result}"])
        return
    if t in APPROVAL_TYPES:
        aid = _stash_action(action, chat_id)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"appr:ok:{aid}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"appr:no:{aid}"),
        ]])
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=_approval_card_text(action),
            parse_mode=constants.ParseMode.HTML,
            reply_markup=kb,
        )
        return
    await ctx.bot.send_message(chat_id=chat_id, text=f"⚠️ Unknown action type: {t}")

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    chat_id = msg.chat_id
    user = msg.from_user
    if chat_id != GROUP_ID and user.id not in ADMIN_IDS: return
    text = msg.text.strip()
    if not text: return
    log.info("MSG chat=%s user=%s text=%r", chat_id, user.username, text[:120])
    await ctx.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
    try:
        parsed = await kimi_chat(chat_id, text)
    except httpx.HTTPStatusError as e:
        await msg.reply_text(f"⚠️ Kimi {e.response.status_code}: {e.response.text[:300]}")
        return
    except Exception as e:
        log.exception("kimi error")
        await msg.reply_text(f"⚠️ Brain error: {type(e).__name__}: {e}")
        return
    say = (parsed.get("say") or "").strip()
    actions = parsed.get("do", []) or []
    if say:
        await msg.reply_text(say[:3800])
    for action in actions:
        await _handle_proposed_action(ctx, chat_id, action)

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q: return
    await q.answer()
    data = q.data or ""
    if not data.startswith("appr:"):
        return
    _, verdict, aid = data.split(":", 2)
    pending = _load_pending()
    entry = pending.get(aid)
    user_name = q.from_user.username or q.from_user.first_name or str(q.from_user.id)
    if not entry:
        try: await q.edit_message_text(f"{q.message.text}\n\n⚠️ Action expired or already handled.", parse_mode=None)
        except Exception: pass
        return
    if not await _is_authorized_approver(ctx, q.from_user.id):
        await ctx.bot.send_message(chat_id=q.message.chat_id, text=f"Sorry {user_name}, only ops-group members can approve.")
        return
    action = entry["action"]
    orig_chat = entry["chat_id"]
    pending.pop(aid, None); _save_pending(pending)
    _append_jsonl(APPROVAL_LOG, {"aid": aid, "user": user_name, "verdict": verdict, "action": action, "ts": datetime.now(timezone.utc).isoformat()})
    if verdict == "no":
        try: await q.edit_message_text(f"❌ <b>Rejected by {user_name}</b>\n{action.get('description','')}", parse_mode=constants.ParseMode.HTML)
        except Exception: pass
        return
    # approved — execute
    try: await q.edit_message_text(f"✅ <b>Approved by {user_name}</b> — executing…\n{action.get('description','')}", parse_mode=constants.ParseMode.HTML)
    except Exception: pass
    result = execute_action(action)
    truncated = result[:3500]
    await ctx.bot.send_message(chat_id=orig_chat, text=f"📤 <b>Result</b> [<code>{action.get('type')}</code>]\n<pre>{truncated}</pre>", parse_mode=constants.ParseMode.HTML)
    await _send_action_results_back(ctx, orig_chat, [f"[{action.get('type')}] result:\n{result}"])

# ─── command shortcuts ───────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 NaReem online. Full admin access on TNT, gated by your approval.\n\n"
        "Commands: /status /leads /jobs /spend /pending /help\n"
        "Or just talk — I'll plan, quote, execute (with approval cards)."
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/status — KPI dashboard\n"
        "/leads — recent leads\n"
        "/jobs — upcoming jobs\n"
        "/spend — ad spend & CPL\n"
        "/pending — open approval queue\n"
        "/help — this menu\n\n"
        "Just talk normally for everything else."
    )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = json.loads(_exec_status_kpi({}))
    invoices = _load_json(DATA / "invoices.json", [])
    rev = sum(float(i.get("amount", 0) or 0) for i in (invoices if isinstance(invoices, list) else []))
    pending_n = len(_load_pending())
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await update.message.reply_text(
        f"📊 TNT Status — {today}\n"
        f"Leads: {s['leads']}\n"
        f"Quotes: {s['quotes']}\n"
        f"Jobs: {s['jobs']}\n"
        f"Invoices: {s['invoices']} (${rev:,.0f})\n"
        f"Pending approvals: {pending_n}"
    )

async def cmd_leads(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    leads = _load_json(DATA / "leads.json", [])
    if not isinstance(leads, list) or not leads:
        await update.message.reply_text("No leads logged yet.")
        return
    lines = [f"• {l.get('name','?')} — {l.get('phone','?')} ({l.get('status','new')})" for l in leads[-5:]]
    await update.message.reply_text("📞 Last 5 leads:\n" + "\n".join(lines))

async def cmd_jobs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    jobs = _load_json(DATA / "jobs.json", [])
    if not isinstance(jobs, list) or not jobs:
        await update.message.reply_text("No jobs booked yet.")
        return
    upcoming = [j for j in jobs if j.get("status") in ("scheduled","confirmed")][-5:]
    if not upcoming:
        await update.message.reply_text("No upcoming jobs scheduled.")
        return
    lines = [f"• {j.get('scheduled_at','?')} — {j.get('customer','?')} (${j.get('price','?')})" for j in upcoming]
    await update.message.reply_text("🚛 Upcoming jobs:\n" + "\n".join(lines))

async def cmd_spend(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = _load_json(ROOT / "spend.json", {"today": 0, "month": 0, "cpl": None})
    await update.message.reply_text(
        f"💰 Ad spend\nToday: ${data.get('today',0):.2f}\nMonth: ${data.get('month',0):.2f}\nCPL: {data.get('cpl') or '—'}"
    )

async def cmd_pending(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    p = _load_pending()
    if not p:
        await update.message.reply_text("No pending approvals.")
        return
    lines = [f"• {aid[:6]} — {e['action'].get('type')}: {e['action'].get('description','')[:60]}" for aid, e in list(p.items())[:10]]
    await update.message.reply_text(f"⏳ Open approvals ({len(p)}):\n" + "\n".join(lines))

async def on_error(update, ctx):
    log.exception("handler error: %s", ctx.error)

def main():
    log.info("NaReem v2 starting — group=%s admins=%s model=%s", GROUP_ID, ADMIN_IDS, KIMI_MODEL)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("leads", cmd_leads))
    app.add_handler(CommandHandler("jobs", cmd_jobs))
    app.add_handler(CommandHandler("spend", cmd_spend))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CallbackQueryHandler(on_callback, pattern=r"^appr:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
