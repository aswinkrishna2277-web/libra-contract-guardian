#!/usr/bin/env python3
"""
check_setup.py — Libra Contract Guardian first-run environment check.

Pure standard library only (no third-party imports), so it can run BEFORE the
virtual environment or any dependencies are installed. It reports, in plain
language, what is ready and what still needs doing:

  1. Python version (3.11+ recommended)
  2. Whether the virtual environment exists
  3. Whether Ollama is running (the local AI server)
  4. Whether the default model is pulled

It never fails hard — it prints guidance and exits 0 so a launcher can show the
report and still continue. Run directly:  python check_setup.py
"""

import sys
import os
import json
import urllib.request
import urllib.error

OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "mistral:7b-instruct"

GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"; DIM = "\033[2m"; RESET = "\033[0m"
# Windows terminals may not render ANSI; degrade gracefully.
if os.name == "nt" and not os.environ.get("WT_SESSION"):
    GREEN = YELLOW = RED = DIM = RESET = ""


def ok(msg):    print(f"  {GREEN}[OK]{RESET}   {msg}")
def warn(msg):  print(f"  {YELLOW}[!]{RESET}    {msg}")
def info(msg):  print(f"  {DIM}{msg}{RESET}")


def check_python():
    v = sys.version_info
    if (v.major, v.minor) >= (3, 11):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
        return True
    warn(f"Python {v.major}.{v.minor} detected — 3.11 or newer is recommended.")
    info("Download: https://www.python.org/downloads/")
    return False


def check_venv():
    here = os.path.dirname(os.path.abspath(__file__))
    win = os.path.join(here, "venv", "Scripts", "activate.bat")
    nix = os.path.join(here, "venv", "bin", "activate")
    if os.path.exists(win) or os.path.exists(nix):
        ok("Virtual environment present")
        return True
    warn("No virtual environment yet — it will be created on first launch.")
    return False


def check_ollama():
    """Return (running: bool, models: list[str])."""
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
        models = [m.get("name", "") for m in data.get("models", [])]
        ok("Ollama is running")
        return True, models
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        warn("Ollama is not running (the local AI server).")
        info("The app still works in deterministic mode without it, but for full")
        info("AI-phrased analysis: install from https://ollama.com and start it.")
        return False, []


def check_model(models):
    if not models:
        return False
    # Match the default model family loosely (mistral:7b-instruct, mistral:latest…)
    base = DEFAULT_MODEL.split(":")[0]
    if any(DEFAULT_MODEL == m or m.startswith(base) for m in models):
        ok(f"A '{base}' model is available")
        return True
    warn(f"The default model is not pulled. Run:  ollama pull {DEFAULT_MODEL}")
    if models:
        info("Models currently available: " + ", ".join(models))
    return False


def main():
    print()
    print("  Libra Contract Guardian — environment check")
    print("  " + "-" * 44)
    py = check_python()
    check_venv()
    running, models = check_ollama()
    if running:
        check_model(models)
    print("  " + "-" * 44)

    # Overall guidance — never blocks; just orients the user.
    if py and running:
        print(f"  {GREEN}Ready.{RESET} Launch the app and you are good to go.")
    elif py and not running:
        print(f"  {YELLOW}Mostly ready.{RESET} The app will run in deterministic mode;")
        print("  start Ollama for full AI analysis.")
    else:
        print(f"  {YELLOW}Action needed above.{RESET} The app will still attempt to start.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
