# ================================================================
#  LIBRA CONTRACT GUARDIAN v1.0 – PRPP Engine
#  Post-Report Provenance PROCEDURE (Civil Procedure Framework)
#
#  Built on R.A. Aswin Krishna's forthcoming EIPR article:
#  "Training Data Disclosure in AI Copyright Litigation:
#   The Post-Report Provenance Procedure" (under review, 2026)
#
#  NOT a contractual checklist — a three-stage civil-procedure
#  framework operating through PD 57AD in the Business & Property
#  Courts of England and Wales, addressing the evidentiary vacuum
#  after the UK Govt March 2026 Report on Copyright and AI.
#
#  PRODUCTION BUILD — R.A. Aswin Krishna, IP-AI Practitioner
# ================================================================

# Lazy imports from app.py are done INSIDE each function to avoid
# circular-import issues (app.py imports this module; this module
# needs helpers from app.py).


from dataclasses import dataclass, field


def _app_helpers():
    """Lazy import of helper functions from app.py — avoids circular-import errors."""
    from app import (
        call_ai,
        parse_json_response,
        compute_compliance_strength,
        normalize_score,
        SYSTEM_LEGAL,
    )
    return {
        "call_ai": call_ai,
        "parse_json_response": parse_json_response,
        "compute_compliance_strength": compute_compliance_strength,
        "normalize_score": normalize_score,
        "SYSTEM_LEGAL": SYSTEM_LEGAL,
    }


# ════════════════════════════════════════════════════════════════════════════
#  GRANULAR DETERMINISTIC API  (Phase 2B)
#
#  The three PRPP stages, exposed as pure, individually-testable functions and
#  dataclasses. prpp_procedure_assessment()'s deterministic fallback is built on
#  these, so the same logic that runs in production is the logic under test.
# ════════════════════════════════════════════════════════════════════════════

# ---- Signal dataclasses -----------------------------------------------------
@dataclass
class Stage1Signals:
    """Prima facie trigger signals (Stage 1)."""
    hosted_repository: bool = False
    regurgitation: bool = False
    mia_statistical: bool = False
    hosted_repository_terms: list = field(default_factory=list)
    regurgitation_terms: list = field(default_factory=list)
    mia_terms: list = field(default_factory=list)


@dataclass
class Stage2Signals:
    """Disclosure-feasibility signals (Stage 2)."""
    jurisdiction_uk: bool = False
    ipec_track: bool = False
    sme_defendant: bool = False
    cross_border: bool = False


@dataclass
class Stage3Signals:
    """Adverse-inference signals (Stage 3)."""
    spoliation: bool = False
    proceedings_commenced: bool = False
    pre_action: bool = False


# ---- Term tables (single source of truth for detection) ---------------------
_HOSTED_TERMS = [
    "common crawl", "laion", "books3", "the pile", "refinedweb",
    "webscraped", "scraped from", "hosted on", "indexed",
    "model card", "training corpus", "training set",
    "hosted repository", "hosted domain", "scraped by",
]
_REGURG_TERMS = [
    "near-verbatim", "verbatim", "reproduces", "regurgitat",
    "memorisation", "memorization", "output similarity",
    "extracted", "recovered", "nv-recall", "jailbreak",
]
_MIA_TERMS = [
    "membership inference", "mia", "confidence score",
    "statistical attack", "probability attack",
]
_UK_TERMS = ["uk ", "uk.", "english ", "england", "united kingdom",
             "b&p", "business and property", "high court"]
_IPEC_TERMS = ["ipec", "intellectual property enterprise court"]
_SME_TERMS = ["sme", "small business", "open-source", "open source", "startup"]
_CROSS_BORDER_TERMS = ["us defendant", "california", "service out",
                       "based in", "foreign defendant", "service abroad",
                       "out of jurisdiction"]
_SPOLIATION_TERMS = [
    "deleted", "overwritten", "not retained", "no records", "destroyed",
    "refuses to produce", "non-compliance", "failed to disclose", "spoliation",
]
_PROCEEDINGS_TERMS = [
    "proceedings issued", "proceedings commenced", "claim form was issued",
    "claim form issued", "particulars of claim", "after the cmc", "after proceedings",
    "claim issued",
]
_PRE_ACTION_TERMS = [
    "letter before claim", "pre-action", "pre action", "letter of claim",
    "might delete", "being drafted", "contemplated",
]


# Negation-aware matching. Substring matching alone cannot distinguish a
# statement from its denial: stress testing showed a fact pattern reading
# "NO evidence the work was in any training corpus ... nothing was deleted"
# scoring 71/100 "Moderate" viability. Terms whose every occurrence is
# governed by a negation are suppressed, and the suppression is recorded so
# any assessment can be reconstructed later.
try:
    from negation_guard import filter_negated_terms as _filter_negated
    _NEGATION_GUARD_OK = True
except Exception:  # pragma: no cover - guard must never break detection
    _NEGATION_GUARD_OK = False

# Populated on each detection pass so callers can audit what was suppressed.
LAST_SUPPRESSED: list = []


def _matched(text_lower: str, terms: list, original_text: str = "") -> list:
    hits = [t for t in terms if t in text_lower]
    if not hits or not _NEGATION_GUARD_OK:
        return hits
    surviving, suppressed = _filter_negated(original_text or text_lower, hits)
    if suppressed:
        LAST_SUPPRESSED.extend(suppressed)
    return surviving


def detect_stage1_signals(text: str) -> Stage1Signals:
    """Detect the three Stage 1 evidentiary routes in free text."""
    tl = (text or "").lower()
    LAST_SUPPRESSED.clear()
    hosted = _matched(tl, _HOSTED_TERMS, text or "")
    regurg = _matched(tl, _REGURG_TERMS, text or "")
    mia = _matched(tl, _MIA_TERMS, text or "")
    return Stage1Signals(
        hosted_repository=bool(hosted),
        regurgitation=bool(regurg),
        mia_statistical=bool(mia),
        hosted_repository_terms=hosted,
        regurgitation_terms=regurg,
        mia_terms=mia,
    )


def detect_stage2_signals(text: str) -> Stage2Signals:
    """Detect Stage 2 jurisdiction / forum / party signals."""
    tl = (text or "").lower()
    return Stage2Signals(
        jurisdiction_uk=any(s in tl for s in _UK_TERMS),
        ipec_track=any(s in tl for s in _IPEC_TERMS),
        sme_defendant=any(s in tl for s in _SME_TERMS),
        cross_border=any(s in tl for s in _CROSS_BORDER_TERMS),
    )


def detect_stage3_signals(text: str) -> Stage3Signals:
    """Detect Stage 3 spoliation / proceedings-stage signals."""
    tl = (text or "").lower()
    return Stage3Signals(
        spoliation=bool(_matched(tl, _SPOLIATION_TERMS, text or "")),
        proceedings_commenced=bool(_matched(tl, _PROCEEDINGS_TERMS, text or "")),
        pre_action=bool(_matched(tl, _PRE_ACTION_TERMS, text or "")),
    )


# ---- Stage scoring (pure functions) -----------------------------------------
def score_stage_1(sig: Stage1Signals):
    """Return (trigger_score, hosted_strength, regurg_strength, mia_strength).
    Floor of 20; full signals push the trigger to >= 95."""
    trigger = 20
    hosted_strength = 80 if sig.hosted_repository else 20
    regurg_strength = 75 if sig.regurgitation else 20
    mia_strength = 70 if sig.mia_statistical else 20
    if sig.hosted_repository:
        trigger += 40
    if sig.regurgitation:
        trigger += 35
    if sig.mia_statistical:
        trigger += 20
    trigger = min(100, trigger)
    return trigger, hosted_strength, regurg_strength, mia_strength


def score_stage_2(sig: Stage2Signals) -> int:
    """UK jurisdiction baseline 60 (else 35). IPEC track applies a fixed -30
    penalty (PD 57AD does not apply in the IPEC). SME applies a smaller -15."""
    score = 60 if sig.jurisdiction_uk else 35
    if sig.ipec_track:
        score -= 30
    if sig.sme_defendant:
        score = max(0, score - 15)
    return max(0, min(100, score))


def score_stage_3(sig: Stage3Signals) -> int:
    """Adverse-inference availability. Spoliation is the main driver; per Earles
    there is no general pre-action preservation duty, so pre-action-only facts
    score below the baseline."""
    score = 30
    if sig.spoliation:
        score += 40
    if sig.proceedings_commenced:
        score += 20
    # Earles penalty: pre-action correspondence WITHOUT proceedings commenced
    # cannot, on its own, found a preservation duty.
    if sig.pre_action and not sig.proceedings_commenced:
        score -= 15
    return max(0, min(100, score))


def score_overall(step_1: int, step_2: int, step_3: int):
    """Weighted overall viability and its level label."""
    overall = int((step_1 * 0.45) + (step_2 * 0.30) + (step_3 * 0.25))
    level = ("Strong" if overall >= 75 else
             "Moderate" if overall >= 50 else
             "Weak" if overall >= 30 else "Not Viable")
    return overall, level


def compute_prpp_scores(text: str):
    """Detect all signals and score all stages for a scenario.
    Returns (scores_dict, Stage1Signals, Stage2Signals, Stage3Signals)."""
    s1 = detect_stage1_signals(text)
    s2 = detect_stage2_signals(text)
    s3 = detect_stage3_signals(text)
    trigger, hosted, regurg, mia = score_stage_1(s1)
    step_2 = score_stage_2(s2)
    step_3 = score_stage_3(s3)
    overall, level = score_overall(trigger, step_2, step_3)
    scores = {
        "step_1": trigger, "step_2": step_2, "step_3": step_3,
        "overall": overall, "level": level,
        "hosted_strength": hosted, "regurg_strength": regurg, "mia_strength": mia,
    }
    return scores, s1, s2, s3


def select_authorities_for_prpp(text: str, s1: Stage1Signals,
                                s2: Stage2Signals, s3: Stage3Signals) -> list:
    """Select the authority IDs relevant to this PRPP scenario. Always includes
    the procedural backbone (PD 57AD, CPR r.6.37, adverse-inference lineage,
    CDPA s.29A); adds route- and jurisdiction-specific authorities by signal."""
    ids = [
        "RULE_PD_57AD",
        "RULE_CPR_6_37",
        "STATUTE_CDPA_S29A",
        "CASE_WISNIEWSKI_1998",
        "CASE_GETTY_V_STABILITY_2025",
        # Always cited in the deterministic recommendation text below, so they
        # must be in the allowed set (the output verifier checks every citation
        # that actually appears in the produced text):
        "CASE_IPCOM_V_HTC_2013",   # confidentiality ring
        "RULE_CPR_PT_35",          # expert evidence
        "RULE_CPR_31_22",          # disclosure-order collateral-use
    ]
    if s1.hosted_repository:
        ids.append("REPORT_UK_MAR2026_COPYRIGHT_AI")
    if s1.regurgitation:
        ids.append("CASE_KNESCHKE_V_LAION_2025")
    if s3.spoliation or s3.proceedings_commenced:
        ids.append("CASE_WETTON_V_AHMED_2011")
        ids.append("CASE_EARLES_V_BARCLAYS_2009")
    if s2.cross_border:
        ids.append("CASE_BROWNLIE_2017")
    # De-duplicate, preserve order, and keep only IDs that exist in the DB.
    seen, out = set(), []
    try:
        from authority_db import AUTHORITIES
        valid = set(AUTHORITIES.keys())
    except Exception:
        valid = None
    for i in ids:
        if i in seen:
            continue
        if valid is not None and i not in valid:
            continue
        seen.add(i)
        out.append(i)
    # Safety: guarantee the procedural backbone even if DB lookup filtered hard.
    for must in ("RULE_PD_57AD", "STATUTE_CDPA_S29A"):
        if must not in out:
            out.append(must)
    return out


def prpp_procedure_assessment(
    scenario_text: str,
    claimant_role: str = "copyright owner",
    defendant_role: str = "AI developer",
    contract_text: str | None = None,
) -> dict:
    """
    PRPP (Post-Report Provenance Procedure) — Civil-Procedure Assessment.

    Assesses whether a claimant/scenario satisfies each of the three PRPP stages:
        Step 1  — Prima facie trigger (good-arguable-case threshold under CPR r.6.37)
        Step 2  — Model C Extended Disclosure feasibility under PD 57AD
        Step 3  — Adverse-inference viability if non-compliance occurs

    Inputs:
        scenario_text: facts of the case, or contract in AI-licensing context
        claimant_role: typically "copyright owner"
        defendant_role: typically "AI developer"
        contract_text: optional related contract text for provenance analysis

    Output: structured PRPP assessment with:
        - step_1_trigger_score (0-100) and per-route strength
        - step_2_disclosure_feasibility (0-100)
        - step_3_adverse_inference_risk (0-100)
        - overall_prpp_viability (0-100)
        - procedural_recommendations with statute / case citations
        - confidence_score and reasoning
    """
    # ── Graceful degradation guard ──────────────────────────────────────────
    # _app_helpers() lazily imports app.py to reach the LLM call path. If app.py
    # is unavailable — no Streamlit, no Ollama, running as a library, or a
    # frozen build missing a dependency — this raised and took the whole
    # assessment down with it. The deterministic path needs no helpers at all,
    # so an unavailable LLM must degrade to it rather than fail.
    try:
        _h = _app_helpers()
        call_ai = _h["call_ai"]
        parse_json_response = _h["parse_json_response"]
        compute_compliance_strength = _h["compute_compliance_strength"]
        normalize_score = _h["normalize_score"]
        SYSTEM_LEGAL = _h["SYSTEM_LEGAL"]
        _helpers_ok = True
    except Exception:
        _helpers_ok = False
        call_ai = None
        parse_json_response = None
        SYSTEM_LEGAL = ""

        def compute_compliance_strength(_text):  # deterministic-safe stand-in
            return 0

        def normalize_score(value, default: int = 50) -> int:
            try:
                return max(0, min(100, int(float(value))))
            except (TypeError, ValueError):
                return default

    # ── Empty / insubstantial input guard ───────────────────────────────────
    # An empty or near-empty scenario must never reach the language model. The
    # model will still produce a confident-looking assessment from nothing, and
    # because setdefault() supplies "Moderate" when the response omits a level,
    # an EMPTY document could be reported as a Moderate-viability claim. Testing
    # confirmed exactly that. There is no fact pattern to assess here, so we go
    # straight to the deterministic path, which correctly floors at Not Viable.
    _skip_ai = (not _helpers_ok) or len((scenario_text or "").split()) < 12

    snippet = " ".join(scenario_text.split()[:2500])
    cs_kw = compute_compliance_strength(contract_text or scenario_text)

    prompt = f"""You are a UK IP and civil-procedure specialist. Assess this scenario for viability under the Post-Report Provenance Procedure (PRPP) — R.A. Aswin Krishna's civil-procedure framework operating through PD 57AD in the Business and Property Courts.

PRPP IS A LITIGATION-DISCLOSURE FRAMEWORK, NOT A CONTRACTUAL CHECKLIST. It has three sequential stages:

STAGE 1 — PRIMA FACIE TRIGGER (Good Arguable Case under CPR r.6.37):
  Three evidentiary routes to establish plausible inference of ingestion:
  (a) Hosted repository evidence — claimant's works hosted on domain scraped by known dataset (Common Crawl, LAION-5B, Books3), cross-referenced with developer's public model card disclosures
  (b) Circumstantial regurgitation — model produces near-verbatim reproduction of the claimant's protected work under targeted prompting, supported by reproducible extraction testing and CPR Part 35 expert evidence
  (c) Membership Inference Attack (MIA) — statistical evidence via CPR Pt 35 expert

STAGE 2 — MODEL C EXTENDED DISCLOSURE (PD 57AD):
  Assess feasibility of compelling production of:
  • Cryptographic hash manifests (SHA-256)
  • Training dataset deduplication logs
  • Within a confidentiality ring (external-eyes-only — IPCom v HTC [2013] EWHC 2880 (Ch) at [360]–[377]; Mitsubishi v OnePlus [2020] EWCA Civ 1562 at [18]–[23]; cf. Infederation v Google [2020] EWHC 657 (Ch) at [27]–[42] cautioning against over-restrictive rings)
  Consider proportionality under PD 57AD para 6.4 + CPR r.1.1, and SME cost concerns (March 2026 Report p.66).

STAGE 3 — ADVERSE INFERENCE ON NON-COMPLIANCE (Wisniewski v Central Manchester HA [1998] EWCA Civ 596; [1998] PIQR P324 (witnesses); Wetton v Ahmed [2011] EWCA Civ 610 (documents); Earles v Barclays Bank Plc [2009] EWHC 2500 (Mercantile) (electronic records)):
  Assess likelihood that developer's non-compliance or non-preservation would support discretionary adverse inference on factual issue of ingestion.
  Distinguish deliberate spoliation from routine data-minimisation. Note: per Earles, no general pre-action preservation duty — duty engages once proceedings contemplated.

SCENARIO / CLAIMANT ROLE: {claimant_role}
DEFENDANT ROLE: {defendant_role}

Return ONLY valid JSON:
{{
  "step_1_prima_facie": {{
    "trigger_score": 0-100,
    "hosted_repository": {{"strength": 0-100, "finding": "..."}},
    "circumstantial_regurgitation": {{"strength": 0-100, "finding": "..."}},
    "mia_statistical": {{"strength": 0-100, "finding": "..."}},
    "overall_finding": "whether a good-arguable-case threshold is satisfied"
  }},
  "step_2_disclosure": {{
    "feasibility_score": 0-100,
    "proportionality_analysis": "...",
    "confidentiality_ring_tier": "external-eyes-only | three-tier | self-certified (SME)",
    "expected_documents": ["SHA-256 manifests", "deduplication logs", ...],
    "pd_57ad_model": "Model C Extended Disclosure"
  }},
  "step_3_adverse_inference": {{
    "risk_score": 0-100,
    "spoliation_factors": ["..."],
    "non_culpable_explanations": ["..."],
    "wisniewski_application": "..."
  }},
  "overall_prpp_viability": 0-100,
  "overall_level": "Strong | Moderate | Weak | Not Viable",
  "procedural_recommendations": [
    {{"step": "1|2|3", "action": "...", "citation": "PD 57AD / CPR / case"}}
  ],
  "litigation_exposure": [
    {{"risk": "...", "statute": "CDPA 1988 s.16 / Getty v Stability AI", "likelihood": "High|Medium|Low"}}
  ],
  "triggers": ["..."],
  "confidence_score": 0-100,
  "confidence_reasoning": "..."
}}

SCENARIO / FACTS:
{snippet}"""

    raw = "" if _skip_ai else call_ai(prompt, SYSTEM_LEGAL)
    parsed = None if _skip_ai else parse_json_response(raw, "prpp")

    if parsed and parsed.get("step_1_prima_facie"):
        # Normalise all scores
        s1 = parsed.get("step_1_prima_facie", {})
        s2 = parsed.get("step_2_disclosure", {})
        s3 = parsed.get("step_3_adverse_inference", {})
        parsed["step_1_prima_facie"]["trigger_score"] = normalize_score(s1.get("trigger_score", 50))
        parsed["step_2_disclosure"]["feasibility_score"] = normalize_score(s2.get("feasibility_score", 50))
        parsed["step_3_adverse_inference"]["risk_score"] = normalize_score(s3.get("risk_score", 50))
        parsed["overall_prpp_viability"] = normalize_score(parsed.get("overall_prpp_viability", 50))

        # Derive the level from the SCORE rather than assuming "Moderate".
        # A blanket setdefault meant an AI response that omitted the level was
        # reported as Moderate regardless of the score it actually returned —
        # so a viability of 12 could be labelled "Moderate". The label must
        # always agree with the number beside it, using the same thresholds as
        # the deterministic path.
        _ov = parsed["overall_prpp_viability"]
        _derived_level = (
            "Strong" if _ov >= 75 else
            "Moderate" if _ov >= 50 else
            "Weak" if _ov >= 30 else
            "Not Viable"
        )
        _ai_level = str(parsed.get("overall_level", "")).strip()
        if _ai_level not in ("Strong", "Moderate", "Weak", "Not Viable"):
            parsed["overall_level"] = _derived_level
        else:
            # Even a well-formed label is overridden if it contradicts the
            # score, so the two can never disagree in front of a user.
            parsed["overall_level"] = _ai_level if _ai_level == _derived_level else _derived_level
        parsed.setdefault("procedural_recommendations", [])
        parsed.setdefault("litigation_exposure", [])
        parsed.setdefault("triggers", [])
        parsed.setdefault("confidence_score", 75)
        parsed.setdefault("confidence_reasoning", "AI analysis with statute and case-law matching.")

        # ── Record-shape normalisation ──────────────────────────────────────
        # setdefault above guarantees the top-level keys exist, but NOT the
        # shape of the records inside them. The model can return
        # {"step": "1", "action": "..."} with no "citation", producing a list
        # whose records differ from the deterministic path's. Any consumer
        # expecting a stable contract (the UI, PDF export, the citation
        # provenance test) then raises KeyError. Confirmed in testing:
        # test_phase_2b.py crashed on rec["citation"] when Ollama was live.
        #
        # Both paths must return records of identical shape. Missing fields are
        # filled with an empty string rather than dropped, so a partial AI
        # response degrades to incomplete-but-valid instead of malformed.
        _norm_recs = []
        for _rec in parsed.get("procedural_recommendations") or []:
            if not isinstance(_rec, dict):
                # A bare string is a plausible model response; keep the text.
                _rec = {"action": str(_rec)}
            _norm_recs.append({
                "step": str(_rec.get("step", "")),
                "action": str(_rec.get("action", "")),
                "citation": str(_rec.get("citation", "")),
            })
        parsed["procedural_recommendations"] = _norm_recs

        _norm_risks = []
        for _risk in parsed.get("litigation_exposure") or []:
            if not isinstance(_risk, dict):
                _risk = {"risk": str(_risk)}
            _norm_risks.append({
                "risk": str(_risk.get("risk", "")),
                "statute": str(_risk.get("statute", "")),
                "severity": str(_risk.get("severity", "")),
            })
        parsed["litigation_exposure"] = _norm_risks

        # triggers must be a list of strings, not dicts or nested lists.
        parsed["triggers"] = [
            str(_t) for _t in (parsed.get("triggers") or []) if _t is not None
        ]

        parsed["mode"] = "ai_phrased_verified"
        parsed.setdefault("allowed_authority_ids",
                          select_authorities_for_prpp(
                              scenario_text,
                              detect_stage1_signals(scenario_text),
                              detect_stage2_signals(scenario_text),
                              detect_stage3_signals(scenario_text)))
        return parsed

    # ── Deterministic Fallback (built on the granular Stage API) ────────────
    scores, s1sig, s2sig, s3sig = compute_prpp_scores(scenario_text)
    step_1_score = scores["step_1"]
    step_2_score = scores["step_2"]
    step_3_score = scores["step_3"]
    overall = scores["overall"]
    level = scores["level"]

    hosted_signals      = s1sig.hosted_repository
    regurgitation_signals = s1sig.regurgitation
    mia_signals         = s1sig.mia_statistical
    jurisdiction_uk     = s2sig.jurisdiction_uk
    ipec_track          = s2sig.ipec_track
    sme_flag            = s2sig.sme_defendant
    spoliation_signals  = s3sig.spoliation

    allowed_ids = select_authorities_for_prpp(scenario_text, s1sig, s2sig, s3sig)

    s1_finding = ("Prima facie evidentiary signals detected" if step_1_score >= 60 else
                  "Partial evidentiary signals — more facts needed" if step_1_score >= 35 else
                  "Insufficient prima facie basis — claimant should develop hosted-repository or regurgitation evidence")

    # IPEC: PD 57AD does NOT apply in the Intellectual Property Enterprise Court.
    if ipec_track:
        s2_proportionality = (
            "PD 57AD does NOT apply in the IPEC (Intellectual Property Enterprise Court); "
            "disclosure there is governed by the simplified CPR Part 63 / IPEC regime with "
            "capped, issue-specific orders. Consider whether the Business and Property Courts "
            "are the appropriate forum if Model C Extended Disclosure is required."
        )
        pd_57ad_model = "N/A — IPEC simplified regime (PD 57AD does not apply)"
    else:
        s2_proportionality = (
            "UK Business & Property Courts jurisdiction assumed. Model C Extended Disclosure under "
            "PD 57AD para 6.4 requires proportionality assessment under CPR r.1.1. "
            + ("SME defendant — consider self-certified lower-cost tier. " if sme_flag else "")
            + "Expert-led inspection may be disproportionate in lower-value claims."
        )
        pd_57ad_model = "Model C Extended Disclosure"

    s3_finding = ("Adverse inference highly available" if step_3_score >= 70 else
                  "Moderate inference risk — depends on developer conduct" if step_3_score >= 40 else
                  "Low spoliation risk — developer appears compliant")

    triggers = [
        "Hosted repository signals: " + ("YES" if hosted_signals else "NO"),
        "Regurgitation signals: " + ("YES" if regurgitation_signals else "NO"),
        "MIA references: " + ("YES" if mia_signals else "NO"),
        "Spoliation signals: " + ("YES" if spoliation_signals else "NO"),
        "UK jurisdiction: " + ("YES" if jurisdiction_uk else "UNCERTAIN"),
        "IPEC track: " + ("YES" if ipec_track else "NO"),
        "SME defendant: " + ("YES" if sme_flag else "NO"),
    ]

    return {
        "mode": "deterministic",
        "step_1_prima_facie": {
            "trigger_score": step_1_score,
            "hosted_repository": {
                "strength": scores["hosted_strength"],
                "finding": "Factual basis for hosted-repository route present" if hosted_signals
                           else "No hosted-repository evidence detected — consider model card + scraping-dataset correlation"
            },
            "circumstantial_regurgitation": {
                "strength": scores["regurg_strength"],
                "finding": "Regurgitation evidence present — commission reproducible extraction testing with a CPR Part 35 expert" if regurgitation_signals
                           else "No regurgitation evidence detected — conduct targeted prompting tests"
            },
            "mia_statistical": {
                "strength": scores["mia_strength"],
                "finding": "MIA methodology referenced — CPR Pt 35 expert required" if mia_signals
                           else "No MIA evidence — black-box variants available but less reliable"
            },
            "overall_finding": s1_finding,
        },
        "step_2_disclosure": {
            "feasibility_score": step_2_score,
            "proportionality_analysis": s2_proportionality,
            "confidentiality_ring_tier": "self-certified (SME)" if sme_flag
                                         else "external-eyes-only (IPCom v HTC)",
            "expected_documents": [
                "SHA-256 cryptographic hash manifests",
                "Deduplication logs (per Lee et al. 2022)",
                "Dataset composition records",
                "Model card technical documentation",
            ],
            "pd_57ad_model": pd_57ad_model,
        },
        "step_3_adverse_inference": {
            "risk_score": step_3_score,
            "spoliation_factors": (
                ["Deletion or non-retention after notice of claim detected"] if spoliation_signals
                else ["No clear spoliation signals present"]
            ),
            "non_culpable_explanations": [
                "Routine data-minimisation protocols (pre-contemplation of litigation)",
                "Server infrastructure optimisation overwrites",
                "Trade-secrecy commercial prioritisation (contestable on facts)",
            ],
            "wisniewski_application": (
                "Strong Wisniewski basis — court likely to draw discretionary inference on factual ingestion"
                if step_3_score >= 70 else
                "Moderate Wisniewski basis — outcome depends on credibility of non-culpable explanations"
                if step_3_score >= 40 else
                "Weak Wisniewski basis — no evidence of deliberate withholding"
            ),
        },
        "overall_prpp_viability": overall,
        "overall_level": level,
        "procedural_recommendations": [
            {"step": "1", "action": "Develop evidentiary package on hosted-repository route using Common Crawl/LAION logs and model card cross-reference", "citation": "PD 57AD; CPR r.6.37 (good arguable case)"},
            {"step": "1", "action": "Commission targeted regurgitation prompting tests under a reproducible, documented protocol", "citation": "CPR Pt 35 expert evidence"},
            {"step": "2", "action": "Prepare Disclosure Review Document listing 'Algorithmic Ingestion' as contested Issue", "citation": "PD 57AD; the Disclosure Pilot provisions"},
            {"step": "2", "action": "Draft Model C Extended Disclosure order with confidentiality-ring architecture", "citation": "CPR r.31.22(2); IPCom v HTC [2013] EWHC 2880 (Ch)"},
            {"step": "3", "action": "Send pre-action preservation letter to preserve cryptographic records and engage the documents-preservation duty (per Earles v Barclays, the duty engages once proceedings contemplated)", "citation": "PD 57AD para 3.1; Earles v Barclays Bank Plc [2009] EWHC 2500 (Mercantile); Wetton v Ahmed [2011] EWCA Civ 610"},
        ],
        "litigation_exposure": [
            {"risk": "Output-based copyright claim under s.16(3) CDPA 1988 fails Designers Guild substantial-part test due to probabilistic synthesis",
             "statute": "CDPA 1988 s.16(3); Designers Guild v Russell Williams",
             "likelihood": "High"},
            {"risk": "Secondary-infringement claim against model weights blocked post-Getty unless appeal reverses",
             "statute": "CDPA 1988 ss.22-23; Getty v Stability AI [2025] EWHC 2863 (Ch)",
             "likelihood": "High"},
            {"risk": "EU AI Act Art.53(1)(d) aggregated disclosures insufficient for causal nexus",
             "statute": "EU AI Act Art.53(1)(d); Martens 2025",
             "likelihood": "Medium"},
        ],
        "triggers": triggers,
        "confidence_score": min(70, max(30, 40 + (10 if hosted_signals else 0) + (10 if regurgitation_signals else 0) + (10 if jurisdiction_uk else 0))),
        "confidence_reasoning": (
            "Deterministic scenario analysis (AI unavailable or failed to parse). "
            "Confidence capped at 70% for deterministic mode. "
            "For a full case-specific PRPP memorandum, use AI analysis mode."
        ),
        "allowed_authority_ids": allowed_ids,
    }


# ────────────────────────────────────────────────────────────────────────────
# Backwards compatibility shim for older callers
# The old prpp_simulator name is preserved to avoid breaking existing tabs.
# ────────────────────────────────────────────────────────────────────────────
def prpp_simulator(text: str, analysis: dict | None = None) -> dict:
    """
    Legacy entry point. Delegates to prpp_procedure_assessment with sensible defaults.
    Adapts the new procedure-oriented output into the old contractual-checklist shape
    where possible, so older UI code continues to function.
    """
    result = prpp_procedure_assessment(
        scenario_text=text,
        claimant_role="copyright owner",
        defendant_role="AI developer",
        contract_text=text,
    )

    # Translate new output into legacy contract-checklist shape for UI compatibility
    overall = result["overall_prpp_viability"]
    s1 = result["step_1_prima_facie"]
    s2 = result["step_2_disclosure"]
    s3 = result["step_3_adverse_inference"]

    # The jurisdiction gateway must NOT depend on a string match against the
    # triggers list: the AI-phrased path returns free-text triggers (e.g. "UK
    # forum confirmed"), so the exact-string check "UK jurisdiction: YES" failed
    # whenever the local model was running -- the gateway showed FAIL even for
    # "proceedings in the High Court of England and Wales". Re-detect the
    # signal deterministically from the scenario text so the result is
    # identical regardless of which path (deterministic or AI) produced it.
    try:
        _uk_jurisdiction_detected = detect_stage2_signals(text).jurisdiction_uk
    except Exception:
        _uk_jurisdiction_detected = "UK jurisdiction: YES" in (result.get("triggers") or [])

    checklist = [
        {"item": "Hosted Repository Evidence (Step 1)",
         "status": "pass" if s1["hosted_repository"]["strength"] >= 60 else "fail",
         "detail": s1["hosted_repository"]["finding"],
         "statute": "PD 57AD; Common Crawl/LAION-5B cross-reference", "weight": 20},
        {"item": "Circumstantial Regurgitation (Step 1)",
         "status": "pass" if s1["circumstantial_regurgitation"]["strength"] >= 60 else "fail",
         "detail": s1["circumstantial_regurgitation"]["finding"],
         "statute": "CPR Pt 35 expert evidence", "weight": 18},
        {"item": "Membership Inference Attack (Step 1)",
         "status": "pass" if s1["mia_statistical"]["strength"] >= 60 else "partial",
         "detail": s1["mia_statistical"]["finding"],
         "statute": "CPR Pt 35 expert evidence", "weight": 12},
        {"item": "Model C Extended Disclosure Viability (Step 2)",
         "status": "pass" if s2["feasibility_score"] >= 60 else "partial",
         "detail": s2["proportionality_analysis"][:240],
         "statute": "PD 57AD para 6.4; CPR r.1.1", "weight": 15},
        {"item": "Confidentiality Ring Availability (Step 2)",
         "status": "pass" if s2["feasibility_score"] >= 50 else "fail",
         "detail": f"Proposed tier: {s2['confidentiality_ring_tier']}",
         "statute": "CPR r.31.22(2); IPCom v HTC at [360]–[377]; Mitsubishi v OnePlus at [18]–[23]", "weight": 10},
        {"item": "Adverse Inference Viability (Step 3)",
         "status": "pass" if s3["risk_score"] >= 60 else "partial" if s3["risk_score"] >= 35 else "fail",
         "detail": s3["wisniewski_application"],
         "statute": "Wisniewski [1998] EWCA Civ 596; Wetton v Ahmed [2011] EWCA Civ 610; Earles [2009] EWHC 2500 (Mercantile)", "weight": 15},
        {"item": "UK Jurisdictional Gateway",
         "status": "pass" if _uk_jurisdiction_detected else "fail",
         "detail": "England & Wales forum required for PD 57AD",
         "statute": "CPR r.6.36; PD 6B", "weight": 5},
        {"item": "PD 57AD vs IPEC Forum Selection",
         "status": "pass" if s2["feasibility_score"] >= 50 else "partial",
         "detail": "Business & Property Courts for PRPP; IPEC uses simplified regime",
         "statute": "PD 57AD; CPR Pt 63", "weight": 5},
    ]

    return {
        # Legacy keys for backwards compatibility
        "readiness_score": overall,
        "readiness_level": result["overall_level"],
        "overall_litigation_risk": "Low" if overall >= 75 else "Medium" if overall >= 50 else "High",
        "compliance_strength_score": overall,
        "prpp_score_breakdown": {
            "prima_facie_trigger": (s1["trigger_score"] * 25) // 100,
            "disclosure_feasibility": (s2["feasibility_score"] * 25) // 100,
            "adverse_inference": (s3["risk_score"] * 25) // 100,
            "overall_procedural_fit": (overall * 25) // 100,
        },
        "checklist": checklist,
        "triggers": result["triggers"],
        "recommendations": [r["action"] + f" [{r['citation']}]" for r in result["procedural_recommendations"]],
        "litigation_exposure": [r["risk"] + f" [{r['statute']}]" for r in result["litigation_exposure"]],
        "confidence_score": result["confidence_score"],
        "confidence_sources_matched": ["PD 57AD", "CPR 57AD", "Wisniewski [1998] EWCA Civ 596",
                                       "Wetton v Ahmed [2011] EWCA Civ 610", "Earles v Barclays [2009] EWHC 2500 (Mercantile)",
                                       "Getty v Stability AI", "CDPA 1988 s.29A"],
        # New procedural keys for the new PRPP-specific UI
        "_procedural": result,
        "_engine_version": "2.0-phase-2b",
    }
