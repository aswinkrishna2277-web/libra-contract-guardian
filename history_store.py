"""
history_store.py — Libra Contract Guardian local analysis history.

A privacy-first, local-only persistence layer. Stores ANALYSIS RESULTS so a
user can revisit past work and recognise previously-analysed documents — WITHOUT
storing the client's raw document text by default.

Design principles (these are deliberate and defensible):
  1. LOCAL ONLY. The database is a SQLite file under ~/.libra/. It never leaves
     the machine. No cloud, no network, consistent with Libra's privacy model.
  2. DATA MINIMISATION BY DEFAULT. We store the analysis output, the filename,
     and a SHA-256 hash of the document. The hash lets us say "you have analysed
     this exact file before" without retaining the file itself.
  3. FULL-TEXT IS EXPLICIT OPT-IN. The raw document text is stored ONLY when the
     caller passes store_full_text=True, and that choice is recorded on the row.
  4. USER CONTROL. History can be listed, opened, deleted individually, or
     cleared entirely.

This module has no Streamlit or app dependencies, so it is independently
testable and reusable.
"""

from __future__ import annotations

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timezone
from typing import Any


# ─── Location (matches privacy_guard's ~/.libra convention) ──────────────────
def _default_dir() -> str:
    base = os.environ.get("LIBRA_LOG_DIR")
    if base:
        return base
    return os.path.join(os.path.expanduser("~"), ".libra")


def _db_path() -> str:
    return os.path.join(_default_dir(), "history.db")


# ─── Schema ──────────────────────────────────────────────────────────────────
_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT    NOT NULL,
    engine          TEXT    NOT NULL,   -- 'contract' | 'prpp' | 'tdm' | 'trademark'
    mode            TEXT,               -- e.g. 'search' | 'high_research'
    doc_name        TEXT,
    doc_hash        TEXT,               -- sha256 of the source text (or '')
    risk_level      TEXT,
    risk_score      INTEGER,
    result_json     TEXT    NOT NULL,   -- the full result dict, serialised
    full_text       TEXT,               -- NULL unless explicit opt-in
    stored_full_text INTEGER NOT NULL DEFAULT 0  -- 1 if user opted in
);
CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_analyses_hash    ON analyses(doc_hash);
CREATE INDEX IF NOT EXISTS idx_analyses_engine  ON analyses(engine);
"""


def _connect() -> sqlite3.Connection:
    os.makedirs(_default_dir(), exist_ok=True)
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the database and schema if they do not exist. Idempotent."""
    conn = _connect()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


# ─── Helpers ─────────────────────────────────────────────────────────────────
def hash_document(text: str) -> str:
    """Stable SHA-256 of document text — used to recognise repeat documents."""
    return hashlib.sha256((text or "").encode("utf-8", errors="ignore")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ─── Write ───────────────────────────────────────────────────────────────────
def save_analysis(
    engine: str,
    result: dict[str, Any],
    *,
    doc_name: str = "",
    doc_text: str = "",
    mode: str = "",
    risk_level: str = "",
    risk_score: int | None = None,
    store_full_text: bool = False,
) -> int | None:
    """Persist one analysis result. Returns the new row id, or None on failure.

    By default the raw document text is NOT stored — only its hash. Pass
    store_full_text=True to retain the full text (an explicit, recorded choice).
    Never raises to the caller; persistence failure must not break analysis.
    """
    try:
        init_db()
        doc_hash = hash_document(doc_text) if doc_text else ""
        full_text_to_store = doc_text if (store_full_text and doc_text) else None
        payload = json.dumps(result, default=str)[:5_000_000]  # safety cap
        conn = _connect()
        try:
            cur = conn.execute(
                """INSERT INTO analyses
                   (created_at, engine, mode, doc_name, doc_hash, risk_level,
                    risk_score, result_json, full_text, stored_full_text)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (_now(), engine, mode, doc_name, doc_hash, risk_level,
                 risk_score, payload, full_text_to_store,
                 1 if full_text_to_store is not None else 0),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
    except Exception:
        # Persistence is best-effort. A failure here must never break the app.
        return None


# ─── Read ────────────────────────────────────────────────────────────────────
def list_analyses(limit: int = 50, engine: str | None = None) -> list[dict]:
    """Return recent analyses (newest first) as lightweight summary rows.

    Does NOT include result_json or full_text — call get_analysis(id) for those.
    """
    try:
        init_db()
        conn = _connect()
        try:
            if engine:
                rows = conn.execute(
                    """SELECT id, created_at, engine, mode, doc_name, doc_hash,
                              risk_level, risk_score, stored_full_text
                       FROM analyses WHERE engine=? ORDER BY id DESC LIMIT ?""",
                    (engine, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT id, created_at, engine, mode, doc_name, doc_hash,
                              risk_level, risk_score, stored_full_text
                       FROM analyses ORDER BY id DESC LIMIT ?""",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


def get_analysis(analysis_id: int) -> dict | None:
    """Return one full analysis row (including the parsed result dict)."""
    try:
        init_db()
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM analyses WHERE id=?", (analysis_id,)
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            try:
                d["result"] = json.loads(d.get("result_json") or "{}")
            except Exception:
                d["result"] = {}
            return d
        finally:
            conn.close()
    except Exception:
        return None


def find_by_document(doc_text: str, limit: int = 10) -> list[dict]:
    """Find prior analyses of the SAME document (by hash). Lets the UI say
    'you have analysed this exact file before'."""
    try:
        h = hash_document(doc_text)
        if not h:
            return []
        init_db()
        conn = _connect()
        try:
            rows = conn.execute(
                """SELECT id, created_at, engine, mode, doc_name, risk_level, risk_score
                   FROM analyses WHERE doc_hash=? ORDER BY id DESC LIMIT ?""",
                (h, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


# ─── Delete ──────────────────────────────────────────────────────────────────
def delete_analysis(analysis_id: int) -> bool:
    try:
        init_db()
        conn = _connect()
        try:
            conn.execute("DELETE FROM analyses WHERE id=?", (analysis_id,))
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


def clear_all() -> bool:
    """Delete every saved analysis. Used by the 'clear history' control."""
    try:
        init_db()
        conn = _connect()
        try:
            conn.execute("DELETE FROM analyses")
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


def count_analyses() -> int:
    try:
        init_db()
        conn = _connect()
        try:
            n = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
            return int(n)
        finally:
            conn.close()
    except Exception:
        return 0


def stats() -> dict:
    """Small summary for a history dashboard."""
    try:
        init_db()
        conn = _connect()
        try:
            total = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
            by_engine = {
                r["engine"]: r["n"]
                for r in conn.execute(
                    "SELECT engine, COUNT(*) AS n FROM analyses GROUP BY engine"
                ).fetchall()
            }
            with_text = conn.execute(
                "SELECT COUNT(*) FROM analyses WHERE stored_full_text=1"
            ).fetchone()[0]
            return {"total": int(total), "by_engine": by_engine,
                    "with_full_text": int(with_text)}
        finally:
            conn.close()
    except Exception:
        return {"total": 0, "by_engine": {}, "with_full_text": 0}
