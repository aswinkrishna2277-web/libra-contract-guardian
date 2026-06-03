"""
Phase 2C test suite — refactored TDM (Text & Data Mining) engine.

Verifies:
  1. Signal detection (risk + mitigation, pure functions)
  2. Deterministic scoring
  3. Authority selection
  4. Structured rendering (every citation from authority DB)
  5. Citation provenance (output verifier passes)
  6. Backwards compatibility with v1 output shape
  7. Edge cases: high-risk, protective, empty, mixed

Run: python test_phase_2c.py
"""

import sys
import tdm


def t(label: str, passed: bool, reason: str = "") -> bool:
    if passed:
        print(f"  ✓ {label}" + (f" — {reason}" if reason else ""))
        return True
    print(f"  ✗ {label}" + (f" — {reason}" if reason else ""))
    return False


def run_all() -> int:
    failures = 0
    print("\nPhase 2C — TDM Engine Refactor — Integration Tests")
    print("─" * 70)

    # ── [1] Signal detection ────────────────────────────────────────────────
    print("\n[1] signal detection")

    sig = tdm.detect_tdm_signals(
        "The licensed dataset may be used for model training and TDM purposes. "
        "Scraping from Common Crawl is permitted."
    )
    failures += not t("Risk findings detected", len(sig.risk_findings) >= 3)
    failures += not t(
        "TDM trigger captured (highest-weight term)",
        any(term == "tdm" for term, _, _, _ in sig.risk_findings),
    )
    failures += not t("Scraping clause detected", sig.scraping_clause)
    failures += not t("Training rights undefined when not excluded",
                      sig.training_rights_undefined)

    sig_protective = tdm.detect_tdm_signals(
        "The dataset shall not be used for training. TDM exclusion applies. "
        "Provenance schedule attached. Audit rights granted. "
        "Licensor warrants lawfully obtained material. "
        "Machine-readable reservation respected per Art. 4(3)."
    )
    failures += not t("Multiple mitigations detected",
                      len(sig_protective.mitigation_findings) >= 4,
                      f"count: {len(sig_protective.mitigation_findings)}")
    failures += not t("Mitigation includes TDM exclusion",
                      any("TDM expressly excluded" == desc
                          for _, _, desc in sig_protective.mitigation_findings))

    sig_empty = tdm.detect_tdm_signals("")
    failures += not t("Empty input → no risk findings",
                      len(sig_empty.risk_findings) == 0)
    failures += not t("Empty input → no mitigation findings",
                      len(sig_empty.mitigation_findings) == 0)

    # ── [2] Deterministic scoring ───────────────────────────────────────────
    print("\n[2] deterministic scoring")

    # High-risk contract scores
    sig_high = tdm.detect_tdm_signals(
        "Training data, dataset, TDM, model training, scraping, machine learning."
    )
    scores_high = tdm.score_tdm(sig_high, has_substantive_text=True)
    failures += not t(
        "High-risk contract → score >= 50",
        scores_high.risk_score >= 50,
        f"score: {scores_high.risk_score}",
    )
    failures += not t(
        "High-risk → risk_level High or Critical",
        scores_high.risk_level in ("High", "Critical"),
    )

    # Protective contract scores
    sig_safe = tdm.detect_tdm_signals(
        "The dataset shall not be used for training. TDM exclusion. "
        "Provenance warranty. Audit rights. Machine-readable reservation."
    )
    scores_safe = tdm.score_tdm(sig_safe, has_substantive_text=True)
    failures += not t(
        "Protective contract → score < 25",
        scores_safe.risk_score < 25,
        f"score: {scores_safe.risk_score}",
    )
    failures += not t(
        "Protective → risk_level Low",
        scores_safe.risk_level == "Low",
    )

    # Empty input scores
    scores_empty = tdm.score_tdm(
        tdm.detect_tdm_signals(""),
        has_substantive_text=False,
    )
    failures += not t("Empty → risk 0", scores_empty.risk_score == 0)
    failures += not t("Empty → level N/A", scores_empty.risk_level == "N/A")
    failures += not t("Empty → compliance 0 (not misleading 100%)",
                      scores_empty.compliance_strength == 0)

    # Mitigation reduces the raw risk
    sig_mixed = tdm.detect_tdm_signals(
        "Training data; dataset; TDM. But TDM exclusion applies and audit rights granted."
    )
    scores_mixed = tdm.score_tdm(sig_mixed, has_substantive_text=True)
    failures += not t(
        "Mixed contract → mitigation reduces score below raw",
        scores_mixed.risk_score < scores_mixed.raw_risk,
        f"raw: {scores_mixed.raw_risk}, final: {scores_mixed.risk_score}",
    )

    # ── [3] Authority selection ─────────────────────────────────────────────
    print("\n[3] authority selection")

    sig = tdm.detect_tdm_signals("Training data. Dataset. AI training contract.")
    ids = tdm.select_authorities_for_tdm("Training data. Dataset. AI training contract.", sig)

    failures += not t("Authority IDs returned", len(ids) >= 5,
                      f"count: {len(ids)}")
    failures += not t("All IDs are strings",
                      all(isinstance(i, str) for i in ids))
    failures += not t("No duplicates", len(ids) == len(set(ids)))
    failures += not t("CDPA s.29A in allowed",
                      "STATUTE_CDPA_S29A" in ids)
    failures += not t("DSM Art. 4 in allowed",
                      "DIR_DSM_ART_4" in ids)
    failures += not t("EU AI Act in allowed",
                      "REG_EU_AI_ACT_ART_53" in ids)
    failures += not t("Getty or Kneschke in allowed (AI training cases)",
                      "CASE_GETTY_V_STABILITY_2025" in ids or
                      "CASE_KNESCHKE_V_LAION_2025" in ids)

    # ── [4] Structured render shape (v1 compatibility) ──────────────────────
    print("\n[4] structured render shape (v1 backwards compat)")

    result = tdm.tdm_risk_engine(
        "The Licensee may use the licensed dataset for training. "
        "Scraping from Common Crawl is permitted."
    )

    # v1 required keys
    v1_keys = [
        "mode",
        "risk_score",
        "risk_level",
        "compliance_strength_score",
        "tdm_issues",
        "mitigation_clauses_found",
        "scraping_clause_detected",
        "dataset_ownership_ambiguous",
        "training_rights_undefined",
        "provenance_tracking_absent",
        "semantic_dilution_risk",
        "litigation_risks",
        "legal_exposure_summary",
        "triggers",
        "recommendations",
        "confidence_score",
        "confidence_reasoning",
    ]
    for key in v1_keys:
        failures += not t(f"v1 key present: {key}", key in result)

    # v2 additions
    failures += not t("v2: mode is 'deterministic' or 'ai_phrased_verified'",
                      result["mode"] in ("deterministic", "ai_phrased_verified"))
    failures += not t("v2: allowed_authority_ids present",
                      "allowed_authority_ids" in result)

    # Types
    failures += not t("risk_score is int", isinstance(result["risk_score"], int))
    failures += not t("risk_score in [0, 100]",
                      0 <= result["risk_score"] <= 100)
    failures += not t("tdm_issues is list", isinstance(result["tdm_issues"], list))
    failures += not t("litigation_risks is list",
                      isinstance(result["litigation_risks"], list))
    failures += not t("recommendations is list",
                      isinstance(result["recommendations"], list))

    # ── [5] Citation provenance (no fabrication) ────────────────────────────
    print("\n[5] citation provenance")

    from output_verifier import verify

    text_parts = [result.get("legal_exposure_summary", "")]
    text_parts += [i.get("statute", "") for i in result["tdm_issues"]]
    text_parts += [i.get("detail", "") for i in result["tdm_issues"]]
    text_parts += [m.get("statute", "") for m in result["mitigation_clauses_found"]]
    text_parts += [r.get("statute", "") for r in result["litigation_risks"]]
    text_parts += [r.get("risk", "") for r in result["litigation_risks"]]
    text_parts += result["recommendations"]
    text_parts += result["triggers"]

    combined = " ".join(text_parts)
    verification = verify(combined, allowed_authority_ids=result["allowed_authority_ids"])

    failures += not t(
        "All output citations in allowed set (no fabrication)",
        verification.is_valid,
        f"unknown: {[c.raw_text for c in verification.citations_unknown]}",
    )

    failures += not t(
        "At least 5 citations actually detected in output",
        len(verification.citations_found) >= 5,
        f"count: {len(verification.citations_found)}",
    )

    # ── [6] High vs protective contract behaviour ───────────────────────────
    print("\n[6] high-risk vs protective contract")

    high = tdm.tdm_risk_engine(
        "Training data. Dataset. TDM operations. Model training permitted. "
        "Scraping from Common Crawl. Machine learning. No restrictions."
    )
    protective = tdm.tdm_risk_engine(
        "The dataset shall not be used for training, machine learning, or TDM. "
        "TDM exclusion. Training exclusion. Provenance schedule. Audit rights. "
        "Machine-readable reservation. Lawfully obtained warranty. "
        "CDPA s.29A compliance. DSM Directive Art. 4(3) opt-out."
    )

    failures += not t(
        "High-risk contract scores higher than protective",
        high["risk_score"] > protective["risk_score"],
        f"high: {high['risk_score']}, protective: {protective['risk_score']}",
    )
    failures += not t(
        "Protective contract has mitigation clauses listed",
        len(protective["mitigation_clauses_found"]) >= 4,
        f"count: {len(protective['mitigation_clauses_found'])}",
    )

    # ── [7] Empty-text guard ────────────────────────────────────────────────
    print("\n[7] empty-text guard")

    empty_result = tdm.tdm_risk_engine("")
    failures += not t("Empty → risk_score 0",
                      empty_result["risk_score"] == 0)
    failures += not t("Empty → risk_level 'N/A'",
                      empty_result["risk_level"] == "N/A")
    failures += not t("Empty → compliance 0 (not misleading 100%)",
                      empty_result["compliance_strength_score"] == 0)
    failures += not t("Empty → tdm_issues empty",
                      len(empty_result["tdm_issues"]) == 0)

    # ── [8] No-LLM dependency ───────────────────────────────────────────────
    print("\n[8] no-LLM dependency (deterministic path runs without app.py)")

    failures += not t(
        "Mode is 'deterministic' or 'ai_phrased_verified' (engine completes)",
        result["mode"] in ("deterministic", "ai_phrased_verified"),
        f"mode: {result['mode']}",
    )
    failures += not t(
        "Confidence capped at 68 for deterministic mode",
        result["confidence_score"] <= 68,
        f"confidence: {result['confidence_score']}",
    )

    # ── [9] DSM Art. 4 + Kneschke citations appear in DSM-relevant cases ────
    print("\n[9] EU-jurisdictional citations (DSM, Kneschke, AI Act)")

    eu_result = tdm.tdm_risk_engine(
        "The Licensor permits TDM under Article 4 DSM Directive. "
        "EU deployment contemplated. Machine-readable reservation respected."
    )
    # Look for Kneschke or DSM citations across the output
    all_text = " ".join(
        [r.get("statute", "") for r in eu_result["litigation_risks"]]
        + eu_result["recommendations"]
        + [eu_result.get("legal_exposure_summary", "")]
    )
    failures += not t("DSM citation appears in EU-relevant output",
                      "DSM" in all_text or "Directive 2019/790" in all_text)

    # ── [10] Cross-engine signal: analysis dict carries through ─────────────
    print("\n[10] cross-engine analysis dict integration")

    result_with_analysis = tdm.tdm_risk_engine(
        "Training data and dataset references.",
        analysis={"key_risk_areas": {"tdm_training_data": 60}},
    )
    failures += not t(
        "Analysis dict is accepted (no crash)",
        "risk_score" in result_with_analysis,
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
