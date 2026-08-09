# ================================================================
#  LIBRA CONTRACT GUARDIAN v2.0 – TDM Engine (Phase 2C refactor)
#  Text & Data Mining Risk Analyser for AI-Adjacent Contracts
#
#  CDPA 1988 s.29A | DSM Art. 3-4 | EU AI Act Art. 53
#
#  ARCHITECTURE (Phase 2C):
#    1. Python detects signals deterministically (risk + mitigation)
#    2. Python scores the contract from signals alone
#    3. authority_selector picks authority IDs deterministically
#    4. LLM (if available) only PHRASES the result; never scores, never cites
#    5. output_verifier rejects any LLM output that strays from allowed IDs
#    6. If LLM unavailable / fails verification → deterministic render used
#
#  Authority-database citations are NEVER fabricated. Same architecture
#  as PRPP v2. The drop-in entry point is `tdm_risk_engine(text, analysis)`.
#
#  PRODUCTION BUILD — R.A. Aswin Krishna, IP-AI Practitioner
# ================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from authority_db import (
    get,
    format_citation,
)
from authority_selector import (
    select_from_selectors,
    enrich_by_keywords,
    authorities_to_prompt_block,
)
from output_verifier import (
    verify,
    VerificationReport,
)


def _app_helpers():
    """Lazy import — avoids circular import errors at module load time."""
    from app import (
        call_ai,
        parse_json_response,
        compute_compliance_strength,
        compute_risk_mitigation_adjustment,
        normalize_score,
        SYSTEM_LEGAL,
    )
    return {
        "call_ai": call_ai,
        "parse_json_response": parse_json_response,
        "compute_compliance_strength": compute_compliance_strength,
        "compute_risk_mitigation_adjustment": compute_risk_mitigation_adjustment,
        "normalize_score": normalize_score,
        "SYSTEM_LEGAL": SYSTEM_LEGAL,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  SIGNAL DETECTION VOCABULARIES
# ═══════════════════════════════════════════════════════════════════════════

# RISK TRIGGERS — terms whose presence increases TDM risk
# Each tuple: (term, points, finding_description, statute_id)
RISK_TRIGGERS: list[tuple[str, int, str, str]] = [
    ("training data",     16, "Training-data reference present",          "STATUTE_CDPA_S29A"),
    ("dataset",           14, "Dataset reference present",                "STATUTE_CDPA_S29A"),
    ("data mining",       12, "Data-mining language present",             "STATUTE_CDPA_S29A"),
    ("text and data",     12, "Text-and-data mining language present",    "STATUTE_CDPA_S29A"),
    ("text & data",       12, "Text-and-data mining language present",    "STATUTE_CDPA_S29A"),
    ("scrape",            12, "Scraping / crawl language present",        "STATUTE_CDPA_S16"),
    ("crawl",             10, "Crawl language present",                   "STATUTE_CDPA_S16"),
    ("tdm",               18, "TDM acronym used in contract",             "STATUTE_CDPA_S29A"),
    ("model training",    16, "Model-training language present",          "STATUTE_CDPA_S16"),
    ("machine learning",  14, "Machine-learning use referenced",          "STATUTE_CDPA_S29A"),
    ("statistical model", 12, "Statistical-modelling use referenced",     "STATUTE_CDPA_S29A"),
    ("lineage",           12, "Lineage referenced or ambiguous",          "DIR_DSM_ART_4"),
    ("provenance",         8, "Provenance referenced (verify scope)",     "DIR_DSM_ART_4"),
]

# MITIGATION SIGNALS — terms whose presence reduces TDM risk
# Each tuple: (term, points_reduction, finding_description)
MITIGATION_SIGNALS: list[tuple[str, int, str]] = [
    ("tdm exclusion",                14, "TDM expressly excluded"),
    ("training exclusion",           14, "Training use expressly excluded"),
    ("not used for training",        14, "Training use prohibited"),
    ("not be used for training",     14, "Training use prohibited"),
    ("excluded from",                10, "Use-exclusion clause present"),
    ("no model training",            14, "Model training prohibited"),
    ("not be used for machine",      14, "Machine-learning use prohibited"),
    ("no machine learning",          12, "Machine-learning use prohibited"),
    ("provenance schedule",          10, "Provenance schedule present"),
    ("data provenance schedule",     12, "Data provenance schedule present"),
    ("audit rights",                 10, "Audit rights present"),
    ("right to audit",               10, "Right to audit present"),
    ("opt-out",                       8, "Opt-out provision present"),
    ("opt out",                       8, "Opt-out provision present"),
    ("rights reservation",            8, "Rights reservation clause present"),
    ("machine-readable reservation", 10, "Machine-readable Art. 4(3) reservation"),
    ("licensed dataset",             10, "Dataset is licensed — lower risk"),
    ("lawfully obtained",             8, "Lawful acquisition warranted"),
    ("warrants that",                 6, "Provenance warranty present"),
    ("provenance warranty",          12, "Provenance warranty present"),
    ("cdpa 1988",                     6, "Statute awareness in contract body"),
    ("cdpa s.29a",                    8, "CDPA s.29A expressly cited"),
    ("section 29a",                   8, "CDPA s.29A expressly cited"),
    ("dsm directive",                 6, "DSM Directive referenced"),
    ("art. 4(3)",                     6, "DSM Art. 4(3) opt-out referenced"),
    ("article 4(3)",                  6, "DSM Art. 4(3) opt-out referenced"),
    ("ai act",                        6, "EU AI Act referenced"),
    ("article 53",                    6, "EU AI Act Art. 53 referenced"),
]


@dataclass
class TDMSignals:
    """Detected risk and mitigation signals."""
    risk_findings: list[tuple[str, int, str, str]] = field(default_factory=list)
    # each: (term, points, description, statute_id)
    mitigation_findings: list[tuple[str, int, str]] = field(default_factory=list)
    # each: (term, points_reduction, description)

    # Convenience structural flags
    scraping_clause: bool = False
    dataset_ownership_ambiguous: bool = False
    training_rights_undefined: bool = False
    provenance_absent: bool = False
    semantic_dilution: bool = False


# Negation-aware detection. Substring matching cannot tell a permission from
# a prohibition: stress testing showed "expressly prohibits any dataset
# creation. There shall be no scraping, no crawling, no data mining" scoring
# 36/100 "Medium risk" — maximally protective drafting scored as risk.
try:
    from negation_guard import term_is_negated as _term_is_negated
    _NEGATION_GUARD_OK = True
except Exception:  # pragma: no cover - guard must never break detection
    _NEGATION_GUARD_OK = False

# Populated on each detection pass so callers can audit what was suppressed.
LAST_SUPPRESSED: list = []


def detect_tdm_signals(text: str) -> TDMSignals:
    """Pure function: contract text → TDM risk and mitigation signals."""
    tl = (text or "").lower()
    sig = TDMSignals()
    LAST_SUPPRESSED.clear()

    for term, pts, msg, statute_id in RISK_TRIGGERS:
        if term in tl:
            # A risk term that is prohibited everywhere it appears is a
            # PROTECTION, not a risk. Mitigation terms are never suppressed:
            # they are protective by definition.
            if _NEGATION_GUARD_OK:
                negated, neg_word = _term_is_negated(text or "", term)
                if negated:
                    LAST_SUPPRESSED.append((term, neg_word or "negation"))
                    continue
            sig.risk_findings.append((term, pts, msg, statute_id))

    for term, reduction, desc in MITIGATION_SIGNALS:
        if term in tl:
            sig.mitigation_findings.append((term, reduction, desc))

    # Structural flags (used by old shape; preserved for backwards compat)
    sig.scraping_clause = ("scrape" in tl) or ("crawl" in tl)
    sig.dataset_ownership_ambiguous = (
        "dataset" in tl
        and "own" not in tl
        and "licensed" not in tl
    )
    sig.training_rights_undefined = (
        "train" in tl
        and "training rights" not in tl
        and "training exclusion" not in tl
        and "not used for training" not in tl
        and "not be used for training" not in tl
    )
    sig.provenance_absent = (
        "provenance" not in tl
        and "provenance schedule" not in tl
    )
    sig.semantic_dilution = "semantic dilution" in tl or "contamination" in tl

    return sig


# ═══════════════════════════════════════════════════════════════════════════
#  DETERMINISTIC SCORING
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class TDMScores:
    """Deterministic TDM scoring result."""
    raw_risk: int           # before mitigation
    mitigation_adjustment: int  # points subtracted from raw_risk
    risk_score: int         # final 0-100
    risk_level: str         # Low / Medium / High / Critical
    compliance_strength: int  # 0-100 (complement of risk + mitigation bonus)


def score_tdm(
    signals: TDMSignals,
    has_substantive_text: bool,
    external_keyword_strength: int = 0,  # from compute_compliance_strength (app.py)
    external_mitigation_adj: int = 0,    # from compute_risk_mitigation_adjustment
) -> TDMScores:
    """
    Pure function: signals + (optional) external app.py adjustments → scores.

    The external_keyword_strength and external_mitigation_adj are kept for
    backwards compatibility with the old keyword-strength helpers in app.py.
    If unavailable (testing without app.py), they default to 0.
    """
    raw = sum(pts for _, pts, _, _ in signals.risk_findings)
    mit = sum(reduction for _, reduction, _ in signals.mitigation_findings)

    # Apply the external mitigation adjustment on top
    total_mit = mit + max(0, external_mitigation_adj)
    score = max(0, min(100, raw - total_mit))

    level = (
        "Critical" if score >= 75 else
        "High" if score >= 50 else
        "Medium" if score >= 25 else
        "Low"
    )

    # Empty-text guard
    if not has_substantive_text:
        return TDMScores(
            raw_risk=0,
            mitigation_adjustment=0,
            risk_score=0,
            risk_level="N/A",
            compliance_strength=0,
        )

    compliance = max(external_keyword_strength, min(100, 100 - score))

    return TDMScores(
        raw_risk=raw,
        mitigation_adjustment=total_mit,
        risk_score=score,
        risk_level=level,
        compliance_strength=compliance,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  AUTHORITY SELECTION
# ═══════════════════════════════════════════════════════════════════════════

def select_authorities_for_tdm(text: str, signals: TDMSignals) -> list[str]:
    """
    Select authority IDs for a TDM contract analysis.

    Always includes the CONTRACT_TDM and CONTRACT_AI_TRAINING selector
    groups; enriches by keywords detected in the contract.
    """
    # CONTRACT_TDM and CONTRACT_AI_TRAINING cover the core: s.29A,
    # DSM Art. 3 & 4, AI Act Art. 53, Getty, Kneschke, March 2026 Report.
    base = select_from_selectors(["CONTRACT_TDM", "CONTRACT_AI_TRAINING"])
    enriched = enrich_by_keywords(text, base)

    # Deduplicate IDs while preserving order
    seen: set[str] = set()
    ids: list[str] = []
    for a in enriched:
        if a.id not in seen:
            seen.add(a.id)
            ids.append(a.id)
    return ids


# ═══════════════════════════════════════════════════════════════════════════
#  STRUCTURED RENDERING (deterministic fallback)
# ═══════════════════════════════════════════════════════════════════════════

def _cite(auth_id: str) -> str:
    """Safe formatter: returns short citation, or the ID if not found."""
    try:
        return format_citation(auth_id, short=True)
    except Exception:
        return auth_id


def render_deterministic_tdm(
    text: str,
    signals: TDMSignals,
    scores: TDMScores,
    allowed_ids: list[str],
) -> dict:
    """
    Render the full TDM assessment from deterministic data alone.

    Every citation comes from the verified authority database. The shape
    mirrors the old `tdm_risk_engine` output so the UI does not need to
    change.
    """
    # Build tdm_issues from detected risk findings
    tdm_issues = []
    for term, pts, msg, statute_id in signals.risk_findings:
        severity = "High" if pts >= 16 else "Medium"
        exposure_type = (
            "Copyright infringement" if "CDPA" in statute_id else
            "Regulatory" if "DSM" in statute_id or "AI_ACT" in statute_id else
            "Contract breach"
        )
        tdm_issues.append({
            "issue": msg,
            "detail": f"Contract contains '{term}' language. Review against {_cite(statute_id)}.",
            "statute": _cite(statute_id),
            "severity": severity,
            "exposure_type": exposure_type,
        })

    # Build mitigation_clauses_found
    mitigation_clauses = [
        {
            "clause": desc,
            "protection_type": "Protective language",
            "statute": _cite("STATUTE_CDPA_S29A"),
        }
        for _, _, desc in signals.mitigation_findings
    ]

    # Litigation risks — drawn from verified authorities
    high_risk = scores.risk_score >= 50
    medium_risk = scores.risk_score >= 25
    litigation_risks = [
        {
            "risk": (
                "Copyright infringement claim if dataset is ingested without "
                "licence and CDPA s.29A non-commercial-research exception is unavailable."
            ),
            "statute": f"{_cite('STATUTE_CDPA_S16')}; {_cite('STATUTE_CDPA_S29A')}",
            "likelihood": "High" if high_risk else "Medium" if medium_risk else "Low",
            "remedy": "Injunction / Damages",
        },
        {
            "risk": (
                "DSM Art. 4(3) opt-out breach if scraping ignores machine-readable "
                "rights reservation (see Kneschke v LAION on machine-actionability)."
            ),
            "statute": f"{_cite('DIR_DSM_ART_4')}; {_cite('CASE_KNESCHKE_V_LAION_2025')}",
            "likelihood": "Medium" if medium_risk else "Low",
            "remedy": "Licensing demand / injunction in EU jurisdictions",
        },
        {
            "risk": (
                "EU AI Act Art. 53(1)(d) transparency obligation may require "
                "publication of aggregated training-data summary — insufficient "
                "for UK-claimant evidentiary needs but a regulatory trigger."
            ),
            "statute": _cite("REG_EU_AI_ACT_ART_53"),
            "likelihood": "Medium" if medium_risk else "Low",
            "remedy": "Regulatory sanction",
        },
    ]

    # Triggers list (UI compatibility)
    triggers = [
        f"{msg} — {_cite(statute_id)}"
        for _, _, msg, statute_id in signals.risk_findings
    ][:10]

    # Recommendations — pulled from verified authorities
    recommendations = [
        f"State expressly whether use for statistical modelling or pattern "
        f"extraction is permitted ({_cite('STATUTE_CDPA_S29A')}).",
        f"Require proof of source rights, licences, and provenance for all "
        f"ingested material ({_cite('STATUTE_CDPA_S16')}; {_cite('REPORT_UK_MAR2026_COPYRIGHT_AI')}).",
        f"Clarify whether public web scraping, licensed datasets, or third-"
        f"party corpora are excluded ({_cite('STATUTE_CDPA_S16')}).",
        f"Add warranty that no restricted or unlawfully acquired content is "
        f"used ({_cite('STATUTE_CDPA_S29A')}; {_cite('CASE_KNESCHKE_V_LAION_2025')}).",
        f"Add EU AI Act Art. 53 transparency-compatible provenance clause if "
        f"EU deployment is contemplated ({_cite('REG_EU_AI_ACT_ART_53')}).",
        f"Include cryptographic hash-manifest retention clause per author's "
        f"PRPP framework ({_cite('ACADEMIC_KRISHNA_PRPP_2026')}).",
    ]

    # Exposure summary
    if not text or len(text.strip()) <= 50:
        exposure_summary = "No substantive contract text provided — analysis pending input."
    else:
        exposure_summary = (
            f"TDM risk score: {scores.risk_score}/100 after "
            f"{scores.mitigation_adjustment}-pt mitigation adjustment "
            f"({len(signals.mitigation_findings)} mitigation clauses detected). "
            f"Primary exposure under {_cite('STATUTE_CDPA_S29A')}; "
            f"secondary under {_cite('DIR_DSM_ART_4')} and "
            f"{_cite('REG_EU_AI_ACT_ART_53')}."
        )

    # Confidence — capped at 68 for deterministic-only mode
    triggers_possible = len(RISK_TRIGGERS)
    triggers_matched = len(signals.risk_findings)
    mitigations_found = len(signals.mitigation_findings)
    raw_conf = round((triggers_matched / max(triggers_possible, 1)) * 100)
    adj_conf = min(68, max(25, raw_conf + min(10, mitigations_found * 2)))

    return {
        "mode": "deterministic",
        "risk_score": scores.risk_score,
        "risk_level": scores.risk_level,
        "compliance_strength_score": scores.compliance_strength,
        "tdm_issues": tdm_issues,
        "mitigation_clauses_found": mitigation_clauses,
        "scraping_clause_detected": signals.scraping_clause,
        "dataset_ownership_ambiguous": signals.dataset_ownership_ambiguous,
        "training_rights_undefined": signals.training_rights_undefined,
        "provenance_tracking_absent": signals.provenance_absent,
        "semantic_dilution_risk": signals.semantic_dilution,
        "litigation_risks": litigation_risks,
        "legal_exposure_summary": exposure_summary,
        "triggers": triggers,
        "recommendations": recommendations,
        "confidence_score": adj_conf,
        "confidence_reasoning": (
            f"Deterministic scoring — {triggers_matched}/{triggers_possible} "
            f"risk triggers matched, {mitigations_found} mitigation clauses "
            f"detected, mitigation adjustment {scores.mitigation_adjustment} pts. "
            "Citations drawn exclusively from the verified authority database. "
            "Confidence capped at 68% for deterministic-only mode."
        ),
        "allowed_authority_ids": allowed_ids,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  LLM-AS-PHRASER (optional natural-language polish layer)
# ═══════════════════════════════════════════════════════════════════════════

def _build_tdm_phrasing_prompt(deterministic_result: dict, allowed_ids: list[str]) -> str:
    """Build the constrained phrasing prompt for the LLM."""
    auth_objects = [get(aid) for aid in allowed_ids if get(aid) is not None]
    auth_block = authorities_to_prompt_block(auth_objects)

    score = deterministic_result["risk_score"]
    level = deterministic_result["risk_level"]
    compliance = deterministic_result["compliance_strength_score"]

    return f"""You are phrasing a TDM (Text & Data Mining) contract risk assessment.

YOUR ROLE IS LIMITED: you are NOT scoring, NOT selecting authorities, NOT
making legal conclusions. The scoring and authority selection have already
been done deterministically. Your only job is to phrase the finalised result
in clear professional English.

STRICT CITATION RULES:
1. You may cite ONLY the authorities listed in the "AVAILABLE AUTHORITIES"
   block below.
2. Use the FULL CITATION on first mention and the SHORT FORM thereafter.
3. Do NOT use bracket-tag forms such as "[STATUTE_FOO]" or "[CASE_BAR]".
   These are internal identifiers and must never appear in the output.
4. Do NOT write authority names in ALL_CAPS_WITH_UNDERSCORES.
5. Any internal-identifier leak causes your output to be rejected.

CITATION FORM EXAMPLES (these are the only acceptable forms):
- "CDPA 1988 s.29A" or "section 29A of the Copyright, Designs and Patents Act 1988"
- "Article 4(3) of the DSM Directive" or "DSM Directive Art. 4(3)"
- "EU AI Act, Art. 53"
- "Kneschke v LAION" (subsequent ref) or "Robert Kneschke v LAION e.V., OLG Hamburg, 10 December 2025" (first ref)

{auth_block}

DETERMINISTIC SCORING RESULT (finalised — do not alter):
  - Risk score: {score}/100 ({level})
  - Compliance strength: {compliance}/100

Return ONLY valid JSON in this exact shape:
{{
  "executive_summary": "2-3 sentences phrasing the overall risk. Use citation forms only — no internal IDs.",
  "mitigation_narrative": "2-3 sentences phrasing the mitigation analysis.",
  "recommendations_narrative": "2-3 sentences phrasing the top recommendations."
}}

DO NOT include any other keys. DO NOT include internal-identifier strings (anything matching CASE_*, STATUTE_*, RULE_*, REG_*, DIR_*, REPORT_*, ACADEMIC_*)."""


def _try_llm_phrasing(deterministic_result: dict, allowed_ids: list[str]) -> Optional[dict]:
    """Optional LLM phrasing layer. Returns None on any failure or unsafe output."""
    try:
        helpers = _app_helpers()
    except Exception:
        return None

    call_ai = helpers["call_ai"]
    parse_json_response = helpers["parse_json_response"]
    SYSTEM_LEGAL = helpers["SYSTEM_LEGAL"]

    prompt = _build_tdm_phrasing_prompt(deterministic_result, allowed_ids)

    try:
        raw = call_ai(prompt, SYSTEM_LEGAL)
    except Exception:
        return None

    if not raw:
        return None

    parsed = parse_json_response(raw, "tdm_phrasing")
    if not parsed or not isinstance(parsed, dict):
        return None

    combined = " ".join([
        str(parsed.get("executive_summary", "")),
        str(parsed.get("mitigation_narrative", "")),
        str(parsed.get("recommendations_narrative", "")),
    ])

    report: VerificationReport = verify(combined, allowed_authority_ids=allowed_ids)
    if not report.is_valid:
        return None

    return {
        "executive_summary": parsed.get("executive_summary", ""),
        "mitigation_narrative": parsed.get("mitigation_narrative", ""),
        "recommendations_narrative": parsed.get("recommendations_narrative", ""),
        "_verification_report": {
            "is_valid": report.is_valid,
            "citations_verified": [c.raw_text for c in report.citations_verified],
            "citations_unknown": [c.raw_text for c in report.citations_unknown],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT — drop-in replacement for v1 tdm_risk_engine
# ═══════════════════════════════════════════════════════════════════════════

def tdm_risk_engine(text: str, analysis: dict | None = None) -> dict:
    """
    TDM risk engine (Phase 2C refactored).

    Pipeline:
      1. Signal detection (no LLM)
      2. Deterministic scoring (no LLM)
      3. Authority selection (no LLM)
      4. Structured render with citations from authority database
      5. Optional LLM phrasing (verified before display)
      6. If phrasing fails verification → deterministic render unchanged

    Citations are NEVER fabricated. Drop-in replacement for v1.

    Args:
        text: contract text to analyse
        analysis: optional analysis dict from broader pipeline (used for
                  cross-engine score combination, backwards-compat)

    Returns:
        Dict in the v1 shape, plus extra keys: mode, allowed_authority_ids,
        and optionally llm_phrasing.
    """
    # Pull optional external adjustments from app.py (backwards-compat)
    external_strength = 0
    external_mit_adj = 0
    try:
        helpers = _app_helpers()
        external_strength = helpers["compute_compliance_strength"](text or "")
        external_mit_adj = helpers["compute_risk_mitigation_adjustment"](text or "")
    except Exception:
        # No app.py available (testing or standalone) — fall through to 0
        pass

    # Signal detection
    signals = detect_tdm_signals(text or "")
    has_substantive_text = bool(text and len(text.strip()) > 50)

    # Scoring
    scores = score_tdm(
        signals,
        has_substantive_text=has_substantive_text,
        external_keyword_strength=external_strength,
        external_mitigation_adj=external_mit_adj,
    )

    # Optional cross-engine adjustment from analysis dict (v1 behaviour preserved)
    if analysis and has_substantive_text:
        raw_tdm = int(analysis.get("key_risk_areas", {}).get("tdm_training_data", 0) / 2)
        adjusted = max(0, min(100, scores.risk_score + raw_tdm - external_mit_adj))
        scores = TDMScores(
            raw_risk=scores.raw_risk,
            mitigation_adjustment=scores.mitigation_adjustment + external_mit_adj,
            risk_score=adjusted,
            risk_level=(
                "Critical" if adjusted >= 75 else
                "High" if adjusted >= 50 else
                "Medium" if adjusted >= 25 else
                "Low"
            ),
            compliance_strength=max(external_strength, min(100, 100 - adjusted)),
        )

    # Authority selection
    allowed_ids = select_authorities_for_tdm(text or "", signals)

    # Deterministic render (always produced)
    result = render_deterministic_tdm(text or "", signals, scores, allowed_ids)

    # Optional LLM phrasing layer
    phrasing = _try_llm_phrasing(result, allowed_ids)
    if phrasing is not None:
        result["mode"] = "ai_phrased_verified"
        result["llm_phrasing"] = phrasing
        # Confidence bump for verified phrasing — capped at 85
        result["confidence_score"] = min(85, result["confidence_score"] + 12)
        result["confidence_reasoning"] = (
            "Deterministic scoring with LLM phrasing layer (verified against "
            "the authority database). All citations confirmed in the allowed "
            "authority set; no out-of-set citations detected."
        )

    return result
