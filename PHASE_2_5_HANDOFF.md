# Phase 2.5 — Data Protection Layer (Complete)

**Status:** 286 integration tests passing (added 31 for the privacy guard)
**New file:** `privacy_guard.py`, `test_phase_2_5.py`
**Modified:** `app.py` (three network call sites now guarded)

---

## What this does

Your evidence pack claims Libra "runs entirely locally, usable on confidential matters" and that "no client data leaves the device." Phase 2.5 makes that claim true and verifiable, rather than just asserted.

Before this phase, three places in `app.py` made outbound network calls:

1. **DuckDuckGo trademark search** — sent the proposed mark name to DuckDuckGo
2. **Wikipedia trademark lookup** — sent the proposed mark name to Wikipedia
3. **Legal-source link checker** — checked that public legislation URLs are alive (no user data, but still a network call)

The first two transmitted user input off-device. That contradicted the "nothing leaves the device" claim. Phase 2.5 puts all three behind a single, auditable privacy guard.

## How the guard works

`privacy_guard.py` is the single control point for every decision that could send data off-device.

**Local-only mode (default ON):** blocks every outbound call except to the local AI model at 127.0.0.1. When on, no document, no contract, no trademark, nothing leaves the machine. The local LLM call (Ollama on 127.0.0.1:11434) always passes because it is on-device.

**Defence in depth:** turning off local-only mode does NOT by itself permit any call. To make an off-device call, THREE conditions must all hold: local-only is off, explicit consent is granted, AND the specific category (e.g. trademark web search) is enabled. A single accidental toggle cannot open the door.

**Network audit log:** every attempt — allowed or blocked — is recorded in a local file (`~/.libra/network_audit.log`) with a timestamp, the destination host, and the call category. You can review exactly what the app did or tried to do. Critically, the log records hosts and categories only — never the document content or user input.

**Cloud-sync risk detection:** the guard can check whether Libra is running from inside a OneDrive / Dropbox / Google Drive folder. This is the single most common way "local-only" software accidentally leaks data on Windows — the sync client copies files to the cloud independently of the app. The guard flags this so you can move Libra out of the synced folder for confidential work.

## The honesty this buys you

When a UK firm or in-house counsel presses on "how do you handle the data," you can now say, accurately:

- "Local-only mode is on by default and blocks every outbound call except to the on-device AI model."
- "Every network attempt is logged locally; I can show you the audit log."
- "The trademark web search is the only feature that transmits anything off-device, and it transmits only the mark name you type — never an uploaded document — and it is disabled by default."
- "The app warns you if you are running it from a cloud-synced folder, because that is the real confidentiality risk on a Windows machine."

That is a confident, specific, defensible answer. It is the difference between a portfolio demo and something you can credibly say you use on real matters.

## Deployment

In `C:\Users\aswin\OneDrive\Desktop\Libra version 2\`:

1. Drop in two new files:
   - `privacy_guard.py`
   - `test_phase_2_5.py`
2. Overwrite one file:
   - `app.py` (the three network call sites are now guarded)
3. Stop Streamlit (Ctrl+C), then:
   ```
   venv\Scripts\activate
   python test_phase_2_5.py
   streamlit run app.py
   ```
   Expect 31/31 on the privacy suite.

## IMPORTANT — the OneDrive warning applies to YOU

Your project lives at `C:\Users\aswin\OneDrive\Desktop\Libra version 2`. That is **inside OneDrive**. The privacy guard will flag this, and it is correct to.

What this means: if you process a confidential client document with Libra while it sits in that folder, OneDrive's sync client may copy that document to Microsoft's cloud — not because Libra sent it, but because OneDrive syncs everything in that folder automatically.

For genuinely confidential matters, you have two options:
1. Move the whole `Libra version 2` folder OUT of OneDrive (e.g. to `C:\Libra` or `C:\Users\aswin\Documents\Libra`), OR
2. Right-click the folder in OneDrive → "Always keep on this device" is not enough — you need to pause syncing or use "Free up space" carefully. The cleaner fix is to move it out.

This is not a Libra bug. It is a property of running any document tool inside OneDrive. But you should know about it before you tell anyone you process confidential matters locally, because a sophisticated client will ask exactly this question.

## What you can now add to the UI (optional, later)

The privacy guard exposes functions the app can surface in a Settings or Privacy tab:

- `privacy_guard.get_policy()` / `set_policy(...)` — toggle local-only mode and category permissions
- `privacy_guard.audit_summary()` — show counts of allowed/blocked calls
- `privacy_guard.get_audit()` — show the recent network attempts
- `privacy_guard.privacy_statement()` — the plain-language privacy statement
- `privacy_guard.assess_onedrive_risk(working_dir)` — the cloud-sync warning

Wiring these into a visible Privacy tab would be a nice Phase 4 (demo polish) addition — it lets you SHOW the privacy posture during a demo rather than just describe it. Not required now; the guard works regardless of whether the UI surfaces it.

## What this does NOT do

- It does not encrypt files at rest. If you need that, it is a separate piece of work.
- It does not stop YOU from copying a document somewhere. It governs what the app does, not what you do.
- It does not change the local LLM — that was already localhost-only via `local_llm.py`'s own hardcoded check, which remains as defence in depth.

## Test status

| Suite | Tests | Status |
|---|---|---|
| Phase 2A | 28 | ✓ |
| Phase 2B | 47 | ✓ |
| Phase 2C TDM | 56 | ✓ |
| Phase 2C Trademark | 33 | ✓ |
| Phase 2C-fix (ID leak) | 60 | ✓ |
| Trademark similarity | 31 | ✓ |
| Phase 2.5 privacy guard | 31 | ✓ |
| **Total** | **286** | **✓** |

## Where this leaves the project

You now have, as a coherent whole:
- The accepted EIPR paper
- A working prototype: PRPP, TDM, and Trademark engines refactored, citations verified, the BURRBERY gap fixed
- A defensible privacy posture: local-only by default, audited, with the cloud-sync risk surfaced
- A one-page evidence pack and three outreach templates

The remaining build work is **Phase 2D** (refactor the last four engines in `app.py`) and **Phase 4** (demo polish, including optionally surfacing the privacy controls in the UI). Phase 3 documentation is partly done via the evidence pack; a fuller defensibility pack could come in Phase 4.

The highest-leverage non-build task now is the outreach itself — you have the kit; the next move is sending it to ten well-chosen people.
