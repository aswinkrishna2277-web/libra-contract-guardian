"""
libra_logging.py — Libra Contract Guardian application logging.

PRIVACY-FIRST DESIGN. This logger exists to make the application debuggable in
real use, WITHOUT ever compromising Libra's core guarantee that no document
content leaves the machine — including to a log file on the machine itself.

Guarantees:
  1. LOCAL ONLY. Logs are written to ~/.libra/logs/ (matching the privacy_guard
     and history_store conventions). Nothing is ever transmitted off-host.
  2. NO DOCUMENT CONTENT. The logger records events, errors, timings, function
     names, and error *types* — never contract text, never analysis output,
     never anything derived from a user's document. A redaction guard scrubs
     anything that looks like bulk content before it is written.
  3. NEVER CRASHES THE APP. Every logging operation is defensive. If the log
     directory cannot be created or written, logging silently downgrades to a
     no-op. Logging must never be the reason the application fails.
  4. BOUNDED. A rotating file handler caps total log size so the file can never
     grow without limit.

Usage:
    from libra_logging import get_logger
    log = get_logger(__name__)
    log.info("analysis_started", extra={"engine": "contract"})
    log.exception("extraction_failed")   # records traceback, not document text

Design note: callers pass STRUCTURAL facts (engine name, error type, duration),
never document-derived strings. The redaction guard is a safety net, not a
licence to log content.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import re

# ── Location (matches ~/.libra convention used elsewhere) ────────────────────
_MAX_BYTES = 1_000_000      # 1 MB per file
_BACKUP_COUNT = 3           # keep 3 rotated files → ~4 MB ceiling total
_LOGGER_PREFIX = "libra"

# A single guard flag so we only attempt setup once and degrade quietly after.
_CONFIGURED = False
_FILE_HANDLER: logging.Handler | None = None


def _log_dir() -> str:
    base = os.environ.get("LIBRA_LOG_DIR")
    if base:
        return os.path.join(base, "logs")
    return os.path.join(os.path.expanduser("~"), ".libra", "logs")


def _log_path() -> str:
    return os.path.join(_log_dir(), "libra.log")


# ── Redaction guard ──────────────────────────────────────────────────────────
# Defence in depth: even if a caller mistakenly passes a long content string,
# scrub it before it reaches disk. We redact any single token/run longer than
# a threshold (document text and extracts are long; structural log fields are
# short), and collapse anything that looks like a multi-line blob.
_LONG_RUN = re.compile(r"\S{200,}")          # 200+ non-space chars = likely content
_REDACTED = "[redacted:len=%d]"


def _scrub(text: str) -> str:
    """Remove anything that looks like bulk document content from a log string."""
    try:
        if text is None:
            return ""
        s = str(text)
        # Collapse very long single runs (e.g. a pasted blob with no spaces).
        s = _LONG_RUN.sub(lambda m: _REDACTED % len(m.group(0)), s)
        # Hard cap any individual message: structural logs are short; anything
        # over 1000 chars is suspicious, so truncate with a marker.
        if len(s) > 1000:
            s = s[:1000] + (_REDACTED % (len(s) - 1000))
        return s
    except Exception:
        return "[unloggable]"


class _RedactingFormatter(logging.Formatter):
    """Formatter that scrubs the final message before it is written."""

    def format(self, record: logging.LogRecord) -> str:
        try:
            original = super().format(record)
            return _scrub(original)
        except Exception:
            # Formatting must never raise into the logging machinery.
            return "[log-format-error]"


def _configure() -> None:
    """Set up the rotating file handler once. Silent no-op on any failure."""
    global _CONFIGURED, _FILE_HANDLER
    if _CONFIGURED:
        return
    _CONFIGURED = True   # set first: even if setup fails, never retry-loop
    try:
        d = _log_dir()
        os.makedirs(d, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            _log_path(),
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
            delay=True,                # don't open the file until first write
        )
        handler.setFormatter(_RedactingFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        handler.setLevel(logging.INFO)
        _FILE_HANDLER = handler
    except Exception:
        # Cannot create/write the log dir — degrade to no-op logging.
        _FILE_HANDLER = None


def get_logger(name: str = "libra") -> logging.Logger:
    """
    Return a configured Libra logger. Safe to call anywhere; if file logging
    cannot be set up, returns a logger that simply discards records (the app
    is never affected).
    """
    _configure()
    logger_name = name if name.startswith(_LOGGER_PREFIX) else f"{_LOGGER_PREFIX}.{name}"
    logger = logging.getLogger(logger_name)
    # Attach our file handler exactly once per logger.
    if _FILE_HANDLER is not None and _FILE_HANDLER not in logger.handlers:
        logger.addHandler(_FILE_HANDLER)
        logger.setLevel(logging.INFO)
        logger.propagate = False   # don't leak to Streamlit's root handlers
    elif _FILE_HANDLER is None and not logger.handlers:
        # No file handler available: attach a NullHandler so calls are no-ops
        # and Python doesn't emit "No handlers could be found" warnings.
        logger.addHandler(logging.NullHandler())
        logger.propagate = False
    return logger


def log_path() -> str:
    """Public helper: where the log file lives (for a UI 'open logs' affordance)."""
    return _log_path()
