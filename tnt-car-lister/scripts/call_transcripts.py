#!/usr/bin/env python3
"""TNT call transcription pipeline.

Sources
  - Retell  (Avery agent / +16786733121): full transcript + AI summary + recording URL via API.
  - Gemini fallback: transcribe ANY audio URL or file (use for GHL LC-Phone / Beside recordings
    once you can hand it an audio URL — GHL's own API blocks recording download with the PIT).

Config
  RETELL_API_KEY -> /root/two-and-through-ops/config/.retell.env
  GEMINI_API_KEY -> /root/two-and-through-ops/.env  (or /root/.hermes/.env, /root/nareem/.env)

Output
  data/call-transcripts/<call_id>.json   (raw + parsed)
  data/call-transcripts/<call_id>.txt    (human-readable: summary + transcript)
  data/call-transcripts/.seen.json       (dedup for `sync`)

Usage
  call_transcripts.py sync [--days N]         # pull Retell calls from last N days (default 14); cron-friendly
  call_transcripts.py call <retell_call_id>   # one Retell call
  call_transcripts.py phone +1XXXXXXXXXX      # all Retell calls from/to a number
  call_transcripts.py transcribe <url|path>   # Gemini-transcribe any audio (recording), prints transcript
"""
import os, sys, json, time, base64, urllib.request, urllib.error

OPS = "/root/two-and-through-ops"
OUT = os.path.join(OPS, "data", "call-transcripts")
SEEN = os.path.join(OUT, ".seen.json")


def _cfg(path, key):
    try:
        for ln in open(path):
            ln = ln.strip()
            if ln.startswith(key + "=") and not ln.startswith("#"):
                return ln.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def retell_key():
    return _cfg(os.path.join(OPS, "config", ".retell.env"), "RETELL_API_KEY")


def gemini_key():
    for f in (os.path.join(OPS, ".env"), "/root/.hermes/.env", "/root/nareem/.env"):
        k = _cfg(f, "GEMINI_API_KEY")
        if k:
            return k
    return ""


def _req(url, headers, method="GET", body=None, raw=False, timeout=120):
    data = json.dumps(body).encode() if (body is not None and not raw) else body
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
        return b if raw else json.loads(b)


def retell_req(path, method="GET", body=None):
    H = {"Authorization": "Bearer " + retell_key(), "Content-Type": "application/json"}
    return _req("https://api.retellai.com" + path, H, method, body)


def _save(call):
    os.makedirs(OUT, exist_ok=True)
    cid = call.get("call_id") or call.get("id") or str(int(time.time()))
    json.dump(call, open(os.path.join(OUT, cid + ".json"), "w"), indent=1)
    an = call.get("call_analysis") or {}
    ts = call.get("start_timestamp")
    when = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(ts / 1000)) if ts else "?"
    lines = [
        f"call_id : {cid}",
        f"when    : {when}",
        f"from    : {call.get('from_number','')}   to: {call.get('to_number','')}",
        f"recording: {call.get('recording_url','')}",
        "",
        "SUMMARY:", an.get("call_summary", "") or "(none)",
        "",
        "TRANSCRIPT:", call.get("transcript", "") or "(none)",
    ]
    open(os.path.join(OUT, cid + ".txt"), "w").write("\n".join(lines))
    return cid


def cmd_sync(days=14):
    now = int(time.time() * 1000)
    lower = now - days * 86400 * 1000
    res = retell_req("/v2/list-calls", "POST", {
        "filter_criteria": {"start_timestamp": {"lower_threshold": lower, "upper_threshold": now}},
        "sort_order": "descending", "limit": 500,
    })
    calls = res if isinstance(res, list) else res.get("calls", [])
    seen = set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()
    new = 0
    for c in calls:
        cid = c.get("call_id")
        if not cid or cid in seen:
            continue
        _save(c)
        seen.add(cid)
        new += 1
    os.makedirs(OUT, exist_ok=True)
    json.dump(sorted(seen), open(SEEN, "w"))
    print(f"sync: {len(calls)} calls in window, {new} new saved -> {OUT}")


def cmd_call(cid):
    c = retell_req("/v2/get-call/" + cid)
    p = _save(c)
    print("saved", p)
    print(open(os.path.join(OUT, p + ".txt")).read())


def cmd_phone(num):
    res = retell_req("/v2/list-calls", "POST",
                     {"filter_criteria": {"from_number": [num], "to_number": [num]},
                      "sort_order": "descending", "limit": 100})
    calls = res if isinstance(res, list) else res.get("calls", [])
    # API ANDs criteria; also do a client-side OR sweep as fallback
    if not calls:
        res = retell_req("/v2/list-calls", "POST", {"sort_order": "descending", "limit": 500})
        allc = res if isinstance(res, list) else res.get("calls", [])
        calls = [c for c in allc if num in (c.get("from_number", "") + c.get("to_number", ""))]
    print(f"{len(calls)} Retell calls for {num}")
    for c in calls:
        print(" ", _save(c))


def gemini_transcribe(src):
    key = gemini_key()
    if not key:
        return "ERROR: no GEMINI_API_KEY"
    if src.startswith("http"):
        audio = _req(src, {"User-Agent": "Mozilla/5.0"}, raw=True)
    else:
        audio = open(src, "rb").read()
    mime = "audio/mpeg"
    if src.lower().endswith(".wav"):
        mime = "audio/wav"
    elif src.lower().endswith(".m4a"):
        mime = "audio/mp4"
    body = {"contents": [{"parts": [
        {"text": "Transcribe this phone call verbatim with speaker labels (Agent / Caller). "
                 "After the transcript, add a line 'VEHICLE DETAILS:' listing any year, make, "
                 "model, VIN, engine code, fault/OBD codes, or condition mentioned."},
        {"inline_data": {"mime_type": mime, "data": base64.b64encode(audio).decode()}}]}]}
    H = {"Content-Type": "application/json"}
    d = _req("https://generativelanguage.googleapis.com/v1beta/models/"
             "gemini-2.5-flash:generateContent?key=" + key, H, "POST", body, timeout=300)
    try:
        return d["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return json.dumps(d)[:1000]


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    cmd = a[0]
    if cmd == "sync":
        days = 14
        if "--days" in a:
            days = int(a[a.index("--days") + 1])
        cmd_sync(days)
    elif cmd == "call" and len(a) > 1:
        cmd_call(a[1])
    elif cmd == "phone" and len(a) > 1:
        cmd_phone(a[1])
    elif cmd == "transcribe" and len(a) > 1:
        print(gemini_transcribe(a[1]))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
