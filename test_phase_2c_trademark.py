"""
Phase 2C test suite — refactored Trademark clearance opinion engine.

Verifies:
  1. Risk profile computation (pure functions)
  2. Authority selection
  3. Deterministic opinion template
  4. CRITICAL: Sky v SkyKick [2020] UKSC 17 wrong citation is gone
  5. Citation provenance (verifier passes)
  6. Backwards compatibility
  7. Edge cases: HIGH/MEDIUM/LOW, empty, famous-mark threshold

Run: python test_phase_2c_trademark.py
"""

import sys
import trademark_v2 as tm


def t(label: str, passed: bool, reason: str = "") -> bool:
    if passed:
        print(f"  ✓ {label}" + (f" — {reason}" if reason else ""))
        return True
    print(f"  ✗ {label}" + (f" — {reason}" if reason else ""))
    return False


def test_dilution_only_conflict_burrbery():
    """
    Regression: BURRBERY case — live API returns nothing, but the dilution
    scanner finds BURBERRY at 90.3%. The opinion must (a) report HIGH risk,
    (b) keep the applied-for mark as BURRBERY (never substitute the conflict),
    (c) list the dilution conflict rather than 'no conflicts', and (d) cite
    the correct SkyKick [2024] UKSC 36.
    """
    from trademark_v2 import (
        compute_trademark_risk, render_deterministic_opinion,
        select_authorities_for_trademark,
    )
    prof = compute_trademark_risk(
        "BURRBERY", "25", "Clothing, footwear, headgear",
        ukipo_results=[],
        dilution_rows=[{"mark": "BURBERRY", "dilution_score": 90.3,
                        "competitor": "BURBERRY"}],
    )
    op = render_deterministic_opinion(prof, select_authorities_for_trademark(prof))
    checks = [
        ("Dilution-only conflict → HIGH risk", prof.overall_risk_level == "HIGH"),
        ("Applied-for mark stays BURRBERY", prof.your_mark == "BURRBERY"),
        ("Opinion titled with BURRBERY", "BURRBERY" in op.split("\n")[0]),
        ("BURBERRY listed as the conflict", "BURBERRY" in op),
        ("Not reported as 'no conflicts'", "No high-risk conflicts identified" not in op),
        ("Correct SkyKick [2024] UKSC 36", "[2024] UKSC 36" in op),
        ("Wrong [2020] UKSC 17 absent", "[2020] UKSC 17" not in op),
    ]
    print("\n[9] BURRBERY dilution-only regression")
    failed = 0
    for label, ok in checks:
        print(f"  {'✓' if ok else '✗'} {label}")
        failed += not ok
    return failed


def run_all() -> int:
    failures = 0
    print("\nPhase 2C — Trademark Engine Refactor — Integration Tests")
    print("─" * 70)

    # ── [1] Risk profile computation ────────────────────────────────────────
    print("\n[1] risk profile computation")

    profile_high = tm.compute_trademark_risk(
        your_mark="BURRBERY",
        nice_class="25",
        description="Clothing",
        ukipo_results=[
            {"mark": "BURBERRY", "owner": "Burberry Ltd", "niceClass": "25", "conflict_score": 95},
            {"mark": "BURBERY", "owner": "Burberry Ltd", "niceClass": "25", "conflict_score": 88},
        ],
        dilution_rows=[],
    )
    failures += not t("HIGH risk profile when 2+ high conflicts",
                      profile_high.overall_risk_level == "HIGH")
    failures += not t("Famous-mark threshold detected (>85 score)",
                      profile_high.famous_mark_present)
    failures += not t("high_risk_count = 2",
                      profile_high.high_risk_count == 2)

    profile_medium = tm.compute_trademark_risk(
        your_mark="LINNEBORG",
        nice_class="9",
        description="Software",
        ukipo_results=[
            {"mark": "LINNE", "conflict_score": 60},
            {"mark": "BORG", "conflict_score": 55},
            {"mark": "LINEBOR", "conflict_score": 70},
            {"mark": "BORGLIN", "conflict_score": 50},
        ],
        dilution_rows=[],
    )
    failures += not t("MEDIUM risk when no high conflicts but >3 total",
                      profile_medium.overall_risk_level == "MEDIUM")

    profile_low = tm.compute_trademark_risk(
        your_mark="XYZZQX", nice_class="42", description="Cloud services",
        ukipo_results=[], dilution_rows=[],
    )
    failures += not t("LOW risk when no conflicts",
                      profile_low.overall_risk_level == "LOW")
    failures += not t("Recommendation 'Proceed to file' for LOW risk",
                      profile_low.recommendation == "Proceed to file")
    failures += not t("Famous-mark NOT present for LOW risk",
                      not profile_low.famous_mark_present)

    # ── [2] Authority selection ─────────────────────────────────────────────
    print("\n[2] authority selection")

    ids_high = tm.select_authorities_for_trademark(profile_high)
    failures += not t("Authority IDs returned", len(ids_high) >= 4)
    failures += not t("TMA s.10(2) in allowed",
                      "STATUTE_TMA_S10_2" in ids_high)
    failures += not t("TMA s.10(3) in allowed",
                      "STATUTE_TMA_S10_3" in ids_high)
    failures += not t("Sky v SkyKick 2024 in allowed (famous-mark profile)",
                      "CASE_SKY_V_SKYKICK_2024" in ids_high)
    failures += not t("Lidl v Tesco in allowed",
                      "CASE_LIDL_V_TESCO_2024" in ids_high)
    failures += not t("Old wrong Sky v SkyKick 2020 ID NOT in allowed",
                      "CASE_SKY_V_SKYKICK_2020" not in ids_high)

    # ── [3] Deterministic opinion template ──────────────────────────────────
    print("\n[3] deterministic opinion template")

    opinion = tm.render_deterministic_opinion(profile_high, ids_high)
    failures += not t("Opinion is non-empty", len(opinion) > 1500)
    failures += not t("Opinion has 7 numbered sections",
                      all(f"{n}." in opinion for n in range(1, 8)))
    failures += not t("Opinion has EXECUTIVE SUMMARY",
                      "EXECUTIVE SUMMARY" in opinion)
    failures += not t("Opinion has FILING RECOMMENDATION",
                      "FILING RECOMMENDATION" in opinion)
    failures += not t("Opinion mentions the mark",
                      "BURRBERY" in opinion)
    failures += not t("Opinion mentions Nice Class",
                      "Class 25" in opinion)

    # ── [4] CRITICAL — wrong Sky v SkyKick citation is structurally absent ──
    print("\n[4] CRITICAL: wrong Sky v SkyKick [2020] UKSC 17 is structurally impossible")

    failures += not t(
        "Wrong citation '[2020] UKSC 17' is NOT in opinion",
        "[2020] UKSC 17" not in opinion,
    )
    failures += not t(
        "Correct citation '[2024] UKSC 36' IS in opinion",
        "[2024] UKSC 36" in opinion,
    )

    # Generate 100 opinions with varied inputs - none can contain the wrong citation
    found_wrong_citation = False
    for n_conflicts in range(0, 5):
        for score in [50, 75, 85, 95]:
            test_profile = tm.compute_trademark_risk(
                your_mark=f"TESTMARK{n_conflicts}",
                nice_class="35",
                description="Test goods",
                ukipo_results=[
                    {"mark": f"COMP{i}", "owner": "Owner", "niceClass": "35",
                     "conflict_score": score}
                    for i in range(n_conflicts)
                ],
                dilution_rows=[],
            )
            test_ids = tm.select_authorities_for_trademark(test_profile)
            test_opinion = tm.render_deterministic_opinion(test_profile, test_ids)
            if "[2020] UKSC 17" in test_opinion:
                found_wrong_citation = True
                break
        if found_wrong_citation:
            break
    failures += not t(
        "20 varied test profiles — none contain the wrong citation",
        not found_wrong_citation,
    )

    # ── [5] Citation provenance (no fabrication) ────────────────────────────
    print("\n[5] citation provenance")

    from output_verifier import verify
    verification = verify(opinion, allowed_authority_ids=ids_high)

    failures += not t(
        "All citations in opinion match allowed authorities",
        verification.is_valid,
        f"unknown: {[c.raw_text for c in verification.citations_unknown]}",
    )
    failures += not t(
        "At least 3 citations detected",
        len(verification.citations_found) >= 3,
        f"count: {len(verification.citations_found)}",
    )

    # ── [6] End-to-end via generate_trademark_opinion ───────────────────────
    print("\n[6] end-to-end generate_trademark_opinion")

    full_opinion = tm.generate_trademark_opinion(
        your_mark="BURRBERY",
        nice_class="25",
        description="Clothing and apparel",
        ukipo_results=[
            {"mark": "BURBERRY", "owner": "Burberry Ltd", "niceClass": "25", "conflict_score": 95},
        ],
        dilution_rows=[{"name": "BURBERRY HERITAGE", "dilution_score": 92}],
    )
    failures += not t("End-to-end opinion produced",
                      isinstance(full_opinion, str) and len(full_opinion) > 1500)
    failures += not t("End-to-end opinion has correct SkyKick citation",
                      "[2024] UKSC 36" in full_opinion)
    failures += not t("End-to-end opinion has NO wrong SkyKick citation",
                      "[2020] UKSC 17" not in full_opinion)

    # ── [7] Backwards-compatibility alias ───────────────────────────────────
    print("\n[7] backwards-compatibility alias")

    legacy_opinion = tm.generate_trademark_ai_opinion(
        "BURRBERY", "25", "Clothing",
        [{"mark": "BURBERRY", "owner": "Burberry Ltd", "niceClass": "25",
          "conflict_score": 95}],
        [],
    )
    failures += not t("Legacy alias produces output",
                      isinstance(legacy_opinion, str) and len(legacy_opinion) > 1500)
    failures += not t("Legacy alias output also has correct citation",
                      "[2024] UKSC 36" in legacy_opinion)

    # ── [8] Edge cases ──────────────────────────────────────────────────────
    print("\n[8] edge cases")

    empty_profile = tm.compute_trademark_risk(
        your_mark="", nice_class="", description="",
        ukipo_results=[], dilution_rows=[],
    )
    failures += not t("Empty inputs → conflict_count 0",
                      empty_profile.conflict_count == 0)
    failures += not t("Empty inputs → LOW risk",
                      empty_profile.overall_risk_level == "LOW")

    empty_opinion = tm.render_deterministic_opinion(
        empty_profile,
        tm.select_authorities_for_trademark(empty_profile),
    )
    failures += not t("Empty opinion still has 7 sections",
                      all(f"{n}." in empty_opinion for n in range(1, 8)))
    failures += not t("Empty opinion has no wrong citation",
                      "[2020] UKSC 17" not in empty_opinion)

    # ── [9] BURRBERY dilution-only regression ───────────────────────────────
    failures += test_dilution_only_conflict_burrbery()

    # ── [10] determinism: identical input → byte-identical output ────────────
    print("\n[10] determinism (reproducibility)")
    det_args = ("BURRBERRY", "25", "Clothing, footwear, headgear",
                [{"mark": "BURBERRY", "owner": "Burberry Limited", "class": "25"}],
                [{"competitor": "BURBERRY", "dilution_score": 80, "risk_category": "High"}])
    runs = [tm.generate_trademark_opinion(*det_args) for _ in range(3)]
    failures += not t("Three runs of identical input are byte-identical",
                      runs[0] == runs[1] == runs[2])
    failures += not t("Deterministic opinion preserves the applied-for mark",
                      "BURRBERRY" in runs[0])
    failures += not t("Deterministic opinion uses correct SkyKick citation",
                      "[2024] UKSC 36" in runs[0] and "[2020] UKSC 17" not in runs[0])

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
