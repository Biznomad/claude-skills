# TNT Voice Stack — call transcript sources

Three different systems handle calls. A given call's transcript lives in exactly ONE of them — find the right source before assuming anything is missing.

## Which provider has which call

| Line | Provider | Who | Has transcript? | How to get it |
|---|---|---|---|---|
| **+16786733121** | **Retell** (Avery AI agent) | inbound AI intake | ✅ API — full transcript + AI summary + recording | `call_transcripts.py` (Retell API) |
| **678-501-7902** | **Beside** ("Ava" receptionist) | main line AI | ✅ via Beside app/webhook | webhook → `data/beside-call-bridge.json`; or scrape via `scripts/beside_poller.py` (saved Playwright session, goes stale, re-login = phone OTP) |
| outbound human dials | **GHL LC-Phone** | owner/staff calling out | ❌ recording NOT downloadable (403 with PIT token); Voice-AI transcript NOT in API (400/404) | GHL UI only — view in conversation |

## Keys
- `RETELL_API_KEY` → `/root/two-and-through-ops/config/.retell.env`
- `GEMINI_API_KEY` → `/root/two-and-through-ops/.env` (also `/root/.hermes/.env`, `/root/nareem/.env`)
- Beside session → `/root/two-and-through-ops/beside-poller/storage_state.json`

## Retell API
```
POST https://api.retellai.com/v2/list-calls   {filter_criteria:{from_number, to_number, start_timestamp}, limit}
GET  https://api.retellai.com/v2/get-call/<call_id>   → transcript, call_analysis.call_summary, recording_url
```
Retell agent id: `agent_add06eb5b1df7f32ea4debf2a7`.

## The transcribe fallback (any audio)
`call_transcripts.py transcribe <url|path>` downloads the audio and feeds it to Gemini `gemini-2.5-flash` with a prompt that transcribes verbatim (speaker labels) + extracts a `VEHICLE DETAILS:` block (year/make/model/VIN/engine code/condition). Works for Retell recordings AND any GHL/Beside recording URL you can obtain. **This is how to pull the spoken engine code / mileage.**

## Common failure: "call isn't in Retell"
A lead's calls may predate a provider migration or have hit a different line. Example: 2026-07-16 leads hit the Beside line, so they are ABSENT from Retell (Retell's calls ran only 6/14–7/14). Before concluding a transcript is gone, confirm which line handled it from the GHL conversation (call message `to_number`).

## Gemini 429
The `GEMINI_API_KEY` is shared across the fleet and hits daily free-tier quota. Symptom: every classify/transcribe call fails. It resets on its own (rolls daily). Don't force operations that depend on it — wait for reset or retry next day.
