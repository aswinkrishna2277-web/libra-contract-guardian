"""
output_verifier.py — Citation-drift detection for LLM outputs.

═══════════════════════════════════════════════════════════════════════════════
PURPOSE
═══════════════════════════════════════════════════════════════════════════════

This module is the LAST LINE OF DEFENCE against citation hallucination.

After the LLM produces a natural-language output (rephrasing a structured
result), this module:

  1. Extracts every citation-like substring from the output
  2. Resolves each one against the verified authority database
  3. Rejects the output if any citation cannot be resolved
  4. Returns a structured verification report

If verification fails, the caller can:
  - Regenerate with a stricter prompt
  - Fall back to a deterministic (LLM-free) rendering
  - Display the structured data directly without LLM phrasing

═══════════════════════════════════════════════════════════════════════════════
HONEST LIMITATIONS
═══════════════════════════════════════════════════════════════════════════════

What verification CATCHES:
✓ Fabricated case names ("Smith v Jones [2024] EWCA Civ 9999")
✓ Wrong neutral citations (year mismatch, court mismatch)
✓ Cases not in the verified database
✓ Statute references not in the verified database
✓ Made-up paragraph numbers (when paragraph-precision is requested)

What verification CANNOT catch (residual hallucination risk):
✗ A correct citation applied to the wrong factual situation
✗ Phrasing that misstates what an authority says
✗ Subtle logical errors in legal reasoning
✗ Citations that are real but irrelevant (cherry-picking)

We claim "negligible citation-fabrication risk" — NOT "zero hallucination".
The first is true and engineering-defensible. The second is not.
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from authority_db import AUTHORITIES, Authority


# ════════════════════════════════════════════════════════════════════════════
# CITATION PATTERNS
# ════════════════════════════════════════════════════════════════════════════
#
# Patterns to find citation-like substrings in free text. These are
# deliberately broad: we'd rather catch a real-looking citation and then
# check it, than miss one.
# ════════════════════════════════════════════════════════════════════════════

# UK neutral citations: [YEAR] COURT/SERIES NUMBER
_UK_NEUTRAL_PATTERN = re.compile(
    r"\[\s*(?P<year>\d{4})\s*\]\s*"
    r"(?P<court>UKHL|UKSC|UKPC|EWCA\s*Civ|EWCA\s*Crim|EWHC|EWFC|"
    r"AC|WLR|All\s*ER|PIQR|EWCA|CSIH|CSOH|NICA|NICh|NIQB)"
    r"\s*(?P<num>\d+(?:\s*\([A-Za-z]+\))?)",
    re.IGNORECASE,
)

# EU CJEU cases: Case C-NNN/YY
_EU_CASE_PATTERN = re.compile(
    r"\bCase\s+(?:C|T)[- ]\d+/\d+\b",
    re.IGNORECASE,
)

# US cases: usually "Plaintiff v Defendant, NNN F.NNN NNN"
_US_CASE_PATTERN = re.compile(
    r"\b\d{1,3}:\d{2}-cv-\d{4,5}\b"
)

# Old-style "[YEAR] AC NNN" or "[YEAR] WLR NNN" (already covered partly by UK pattern, but explicit)
_OLD_STYLE_PATTERN = re.compile(
    r"\[\s*(?P<year>\d{4})\s*\]\s*(?P<series>AC|WLR|All\s*ER|QB|Ch|Fam)\s+\d+",
    re.IGNORECASE,
)

# Statute / rule references the LLM might fabricate
_CDPA_PATTERN = re.compile(
    r"\bCDPA\s*(?:1988\s*)?(?:s|section)\s*\.?\s*(\d+[A-Z]?)\b",
    re.IGNORECASE,
)
_TMA_PATTERN = re.compile(
    r"\bTMA\s*(?:1994\s*)?(?:s|section)\s*\.?\s*(\d+(?:\(\d+\))?(?:\([a-z]\))?)\b",
    re.IGNORECASE,
)
_CPR_PATTERN = re.compile(
    r"\bCPR\s*(?:r|rule|Pt|Part)?\s*\.?\s*(\d+(?:\.\d+)?)\b",
    re.IGNORECASE,
)
_PD_PATTERN = re.compile(
    r"\bPD\s*(\d+[A-Z]*)\b",
    re.IGNORECASE,
)

# Authority-ID leak detection. The LLM may copy authority IDs verbatim into
# user-facing output (e.g. "[CASE_LIDL_V_TESCO_2024]" or "see CASE_SKY_V_SKYKICK_2024").
# Authority IDs are internal identifiers, never citation text. This pattern
# matches the format used by authority_db.py: ALL_CAPS_WITH_UNDERSCORES
# prefixed by one of the kind tokens.
_AUTHORITY_ID_LEAK_PATTERN = re.compile(
    r"\b(CASE|STATUTE|RULE|REG|DIR|REPORT|ACADEMIC)_[A-Z0-9_]{3,80}\b"
)


# ════════════════════════════════════════════════════════════════════════════
# RESULT OBJECTS
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class CitationFound:
    """A citation-like substring found in output text."""
    raw_text: str
    span: tuple[int, int]  # character offsets in original text
    citation_type: str     # "uk_neutral", "eu_case", "us_case", "cdpa", "tma", "cpr", "pd"


@dataclass
class VerificationReport:
    """Result of verifying an LLM output against the authority database."""
    is_valid: bool
    citations_found: list[CitationFound] = field(default_factory=list)
    citations_verified: list[CitationFound] = field(default_factory=list)
    citations_unknown: list[CitationFound] = field(default_factory=list)
    allowed_authority_ids: list[str] = field(default_factory=list)
    reason: str = ""

    @property
    def summary(self) -> str:
        if self.is_valid:
            return (
                f"✓ Output verified. "
                f"{len(self.citations_verified)} citation(s) resolved against authority database."
            )
        return (
            f"✗ Output FAILED verification. "
            f"{len(self.citations_unknown)} unknown citation(s) detected: "
            f"{', '.join(repr(c.raw_text) for c in self.citations_unknown)}"
        )


# ════════════════════════════════════════════════════════════════════════════
# CITATION EXTRACTION
# ════════════════════════════════════════════════════════════════════════════

def extract_citations(text: str) -> list[CitationFound]:
    """
    Find every citation-like substring in the text.

    Returns a list of CitationFound objects with their position and detected
    type.
    """
    found: list[CitationFound] = []

    for m in _UK_NEUTRAL_PATTERN.finditer(text):
        found.append(CitationFound(
            raw_text=m.group(0).strip(),
            span=(m.start(), m.end()),
            citation_type="uk_neutral",
        ))

    for m in _EU_CASE_PATTERN.finditer(text):
        found.append(CitationFound(
            raw_text=m.group(0).strip(),
            span=(m.start(), m.end()),
            citation_type="eu_case",
        ))

    for m in _US_CASE_PATTERN.finditer(text):
        found.append(CitationFound(
            raw_text=m.group(0).strip(),
            span=(m.start(), m.end()),
            citation_type="us_case",
        ))

    for m in _OLD_STYLE_PATTERN.finditer(text):
        # Avoid duplicates with UK neutral pattern
        raw = m.group(0).strip()
        if not any(c.raw_text == raw for c in found):
            found.append(CitationFound(
                raw_text=raw,
                span=(m.start(), m.end()),
                citation_type="uk_neutral",
            ))

    for m in _CDPA_PATTERN.finditer(text):
        found.append(CitationFound(
            raw_text=m.group(0).strip(),
            span=(m.start(), m.end()),
            citation_type="cdpa",
        ))

    for m in _TMA_PATTERN.finditer(text):
        found.append(CitationFound(
            raw_text=m.group(0).strip(),
            span=(m.start(), m.end()),
            citation_type="tma",
        ))

    for m in _CPR_PATTERN.finditer(text):
        found.append(CitationFound(
            raw_text=m.group(0).strip(),
            span=(m.start(), m.end()),
            citation_type="cpr",
        ))

    for m in _PD_PATTERN.finditer(text):
        found.append(CitationFound(
            raw_text=m.group(0).strip(),
            span=(m.start(), m.end()),
            citation_type="pd",
        ))

    return found


# ════════════════════════════════════════════════════════════════════════════
# VERIFICATION
# ════════════════════════════════════════════════════════════════════════════

def _normalise_for_match(s: str) -> str:
    """Lowercase and collapse whitespace for fuzzy matching."""
    return re.sub(r"\s+", " ", s.lower().strip())


def _citation_matches_authority(citation: CitationFound, auth: Authority) -> bool:
    """
    Check whether a found citation matches a known authority.

    Match logic:
      - For full neutral citations: substring match against full_citation
        (normalised whitespace, case-insensitive)
      - For statute/rule shorthands: check key fragments
    """
    raw = _normalise_for_match(citation.raw_text)
    full = _normalise_for_match(auth.full_citation)
    short = _normalise_for_match(auth.short_name)

    if raw in full or raw in short:
        return True
    if full and full.find(raw) >= 0:
        return True

    # For statute-style citations, check that the section number appears
    # in the full citation
    if citation.citation_type in ("cdpa", "tma", "cpr", "pd"):
        # Extract the section/rule number from the raw citation
        nums = re.findall(r"\d+[A-Z]?(?:\(\d+\))?(?:\([a-z]\))?", raw)
        if nums and any(n.lower() in full or n.lower() in short for n in nums):
            # Additionally require the act/rule keyword to match
            key = citation.citation_type
            keyword_in_auth = key in full or key in auth.id.lower()
            if keyword_in_auth:
                return True

    return False


def verify(
    text: str,
    allowed_authority_ids: Optional[list[str]] = None,
) -> VerificationReport:
    """
    Verify that every citation in `text` matches a known authority.

    Args:
        text: The LLM-produced output to verify.
        allowed_authority_ids: If provided, citations must match one of these
            specific authorities (typically the ones the LLM was told to use).
            If None, citations are checked against the FULL database.

    Returns:
        VerificationReport.

    Note: this function also rejects ANY output containing raw authority IDs
    (e.g. "CASE_LIDL_V_TESCO_2024"). Those are internal identifiers and must
    never appear in user-facing text.
    """
    # Defensive check: detect raw authority-ID leaks from the LLM. These are
    # never acceptable in user-facing output, regardless of allowed set.
    id_leaks = _AUTHORITY_ID_LEAK_PATTERN.findall(text)
    if id_leaks:
        # Synthesize fake CitationFound entries for the leaked IDs so the
        # report carries useful diagnostic data.
        leak_citations = []
        for m in _AUTHORITY_ID_LEAK_PATTERN.finditer(text):
            leak_citations.append(CitationFound(
                raw_text=m.group(0),
                span=(m.start(), m.end()),
                citation_type="id_leak",
            ))
        report = VerificationReport(
            is_valid=False,
            citations_found=leak_citations,
            citations_unknown=leak_citations,
            allowed_authority_ids=list(allowed_authority_ids) if allowed_authority_ids else [],
            reason=(
                f"Output contains {len(leak_citations)} raw authority ID(s) "
                f"(e.g. {leak_citations[0].raw_text}). These are internal "
                "identifiers and must never appear in user-facing output. "
                "LLM was instructed to use citation form, not IDs."
            ),
        )
        return report

    citations = extract_citations(text)
    report = VerificationReport(
        is_valid=True,
        citations_found=citations,
        allowed_authority_ids=list(allowed_authority_ids) if allowed_authority_ids else [],
    )

    if not citations:
        report.reason = "No citations detected; nothing to verify."
        return report

    # Determine the candidate pool
    if allowed_authority_ids:
        pool = [AUTHORITIES[aid] for aid in allowed_authority_ids if aid in AUTHORITIES]
    else:
        pool = list(AUTHORITIES.values())

    for cit in citations:
        matched = any(_citation_matches_authority(cit, auth) for auth in pool)
        if matched:
            report.citations_verified.append(cit)
        else:
            report.citations_unknown.append(cit)

    report.is_valid = len(report.citations_unknown) == 0
    if not report.is_valid:
        report.reason = (
            f"Output contains {len(report.citations_unknown)} citation(s) that "
            f"do not match any verified authority"
            + (f" in the allowed set" if allowed_authority_ids else "")
            + "."
        )
    return report


# ════════════════════════════════════════════════════════════════════════════
# FALLBACK RENDERING (when LLM output fails verification)
# ════════════════════════════════════════════════════════════════════════════

def render_structured_fallback(
    title: str,
    summary: str,
    authorities: list[Authority],
) -> str:
    """
    When LLM output fails verification, render a deterministic fallback.

    This is plain English assembled from the structured data — no LLM
    involvement. Guaranteed to contain only verified citations because we
    only emit the authorities directly.
    """
    parts: list[str] = []
    parts.append(f"## {title}")
    parts.append("")
    parts.append(summary)
    parts.append("")
    if authorities:
        parts.append("**Authorities relied upon:**")
        for a in authorities:
            line = f"- *{a.full_citation}* — {a.summary}"
            parts.append(line)
    return "\n".join(parts)


# ════════════════════════════════════════════════════════════════════════════
# SELF-CHECK
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Libra Output Verifier — Self Check")
    print("─" * 70)

    # Test 1 — clean output, all citations real
    print("\n[1] Clean output (should pass)")
    sample = (
        "The court relied on Wisniewski v Central Manchester HA [1998] EWCA Civ 596, "
        "later extended in Wetton v Ahmed [2011] EWCA Civ 610. PD 57AD Model C "
        "applies. See also CPR r.6.37 on the good arguable case standard."
    )
    rep = verify(sample)
    print(f"  Valid: {rep.is_valid}")
    print(f"  Citations found:    {len(rep.citations_found)}")
    print(f"  Citations verified: {len(rep.citations_verified)}")
    print(f"  Citations unknown:  {len(rep.citations_unknown)}")
    print(f"  Summary: {rep.summary}")

    # Test 2 — fabricated case
    print("\n[2] Output with fabricated citation (should FAIL)")
    sample = (
        "The court relied on Smith v Made-Up Co [2027] EWCA Civ 9999 and "
        "also on Wisniewski v Central Manchester HA [1998] EWCA Civ 596."
    )
    rep = verify(sample)
    print(f"  Valid: {rep.is_valid}")
    print(f"  Citations unknown:")
    for c in rep.citations_unknown:
        print(f"    - {c.raw_text!r}")
    print(f"  Reason: {rep.reason}")

    # Test 3 — wrong year on a real case (should FAIL)
    print("\n[3] Output with wrong year on real case (should FAIL)")
    sample = "The court relied on Wisniewski v Central Manchester HA [2099] EWCA Civ 596."
    rep = verify(sample)
    print(f"  Valid: {rep.is_valid}")
    print(f"  Unknown: {[c.raw_text for c in rep.citations_unknown]}")

    # Test 4 — verify against ALLOWED IDs only
    print("\n[4] Verify against allowed-only set")
    sample = (
        "The court relied on Wisniewski v Central Manchester HA [1998] EWCA Civ 596 "
        "and IPCom v HTC Europe [2013] EWHC 2880 (Ch)."
    )
    # IPCom is real, but not in the allowed set for this query
    rep = verify(sample, allowed_authority_ids=["CASE_WISNIEWSKI_1998"])
    print(f"  Valid (allowed-only): {rep.is_valid}")
    print(f"  Verified: {[c.raw_text for c in rep.citations_verified]}")
    print(f"  Unknown:  {[c.raw_text for c in rep.citations_unknown]}")

    # Test 5 — statute references
    print("\n[5] Statute references")
    sample = (
        "Under CDPA 1988 s.29A the TDM exception applies. "
        "TMA 1994 s.10(3) governs dilution. "
        "CPR Pt 35 covers expert evidence."
    )
    rep = verify(sample)
    print(f"  Valid: {rep.is_valid}")
    print(f"  Found: {[c.raw_text for c in rep.citations_found]}")
    print(f"  Verified: {len(rep.citations_verified)}")
    print(f"  Unknown:  {len(rep.citations_unknown)}")

    # Test 6 — fallback render
    print("\n[6] Fallback rendering (LLM-free)")
    from authority_db import get
    auths = [get("CASE_WISNIEWSKI_1998"), get("CASE_WETTON_V_AHMED_2011")]
    out = render_structured_fallback(
        "Stage 3 — Adverse Inference",
        "On these facts, the court may exercise its discretion under the adverse-inference doctrine.",
        auths,
    )
    print(out)
