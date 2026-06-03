# Libra — Local LLM Setup Guide

**One-time setup. Run these steps once on your machine. After this, launching Libra is a single command.**

---

## Step 1 — Install Ollama

Ollama is a free, open-source local LLM runtime. It's the engine that runs the model on your machine. No data leaves your computer.

### Windows

1. Open https://ollama.com/download in a browser
2. Click "Download for Windows"
3. Run the installer (`OllamaSetup.exe`)
4. Accept defaults — installs to `C:\Users\YourName\AppData\Local\Programs\Ollama`

After install, Ollama runs automatically in the background. You'll see its icon in the system tray.

### macOS

```bash
# Option A: Download from website
# Visit https://ollama.com/download and run the .dmg installer

# Option B: Install via Homebrew
brew install ollama
```

After install:
```bash
# Start Ollama
ollama serve
```

(Leave this terminal open. Ollama needs to run in the background.)

### Linux (Ubuntu/Debian)

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Verify it's running
systemctl status ollama
```

---

## Step 2 — Verify Ollama works

Open a terminal (or Command Prompt on Windows) and run:

```bash
ollama --version
```

You should see something like `ollama version is 0.3.x`. If you see "command not found," reinstall.

---

## Step 3 — Download the model

This is the one-time download. The model file is ~4.7GB. Get on a stable internet connection.

```bash
ollama pull mistral:7b-instruct
```

This downloads Mistral 7B Instruct — a 7-billion-parameter language model trained to follow instructions. It's free, open-source, and licensed under Apache 2.0 (you can use it commercially without restrictions).

Wait for download to complete. You'll see a progress bar. On a 50 Mbps connection this takes about 15 minutes.

---

## Step 4 — Test the model

Run a quick test to confirm the model works:

```bash
ollama run mistral:7b-instruct "Respond with exactly: HELLO LIBRA"
```

You should see the model respond. The first response is slow (model loading into memory); subsequent responses are fast.

If the response is gibberish or fails entirely, your hardware may be too constrained. Report back and we'll switch to a smaller model.

---

## Step 5 — Verify memory usage

While the model is loaded, check that your machine isn't struggling:

**Windows:** Open Task Manager → Performance tab → Memory. Should show the model using ~5GB.

**macOS:** Open Activity Monitor → Memory tab. Look for "ollama" process using ~5GB.

**Linux:** Run `free -h` in a terminal. Used memory should have increased by ~5GB.

If your system feels sluggish or you're using swap heavily, we need to drop to a smaller model (Phi-3-mini, ~2.3GB).

---

## Step 6 — Install Python dependencies for Libra

Open a terminal in the Libra project folder and run:

```bash
# Create a virtual environment (one-time)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

The updated `requirements.txt` (which I'll generate next) will include the `ollama` Python client. No Anthropic library needed.

---

## What you've just built

After completing these six steps:

- A local LLM runtime is installed on your machine
- A 7B parameter model is downloaded and verified working
- Python environment is ready to run Libra
- **No data ever leaves your machine when you use Libra**

Total time investment: ~30 minutes of attention, ~15 minutes of waiting for downloads.

---

## Troubleshooting

**"Out of memory" errors when running the model:**
Drop to a smaller model:
```bash
ollama pull phi3:mini
```
Then I update Libra's config to use `phi3:mini` instead of `mistral:7b-instruct`.

**Model responses are very slow (>30 seconds for short outputs):**
This is expected on CPU-only machines. The model still works; it's just patient. If unbearable, drop to `phi3:mini` for speed.

**Ollama refuses to start:**
On macOS/Linux, ensure port 11434 isn't already in use:
```bash
lsof -i :11434
```

**Model output is incoherent:**
Some 7B models on heavily-constrained hardware produce poor outputs. Check Step 5. If memory is borderline, dropping to a smaller model improves coherence.

---

## What happens next

Once your setup is verified, the next deliverable is `local_llm.py` — the Libra module that talks to Ollama. After that, I strip out every Anthropic API call in the codebase and replace it with calls to that module. By end of Week 1, the app runs entirely locally with zero external dependencies.

**Confirm completion of Steps 1-6 and I'll generate `local_llm.py` and the updated `requirements.txt`.**
