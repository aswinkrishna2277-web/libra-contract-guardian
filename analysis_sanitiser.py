# ================================================================
#  LIBRA CONTRACT GUARDIAN v2.0 – Analysis Citation Sanitiser
#  Phase 2D: verification pass for the LLM-driven analysis engines
#
#  PURPOSE
#    search_mode_analysis() and high_research_mode_analysis() ask the
#    local LLM to emit citations freely (legal_references, red_flags
#    with embedded citations, per-clause statute_citations). Unlike the
#    PRPP / TDM / Trademark engines, these were never gated by the
#    output verifier, so a hallucinated citation could reach the user.
#
#    This module provides a single post-processing pass that:
#      1. Scans every citation-bearing field the LLM produced
#      2. Verifies each citation against the verified authority database
#      3. Flags (does not silently delete) any citation that cannot be
#         traced, so the user sees a clear warning rather than a false
#         authority
#      4. Strips any leaked internal authority IDs
#      5. Returns an audit of what was checked, kept, and flagged
#
#  DESIGN
#    Conservative: it never invents or "corrects" a citation. It only
#    verifies and flags. The engines keep their existing structure; this
#    is a wrapper applied at the end, mirroring how the verifier gates the
#    other engines.
#
#  PRODUCTION BUILD — R.A. Aswin Krishna, IP-AI Practitioner
# ================================================================

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional

from output_verifier import verify, extract_citations


# Internal-ID leak pattern (same family the verifier rejects)
_ID_LEAK = re.compile(
    r"\b(CASE|STATUTE|RULE|REG|DIR|REPORT|ACADEMIC)_[A-Z0-9_]{3,80}\b"
)


@dataclass
class SanitisationReport:
    """Audit of a single analysis sanitisation pass."""
    citations_checked: int = 0
    citations_verified: int = 0
    citations_flagged: int = 0
    flagged_list: list[str] = field(default_factory=list)
    id_leaks_removed: int = 0
    notes: list[str] = field(default_factory=list)


def _strip_id_leaks(s: str) -> tuple[str, int]:
    """Remove any leaked internal authority IDs from a string."""
    if not isinstance(s, str):
        return s, 0
    leaks = _ID_LEAK.findall(s)
    if not leaks:
        return s, 0
    cleaned = _ID_LEAK.sub("[citation removed]", s)
    return cleaned, len(leaks)


def _verify_citation_string(s: str) -> tuple[bool, list[str]]:
    """
    Verify the citations contained in a free-text string against the
    full authority database.

    Returns (all_ok, unverified_citation_texts).
    A string with no detectable citation is treated as OK (nothing to check).
    Use this for PROSE fields where a citation may or may not be present.
    """
    if not isinstance(s, str) or not s.strip():
        return True, []
    report = verify(s, allowed_authority_ids=None)  # check against full DB
    if report.is_valid:
        return True, []
    return False, [c.raw_text for c in report.citations_unknown]


def _matches_known_authority(s: str) -> bool:
    """
    Check whether a citation-field entry corresponds to a known authority,
    even if it uses a format the verifier's regex patterns don't capture
    (e.g. 'EU AI Act Art. 53', 'DSM Directive Art. 4').

    Matches against each authority's short_name and full_citation using a
    token-overlap heuristic: the entry is considered a match if it shares a
    distinctive substring with a known authority's short_name or citation.
    """
    try:
        from authority_db import AUTHORITIES
    except Exception:
        return False

    norm = re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    if not norm:
        return False
    norm_tokens = set(norm.split())

    for auth in AUTHORITIES.values():
        for candidate in (auth.short_name, auth.full_citation):
            cand_norm = re.sub(r"[^a-z0-9]+", " ", (candidate or "").lower()).strip()
            if not cand_norm:
                continue
            cand_tokens = set(cand_norm.split())
            # Strong signal: the entry is a substring of the candidate or vice versa
            if norm in cand_norm or cand_norm in norm:
                return True
            # Token overlap: share several distinctive tokens
            shared = norm_tokens & cand_tokens
            # Ignore very common tokens
            shared -= {"the", "of", "v", "and", "act", "s", "art", "no", "ltd", "uk", "eu"}
            if len(shared) >= 2:
                return True
    return False


def _verify_citation_field_entry(s: str) -> tuple[bool, list[str]]:
    """
    Verify an entry from a field that is SUPPOSED to be a citation
    (legal_references, statute_citations).

    Logic:
      1. If the verifier's patterns detect a citation, trust its verdict
         (this catches fabricated neutral citations like '[2099] UKSC 999').
      2. Else, if the entry matches a known authority by name/citation
         (covers EU instruments and other formats the regex misses),
         accept it.
      3. Else, the entry contains no traceable authority → flag it.

    Returns (ok, unverified_texts).
    """
    if not isinstance(s, str) or not s.strip():
        return True, []
    report = verify(s, allowed_authority_ids=None)
    if report.citations_found:
        if report.is_valid:
            return True, []
        return False, [c.raw_text for c in report.citations_unknown]
    # No regex-recognised citation — fall back to database name matching.
    if _matches_known_authority(s):
        return True, []
    return False, [s.strip()]


def sanitise_analysis(parsed: dict) -> tuple[dict, SanitisationReport]:
    """
    Post-process an LLM analysis result, verifying every citation-bearing
    field against the verified authority database.

    Fields checked:
      - legal_references: list of citation strings
      - red_flags: list of strings that often embed citations
      - immediate_actions: list of strings that often embed citations
      - detailed_clauses[].statute_citations: list of citation strings
      - detailed_clauses[].analysis / specific_concern: free text

    Behaviour:
      - Internal-ID leaks are stripped everywhere.
      - Citations that cannot be traced to the database are MOVED to a
        new field `unverified_citations` and annotated, rather than
        presented as if authoritative.
      - A `citation_verification` block is added to the result describing
        what happened, so the UI can show an honest status.

    Returns (sanitised_parsed, report).
    """
    report = SanitisationReport()
    if not isinstance(parsed, dict):
        return parsed, report

    unverified_bucket: list[str] = []

    # ── legal_references: the primary citation list ────────────────────────
    refs = parsed.get("legal_references")
    if isinstance(refs, list):
        kept_refs = []
        for ref in refs:
            ref_str = str(ref)
            ref_str, n_leak = _strip_id_leaks(ref_str)
            report.id_leaks_removed += n_leak
            report.citations_checked += 1
            ok, unknown = _verify_citation_field_entry(ref_str)
            if ok:
                report.citations_verified += 1
                kept_refs.append(ref_str)
            else:
                report.citations_flagged += 1
                report.flagged_list.extend(unknown or [ref_str])
                unverified_bucket.append(ref_str)
        parsed["legal_references"] = kept_refs

    # ── red_flags and immediate_actions: free text that embeds citations ──
    for field_name in ("red_flags", "immediate_actions"):
        items = parsed.get(field_name)
        if isinstance(items, list):
            cleaned_items = []
            for item in items:
                item_str = str(item)
                item_str, n_leak = _strip_id_leaks(item_str)
                report.id_leaks_removed += n_leak
                # Only flag if the string actually contains a citation that
                # fails verification; otherwise keep the text as-is.
                cites = extract_citations(item_str)
                if cites:
                    report.citations_checked += len(cites)
                    ok, unknown = _verify_citation_string(item_str)
                    if ok:
                        report.citations_verified += len(cites)
                        cleaned_items.append(item_str)
                    else:
                        report.citations_flagged += len(unknown)
                        report.flagged_list.extend(unknown)
                        # Keep the prose but mark the unverified citation
                        cleaned_items.append(
                            item_str + "  [⚠ citation unverified — confirm manually]"
                        )
                else:
                    cleaned_items.append(item_str)
            parsed[field_name] = cleaned_items

    # ── detailed_clauses: per-clause statute_citations + analysis text ────
    clauses = parsed.get("detailed_clauses")
    if isinstance(clauses, list):
        for clause in clauses:
            if not isinstance(clause, dict):
                continue
            # statute_citations list
            sc = clause.get("statute_citations")
            if isinstance(sc, list):
                kept_sc = []
                for cite in sc:
                    cite_str = str(cite)
                    cite_str, n_leak = _strip_id_leaks(cite_str)
                    report.id_leaks_removed += n_leak
                    report.citations_checked += 1
                    ok, unknown = _verify_citation_field_entry(cite_str)
                    if ok:
                        report.citations_verified += 1
                        kept_sc.append(cite_str)
                    else:
                        report.citations_flagged += 1
                        report.flagged_list.extend(unknown or [cite_str])
                        unverified_bucket.append(cite_str)
                clause["statute_citations"] = kept_sc
            # free-text fields: strip ID leaks only (don't flag prose)
            for tf in ("analysis", "specific_concern"):
                if isinstance(clause.get(tf), str):
                    clause[tf], n_leak = _strip_id_leaks(clause[tf])
                    report.id_leaks_removed += n_leak

    # ── attach honest verification status ──────────────────────────────────
    if unverified_bucket:
        # Deduplicate
        seen = set()
        uniq = []
        for c in unverified_bucket:
            if c not in seen:
                seen.add(c)
                uniq.append(c)
        parsed["unverified_citations"] = uniq

    if report.citations_flagged:
        report.notes.append(
            f"{report.citations_flagged} citation(s) could not be traced to "
            f"the verified authority database and have been flagged for manual "
            f"confirmation."
        )
    if report.id_leaks_removed:
        report.notes.append(
            f"{report.id_leaks_removed} internal identifier(s) were stripped "
            f"from the output."
        )
    if report.citations_checked and not report.citations_flagged and not report.id_leaks_removed:
        report.notes.append(
            f"All {report.citations_checked} citation(s) verified against the "
            f"authority database."
        )

    parsed["citation_verification"] = {
        "checked": report.citations_checked,
        "verified": report.citations_verified,
        "flagged": report.citations_flagged,
        "id_leaks_removed": report.id_leaks_removed,
        "flagged_citations": report.flagged_list,
        "notes": report.notes,
    }

    return parsed, report
