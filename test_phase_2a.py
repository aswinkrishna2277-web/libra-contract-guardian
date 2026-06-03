"""
test_phase_2a.py — Integration test for the structured fact database.

Run as: python test_phase_2a.py

Tests:
  1. authority_db imports and all entries valid
  2. authority_selector imports and all selectors valid
  3. output_verifier imports and verifies/rejects correctly
  4. End-to-end: scenario → selector → prompt block → mock LLM output → verify
"""

import sys


def t(name: str, condition: bool, detail: str = "") -> bool:
    """Tiny test helper."""
    mark = "✓" if condition else "✗"
    print(f"  {mark} {name}" + (f" — {detail}" if detail else ""))
    return condition


def main() -> int:
    failures = 0

    # ─── 1. authority_db ─────────────────────────────────────────────────
    print("\n[1] authority_db")
    from authority_db import AUTHORITIES, get, find_by_topic, Kind, Jurisdiction, stats

    failures += not t("Has at least 40 authorities", len(AUTHORITIES) >= 40,
                      f"actual: {len(AUTHORITIES)}")
    failures += not t("Has UK cases", any(a.jurisdiction == Jurisdiction.UK and a.kind == Kind.CASE
                                          for a in AUTHORITIES.values()))
    failures += not t("Has Magdeev v Tsvetkov", get("CASE_MAGDEEV_V_TSVETKOV_2020") is not None)
    failures += not t("Has EU directives", any(a.kind == Kind.DIRECTIVE
                                                for a in AUTHORITIES.values()))
    failures += not t("Wisniewski has both citation forms",
                      "EWCA Civ 596" in get("CASE_WISNIEWSKI_1998").full_citation
                      and "PIQR P324" in get("CASE_WISNIEWSKI_1998").full_citation)
    failures += not t("IPEC rule reflects post-2023 move to CPR Part 46",
                      "46.20" in get("RULE_CPR_46_21").full_citation
                      and "Section VII" in get("RULE_CPR_46_21").full_citation)
    failures += not t("Adverse-inference lineage complete",
                      len(find_by_topic("adverse_inference")) >= 3)
    failures += not t("Ahmed et al. flagged as preprint",
                      "PREPRINT" in (get("ACADEMIC_AHMED_EXTRACTION_2026").notes or "").upper())
    failures += not t("PRPP manuscript present",
                      get("ACADEMIC_KRISHNA_PRPP_2026") is not None)

    # ─── 2. authority_selector ───────────────────────────────────────────
    print("\n[2] authority_selector")
    from authority_selector import (
        SELECTORS, KEYWORD_ENRICHMENT, select_for_prpp, select_for_contract,
        select_for_trademark, authorities_to_prompt_block,
    )

    failures += not t("All selectors reference valid IDs",
                      all(aid in AUTHORITIES for ids in SELECTORS.values() for aid in ids))
    failures += not t("All keyword patterns reference valid IDs",
                      all(aid in AUTHORITIES for ids in KEYWORD_ENRICHMENT.values() for aid in ids))

    prpp_strong = select_for_prpp(
        "AI training, hosted repository, regurgitation, "
        "good arguable case, pre-action preservation letter, adverse inference"
    )
    failures += not t("PRPP strong scenario picks Wisniewski",
                      any(a.id == "CASE_WISNIEWSKI_1998" for a in prpp_strong))
    failures += not t("PRPP strong scenario picks Brownlie",
                      any(a.id == "CASE_BROWNLIE_2017" for a in prpp_strong))
    failures += not t("PRPP strong scenario picks Getty",
                      any(a.id == "CASE_GETTY_V_STABILITY_2025" for a in prpp_strong))

    contract = select_for_contract("training data, machine-readable opt-out, TDM")
    failures += not t("Contract analyser picks CDPA s.29A",
                      any(a.id == "STATUTE_CDPA_S29A" for a in contract))
    failures += not t("Contract analyser picks Kneschke",
                      any(a.id == "CASE_KNESCHKE_V_LAION_2025" for a in contract))

    tm = select_for_trademark("BURRBERY", "similarity to mark with reputation")
    failures += not t("Trademark picks dilution authority",
                      any(a.id == "STATUTE_TMA_S10_3" for a in tm))

    block = authorities_to_prompt_block(prpp_strong[:3])
    failures += not t("Prompt block contains 'AVAILABLE AUTHORITIES'",
                      "AVAILABLE AUTHORITIES" in block)
    failures += not t("Prompt block does NOT leak internal IDs (e.g. CASE_*, RULE_*)",
                      "[CASE_" not in block and "[RULE_" not in block
                      and "CASE_WISNIEWSKI" not in block
                      and "RULE_PD_57AD" not in block)
    failures += not t("Prompt block contains full citation",
                      any(a.full_citation.split(" ")[0] in block for a in prpp_strong[:3]))

    # ─── 3. output_verifier ──────────────────────────────────────────────
    print("\n[3] output_verifier")
    from output_verifier import verify, extract_citations, render_structured_fallback

    # Clean text should pass
    rep = verify("Wisniewski v Central Manchester HA [1998] EWCA Civ 596 is foundational.")
    failures += not t("Clean Wisniewski text verifies", rep.is_valid)

    # Fabricated case should fail
    rep = verify("The court applied Smith v Jones [2099] EWCA Civ 9999.")
    failures += not t("Fabricated case rejected", not rep.is_valid)
    failures += not t("Fabricated case identified",
                      any("9999" in c.raw_text for c in rep.citations_unknown))

    # Wrong year, real case → fail
    rep = verify("Wisniewski v Central Manchester HA [2099] EWCA Civ 596 was applied.")
    failures += not t("Wrong-year case rejected", not rep.is_valid)

    # Allowed-only filtering
    rep = verify(
        "Both Wisniewski [1998] EWCA Civ 596 and IPCom [2013] EWHC 2880 (Ch) apply.",
        allowed_authority_ids=["CASE_WISNIEWSKI_1998"],
    )
    failures += not t("Allowed-only filter rejects out-of-scope",
                      not rep.is_valid)
    failures += not t("Allowed-only filter accepts in-scope",
                      any("1998" in c.raw_text for c in rep.citations_verified))

    # Statute extraction
    cits = extract_citations("CDPA 1988 s.29A and TMA 1994 s.10(3)")
    failures += not t("Statute extractor finds CDPA",
                      any(c.citation_type == "cdpa" for c in cits))
    failures += not t("Statute extractor finds TMA",
                      any(c.citation_type == "tma" for c in cits))

    # ─── 4. End-to-end integration ───────────────────────────────────────
    print("\n[4] end-to-end integration")
    from authority_db import get
    from authority_selector import select_for_prpp
    from output_verifier import verify

    scenario = "AI training on Common Crawl, adverse inference, pre-action letter"
    selected = select_for_prpp(scenario, stage=3)
    allowed_ids = [a.id for a in selected]

    # Simulate a "good" LLM output
    good_output = (
        "On these facts, the court may apply the doctrine in "
        "Wisniewski v Central Manchester Health Authority [1998] EWCA Civ 596, "
        "as extended in Wetton v Ahmed [2011] EWCA Civ 610."
    )
    rep = verify(good_output, allowed_authority_ids=allowed_ids)
    failures += not t("End-to-end: well-formed output passes",
                      rep.is_valid,
                      f"reason: {rep.reason}")

    # Simulate a "drifting" LLM output that introduces an out-of-scope case
    bad_output = (
        "On these facts, the court may apply Wisniewski [1998] EWCA Civ 596 and "
        "also Smith v Hallucinated [2024] EWCA Civ 8888."
    )
    rep = verify(bad_output, allowed_authority_ids=allowed_ids)
    failures += not t("End-to-end: drifting output rejected",
                      not rep.is_valid)

    # Fallback rendering uses only verified authorities
    fb = render_structured_fallback(
        "Stage 3 — Adverse Inference",
        "The court may draw an adverse inference.",
        [get("CASE_WISNIEWSKI_1998"), get("CASE_WETTON_V_AHMED_2011")],
    )
    rep_fb = verify(fb)
    failures += not t("Fallback render is self-verifying",
                      rep_fb.is_valid,
                      f"reason: {rep_fb.reason}")

    # ─── Summary ─────────────────────────────────────────────────────────
    print()
    print("─" * 70)
    if failures == 0:
        print(f"✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"✗ {failures} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
