"""
draft_checkpoint.py — Libra Contract Guardian crash-resilient draft checkpoints.

Chunked drafting of a long contract can take many minutes across many model
calls. If the machine loses power, or the app is closed, all completed sections
would otherwise be lost and the whole draft would have to start again.

This module persists each section AS IT COMPLETES, so an interrupted draft can
resume from where it stopped rather than from the beginning.

Design principles (deliberately consistent with history_store.py):
  1. LOCAL ONLY. Checkpoints live under ~/.libra/ — the same convention used by
     history_store.py and privacy_guard.py. Nothing leaves the machine.
  2. TRANSIENT BY DESIGN. A checkpoint exists only while a draft is in progress.
     It is DELETED automatically the moment the draft completes successfully, so
     contract-derived text is not left sitting on disk after it is needed.
  3. NEVER BREAKS DRAFTING. Every function swallows its own errors. Checkpointing
     is best-effort: a failure to save must never abort a draft in progress.
  4. USER CONTROL. Checkpoints can be listed, resumed, or cleared explicitly.

Because a checkpoint necessarily contains contract-derived text, its transience
is the privacy control: it is written only during active generation, and removed
on completion. A stale checkpoint therefore always means "a draft was
interrupted" — which is exactly when the user wants it back.
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


def _checkpoint_dir() -> str:
    return os.path.join(_default_dir(), "checkpoints")


def _key_for(contract_text: str) -> str:
    """Stable identifier for a contract, so its checkpoint can be found again."""
    return hashlib.sha256(
        (contract_text or "").encode("utf-8", errors="ignore")
    ).hexdigest()[:32]


def _path_for(key: str) -> str:
    return os.path.join(_checkpoint_dir(), f"draft_{key}.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ─── Write ───────────────────────────────────────────────────────────────────
def save_progress(
    contract_text: str,
    *,
    doc_name: str = "",
    total_sections: int,
    completed: list[str],
) -> bool:
    """Persist the sections drafted so far. Best-effort; never raises.

    Called after EVERY completed section, so an interruption loses at most one
    section's work rather than the entire draft.
    """
    try:
        os.makedirs(_checkpoint_dir(), exist_ok=True)
        key = _key_for(contract_text)
        payload: dict[str, Any] = {
            "version": 1,
            "key": key,
            "doc_name": doc_name,
            "updated_at": _now(),
            "total_sections": int(total_sections),
            "completed_count": len(completed),
            "completed": completed,
        }
        tmp = _path_for(key) + ".tmp"
        # Write to a temp file then replace, so a crash mid-write cannot leave a
        # half-written checkpoint that would fail to parse on resume.
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        os.replace(tmp, _path_for(key))
        return True
    except Exception:
        return False


# ─── Read ────────────────────────────────────────────────────────────────────
def load_progress(contract_text: str) -> dict | None:
    """Return the saved checkpoint for this contract, or None if there isn't one."""
    try:
        path = _path_for(_key_for(contract_text))
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or "completed" not in data:
            return None
        return data
    except Exception:
        return None


def has_checkpoint(contract_text: str) -> bool:
    return load_progress(contract_text) is not None


def list_checkpoints() -> list[dict]:
    """Summaries of every interrupted draft, newest first."""
    out: list[dict] = []
    try:
        d = _checkpoint_dir()
        if not os.path.isdir(d):
            return []
        for name in os.listdir(d):
            if not (name.startswith("draft_") and name.endswith(".json")):
                continue
            try:
                with open(os.path.join(d, name), "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                out.append({
                    "key": data.get("key", ""),
                    "doc_name": data.get("doc_name", ""),
                    "updated_at": data.get("updated_at", ""),
                    "completed_count": int(data.get("completed_count", 0)),
                    "total_sections": int(data.get("total_sections", 0)),
                })
            except Exception:
                continue
        out.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
        return out
    except Exception:
        return []


# ─── Delete ──────────────────────────────────────────────────────────────────
def clear_progress(contract_text: str) -> bool:
    """Remove this contract's checkpoint. Called on successful completion."""
    try:
        path = _path_for(_key_for(contract_text))
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception:
        return False


def clear_all() -> bool:
    """Remove every checkpoint — the user-facing 'clear interrupted drafts' control."""
    try:
        d = _checkpoint_dir()
        if not os.path.isdir(d):
            return True
        for name in os.listdir(d):
            if name.startswith("draft_") and name.endswith(".json"):
                try:
                    os.remove(os.path.join(d, name))
                except Exception:
                    continue
        return True
    except Exception:
        return False


def count_checkpoints() -> int:
    return len(list_checkpoints())
