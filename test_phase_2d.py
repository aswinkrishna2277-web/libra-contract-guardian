"""
Phase 2D test suite — analysis citation sanitiser.

Verifies:
  1. Verified citations pass through untouched
  2. Fabricated citations are flagged (not silently kept)
  3. Internal-ID leaks are stripped
  4. Per-clause statute_citations are checked
  5. red_flags / immediate_actions prose is annotated when citations fail
  6. A citation_verification audit block is always attached
  7. Empty / malformed input is handled safely

Run: python test_phase_2d.py
"""

import sys
from analysis_sanitiser import sanitise_analysis


def t(label: str, passed: bool, reason: str = "") -> bool:
    if passed:
        print(f"  ✓ {label}" + (f" — {reason}" if reason else ""))
        return True
    print(f"  ✗ {label}" + (f" — {reason}" if reason else ""))
    return False


def run_all() -> int:
    failures = 0
    print("\nPhase 2D — Analysis Citation Sanitiser — Tests")
    print("─" * 70)

    # ── [1] Verified citations pass through ─────────────────────────────────
    print("\n[1] verified citations pass through untouched")

    parsed = {
        "legal_references": [
            "CDPA 1988 s.29A",
            "Wisniewski v Central Manchester HA [1998] EWCA Civ 596",
        ],
        "red_flags": ["No provenance warranty present"],
    }
    out, rep = sanitise_analysis(parsed)
    failures += not t("Verified references retained",
                      len(out["legal_references"]) == 2,
                      f"kept: {out['legal_references']}")
    failures += not t("No citations flagged for valid refs",
                      rep.citations_flagged == 0)
    failures += not t("citation_verification block attached",
                      "citation_verification" in out)

    # ── [2] Fabricated citations are flagged ────────────────────────────────
    print("\n[2] fabricated citations flagged, not silently kept")

    parsed = {
        "legal_references": [
            "CDPA 1988 s.29A",                              # real
            "Fictional v Imaginary [2099] UKSC 999",        # fabricated
        ],
    }
    out, rep = sanitise_analysis(parsed)
    failures += not t("At least one citation flagged",
                      rep.citations_flagged >= 1,
                      f"flagged: {rep.citations_flagged}")
    failures += not t("Fabricated citation removed from legal_references",
                      "Fictional v Imaginary [2099] UKSC 999" not in out["legal_references"])
    failures += not t("Real citation retained",
                      "CDPA 1988 s.29A" in out["legal_references"])
    failures += not t("Fabricated citation moved to unverified_citations",
                      "unverified_citations" in out
                      and any("Fictional" in c or "2099" in c
                              for c in out["unverified_citations"]))

    # ── [3] Internal-ID leaks stripped ──────────────────────────────────────
    print("\n[3] internal-ID leaks stripped")

    parsed = {
        "legal_references": ["CDPA 1988 s.29A"],
        "red_flags": [
            "See CASE_LIDL_V_TESCO_2024 for guidance on unfair advantage",
        ],
        "immediate_actions": [
            "Review under STATUTE_CDPA_S16 obligations",
        ],
    }
    out, rep = sanitise_analysis(parsed)
    failures += not t("ID leaks detected and counted",
                      rep.id_leaks_removed >= 2,
                      f"removed: {rep.id_leaks_removed}")
    failures += not t("CASE_ id removed from red_flags",
                      not any("CASE_LIDL" in s for s in out["red_flags"]))
    failures += not t("STATUTE_ id removed from immediate_actions",
                      not any("STATUTE_CDPA" in s for s in out["immediate_actions"]))

    # ── [4] Per-clause statute_citations checked ────────────────────────────
    print("\n[4] per-clause statute_citations checked")

    parsed = {
        "detailed_clauses": [
            {
                "excerpt": "The licensee may train models on the dataset.",
                "statute_citations": [
                    "CDPA 1988 s.29A",                      # real
                    "Made Up Act 2050 s.999",               # fabricated
                ],
                "analysis": "Risk under CASE_GETTY_V_STABILITY_2025 applies.",
            }
        ],
    }
    out, rep = sanitise_analysis(parsed)
    clause = out["detailed_clauses"][0]
    failures += not t("Fabricated clause citation removed",
                      "Made Up Act 2050 s.999" not in clause["statute_citations"])
    failures += not t("Real clause citation retained",
                      "CDPA 1988 s.29A" in clause["statute_citations"])
    failures += not t("ID leak stripped from clause analysis text",
                      "CASE_GETTY" not in clause["analysis"])

    # ── [5] Prose annotated when embedded citation fails ────────────────────
    print("\n[5] prose with failing citation annotated")

    parsed = {
        "red_flags": [
            "Clause breaches Nonexistent v Fake [2088] EWHC 1 (Ch)",
        ],
    }
    out, rep = sanitise_analysis(parsed)
    failures += not t("Failing-citation prose annotated with warning",
                      any("unverified" in s.lower() for s in out["red_flags"]),
                      f"got: {out['red_flags']}")

    # ── [6] Audit block always present and accurate ─────────────────────────
    print("\n[6] audit block accuracy")

    parsed = {
        "legal_references": ["CDPA 1988 s.16", "TMA 1994 s.10(2)"],
    }
    out, rep = sanitise_analysis(parsed)
    cv = out["citation_verification"]
    failures += not t("Audit reports checked count",
                      cv["checked"] == 2, f"checked: {cv['checked']}")
    failures += not t("Audit reports verified count",
                      cv["verified"] == 2, f"verified: {cv['verified']}")
    failures += not t("Audit reports zero flagged for valid input",
                      cv["flagged"] == 0)
    failures += not t("Audit has explanatory notes",
                      len(cv["notes"]) >= 1)

    # ── [7] Empty / malformed input handled ─────────────────────────────────
    print("\n[7] empty / malformed input")

    out, rep = sanitise_analysis({})
    failures += not t("Empty dict → no crash, audit attached",
                      "citation_verification" in out)

    out2, rep2 = sanitise_analysis({"legal_references": "not a list"})
    failures += not t("Malformed field → no crash",
                      "citation_verification" in out2)

    out3, rep3 = sanitise_analysis(None)
    failures += not t("None input → returned safely",
                      out3 is None)

    # ── [8] Mixed real + fake + leak in one pass ────────────────────────────
    print("\n[8] realistic mixed payload")

    parsed = {
        "legal_references": [
            "CDPA 1988 s.29A",                          # real
            "EU AI Act Art. 53",                        # real
            "Phantom v Ghost [2077] UKSC 1",            # fake
            "RULE_PD_57AD",                             # ID leak
        ],
        "red_flags": [
            "Output may infringe under CDPA 1988 s.16",  # real embedded
            "See REPORT_UK_MAR2026_COPYRIGHT_AI",        # ID leak
        ],
        "detailed_clauses": [
            {"statute_citations": ["DSM Directive Art. 4", "Fake Law 2099"]},
        ],
    }
    out, rep = sanitise_analysis(parsed)
    failures += not t("Real refs survive the mixed pass",
                      "CDPA 1988 s.29A" in out["legal_references"]
                      and "EU AI Act Art. 53" in out["legal_references"])
    failures += not t("Fake ref flagged in mixed pass",
                      rep.citations_flagged >= 1)
    failures += not t("ID leaks removed in mixed pass",
                      rep.id_leaks_removed >= 1)
    failures += not t("Clause real citation kept, fake dropped",
                      "DSM Directive Art. 4" in out["detailed_clauses"][0]["statute_citations"]
                      and "Fake Law 2099" not in out["detailed_clauses"][0]["statute_citations"])

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
