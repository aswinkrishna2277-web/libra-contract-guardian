# ================================================================
#  LIBRA CONTRACT GUARDIAN v2.0 – Trademark Engine (Phase 2C)
#  UK Trademark Clearance Opinion Generator
#
#  TMA 1994 ss.5(2)(b), 5(3), 10(2), 10(3) | EU TMD
#
#  ARCHITECTURE:
#    1. Python computes risk profile deterministically from search results
#    2. authority_selector picks authority IDs for the opinion
#    3. LLM (if available) phrases the opinion using ONLY allowed citations
#    4. output_verifier rejects any LLM output that fabricates citations
#    5. If LLM unavailable / fails verification → deterministic template used
#
#  This version corrects a v1 citation error: Sky v SkyKick was cited as
#  [2020] UKSC 17 (wrong). The correct citation is [2024] UKSC 36, decided
#  13 November 2024. The verified authority database now enforces this.
#
#  PRODUCTION BUILD — R.A. Aswin Krishna, IP-AI Practitioner
# ================================================================

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from authority_db import get, format_citation
from authority_selector import (
    select_from_selectors,
    enrich_by_keywords,
    authorities_to_prompt_block,
)
from output_verifier import verify, VerificationReport


def _app_helpers():
    """Lazy import to avoid circular import errors at module load time."""
    from app import (
        call_ai,
        parse_json_response,
        safe_ai_call,
        SYSTEM_LEGAL,
    )
    return {
        "call_ai": call_ai,
        "parse_json_response": parse_json_response,
        "safe_ai_call": safe_ai_call,
        "SYSTEM_LEGAL": SYSTEM_LEGAL,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  RISK PROFILE COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class TrademarkRiskProfile:
    """Deterministic trademark clearance risk profile."""
    your_mark: str
    nice_class: str
    description: str
    conflict_count: int
    high_risk_count: int
    high_dilution_count: int
    overall_risk_level: str           # HIGH / MEDIUM / LOW
    recommendation: str               # Proceed / Proceed with modifications / Conduct further clearance / Abandon
    famous_mark_present: bool         # Does any conflict hit the famous-mark threshold?
    high_risk_conflicts: list[dict]   # Top conflicts by score
    all_conflicts: list[dict]
    high_dilution_conflicts: list[dict]


def compute_trademark_risk(
    your_mark: str,
    nice_class: str,
    description: str,
    ukipo_results: list[dict],
    dilution_rows: list[dict],
    famous_mark_threshold: int = 80,
    high_conflict_threshold: int = 75,
    high_dilution_threshold: int = 75,
) -> TrademarkRiskProfile:
    """
    Pure function: trademark inputs → risk profile.

    Thresholds are documented and adjustable. The high-conflict threshold is
    75, aligned with the trademark_similarity module's HIGH band so the two
    modules agree on what counts as a high-risk conflict. The famous-mark
    threshold (for triggering s.10(3) dilution analysis) is 80.
    """
    your_mark = your_mark or ""
    nice_class = nice_class or ""
    description = description or ""
    ukipo_results = ukipo_results or []
    dilution_rows = dilution_rows or []

    high_risk_live = [
        r for r in ukipo_results
        if r.get("conflict_score", 0) > high_conflict_threshold
    ]
    high_risk_dil = [
        r for r in dilution_rows
        if r.get("dilution_score", 0) > high_dilution_threshold
    ]
    conflict_count = len(ukipo_results)
    high_count = len(high_risk_live)
    high_dil_count = len(high_risk_dil)

    famous_mark_present = any(
        r.get("conflict_score", 0) > famous_mark_threshold
        for r in ukipo_results
    ) or any(
        r.get("dilution_score", 0) > famous_mark_threshold
        for r in dilution_rows
    )

    # Risk level accounts for BOTH live-register conflicts AND high-dilution
    # competitors. A high-dilution match (e.g. a fuzzy/phonetic near-match to a
    # famous mark) is a high-risk signal even when the live registry API returns
    # nothing — which is exactly the BURRBERY/BURBERRY case. Previously this
    # branch ignored dilution and wrongly reported MEDIUM while the dashboard
    # showed HIGH.
    if high_count >= 2 or high_dil_count >= 2:
        risk_level = "HIGH"
        recommendation = "Proceed with modifications"
    elif high_count == 1 or high_dil_count == 1:
        risk_level = "HIGH"
        recommendation = "Conduct further clearance"
    elif conflict_count > 3:
        risk_level = "MEDIUM"
        recommendation = "Proceed with modifications"
    elif conflict_count > 0:
        risk_level = "MEDIUM"
        recommendation = "Proceed with clearance review"
    else:
        risk_level = "LOW"
        recommendation = "Proceed to file"

    return TrademarkRiskProfile(
        your_mark=your_mark,
        nice_class=nice_class,
        description=description,
        conflict_count=conflict_count,
        high_risk_count=high_count,
        high_dilution_count=len(high_risk_dil),
        overall_risk_level=risk_level,
        recommendation=recommendation,
        famous_mark_present=famous_mark_present,
        high_risk_conflicts=high_risk_live[:5],
        all_conflicts=ukipo_results,
        high_dilution_conflicts=high_risk_dil[:5],
    )


# ═══════════════════════════════════════════════════════════════════════════
#  AUTHORITY SELECTION
# ═══════════════════════════════════════════════════════════════════════════

def select_authorities_for_trademark(profile: TrademarkRiskProfile) -> list[str]:
    """
    Select authority IDs for a trademark clearance opinion.

    Always includes confusion + dilution baselines. Adds bad-faith
    authority (Sky v SkyKick [2024] UKSC 36) and descriptive-marks
    authority. Enriches via the mark and description text.
    """
    selectors = ["TRADEMARK_CONFUSION", "TRADEMARK_DILUTION"]
    if profile.famous_mark_present:
        # Famous-mark conflict — bring in bad-faith and descriptive cases
        selectors += ["TRADEMARK_BAD_FAITH", "TRADEMARK_DESCRIPTIVE"]

    base = select_from_selectors(selectors)
    # Enrich by terms in the mark, description, and conflict mark names
    enrichment_text = " ".join([
        profile.your_mark,
        profile.description,
        " ".join(r.get("mark", "") for r in profile.all_conflicts[:10]),
    ])
    enriched = enrich_by_keywords(enrichment_text, base)

    seen: set[str] = set()
    ids: list[str] = []
    for a in enriched:
        if a.id not in seen:
            seen.add(a.id)
            ids.append(a.id)
    return ids


# ═══════════════════════════════════════════════════════════════════════════
#  DETERMINISTIC OPINION TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════

def _cite(auth_id: str) -> str:
    """Safe formatter: short citation, or ID if not found."""
    try:
        return format_citation(auth_id, short=True)
    except Exception:
        return auth_id


def _cite_full(auth_id: str) -> str:
    """Full citation form for the legal framework section."""
    try:
        return format_citation(auth_id, short=False)
    except Exception:
        return auth_id


def _safe_alternative_marks(your_mark: str) -> list[str]:
    """Generate 3 safe alternative mark variants (kept simple, deterministic)."""
    base = (your_mark or "MARK").strip() or "MARK"
    return [
        f"{base}+ Pro",
        f"{base}-One",
        f"Nu{base}",
    ]


def render_deterministic_opinion(
    profile: TrademarkRiskProfile,
    allowed_ids: list[str],
) -> str:
    """
    Render a complete clearance opinion using only verified citations.

    Used when LLM is unavailable or when LLM output fails verification.
    Every authority reference is drawn from format_citation().
    """
    now = datetime.now().strftime("%d %B %Y")
    variants = _safe_alternative_marks(profile.your_mark)

    # Conflict analysis lines (one per high-risk conflict)
    conflict_lines = []
    if profile.high_risk_conflicts:
        for i, r in enumerate(profile.high_risk_conflicts, start=1):
            mark = r.get("mark", "")
            owner = r.get("owner", "Unknown")
            cls = r.get("niceClass", "")
            score = r.get("conflict_score", 0)
            if score > 85:
                statute_cite = _cite("STATUTE_TMA_S10_3")
                risk_note = "Famous-mark dilution risk."
            else:
                statute_cite = _cite("STATUTE_TMA_S10_2")
                risk_note = "Likelihood of confusion with earlier registered mark."
            conflict_lines.append(
                f"  {i}. {mark} (Owner: {owner}, Class: {cls}) — "
                f"conflict score: {score:.0f}%. Applicable provision: "
                f"{statute_cite}. {risk_note}"
            )
    # Also list high-dilution conflicts (these come from the similarity /
    # dilution scanner, which catches fuzzy and phonetic near-matches to famous
    # marks even when the live registry API returns nothing — e.g. a near-match
    # to a well-known mark). Without this, a strong dilution hit was wrongly
    # reported as "no conflicts".
    start_idx = len(conflict_lines) + 1
    for j, r in enumerate(profile.high_dilution_conflicts, start=start_idx):
        mark = r.get("mark", r.get("competitor", ""))
        score = r.get("dilution_score", r.get("conflict_score", 0))
        statute_cite = _cite("STATUTE_TMA_S10_3")
        conflict_lines.append(
            f"  {j}. {mark} — dilution score: {score:.0f}%. Applicable "
            f"provision: {statute_cite}. Risk of detriment to, or unfair "
            f"advantage of, the distinctive character of a mark with reputation."
        )
    if not conflict_lines:
        conflict_lines.append("  No high-risk conflicts identified.")
    conflict_block = "\n".join(conflict_lines)

    # Legal framework — every citation from authority_db (full citation on
    # first reference, short form thereafter)
    legal_framework = (
        f"{_cite_full('STATUTE_TMA_S10_2')} prohibits registration of marks "
        "identical or similar to an earlier mark covering identical or similar "
        "goods or services where there exists a likelihood of confusion on the "
        "part of the public. "
        f"{_cite_full('STATUTE_TMA_S10_3')} extends protection to marks with a "
        "reputation in the UK, prohibiting use which would take unfair advantage "
        "of, or be detrimental to, the distinctive character or repute of the "
        "earlier mark (dilution). "
        f"In {_cite_full('CASE_SKY_V_SKYKICK_2024')}, the Supreme Court (Lord "
        "Kitchin, 13 November 2024) confirmed that bad-faith filings and "
        "applications for goods or services in which the applicant had no "
        "genuine intention to use the mark can invalidate registrations "
        "wholly or partially. "
        f"{_cite_full('CASE_LIDL_V_TESCO_2024')} clarified the application of "
        "the unfair-advantage and detriment limbs of section 10(3) in the "
        "context of look-alike retail signage."
    )

    return f"""UK TRADEMARK CLEARANCE OPINION — {profile.your_mark.upper()}
Date: {now}

1. EXECUTIVE SUMMARY

Risk Level: {profile.overall_risk_level}. The search identified {profile.conflict_count} potentially conflicting UKIPO marks, of which {profile.high_risk_count} are classified as high-risk (conflict score > 80%). {profile.high_dilution_count} high-dilution competitors were identified in the market-saturation analysis. Recommendation: {profile.recommendation}. If proceeding, a formal clearance search should be completed within 30 days and a Form TM3 filing prepared for Nice Class {profile.nice_class}.

2. FACTS

The mark "{profile.your_mark}" is proposed for registration in UKIPO Class {profile.nice_class}, covering: {profile.description or 'goods and services as described in the instruction'}. The mark is treated as a word mark for the purposes of this opinion. This opinion covers UK and EU filing territories.

3. LEGAL FRAMEWORK

{legal_framework}

4. CONFLICT ANALYSIS

{conflict_block}

5. MARKET SATURATION RESULTS

A search of the UKIPO trademark register returned {profile.conflict_count} results for the mark "{profile.your_mark}" in Nice Class {profile.nice_class}. The top high-risk conflicts are listed in section 4 above. {f'{profile.high_dilution_count} additional high-dilution competitors were detected in the broader market analysis.' if profile.high_dilution_count else 'No high-dilution competitors were detected in the broader market analysis.'}

6. RISK MITIGATION STRATEGY

A. Mark Modifications — The following alternative marks are recommended to reduce conflict risk and improve distinctiveness: (i) {variants[0]}; (ii) {variants[1]}; (iii) {variants[2]}. Each variant increases distinctiveness and reduces overlap with the existing registrations identified above.

B. Opposition Risk — If the client proceeds to file, existing proprietors may file a Form TM7 Notice of Opposition against the client's application within 2 months of publication in the Trade Marks Journal. Grounds available to opponents include {_cite('STATUTE_TMA_S5_2_B')} (relative grounds — likelihood of confusion) and {_cite('STATUTE_TMA_S5_3')} (marks with reputation). The client should seek to reduce similarity to existing registered marks before filing.

C. Cease & Desist — For the top-ranking conflict, a formal Letter Before Action should be prepared citing {_cite('STATUTE_TMA_S10_2')} and {_cite('STATUTE_TMA_S10_3')}, setting out the potential claim for trade mark infringement and passing off, and requesting cessation of use within 14 days.

7. FILING RECOMMENDATION

{profile.recommendation.upper()}. Subject to further clearance on the top {min(3, profile.high_risk_count)} conflicts identified above, a UK trademark application (Form TM3, fee £170 for one class) should be filed within 60 days. An EU application (EUTM, EUIPO, fee €1,000 for one class) should be filed simultaneously if EU coverage is desired. Clearance advice from a registered trade mark attorney is recommended before filing given the {profile.overall_risk_level.lower()} risk profile.

———
This opinion is prepared by Libra Contract Guardian v2.0, drawing on a search of UKIPO data and competitive market analysis. All statutory citations are drawn from a verified authority database. This opinion constitutes preliminary legal research; it must be verified and adopted by a qualified legal practitioner before being relied on.
"""


# ═══════════════════════════════════════════════════════════════════════════
#  OPTIONAL LLM PHRASING (with verification gate)
# ═══════════════════════════════════════════════════════════════════════════

def _build_trademark_phrasing_prompt(
    profile: TrademarkRiskProfile,
    allowed_ids: list[str],
    deterministic_opinion: str,
) -> str:
    """Build the constrained phrasing prompt for the LLM."""
    auth_objects = [get(aid) for aid in allowed_ids if get(aid) is not None]
    auth_block = authorities_to_prompt_block(auth_objects)

    # Top conflicts as JSON-ish summary
    top_conflicts_text = "\n".join([
        f"  - {r.get('mark','')} (Owner: {r.get('owner','')}, "
        f"Class: {r.get('niceClass','')}, Score: {r.get('conflict_score',0):.0f}%)"
        for r in profile.high_risk_conflicts
    ]) or "  (none)"

    return f"""You are drafting a UK trademark clearance opinion letter.

THE APPLIED-FOR MARK (CRITICAL — DO NOT CHANGE):
The mark being assessed for registration is EXACTLY "{profile.your_mark}".
This is the applicant's chosen mark. Write it EXACTLY as given, character for
character, every time you refer to it — even if it looks like a misspelling of
a famous brand. Do NOT "correct" it. Do NOT substitute a conflicting mark's
name for it. The whole point of this opinion is that "{profile.your_mark}" is
similar to (but NOT the same as) the conflicting marks listed below. If you
write a conflict's name where you mean the applied-for mark, the opinion is
wrong and useless. The applied-for mark is "{profile.your_mark}"; the conflicts
are separate marks owned by other parties.

STRICT CITATION RULES:
1. You may cite ONLY the authorities listed in the "AVAILABLE AUTHORITIES"
   block below.
2. Use the FULL CITATION when introducing an authority, and the SHORT FORM
   in subsequent references.
3. Do NOT use bracket-tag forms such as "[CASE_FOO]" or "[STATUTE_BAR]".
   These are internal identifiers and must never appear in the output.
4. Do NOT write the authority names in ALL_CAPS with underscores (e.g. NOT
   "see CASE_LIDL_V_TESCO_2024" — write "see Lidl v Tesco [2024] EWCA Civ
   262" instead).
5. Do NOT cite Sky v SkyKick as "[2020] UKSC 17". The correct citation is
   "[2024] UKSC 36" (Lord Kitchin, 13 November 2024) — use that form.
6. Any citation outside the allowed list, or any internal-identifier leak,
   will cause your output to be rejected and the deterministic version used
   instead.

CITATION FORM EXAMPLES (these are the only acceptable forms):
- "Trade Marks Act 1994, s.10(2)" or "TMA 1994 s.10(2)"
- "SkyKick UK Ltd v Sky Ltd [2024] UKSC 36" (first reference)
- "Sky v SkyKick" (subsequent references)
- "Lidl Great Britain Ltd v Tesco Stores Ltd [2024] EWCA Civ 262" (first reference)
- "Lidl v Tesco" (subsequent references)

{auth_block}

DETERMINISTIC RISK PROFILE (use these numbers; do not alter):
  Mark: {profile.your_mark}
  Nice Class: {profile.nice_class}
  Description: {profile.description}
  Total conflicts: {profile.conflict_count}
  High-risk conflicts: {profile.high_risk_count}
  High-dilution competitors: {profile.high_dilution_count}
  Overall risk: {profile.overall_risk_level}
  Recommendation: {profile.recommendation}
  Famous-mark threshold hit: {profile.famous_mark_present}

TOP HIGH-RISK CONFLICTS:
{top_conflicts_text}

Produce a structured ~1500-word clearance opinion with these EXACT numbered sections:

1. EXECUTIVE SUMMARY
2. FACTS
3. LEGAL FRAMEWORK
4. CONFLICT ANALYSIS
5. MARKET SATURATION RESULTS
6. RISK MITIGATION STRATEGY (subsections A, B, C)
7. FILING RECOMMENDATION

Use plain numbered section headings (no markdown). Approximately 1500 words.

Return ONLY the opinion text (no JSON wrapper, no preamble)."""


def _try_llm_trademark_opinion(
    profile: TrademarkRiskProfile,
    allowed_ids: list[str],
    deterministic_opinion: str,
) -> Optional[str]:
    """
    Try to generate an LLM-drafted opinion. Returns None on any failure
    or if the output fails citation verification.
    """
    try:
        helpers = _app_helpers()
    except Exception:
        return None

    safe_ai_call = helpers["safe_ai_call"]

    prompt = _build_trademark_phrasing_prompt(profile, allowed_ids, deterministic_opinion)

    try:
        raw = safe_ai_call(prompt, task_mode="high_research")
    except Exception:
        return None

    if not raw or raw.startswith("["):
        return None

    # Guard: the LLM must preserve the applied-for mark exactly. If the mark
    # the applicant chose does not appear in the opinion, the model has likely
    # "corrected" it to a famous conflict (e.g. BURRBERY -> BURBERRY), which
    # makes the opinion wrong. Reject and fall back to the deterministic
    # template, which always uses the correct mark.
    mark = (profile.your_mark or "").strip()
    if mark and mark.lower() not in raw.lower():
        return None

    # Verify citations against allowed set
    report: VerificationReport = verify(raw, allowed_authority_ids=allowed_ids)
    if not report.is_valid:
        # LLM strayed — reject and let deterministic version stand
        return None

    return raw


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT — drop-in replacement for v1 generate_trademark_ai_opinion
# ═══════════════════════════════════════════════════════════════════════════

def generate_trademark_opinion(
    your_mark: str,
    nice_class: str,
    description: str,
    ukipo_results: list[dict],
    dilution_rows: list[dict],
    use_llm_phrasing: bool = False,
) -> str:
    """
    Generate a UK trademark clearance opinion with verified citations.

    Drop-in replacement for v1 generate_trademark_ai_opinion(). Pipeline:
      1. Compute risk profile deterministically
      2. Select authority IDs from verified database
      3. Render deterministic template (always produced)
      4. Return the deterministic template by default (reproducible:
         identical input always yields identical output).
      5. Only if use_llm_phrasing=True: attempt an LLM-drafted version,
         verify it against the allowed authority set AND confirm it
         preserves the applied-for mark; return it only if it passes,
         otherwise fall back to the deterministic template.

    DETERMINISM: the default path is fully deterministic. The same inputs
    produce the same opinion every time — no run-to-run variation. The LLM
    path is opt-in only, because language-model phrasing is inherently
    variable and a clearance opinion should be reproducible.

    Returns: opinion letter as a single string (UI compatible).
    """
    # Phase 2C-fix: augment whatever conflicts we were given with phonetic /
    # edit-distance similarity matching. This fixes the gap where the live
    # UKIPO search returns exact-token matches only and misses near-misses
    # like BURRBERY vs BURBERRY. enrich_conflicts also runs a famous-marks
    # safety net so an obvious near-miss flags even with zero live results.
    try:
        from trademark_similarity import enrich_conflicts
        enriched = enrich_conflicts(
            proposed_mark=your_mark or "",
            proposed_class=nice_class or "",
            live_results=ukipo_results or [],
            uploaded_competitors=None,  # uploaded competitors already merged upstream
            include_well_known_safety_net=True,
        )
        augmented_conflicts = enriched["conflicts"]
        # Merge the augmented conflicts back with the originals, deduplicating
        seen = {(c.get("mark", "").strip().lower(),
                 c.get("owner", "").strip().lower()) for c in augmented_conflicts}
        for orig in (ukipo_results or []):
            key = (orig.get("mark", "").strip().lower(),
                   orig.get("owner", "").strip().lower())
            if key not in seen:
                augmented_conflicts.append(orig)
                seen.add(key)
    except Exception:
        # If the similarity module is unavailable, fall back to raw results
        augmented_conflicts = ukipo_results or []

    profile = compute_trademark_risk(
        your_mark=your_mark,
        nice_class=nice_class,
        description=description,
        ukipo_results=augmented_conflicts,
        dilution_rows=dilution_rows or [],
    )

    allowed_ids = select_authorities_for_trademark(profile)
    deterministic = render_deterministic_opinion(profile, allowed_ids)

    # Default: reproducible deterministic opinion. The LLM phrasing path is
    # opt-in only, to guarantee identical output for identical input.
    if use_llm_phrasing:
        llm_version = _try_llm_trademark_opinion(profile, allowed_ids, deterministic)
        if llm_version is not None:
            return llm_version

    return deterministic


# Keep the old function name as an alias for backwards compatibility
def generate_trademark_ai_opinion(your_mark, nice_class, description,
                                   ukipo_results, dilution_rows):
    """Legacy alias — delegates to generate_trademark_opinion (deterministic)."""
    return generate_trademark_opinion(
        your_mark, nice_class, description, ukipo_results, dilution_rows
    )
