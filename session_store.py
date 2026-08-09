"""
session_store.py — Libra Contract Guardian cross-engine session persistence.

Purpose
-------
Libra never loses completed work. Every engine — Analyser, PRPP, TDM, Copyright
Radar, Trademark, Playbook, Cross-Check — writes its finished result here. If the
app closes, crashes, or the machine powers off, the user is offered an EXPLICIT
restore on next launch.

Design principles (deliberately mirroring history_store.py and draft_checkpoint.py)
  1. LOCAL ONLY. A single JSON file under ~/.libra/. Never leaves the machine.
  2. NEVER AUTOMATIC. Saved work is offered, never silently reinstated. The user
     presses Restore, or presses Discard. Nothing happens on its own.
  3. NEVER FATAL. Every function swallows its own errors. Persistence failing
     must never break an analysis the user is in the middle of.
  4. USER CONTROL. Restore and discard are both always available, and the age of
     the saved session is shown so the choice is informed.
  5. TRANSIENT BY DESIGN. This is recovery state, not an archive. history_store
     remains the durable record; this file is cleared whenever the user says so.

This module has no Streamlit or app dependencies, so it is independently testable.
"""

from __future__ import annotations

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Any


# ─── Location (matches history_store / privacy_guard ~/.libra convention) ────
def _default_dir() -> str:
    base = os.environ.get("LIBRA_LOG_DIR")
    if base:
        return base
    return os.path.join(os.path.expanduser("~"), ".libra")


def _session_dir() -> str:
    return os.path.join(_default_dir(), "session")


def _session_path() -> str:
    return os.path.join(_session_dir(), "session.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fingerprint(text: str) -> str:
    """Short hash so a restore can be matched to the document it came from."""
    return hashlib.sha256((text or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


# ─── Write ───────────────────────────────────────────────────────────────────
def save_results(
    *,
    contract_name: str = "",
    contract_text: str = "",
    results: dict[str, Any] | None = None,
) -> bool:
    """
    Persist the current set of engine results.

    `results` maps an engine key to its result dict, e.g.
        {"analysis": {...}, "prpp": {...}, "tdm": {...}}
    Only non-empty results are stored. Returns True on success, False on any
    failure — and never raises, because losing a save must not break an analysis.
    """
    try:
        payload_results = {k: v for k, v in (results or {}).items() if v}
        if not payload_results:
            # Nothing worth saving — remove any stale file rather than keeping
            # a session that no longer reflects any completed work.
            return clear()

        os.makedirs(_session_dir(), exist_ok=True)
        payload = {
            "saved_at": _now(),
            "contract_name": contract_name or "",
            "contract_fingerprint": _fingerprint(contract_text),
            "contract_chars": len(contract_text or ""),
            "contract_text": contract_text or "",
            "engines": sorted(payload_results.keys()),
            "results": payload_results,
        }
        tmp = _session_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, default=str)
        # Atomic replace so an interrupted write can never leave a corrupt file.
        os.replace(tmp, _session_path())
        return True
    except Exception:
        return False


# ─── Read ────────────────────────────────────────────────────────────────────
def load_results() -> dict | None:
    """Return the saved session, or None if there isn't a usable one."""
    try:
        path = _session_path()
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or not data.get("results"):
            return None
        return data
    except Exception:
        return None


def has_session() -> bool:
    return load_results() is not None


def describe() -> dict | None:
    """
    Lightweight summary for the restore prompt — enough for the user to decide
    without loading everything. Returns None when there is nothing saved.
    """
    data = load_results()
    if not data:
        return None
    try:
        saved_at = data.get("saved_at", "")
        age_txt = ""
        if saved_at:
            try:
                then = datetime.fromisoformat(saved_at)
                mins = int((datetime.now(timezone.utc) - then).total_seconds() // 60)
                if mins < 1:
                    age_txt = "just now"
                elif mins < 60:
                    age_txt = f"{mins} minute{'s' if mins != 1 else ''} ago"
                elif mins < 1440:
                    age_txt = f"{mins // 60} hour{'s' if mins // 60 != 1 else ''} ago"
                else:
                    age_txt = f"{mins // 1440} day{'s' if mins // 1440 != 1 else ''} ago"
            except Exception:
                age_txt = ""
        return {
            "saved_at": saved_at,
            "age": age_txt,
            "contract_name": data.get("contract_name", ""),
            "contract_chars": int(data.get("contract_chars") or 0),
            "engines": list(data.get("engines") or []),
            "engine_count": len(data.get("engines") or []),
        }
    except Exception:
        return None


# ─── Delete ──────────────────────────────────────────────────────────────────
def clear() -> bool:
    """Discard the saved session. Used by the explicit Discard control."""
    try:
        path = _session_path()
        if os.path.exists(path):
            os.remove(path)
        tmp = path + ".tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        return True
    except Exception:
        return False


def session_path() -> str:
    """Exposed so the UI can tell the user exactly where the file lives."""
    return _session_path()
