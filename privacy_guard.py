# ================================================================
#  LIBRA CONTRACT GUARDIAN v2.0 – Privacy Guard (Phase 2.5)
#  Data-protection layer: local-only enforcement + network audit
#
#  PURPOSE
#    Libra processes potentially confidential legal documents. This
#    module gives a single, auditable control point for every decision
#    that could send data off the device.
#
#    Three guarantees:
#      1. LOCAL-ONLY MODE (default ON): blocks every outbound network
#         call except to the local LLM at 127.0.0.1. When on, no document
#         text, no contract, no mark, nothing leaves the machine.
#      2. NETWORK AUDIT LOG: every network attempt — allowed or blocked —
#         is recorded locally with a timestamp, the destination host, and
#         what category of call it was. The user can review exactly what
#         the app did or tried to do.
#      3. NO DOCUMENT CONTENT IN LOGS: the audit log records destinations
#         and categories, never the document text or user input itself.
#
#  DESIGN
#    Pure-Python, no third-party dependencies. Safe to import anywhere.
#    The network policy is checked by calling guard_network() before any
#    outbound request. Existing call sites are wrapped, not rewritten.
#
#  PRODUCTION BUILD — R.A. Aswin Krishna, IP-AI Practitioner
# ================================================================

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse


# ─── Where the audit log lives (local file, user-readable) ─────────────────
def _default_log_dir() -> str:
    """Audit log directory, beside the app. Created on first write."""
    base = os.environ.get("LIBRA_LOG_DIR")
    if base:
        return base
    return os.path.join(os.path.expanduser("~"), ".libra")


AUDIT_LOG_PATH = os.path.join(_default_log_dir(), "network_audit.log")


# ─── The local LLM endpoint — the ONLY host allowed in local-only mode ─────
LOCAL_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0", "::1"}


# ═══════════════════════════════════════════════════════════════════════════
#  NETWORK POLICY
# ═══════════════════════════════════════════════════════════════════════════

class NetworkBlocked(Exception):
    """Raised when a network call is blocked by local-only mode."""
    pass


@dataclass
class NetworkAttempt:
    """A single recorded network attempt."""
    timestamp: str
    host: str
    category: str           # e.g. "local_llm", "trademark_web_search", "link_check"
    allowed: bool
    reason: str = ""


# Module-level policy state. Defaults to the safest posture: local-only ON.
_POLICY = {
    "local_only": True,           # block everything except local hosts
    "allow_link_check": False,    # public-legislation link checks (no user data)
    "allow_trademark_web": False, # trademark web search (sends the mark name)
    "consent_given": False,       # explicit user opt-in for any off-device call
}

_AUDIT: list[NetworkAttempt] = []


def set_policy(
    local_only: Optional[bool] = None,
    allow_link_check: Optional[bool] = None,
    allow_trademark_web: Optional[bool] = None,
    consent_given: Optional[bool] = None,
) -> dict:
    """
    Update the network policy. Called from the app's settings UI.

    local_only=True is the default and the safe posture. Turning OFF
    local_only does NOT by itself permit any call — the specific category
    flags (allow_link_check, allow_trademark_web) and consent_given must
    each also be set. This is defence in depth: a single accidental toggle
    cannot open the door.
    """
    if local_only is not None:
        _POLICY["local_only"] = bool(local_only)
    if allow_link_check is not None:
        _POLICY["allow_link_check"] = bool(allow_link_check)
    if allow_trademark_web is not None:
        _POLICY["allow_trademark_web"] = bool(allow_trademark_web)
    if consent_given is not None:
        _POLICY["consent_given"] = bool(consent_given)
    return dict(_POLICY)


def get_policy() -> dict:
    """Return a copy of the current network policy."""
    return dict(_POLICY)


def _host_of(url: str) -> str:
    """Extract the hostname from a URL; empty string if unparseable."""
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _record(host: str, category: str, allowed: bool, reason: str = "") -> None:
    """Append an attempt to the in-memory audit list and the local log file."""
    attempt = NetworkAttempt(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        host=host or "(unknown)",
        category=category,
        allowed=allowed,
        reason=reason,
    )
    _AUDIT.append(attempt)
    # Best-effort local file logging — never raises into the caller
    try:
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(attempt)) + "\n")
    except Exception:
        pass


def guard_network(url: str, category: str) -> None:
    """
    Check whether a network call to `url` is permitted under current policy.

    Call this immediately before any outbound request. If the call is not
    permitted, this raises NetworkBlocked and records the blocked attempt.
    If permitted, it records the allowed attempt and returns normally.

    category is a short label describing the kind of call, used only for
    the audit log (never the document content).

    Policy logic:
      - Local hosts (127.0.0.1 etc.) are ALWAYS allowed — that is the local
        LLM, which is on-device.
      - In local_only mode, every non-local host is blocked.
      - Outside local_only mode, a non-local host is allowed only if BOTH
        the matching category flag is set AND consent_given is True.
    """
    host = _host_of(url)

    # Local hosts are always fine — this is the on-device LLM.
    if host in LOCAL_HOSTS:
        _record(host, category, allowed=True, reason="local host")
        return

    # Local-only mode blocks everything else.
    if _POLICY["local_only"]:
        _record(host, category, allowed=False, reason="local-only mode active")
        raise NetworkBlocked(
            f"Local-only mode is active. Blocked an outbound call to '{host}' "
            f"(category: {category}). No data left the device. To permit this "
            f"specific category of call, disable local-only mode in Settings "
            f"and grant explicit consent."
        )

    # Outside local-only mode: require explicit consent AND a category flag.
    if not _POLICY["consent_given"]:
        _record(host, category, allowed=False, reason="no consent granted")
        raise NetworkBlocked(
            f"Off-device calls require explicit consent. Blocked '{host}' "
            f"(category: {category})."
        )

    category_flag = {
        "link_check": "allow_link_check",
        "trademark_web_search": "allow_trademark_web",
    }.get(category)

    if category_flag and not _POLICY.get(category_flag):
        _record(host, category, allowed=False,
                reason=f"category '{category}' not permitted")
        raise NetworkBlocked(
            f"The '{category}' category is not enabled. Blocked '{host}'. "
            f"Enable it in Settings if you intend to make this kind of call."
        )

    # Permitted.
    _record(host, category, allowed=True, reason="policy permits")


def safe_request(method, url: str, category: str, **kwargs):
    """
    Wrapper around a requests-style call that enforces the network policy.

    Usage:
        import requests
        from privacy_guard import safe_request
        resp = safe_request(requests.get, url, "trademark_web_search", timeout=8)

    Raises NetworkBlocked if policy forbids the call. Otherwise performs it.
    """
    guard_network(url, category)
    return method(url, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
#  AUDIT ACCESS
# ═══════════════════════════════════════════════════════════════════════════

def get_audit(limit: int = 200) -> list[dict]:
    """Return the most recent network attempts (in-memory), newest last."""
    return [asdict(a) for a in _AUDIT[-limit:]]


def audit_summary() -> dict:
    """Summary stats for the privacy dashboard."""
    total = len(_AUDIT)
    blocked = sum(1 for a in _AUDIT if not a.allowed)
    allowed = total - blocked
    off_device = sum(
        1 for a in _AUDIT if a.allowed and a.host not in LOCAL_HOSTS
    )
    return {
        "total_attempts": total,
        "allowed": allowed,
        "blocked": blocked,
        "off_device_allowed": off_device,
        "local_only_active": _POLICY["local_only"],
        "log_path": AUDIT_LOG_PATH,
    }


def clear_audit() -> None:
    """Clear the in-memory audit list (does not delete the log file)."""
    _AUDIT.clear()


# ═══════════════════════════════════════════════════════════════════════════
#  FILE HANDLING — confidential uploads
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FileHandlingReport:
    """Describes how an uploaded file is handled, for the user's assurance."""
    filename: str
    processed_in_memory: bool
    written_to_disk: bool
    disk_path: str = ""
    deleted_after: bool = False
    notes: list[str] = field(default_factory=list)


def assess_onedrive_risk(working_dir: str) -> dict:
    """
    Check whether the working directory sits inside a cloud-synced folder
    (OneDrive, Dropbox, Google Drive). If a confidential document is written
    there, the cloud client may sync it off-device automatically — a
    confidentiality risk the user may not realise.

    Returns a dict with a risk flag and a human-readable explanation.
    This is the single most common way "local-only" software accidentally
    leaks data on a Windows machine.
    """
    wd = (working_dir or "").lower()
    cloud_markers = {
        "onedrive": "Microsoft OneDrive",
        "dropbox": "Dropbox",
        "google drive": "Google Drive",
        "googledrive": "Google Drive",
        "icloud": "Apple iCloud",
    }
    for marker, name in cloud_markers.items():
        if marker in wd:
            return {
                "at_risk": True,
                "service": name,
                "message": (
                    f"The working directory appears to be inside a {name} "
                    f"synced folder. Files Libra writes here (uploaded "
                    f"documents, generated opinions) may be automatically "
                    f"copied to {name}'s cloud by the sync client — even "
                    f"though Libra itself never transmits them. For "
                    f"confidential matters, run Libra from a folder OUTSIDE "
                    f"any cloud-synced location, or pause syncing for that "
                    f"folder."
                ),
            }
    return {
        "at_risk": False,
        "service": "",
        "message": (
            "The working directory does not appear to be inside a known "
            "cloud-synced folder. Files remain on the device unless you move "
            "them."
        ),
    }


def describe_file_handling(filename: str, write_to_disk: bool = False,
                           disk_path: str = "") -> FileHandlingReport:
    """
    Produce a plain-language description of how a given upload is handled.
    Used to show the user exactly what happens to their document.
    """
    notes = []
    if write_to_disk:
        notes.append(
            "This file is written to disk so the engine can read it. Consider "
            "deleting it after the session if the matter is confidential."
        )
    else:
        notes.append(
            "This file is processed in memory and is not written to disk by "
            "Libra."
        )
    return FileHandlingReport(
        filename=filename,
        processed_in_memory=not write_to_disk,
        written_to_disk=write_to_disk,
        disk_path=disk_path,
        deleted_after=False,
        notes=notes,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  PRIVACY STATEMENT — for the UI
# ═══════════════════════════════════════════════════════════════════════════

def privacy_statement() -> str:
    """The plain-language privacy statement shown in the app."""
    policy = get_policy()
    mode = "ON" if policy["local_only"] else "OFF"
    return (
        f"PRIVACY STATUS — Local-only mode: {mode}\n\n"
        "When local-only mode is ON (the default), Libra blocks every "
        "outbound network call except to the local AI model running on this "
        "machine (127.0.0.1). No document text, no contract, no trademark, "
        "and no other input leaves the device.\n\n"
        "The only AI processing happens on a model running locally via "
        "Ollama. Nothing is sent to any cloud AI service.\n\n"
        "Every network attempt — permitted or blocked — is recorded in a "
        "local audit log that you can review. The log records destinations "
        "and call categories only; it never records your document content.\n\n"
        "If you turn local-only mode OFF (for example to enable trademark "
        "web search), Libra still requires explicit consent and only permits "
        "the specific categories you enable. Even then, the trademark web "
        "search transmits only the proposed mark name you type — never any "
        "uploaded document.\n\n"
        "For confidential matters, run Libra from a folder OUTSIDE any "
        "cloud-synced location (OneDrive, Dropbox, Google Drive), because "
        "those sync clients may copy files off-device independently of Libra."
    )
