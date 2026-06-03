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
    _h = _app_helpers()
    call_ai = _h["call_ai"]
    parse_json_response = _h["parse_json_response"]
    compute_compliance_strength = _h["compute_compliance_strength"]
    normalize_score = _h["normalize_score"]
    SYSTEM_LEGAL = _h["SYSTEM_LEGAL"]

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

    raw = call_ai(prompt, SYSTEM_LEGAL)
    parsed = parse_json_response(raw, "prpp")

    if parsed and parsed.get("step_1_prima_facie"):
        # Normalise all scores
        s1 = parsed.get("step_1_prima_facie", {})
        s2 = parsed.get("step_2_disclosure", {})
        s3 = parsed.get("step_3_adverse_inference", {})
        parsed["step_1_prima_facie"]["trigger_score"] = normalize_score(s1.get("trigger_score", 50))
        parsed["step_2_disclosure"]["feasibility_score"] = normalize_score(s2.get("feasibility_score", 50))
        parsed["step_3_adverse_inference"]["risk_score"] = normalize_score(s3.get("risk_score", 50))
        parsed["overall_prpp_viability"] = normalize_score(parsed.get("overall_prpp_viability", 50))
        parsed.setdefault("overall_level", "Moderate")
        parsed.setdefault("procedural_recommendations", [])
        parsed.setdefault("litigation_exposure", [])
        parsed.setdefault("triggers", [])
        parsed.setdefault("confidence_score", 75)
        parsed.setdefault("confidence_reasoning", "AI analysis with statute and case-law matching.")
        parsed["mode"] = "ai"
        return parsed

    # ── Keyword Fallback (deterministic) ───────────────────────────────────
    tl = scenario_text.lower()

    # Stage 1 signal detection
    has_substantive_text = bool(scenario_text and len(scenario_text.strip()) > 30)
    hosted_signals = any(s in tl for s in [
        "common crawl", "laion", "books3", "the pile", "refinedweb",
        "webscraped", "scraped from", "hosted on", "indexed",
        "model card", "training corpus", "training set",
        "hosted repository", "hosted domain"
    ])
    regurgitation_signals = any(s in tl for s in [
        "near-verbatim", "verbatim", "reproduces", "regurgitat",
        "memorisation", "memorization", "output similarity",
        "extracted", "recovered", "nv-recall", "jailbreak"
    ])
    mia_signals = any(s in tl for s in [
        "membership inference", "mia", "confidence score",
        "statistical attack", "probability attack"
    ])

    step_1_score = 20
    if hosted_signals: step_1_score += 40
    if regurgitation_signals: step_1_score += 35
    if mia_signals: step_1_score += 20
    step_1_score = min(100, step_1_score)

    # Stage 2 feasibility - based on jurisdiction + party signals
    jurisdiction_uk = any(s in tl for s in ["uk ", "english ", "england", "united kingdom", "b&p", "business and property"])
    sme_flag = any(s in tl for s in ["sme", "small business", "open-source", "open source", "startup"])

    step_2_score = 60 if jurisdiction_uk else 35
    if sme_flag: step_2_score = max(30, step_2_score - 15)

    # Stage 3 - adverse inference risk
    spoliation_signals = any(s in tl for s in [
        "deleted", "overwritten", "not retained", "no records", "destroyed",
        "refuses to produce", "non-compliance", "failed to disclose"
    ])
    step_3_score = 30
    if spoliation_signals: step_3_score += 40
    step_3_score = min(100, step_3_score)

    # Overall viability = weighted combination
    overall = int((step_1_score * 0.45) + (step_2_score * 0.30) + (step_3_score * 0.25))

    level = ("Strong" if overall >= 75 else
             "Moderate" if overall >= 50 else
             "Weak" if overall >= 30 else "Not Viable")

    # Build findings
    s1_finding = "Prima facie evidentiary signals detected" if step_1_score >= 60 else \
                 "Partial evidentiary signals — more facts needed" if step_1_score >= 35 else \
                 "Insufficient prima facie basis — claimant should develop hosted-repository or regurgitation evidence"

    s2_finding = "PD 57AD disclosure likely proportionate" if step_2_score >= 60 else \
                 "Disclosure feasible but proportionality questions — consider IPEC alternative" if step_2_score >= 40 else \
                 "Non-UK jurisdiction — parallel Letters Rogatory / Norwich Pharmacal required"

    s3_finding = "Adverse inference highly available" if step_3_score >= 70 else \
                 "Moderate inference risk — depends on developer conduct" if step_3_score >= 40 else \
                 "Low spoliation risk — developer appears compliant"

    return {
        "mode": "keyword",
        "step_1_prima_facie": {
            "trigger_score": step_1_score,
            "hosted_repository": {
                "strength": 80 if hosted_signals else 20,
                "finding": "Factual basis for hosted-repository route present" if hosted_signals
                           else "No hosted-repository evidence detected — consider model card + scraping-dataset correlation"
            },
            "circumstantial_regurgitation": {
                "strength": 75 if regurgitation_signals else 20,
                "finding": "Regurgitation evidence present — commission reproducible extraction testing with a CPR Part 35 expert" if regurgitation_signals
                           else "No regurgitation evidence detected — conduct targeted prompting tests"
            },
            "mia_statistical": {
                "strength": 70 if mia_signals else 20,
                "finding": "MIA methodology referenced — CPR Pt 35 expert required" if mia_signals
                           else "No MIA evidence — black-box variants available but less reliable"
            },
            "overall_finding": s1_finding,
        },
        "step_2_disclosure": {
            "feasibility_score": step_2_score,
            "proportionality_analysis": (
                "UK Business & Property Courts jurisdiction assumed. Model C Extended Disclosure under "
                "PD 57AD para 6.4 requires proportionality assessment under CPR r.1.1. "
                + ("SME defendant — consider self-certified lower-cost tier. " if sme_flag else "")
                + "Expert-led inspection may be disproportionate in lower-value claims."
            ),
            "confidentiality_ring_tier": "self-certified (SME)" if sme_flag
                                         else "external-eyes-only (IPCom v HTC)",
            "expected_documents": [
                "SHA-256 cryptographic hash manifests",
                "Deduplication logs (per Lee et al. 2022)",
                "Dataset composition records",
                "Model card technical documentation",
            ],
            "pd_57ad_model": "Model C Extended Disclosure",
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
        "triggers": [
            "Hosted repository signals: " + ("YES" if hosted_signals else "NO"),
            "Regurgitation signals: " + ("YES" if regurgitation_signals else "NO"),
            "MIA references: " + ("YES" if mia_signals else "NO"),
            "Spoliation signals: " + ("YES" if spoliation_signals else "NO"),
            "UK jurisdiction: " + ("YES" if jurisdiction_uk else "UNCERTAIN"),
            "SME defendant: " + ("YES" if sme_flag else "NO"),
        ],
        "confidence_score": min(70, max(30, 40 + (10 if hosted_signals else 0) + (10 if regurgitation_signals else 0) + (10 if jurisdiction_uk else 0))),
        "confidence_reasoning": (
            "Keyword-based scenario analysis (AI unavailable or failed to parse). "
            "Confidence capped at 70% for deterministic mode. "
            "For a full case-specific PRPP memorandum, use AI analysis mode with API key."
        ),
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
         "status": "pass" if "UK jurisdiction: YES" in result["triggers"] else "fail",
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
    }
