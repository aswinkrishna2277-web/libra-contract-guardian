# Libra Contract Guardian — Setup & Run Guide

A privacy-first, local-only legal-intelligence application. Everything runs on
your own machine; no document ever leaves your device.

---

## Requirements

- **Python 3.11 or newer** — https://www.python.org/downloads/
  (On Windows, tick *"Add Python to PATH"* during installation.)
- **Ollama** (optional but recommended) — https://ollama.com
  After installing, pull a model once: `ollama pull mistral:7b-instruct`
  Without Ollama the app still runs, using its deterministic engines; the AI
  phrasing layer is simply skipped.

---

## Easiest way to run

### Windows
Double-click **`Start_Libra_Windows.bat`**.

The first run creates a virtual environment and installs dependencies
automatically (this takes a few minutes once). Every run after that starts in
seconds. A browser tab opens automatically.

### macOS
Double-click **`Start_Libra_Mac.command`**.

If macOS blocks it the first time ("unidentified developer"), right-click the
file → **Open** → **Open**, or run once in Terminal:
`chmod +x Start_Libra_Mac.command` then double-click.

---

## Manual way (either platform)

```bash
# 1. Create a virtual environment (first time only)
python -m venv venv

# 2. Activate it
#    Windows:
venv\Scripts\activate
#    macOS / Linux:
source venv/bin/activate

# 3. Install dependencies (first time only)
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

To stop the app, press **Ctrl+C** in the terminal, or close the launcher window.

---

## Notes on dependencies

The versions in `requirements.txt` are pinned to a known-good set verified on
Windows (June 2026). They use cross-platform wheels and are expected to install
cleanly on macOS as well. If a specific package version is ever unavailable for
your platform, remove the `==version` from that one line and let pip select a
compatible build.

---

## Troubleshooting

- **"python is not recognized"** — Python isn't installed or not on PATH.
  Reinstall from python.org and ensure PATH is selected (Windows).
- **The app opens but analysis says "deterministic fallback"** — Ollama isn't
  running. Start Ollama; the AI phrasing layer will then activate.
- **Moved the project folder and it won't start** — a virtual environment can't
  be moved. Delete the `venv` folder and run the launcher again to rebuild it.
- **Upload rejected as too large** — the limit is 25 MB per document by design.

---

*Libra Contract Guardian v2.0 — a working research prototype maintained by
R.A. Aswin Krishna for his own professional use. Not a commercial product;
not a substitute for qualified legal advice.*
