"""
Test suite — trademark similarity module (the BURRBERY-gap fix).

Verifies:
  1. Edit distance / ratio (with and without rapidfuzz)
  2. Phonetic encoding catches the BURRBERY/BURBERRY case
  3. Containment signal
  4. Combined scoring + risk bands + the phonetic-identity booster
  5. The enrich_conflicts entry point fixes the zero-conflicts bug
  6. No false positives on unrelated marks
  7. Cross-class risk is correctly lower than same-class

Run: python test_trademark_similarity.py
"""

import sys
import trademark_similarity as ts


def t(label: str, passed: bool, reason: str = "") -> bool:
    if passed:
        print(f"  ✓ {label}" + (f" — {reason}" if reason else ""))
        return True
    print(f"  ✗ {label}" + (f" — {reason}" if reason else ""))
    return False


def run_all() -> int:
    failures = 0
    print("\nTrademark Similarity Module — Tests")
    print(f"(acceleration: {'rapidfuzz' if ts._HAS_RAPIDFUZZ else 'pure-Python'})")
    print("─" * 70)

    # ── [1] Edit distance ───────────────────────────────────────────────────
    print("\n[1] edit distance")
    failures += not t("Identical strings → distance 0",
                      ts.edit_distance("burberry", "burberry") == 0)
    failures += not t("One substitution → distance 1",
                      ts.edit_distance("cat", "bat") == 1)
    failures += not t("BURRBERY vs BURBERRY → distance 2",
                      ts.edit_distance("burrbery", "burberry") == 2,
                      f"actual: {ts.edit_distance('burrbery','burberry')}")
    failures += not t("Edit ratio identical = 1.0",
                      ts.edit_ratio("abc", "abc") == 1.0)
    failures += not t("Edit ratio empty vs nonempty = 0.0",
                      ts.edit_ratio("", "abc") == 0.0)
    failures += not t("Pure-Python fallback agrees with current backend",
                      ts._levenshtein_pure("burrbery", "burberry") == 2)

    # ── [2] Phonetic encoding ───────────────────────────────────────────────
    print("\n[2] phonetic encoding (the core of the fix)")
    code_a = ts._metaphone("BURRBERY")
    code_b = ts._metaphone("BURBERRY")
    failures += not t("BURRBERY and BURBERRY encode identically",
                      code_a == code_b,
                      f"{code_a} vs {code_b}")
    failures += not t("Phonetic ratio BURRBERY/BURBERRY = 1.0",
                      ts.phonetic_ratio("BURRBERY", "BURBERRY") == 1.0)
    failures += not t("GOOG3L and GOOGLE phonetically identical",
                      ts.phonetic_ratio("GOOG3L", "GOOGLE") == 1.0)
    failures += not t("Unrelated marks phonetically distant",
                      ts.phonetic_ratio("XYZQVOR", "BURBERRY") < 0.4)
    failures += not t("Empty inputs → phonetic ratio 1.0 (both empty)",
                      ts.phonetic_ratio("", "") == 1.0)

    # ── [3] Containment ─────────────────────────────────────────────────────
    print("\n[3] containment signal")
    failures += not t("SMOOTH inside SMOOTH COFFEE → containment > 0",
                      ts.containment_signal("smooth", "smooth coffee") > 0)
    failures += not t("Identical → containment 1.0",
                      ts.containment_signal("abc", "abc") == 1.0)
    failures += not t("Disjoint marks → containment 0",
                      ts.containment_signal("apple", "orange") == 0.0)

    # ── [4] Combined scoring + bands ────────────────────────────────────────
    print("\n[4] combined scoring + risk bands + booster")

    r_burr = ts.score_pair("BURRBERY", "BURBERRY", "25", "25")
    failures += not t("BURRBERY/BURBERRY same class → HIGH",
                      r_burr.risk_band == "HIGH",
                      f"score={r_burr.conflict_score} band={r_burr.risk_band}")

    r_goog = ts.score_pair("GOOG3L", "GOOGLE", "9", "9")
    failures += not t("GOOG3L/GOOGLE same class → HIGH (booster)",
                      r_goog.risk_band == "HIGH",
                      f"score={r_goog.conflict_score}")

    r_unrelated = ts.score_pair("XYZQVOR", "BURBERRY", "25", "25")
    failures += not t("Unrelated marks → MINIMAL (no false positive)",
                      r_unrelated.risk_band == "MINIMAL",
                      f"score={r_unrelated.conflict_score}")

    # Cross-class should score LOWER than same-class for identical marks
    r_same = ts.score_pair("BURBERRY", "BURBERRY", "25", "25")
    r_cross = ts.score_pair("BURBERRY", "BURBERRY", "25", "18")
    failures += not t("Identical mark: same-class scores higher than cross-class",
                      r_same.conflict_score > r_cross.conflict_score,
                      f"same={r_same.conflict_score} cross={r_cross.conflict_score}")

    failures += not t("Rationale is human-readable (non-empty)",
                      len(r_burr.rationale) > 10)
    failures += not t("Rationale mentions phonetic for BURRBERY",
                      "phonetic" in r_burr.rationale.lower())

    # ── [5] enrich_conflicts — the zero-conflicts bug fix ───────────────────
    print("\n[5] enrich_conflicts fixes the zero-conflicts bug")

    # The exact original failure: BURRBERY, class 25, ZERO live results
    result = ts.enrich_conflicts(
        proposed_mark="BURRBERY",
        proposed_class="25",
        live_results=[],
        uploaded_competitors=[],
    )
    failures += not t("BURRBERY with zero live results → at least 1 conflict",
                      len(result["conflicts"]) >= 1,
                      f"count: {len(result['conflicts'])}")
    failures += not t("The conflict is BURBERRY",
                      any(c["mark"] == "BURBERRY" for c in result["conflicts"]))
    failures += not t("BURBERRY conflict is HIGH risk",
                      any(c["mark"] == "BURBERRY" and c["risk_band"] == "HIGH"
                          for c in result["conflicts"]))
    failures += not t("Safety net is recorded in sources_used",
                      any("safety net" in s for s in result["sources_used"]))
    failures += not t("Note warns the watchlist is not authoritative",
                      "not a substitute" in result["note"].lower()
                      or "indicative" in result["note"].lower())

    # With live results AND uploaded competitors
    result2 = ts.enrich_conflicts(
        proposed_mark="BURRBERY",
        proposed_class="25",
        live_results=[{"mark": "BURBERY", "owner": "Some Co", "niceClass": "25"}],
        uploaded_competitors=[{"mark": "BURBERRY LONDON", "owner": "Burberry Ltd", "niceClass": "25"}],
    )
    failures += not t("Multiple sources combine into conflict list",
                      len(result2["conflicts"]) >= 2,
                      f"count: {len(result2['conflicts'])}")
    failures += not t("Conflicts sorted descending by score",
                      all(result2["conflicts"][i]["conflict_score"] >=
                          result2["conflicts"][i+1]["conflict_score"]
                          for i in range(len(result2["conflicts"]) - 1)))

    # Deduplication: same mark from two sources counted once
    result3 = ts.enrich_conflicts(
        proposed_mark="BURRBERY",
        proposed_class="25",
        live_results=[{"mark": "BURBERRY", "owner": "Burberry Limited", "niceClass": "25"}],
        uploaded_competitors=[{"mark": "BURBERRY", "owner": "Burberry Limited", "niceClass": "25"}],
    )
    burberry_count = sum(1 for c in result3["conflicts"] if c["mark"] == "BURBERRY")
    failures += not t("Duplicate marks deduplicated (BURBERRY appears once)",
                      burberry_count == 1,
                      f"count: {burberry_count}")

    # ── [6] No false positives ──────────────────────────────────────────────
    print("\n[6] no false positives for genuinely distinctive marks")

    clean = ts.enrich_conflicts(
        proposed_mark="ZYXQWVOR",
        proposed_class="42",
        live_results=[],
        uploaded_competitors=[],
    )
    failures += not t("Distinctive made-up mark → zero famous-mark conflicts",
                      len(clean["conflicts"]) == 0,
                      f"unexpected: {[c['mark'] for c in clean['conflicts']]}")

    # ── [7] well-known watchlist behaviour ──────────────────────────────────
    print("\n[7] well-known watchlist")

    failures += not t("Watchlist has famous UK marks",
                      len(ts.WELL_KNOWN_UK_MARKS) >= 10)
    wk = ts.check_against_well_known("TESC0", "35")  # leetspeak Tesco
    failures += not t("TESC0 (leetspeak) flags TESCO",
                      any(c["mark"] == "TESCO" for c in wk),
                      f"hits: {[c['mark'] for c in wk]}")

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
