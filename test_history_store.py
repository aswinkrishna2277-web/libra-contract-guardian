"""
test_history_store.py — verifies the local analysis-history layer.

Confirms persistence works AND that the privacy defaults hold (no full text
stored unless explicitly opted in).
"""

import os
import tempfile

# Isolate the DB into a temp dir so tests never touch a real ~/.libra
_TMP = tempfile.mkdtemp(prefix="libra_hist_test_")
os.environ["LIBRA_LOG_DIR"] = _TMP

import history_store as hs


def t(label, cond):
    print(f"  {'✓' if cond else '✗'} {label}")
    return bool(cond)


def run_all() -> int:
    failures = 0
    # Start clean
    hs.clear_all()

    print("[1] init + empty state")
    failures += not t("count is 0 at start", hs.count_analyses() == 0)
    failures += not t("list empty at start", hs.list_analyses() == [])

    print("\n[2] save results-only (privacy default)")
    rid = hs.save_analysis(
        "contract",
        {"overall_risk_score": 71, "risk_level": "Medium", "citations": ["CDPA s.29A"]},
        doc_name="nda.docx",
        doc_text="This is a confidential contract body that must NOT be stored.",
        mode="search",
        risk_level="Medium",
        risk_score=71,
        store_full_text=False,
    )
    failures += not t("save returned an id", isinstance(rid, int) and rid > 0)
    failures += not t("count is now 1", hs.count_analyses() == 1)

    row = hs.get_analysis(rid)
    failures += not t("row retrievable", row is not None)
    failures += not t("result dict round-trips", row["result"]["overall_risk_score"] == 71)
    failures += not t("doc_name stored", row["doc_name"] == "nda.docx")
    failures += not t("doc_hash stored (non-empty)", bool(row["doc_hash"]))
    # THE PRIVACY CHECK: full text must NOT be present
    failures += not t("full_text is NULL (privacy default)", row["full_text"] is None)
    failures += not t("stored_full_text flag is 0", row["stored_full_text"] == 0)
    failures += not t("confidential body not stored anywhere",
                      "confidential contract body" not in (row.get("full_text") or ""))

    print("\n[3] explicit opt-in stores full text")
    rid2 = hs.save_analysis(
        "contract",
        {"overall_risk_score": 40, "risk_level": "Low"},
        doc_name="optin.docx",
        doc_text="Full text the user explicitly chose to retain.",
        store_full_text=True,
    )
    row2 = hs.get_analysis(rid2)
    failures += not t("opt-in: full_text IS stored", row2["full_text"] is not None)
    failures += not t("opt-in: flag is 1", row2["stored_full_text"] == 1)
    failures += not t("opt-in: text matches", "explicitly chose to retain" in row2["full_text"])

    print("\n[4] recognise repeat document by hash")
    same_text = "This is a confidential contract body that must NOT be stored."
    matches = hs.find_by_document(same_text)
    failures += not t("finds the earlier analysis of same doc", len(matches) >= 1)
    failures += not t("match is the right row", any(m["id"] == rid for m in matches))
    failures += not t("different doc finds nothing",
                      hs.find_by_document("a totally different document") == [])

    print("\n[5] listing + filtering")
    hs.save_analysis("prpp", {"overall_prpp_viability": 63}, doc_name="case.docx",
                     mode="", risk_level="Moderate", risk_score=63)
    all_rows = hs.list_analyses()
    failures += not t("list returns all 3", len(all_rows) == 3)
    failures += not t("newest first", all_rows[0]["engine"] == "prpp")
    contract_only = hs.list_analyses(engine="contract")
    failures += not t("engine filter works", len(contract_only) == 2)
    failures += not t("list rows omit heavy result_json", "result_json" not in all_rows[0])

    print("\n[6] stats")
    s = hs.stats()
    failures += not t("stats total = 3", s["total"] == 3)
    failures += not t("stats by_engine has contract=2", s["by_engine"].get("contract") == 2)
    failures += not t("stats with_full_text = 1", s["with_full_text"] == 1)

    print("\n[7] delete one")
    failures += not t("delete returns True", hs.delete_analysis(rid2) is True)
    failures += not t("count drops to 2", hs.count_analyses() == 2)
    failures += not t("deleted row gone", hs.get_analysis(rid2) is None)

    print("\n[8] clear all")
    failures += not t("clear_all returns True", hs.clear_all() is True)
    failures += not t("count is 0 after clear", hs.count_analyses() == 0)

    print("\n[9] resilience — bad inputs never raise")
    failures += not t("get_analysis(99999) -> None", hs.get_analysis(99999) is None)
    failures += not t("delete_analysis(99999) -> True (no-op ok)", hs.delete_analysis(99999) is True)
    failures += not t("find_by_document('') -> []", hs.find_by_document("") == [])
    # Non-serialisable object in result must not crash (default=str handles it)
    rid3 = hs.save_analysis("tdm", {"obj": object()}, doc_name="x.docx")
    failures += not t("non-serialisable result still saves", isinstance(rid3, int))

    print()
    print("─" * 60)
    if failures == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {failures} test(s) failed")
    return failures


if __name__ == "__main__":
    import sys
    sys.exit(1 if run_all() else 0)
