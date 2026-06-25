#!/usr/bin/env bash
# ============================================================================
#  Libra Contract Guardian v2.0 - macOS / Linux launcher
#  Run with:  ./Start_Libra_Mac.command   (or double-click on macOS)
# ============================================================================

# Move to the directory this script lives in
cd "$(dirname "$0")" || exit 1

echo ""
echo " ========================================================"
echo "  Libra Contract Guardian v2.0"
echo " ========================================================"
echo ""

# --- Pick a python command ---
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo " ERROR: Python is not installed or not on your PATH."
    echo " Install Python 3.11+ from https://www.python.org/downloads/"
    read -r -p " Press Enter to close..."
    exit 1
fi

# --- Create the virtual environment on first run ---
if [ ! -f "venv/bin/activate" ]; then
    echo " [setup] No virtual environment found. Creating one now..."
    "$PY" -m venv venv || { echo " ERROR: could not create venv"; read -r -p " Press Enter..."; exit 1; }
    # shellcheck disable=SC1091
    source venv/bin/activate
    echo " [setup] Installing dependencies (first run only, please wait)..."
    python -m pip install --upgrade pip >/dev/null 2>&1
    pip install -r requirements.txt || { echo " ERROR: dependency install failed"; read -r -p " Press Enter..."; exit 1; }
else
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

echo ""
echo " Tip: for full AI analysis, make sure Ollama is running"
echo "      (the app still works in deterministic mode without it)."
echo ""
echo " Starting Libra... a browser tab will open shortly."
echo " To stop the app, close this window or press Ctrl+C."
echo ""

streamlit run app.py
