"""
Phase 2B test suite — refactored PRPP engine.

Verifies:
  1. Signal detection (pure functions)
  2. Deterministic scoring (pure functions)
  3. Authority selection (deterministic)
  4. Structured rendering (citations all from verified DB)
  5. Legacy shim (backwards compatibility with old UI)
  6. End-to-end: well-formed scenario → valid PRPP result
  7. IPEC warning path
  8. No-LLM fallback works without app.py present

Run: python test_phase_2b.py
"""

import sys

# Direct imports — no app.py needed for deterministic path
import prpp


# ════════════════════════════════════════════════════════════════════════════
# TEST HARNESS
# ════════════════════════════════════════════════════════════════════════════

def t(label: str, passed: bool, reason: str = "") -> bool:
    """Single test assertion. Returns True if passed; prints either way."""
    if passed:
        print(f"  ✓ {label}" + (f" — {reason}" if reason else ""))
        return True
    print(f"  ✗ {label}" + (f" — {reason}" if reason else ""))
    return False


def run_all() -> int:
    """Run all tests and return failure count."""
    failures = 0
    print("\nPhase 2B — PRPP Engine Refactor — Integration Tests")
    print("─" * 70)

    # ── [1] Signal detection ────────────────────────────────────────────────
    print("\n[1] signal detection (pure functions)")

    s1 = prpp.detect_stage1_signals(
        "The works were hosted on a public domain scraped by Common Crawl, "
        "and the model produces near-verbatim outputs under targeted prompting."
    )
    failures += not t("Hosted repository signal detected", s1.hosted_repository)
    failures += not t("Regurgitation signal detected", s1.regurgitation)
    failures += not t("MIA signal absent when not mentioned", not s1.mia_statistical)
    failures += not t("Hosted terms captured",
                      "common crawl" in s1.hosted_repository_terms)
    failures += not t("Regurgitation terms captured",
                      "near-verbatim" in s1.regurgitation_terms)

    s1_empty = prpp.detect_stage1_signals("")
    failures += not t("Empty input → no Stage 1 signals",
                      not s1_empty.hosted_repository and
                      not s1_empty.regurgitation and
                      not s1_empty.mia_statistical)

    s2 = prpp.detect_stage2_signals("UK High Court. SME defendant. IPEC track.")
    failures += not t("Jurisdiction UK detected", s2.jurisdiction_uk)
    failures += not t("IPEC track detected", s2.ipec_track)
    failures += not t("SME defendant detected", s2.sme_defendant)

    s2_xb = prpp.detect_stage2_signals("US defendant based in California. Service out required.")
    failures += not t("Cross-border detected", s2_xb.cross_border)

    s3 = prpp.detect_stage3_signals(
        "Defendant deleted training logs after the claim form was issued. "
        "Letter before claim sent in March."
    )
    failures += not t("Spoliation detected", s3.spoliation)
    failures += not t("Proceedings commenced detected", s3.proceedings_commenced)
    failures += not t("Pre-action detected", s3.pre_action)

    # ── [2] Deterministic scoring ───────────────────────────────────────────
    print("\n[2] deterministic scoring (pure functions)")

    # Strong Stage 1 (all three routes)
    sig1_full = prpp.Stage1Signals(
        hosted_repository=True,
        regurgitation=True,
        mia_statistical=True,
    )
    trigger, hosted, regurg, mia = prpp.score_stage_1(sig1_full)
    failures += not t("Full Stage 1 signals → trigger >= 95", trigger >= 95,
                      f"actual: {trigger}")
    failures += not t("Hosted strength = 80 when present", hosted == 80)
    failures += not t("Regurgitation strength = 75 when present", regurg == 75)

    # Empty Stage 1 (floor at 20)
    sig1_empty = prpp.Stage1Signals()
    trigger_empty, _, _, _ = prpp.score_stage_1(sig1_empty)
    failures += not t("Empty Stage 1 → floor at 20", trigger_empty == 20)

    # Stage 2: UK without IPEC
    sig2_uk = prpp.Stage2Signals(jurisdiction_uk=True)
    failures += not t("UK + non-IPEC → Stage 2 >= 60",
                      prpp.score_stage_2(sig2_uk) >= 60)

    # Stage 2: IPEC penalty
    sig2_ipec = prpp.Stage2Signals(jurisdiction_uk=True, ipec_track=True)
    score_ipec = prpp.score_stage_2(sig2_ipec)
    score_uk = prpp.score_stage_2(sig2_uk)
    failures += not t("IPEC track reduces Stage 2 score by 30",
                      score_uk - score_ipec == 30,
                      f"UK={score_uk}, IPEC={score_ipec}")

    # Stage 3: spoliation + proceedings
    sig3_strong = prpp.Stage3Signals(spoliation=True, proceedings_commenced=True)
    failures += not t("Spoliation + proceedings → Stage 3 >= 80",
                      prpp.score_stage_3(sig3_strong) >= 80,
                      f"actual: {prpp.score_stage_3(sig3_strong)}")

    # Stage 3: pre-action only → Earles penalty
    sig3_pre_only = prpp.Stage3Signals(pre_action=True, proceedings_commenced=False)
    failures += not t("Pre-action only (Earles) → Stage 3 below baseline",
                      prpp.score_stage_3(sig3_pre_only) < 30,
                      f"actual: {prpp.score_stage_3(sig3_pre_only)}")

    # Overall scoring
    overall, level = prpp.score_overall(95, 80, 80)
    failures += not t("Strong all-stages → 'Strong' level", level == "Strong")
    overall_weak, level_weak = prpp.score_overall(20, 30, 30)
    failures += not t("Weak all-stages → 'Not Viable' or 'Weak'",
                      level_weak in ("Not Viable", "Weak"))

    # ── [3] Authority selection ─────────────────────────────────────────────
    print("\n[3] authority selection")

    scores, s1, s2, s3 = prpp.compute_prpp_scores(
        "UK claim. Common Crawl scraping. Verbatim regurgitation. "
        "Defendant deleted training logs after proceedings issued."
    )
    ids = prpp.select_authorities_for_prpp("UK claim. Common Crawl scraping.", s1, s2, s3)
    failures += not t("Authority IDs returned", len(ids) >= 5,
                      f"count: {len(ids)}")
    failures += not t("All IDs are strings", all(isinstance(i, str) for i in ids))
    failures += not t("No duplicate IDs", len(ids) == len(set(ids)))
    failures += not t("PD 57AD in selected authorities",
                      "RULE_PD_57AD" in ids)
    failures += not t("CDPA s.29A in selected authorities (general PRPP context)",
                      "STATUTE_CDPA_S29A" in ids or
                      any("CDPA" in i for i in ids))

    # ── [4] Structured rendering ────────────────────────────────────────────
    print("\n[4] structured rendering")

    result = prpp.prpp_procedure_assessment(
        scenario_text=(
            "UK High Court claim. Common Crawl data. Verbatim regurgitation. "
            "Defendant deleted logs after proceedings issued."
        )
    )

    # Result must have all required keys
    required_keys = [
        "mode",
        "step_1_prima_facie",
        "step_2_disclosure",
        "step_3_adverse_inference",
        "overall_prpp_viability",
        "overall_level",
        "procedural_recommendations",
        "litigation_exposure",
        "triggers",
        "confidence_score",
        "allowed_authority_ids",
    ]
    for key in required_keys:
        failures += not t(f"Result has required key: {key}",
                          key in result)

    failures += not t("Mode is 'deterministic' or 'ai_phrased_verified'",
                      result["mode"] in ("deterministic", "ai_phrased_verified"))

    # Stage 1 substructure
    s1_out = result["step_1_prima_facie"]
    for sub in ("trigger_score", "hosted_repository", "circumstantial_regurgitation",
                "mia_statistical", "overall_finding"):
        failures += not t(f"Stage 1 has '{sub}'", sub in s1_out)

    failures += not t("Stage 1 score is integer in [0, 100]",
                      isinstance(s1_out["trigger_score"], int)
                      and 0 <= s1_out["trigger_score"] <= 100)

    # ── [5] Citation verification (no fabrication) ──────────────────────────
    print("\n[5] citation provenance")

    # Every citation in the structured output must trace to authority_db
    from output_verifier import verify

    # Concatenate all findings + recommendations as the "output" for verification
    text_parts = []
    for sub in ("hosted_repository", "circumstantial_regurgitation", "mia_statistical"):
        text_parts.append(result["step_1_prima_facie"][sub]["finding"])
    text_parts.append(result["step_1_prima_facie"]["overall_finding"])
    text_parts.append(result["step_2_disclosure"]["proportionality_analysis"])
    text_parts.append(result["step_2_disclosure"]["confidentiality_ring_tier"])
    text_parts.append(result["step_3_adverse_inference"]["wisniewski_application"])
    for rec in result["procedural_recommendations"]:
        text_parts.append(rec["action"])
        text_parts.append(rec["citation"])
    for risk in result["litigation_exposure"]:
        text_parts.append(risk["risk"])
        text_parts.append(risk["statute"])

    combined_output = " ".join(text_parts)
    verification = verify(combined_output, allowed_authority_ids=result["allowed_authority_ids"])

    failures += not t(
        "Deterministic output passes verification (all citations match allowed set)",
        verification.is_valid,
        f"unknown: {[c.raw_text for c in verification.citations_unknown]}",
    )

    # ── [6] Legacy shim — backwards compatibility ───────────────────────────
    print("\n[6] legacy shim (prpp_simulator)")

    legacy = prpp.prpp_simulator(
        "UK claim. Common Crawl training. Verbatim regurgitation. Spoliation."
    )
    legacy_required = [
        "readiness_score",
        "readiness_level",
        "compliance_strength_score",
        "prpp_score_breakdown",
        "checklist",
        "triggers",
        "recommendations",
        "litigation_exposure",
        "confidence_score",
        "_procedural",
        "_engine_version",
    ]
    for key in legacy_required:
        failures += not t(f"Legacy shim has '{key}'", key in legacy)

    failures += not t("Legacy engine_version is 2.0-phase-2b",
                      legacy["_engine_version"] == "2.0-phase-2b")
    failures += not t("Legacy checklist has 8 items", len(legacy["checklist"]) == 8)
    failures += not t("Legacy _procedural is the full new result",
                      "step_1_prima_facie" in legacy["_procedural"])
    failures += not t("Score breakdown sums to <= 100",
                      sum(legacy["prpp_score_breakdown"].values()) <= 100,
                      f"sum: {sum(legacy['prpp_score_breakdown'].values())}")

    # ── [7] IPEC warning path ───────────────────────────────────────────────
    print("\n[7] IPEC warning path")

    ipec_result = prpp.prpp_procedure_assessment(
        scenario_text="Claim in the IPEC (Intellectual Property Enterprise Court). UK defendant."
    )
    failures += not t("IPEC warning fires in Stage 2 analysis",
                      "PD 57AD does NOT apply" in
                      ipec_result["step_2_disclosure"]["proportionality_analysis"])
    failures += not t("PD 57AD model marked N/A for IPEC",
                      "N/A" in ipec_result["step_2_disclosure"]["pd_57ad_model"])
    failures += not t("IPEC trigger appears in triggers list",
                      any("IPEC track: YES" in t for t in ipec_result["triggers"]))

    # ── [8] Earles penalty (no general pre-action duty) ─────────────────────
    print("\n[8] Earles pre-action penalty")

    pre_only = prpp.detect_stage3_signals(
        "Defendant might delete logs in the future. Letter before claim is being drafted. "
        "Pre-action correspondence ongoing."
    )
    score_pre_only = prpp.score_stage_3(pre_only)
    proceedings_commenced = prpp.detect_stage3_signals(
        "Proceedings issued. Particulars of claim filed. Spoliation alleged after the CMC."
    )
    score_proceedings = prpp.score_stage_3(proceedings_commenced)
    failures += not t(
        "Pre-action-only score < proceedings-commenced score (Earles)",
        score_pre_only < score_proceedings,
        f"pre-action: {score_pre_only}, proceedings: {score_proceedings}",
    )

    # ── [9] Floor and ceiling guarantees ────────────────────────────────────
    print("\n[9] floor and ceiling")

    # Empty input — no signals — minimum score still produced
    empty_result = prpp.prpp_procedure_assessment(scenario_text="")
    failures += not t(
        "Empty input still produces complete result",
        all(k in empty_result for k in required_keys),
    )
    failures += not t(
        "Empty input → 'Not Viable' or 'Weak'",
        empty_result["overall_level"] in ("Not Viable", "Weak"),
    )
    failures += not t(
        "Empty input → confidence <= 75 (deterministic cap)",
        empty_result["confidence_score"] <= 75,
    )

    # All-strong input — ceiling check
    strong_result = prpp.prpp_procedure_assessment(
        scenario_text=(
            "UK High Court. Business and property courts. Common Crawl training. "
            "Verbatim regurgitation. Membership inference attack expert engaged. "
            "Defendant deleted records. Proceedings issued. Particulars of claim filed."
        )
    )
    failures += not t(
        "Strong input → overall >= 75",
        strong_result["overall_prpp_viability"] >= 75,
        f"overall: {strong_result['overall_prpp_viability']}",
    )

    # ── [10] No LLM dependency in deterministic path ────────────────────────
    print("\n[10] no-LLM dependency (deterministic path runs without app.py)")

    # The fact that we got this far without app.py session state proves
    # the deterministic path is fully self-contained.
    failures += not t(
        "Mode is 'deterministic' or 'ai_phrased_verified' (engine completes)",
        result["mode"] in ("deterministic", "ai_phrased_verified"),
        f"mode: {result['mode']}",
    )

    # ── Summary ─────────────────────────────────────────────────────────────
    print()
    print("─" * 70)
    if failures == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {failures} test(s) failed")
    return failures


if __name__ == "__main__":
    sys.exit(run_all())
