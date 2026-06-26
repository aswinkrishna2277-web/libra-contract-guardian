# Libra Contract Guardian — Setup Guide

A privacy-first, local-only legal-intelligence application. Everything runs on
your own computer. No document ever leaves your machine.

This guide is written to be followed by anyone — no programming needed. It takes
about 15 minutes the first time, then the app opens in seconds after that.

---

## What you need (one-time installs)

### 1. Python (the language Libra runs on)
- Go to **https://www.python.org/downloads/**
- Download the latest version (3.11 or newer)
- Run the installer. **On Windows, tick the box "Add Python to PATH"** on the
  first screen before clicking Install. This step matters.

### 2. Ollama (the local AI engine) — recommended
- Go to **https://ollama.com** and download it for your system.
- Install and open it. Then, one time, open a terminal / command prompt and run:
  ```
  ollama pull mistral:7b-instruct
  ```
  This downloads the AI model Libra uses (a few GB — once only).
- *Optional but recommended.* Without Ollama, Libra still runs fully in
  "deterministic mode" — you just don't get the AI-phrased narrative layer.

---

## Running Libra

### Windows
Double-click **`Start_Libra_Windows.bat`**.

### macOS
Double-click **`Start_Libra_Mac.command`**.
*(Note: the Mac launcher follows standard conventions but has not yet been tested on a Mac, as it was developed on Windows. It should work; please verify on first use.)*
(If macOS blocks it the first time — "unidentified developer" — right-click the
file, choose **Open**, then **Open** again. You only do this once.)

**What happens on first run:** the launcher sets itself up automatically
(creates its workspace and installs what it needs — a few minutes, once). It then
runs a quick environment check and tells you if anything is missing. After that,
your web browser opens with Libra running. Every future launch takes seconds.

**To stop Libra:** close the black launcher window, or press `Ctrl + C` in it.

---

## The environment check

Each time it starts, Libra runs a short check and prints something like:

```
  [OK]   Python 3.12.3
  [OK]   Virtual environment present
  [OK]   Ollama is running
  [OK]   A 'mistral' model is available
  Ready. Launch the app and you are good to go.
```

If any line shows `[!]` instead of `[OK]`, it tells you exactly what to do.
Nothing here stops the app from starting — it is guidance, not a gate.

---

## Troubleshooting

**"python is not recognized" (Windows)**
Python isn't installed, or "Add Python to PATH" wasn't ticked. Reinstall from
python.org and make sure that box is ticked.

**The app starts but analysis says "deterministic fallback"**
Ollama isn't running. Open Ollama (or run `ollama serve`) and try again.

**I moved the Libra folder and now it won't start**
A virtual environment can't be relocated. Delete the `venv` folder inside the
Libra folder and run the launcher again — it rebuilds automatically.

**Upload rejected as too large**
Documents are capped at 25 MB by design. Use a smaller file.

**It's slow to start**
First start of the day is slowest (the AI model loads into memory). This is
normal for a local AI app and speeds up after the first analysis.

---

## Your privacy

Libra is local-only by design. Your documents are processed entirely on your own
machine; nothing is uploaded anywhere. Analysis results are saved locally (in a
private folder on your computer) so you can revisit past work — and the full text
of a document is only ever stored if you explicitly tick that option.

---

*Libra Contract Guardian v2.0 — a local-only legal-analysis application,
engineered to production-grade standards, developed and maintained by
R.A. Aswin Krishna for his own professional use. It is not a commercial product
and not a substitute for qualified legal advice.*
