"""
Phase 2C-fix regression test — authority-ID leak prevention.

Background
──────────
The first deployment of trademark_v2.py produced an opinion containing the
literal string "[CASE_LIDL_V_TESCO_2024]" — the internal authority ID had
leaked from the LLM prompt into the user-facing output text. The LLM
(Mistral 7B) saw the ID in the "ALLOWED AUTHORITIES" block of the prompt
and copied it verbatim.

Two defensive layers were added:
  1. authorities_to_prompt_block() no longer exposes internal IDs to the LLM
  2. output_verifier.verify() now rejects any output containing the pattern
     CASE_*, STATUTE_*, RULE_*, REG_*, DIR_*, REPORT_*, or ACADEMIC_*

This test suite locks both layers in place so they cannot regress silently.
Run: python test_phase_2c_fix.py
"""

import sys


def t(label: str, passed: bool, reason: str = "") -> bool:
    if passed:
        print(f"  ✓ {label}" + (f" — {reason}" if reason else ""))
        return True
    print(f"  ✗ {label}" + (f" — {reason}" if reason else ""))
    return False


def run_all() -> int:
    failures = 0
    print("\nPhase 2C-fix — Authority-ID Leak Regression Tests")
    print("─" * 70)

    # ── [1] Prompt block does NOT expose internal IDs ───────────────────────
    print("\n[1] prompt block does not expose internal IDs to LLM")

    from authority_selector import authorities_to_prompt_block
    from authority_db import get

    sample = [
        get("CASE_LIDL_V_TESCO_2024"),
        get("CASE_SKY_V_SKYKICK_2024"),
        get("STATUTE_TMA_S10_2"),
        get("RULE_PD_57AD"),
    ]
    sample = [a for a in sample if a is not None]
    block = authorities_to_prompt_block(sample)

    forbidden_id_strings = [
        "CASE_LIDL_V_TESCO_2024",
        "CASE_SKY_V_SKYKICK_2024",
        "STATUTE_TMA_S10_2",
        "RULE_PD_57AD",
        "[CASE_",
        "[STATUTE_",
        "[RULE_",
        "_2024]",
        "_2024 ",
    ]
    for f in forbidden_id_strings:
        failures += not t(
            f"Prompt block does NOT contain '{f}'",
            f not in block,
        )

    # But it SHOULD contain the human-facing forms
    failures += not t(
        "Prompt block DOES contain 'Lidl v Tesco' (short form)",
        "Lidl v Tesco" in block,
    )
    failures += not t(
        "Prompt block DOES contain '[2024] UKSC 36' (correct SkyKick citation)",
        "[2024] UKSC 36" in block,
    )
    failures += not t(
        "Prompt block DOES contain a recognisable section title",
        "AVAILABLE AUTHORITIES" in block,
    )

    # ── [2] Verifier rejects raw authority-ID leaks ─────────────────────────
    print("\n[2] verifier rejects raw authority-ID leaks")

    from output_verifier import verify

    # Output with a leaked ID (the actual bug from the field)
    bug_output = (
        "If there are concerns about bad-faith filings or unfair advantage "
        "applications, consult case law such as Lidl v Tesco "
        "([CASE_LIDL_V_TESCO_2024]) for guidance."
    )
    rep = verify(bug_output, allowed_authority_ids=["CASE_LIDL_V_TESCO_2024"])
    failures += not t(
        "Output containing [CASE_LIDL_V_TESCO_2024] is REJECTED",
        not rep.is_valid,
    )
    failures += not t(
        "Rejection reason mentions 'authority ID'",
        "authority ID" in rep.reason.lower() or "internal identifier" in rep.reason.lower(),
    )

    # Variations of the leak pattern
    leak_variations = [
        "See CASE_LIDL_V_TESCO_2024 for the test.",
        "Per STATUTE_CDPA_S29A this is the rule.",
        "Cited authority: RULE_PD_57AD.",
        "Background: REPORT_UK_MAR2026_COPYRIGHT_AI.",
        "Reference DIR_DSM_ART_4 in the opinion.",
        "See REG_EU_AI_ACT_ART_53 for the EU position.",
        "Methodology from ACADEMIC_AHMED_EXTRACTION_2026.",
    ]
    for variation in leak_variations:
        rep = verify(variation, allowed_authority_ids=None)
        failures += not t(
            f"Verifier rejects: '{variation[:50]}...'",
            not rep.is_valid,
        )

    # Clean output (no leak) should still verify
    clean_output = (
        "If there are concerns about bad-faith filings, consult Lidl v Tesco "
        "[2024] EWCA Civ 262 for guidance on the unfair-advantage test."
    )
    rep_clean = verify(clean_output, allowed_authority_ids=["CASE_LIDL_V_TESCO_2024"])
    failures += not t(
        "Clean output (citation form, no IDs) PASSES verification",
        rep_clean.is_valid,
    )

    # ── [3] End-to-end trademark opinion contains no IDs ────────────────────
    print("\n[3] end-to-end trademark opinion is leak-free")

    import trademark_v2 as tm

    # Try several profiles, including the famous-mark case that triggered the bug
    test_profiles = [
        ("BURRBERY", "25", "Clothing", [
            {"mark": "BURBERRY", "owner": "Burberry Ltd", "niceClass": "25", "conflict_score": 95},
            {"mark": "BURBERY", "owner": "Burberry Ltd", "niceClass": "25", "conflict_score": 88},
        ], []),
        ("XYZZQVOR", "42", "Software", [], []),
        ("LINNEBORG", "9", "Electronics", [
            {"mark": "LINNE", "conflict_score": 60},
            {"mark": "BORG", "conflict_score": 55},
        ], []),
        ("SMOOTH COFFEE", "30", "Coffee", [
            {"mark": "SMOOTH", "conflict_score": 72},
        ], []),
    ]

    for mark, cls, desc, ukipo, dil in test_profiles:
        opinion = tm.generate_trademark_opinion(mark, cls, desc, ukipo, dil)
        # No IDs in the deterministic template
        for prefix in ["CASE_", "STATUTE_", "RULE_", "REG_", "DIR_", "REPORT_", "ACADEMIC_"]:
            failures += not t(
                f"Opinion for '{mark}' contains no '{prefix}*' IDs",
                prefix not in opinion,
                f"Leaked: {prefix}... found in opinion" if prefix in opinion else "",
            )
        # And no wrong SkyKick citation
        failures += not t(
            f"Opinion for '{mark}' has no '[2020] UKSC 17'",
            "[2020] UKSC 17" not in opinion,
        )

    # ── [4] Direct test of generate_trademark_opinion's deterministic path ──
    print("\n[4] deterministic trademark opinion is leak-free under stress")

    # 20 stress profiles
    leak_count = 0
    wrong_citation_count = 0
    for n_conflicts in range(0, 5):
        for score in [50, 75, 85, 95]:
            profile = tm.compute_trademark_risk(
                your_mark=f"STRESS{n_conflicts}",
                nice_class="35",
                description="Stress test goods",
                ukipo_results=[
                    {"mark": f"COMP{i}", "owner": "Owner", "niceClass": "35",
                     "conflict_score": score}
                    for i in range(n_conflicts)
                ],
                dilution_rows=[],
            )
            ids = tm.select_authorities_for_trademark(profile)
            opinion = tm.render_deterministic_opinion(profile, ids)
            for prefix in ["CASE_", "STATUTE_", "RULE_", "REG_"]:
                if prefix in opinion:
                    leak_count += 1
                    break
            if "[2020] UKSC 17" in opinion:
                wrong_citation_count += 1

    failures += not t(
        "20 stress profiles — zero contain raw authority IDs",
        leak_count == 0,
        f"leaks: {leak_count}",
    )
    failures += not t(
        "20 stress profiles — zero contain wrong SkyKick citation",
        wrong_citation_count == 0,
        f"wrongs: {wrong_citation_count}",
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
