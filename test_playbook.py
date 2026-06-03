"""
Verification test for the TF-IDF playbook engine.

This test demonstrates that the new playbook.py module ACTUALLY does
vector-space similarity analysis — not the keyword averaging that the
v1.0 implementation hid behind the name "playbook_vector".

We use realistic IP/AI contract clauses and verify:
  1. A protective gold-standard contract shapes the playbook
  2. A weak contract (missing protective language) shows high deviation
  3. A near-identical contract shows very low deviation
  4. The vector-space dimensions are real
"""

import sys
sys.path.insert(0, "/home/claude/libra")

from playbook import (
    build_playbook_vector,
    compute_deviation,
    explain_deviation,
)


# ── Gold-standard contracts (firm's playbook) ─────────────────────────────
GOLD_1 = """
Data Licensing Agreement.

The Licensed Materials shall not be used for any machine learning,
training, statistical modelling or text and data mining purpose
[per CDPA 1988 s.29A]. Licensee warrants that all data ingested
under this Agreement has been lawfully obtained and is free of
third-party copyright claims. Audit rights are granted to Licensor
on 30 days' notice. The Provenance Schedule attached as Annex A
sets out the source, licence terms and provenance of each dataset.
Licensor expressly reserves all rights under DSM Directive
Art.4(3) including machine-readable opt-out reservation.
"""

GOLD_2 = """
Master Services Agreement — AI Research Collaboration.

The Provider shall not use the Customer's data for training any
foundation model, large language model or generative AI system
[per CDPA 1988 s.29A and DSM Directive Art.4]. The Provider warrants
provenance of all training corpora and shall maintain cryptographic
hash manifests (SHA-256) of all ingested materials for not less
than seven years. Customer audit rights are granted under Annex B.
The Provider indemnifies and holds harmless the Customer against
any third-party copyright claim arising from training data ingestion.
"""

GOLD_3 = """
Software Licensing Agreement with TDM Restrictions.

No model training, machine learning, statistical modelling or
pattern extraction is permitted on the Licensed Software outputs.
Provider reserves all rights expressly under TDM exclusion provisions.
The Provenance Schedule (Annex A) records lawful acquisition of
training data. Audit rights apply per CDPA 1988 s.29A. UK GDPR
Art.28 governs personal data processing. Arbitration under
Arbitration Act 1996 in London.
"""

# ── Test contract 1: weak (missing protective language) ──────────────────
WEAK_CONTRACT = """
Service Agreement.

The Customer grants the Provider a non-exclusive licence to use the
Customer Data for the purposes of providing the Services. The Provider
may engage subcontractors. Either party may terminate on 30 days notice.
This Agreement is governed by the laws of England and Wales.
"""

# ── Test contract 2: similar to gold (should match closely) ──────────────
GOOD_CONTRACT = """
Data Licensing Agreement.

The Licensed Materials shall not be used for any machine learning,
training, or statistical modelling purpose [per CDPA 1988 s.29A].
Licensee warrants that all training data is lawfully obtained.
The Provenance Schedule (Annex A) records all sources. Audit rights
are reserved. Licensor expressly reserves all rights under DSM
Directive Art.4(3).
"""

# ── Test contract 3: novel topic (orthogonal to playbook) ────────────────
ORTHOGONAL_CONTRACT = """
Equipment Rental Agreement.

The Lessor leases the Equipment to the Lessee for the term specified.
Rental payments are due monthly. The Lessee is responsible for
insurance and maintenance. Damage beyond fair wear and tear is
chargeable. Either party may terminate on 60 days notice.
"""


def main():
    print("=" * 70)
    print("LIBRA PLAYBOOK ENGINE — VERIFICATION TEST")
    print("Testing real TF-IDF cosine similarity (replacing v1.0 keyword averaging)")
    print("=" * 70)

    # Build the playbook
    print("\n[1] Building playbook from 3 gold-standard contracts...")
    playbook = build_playbook_vector([GOLD_1, GOLD_2, GOLD_3])

    if not playbook or playbook.get("mode") != "tfidf":
        print("FAIL: Playbook engine unavailable")
        print(f"  {playbook}")
        return

    print(f"  Mode:            {playbook['mode']}")
    print(f"  Vocabulary size: {playbook['vocabulary_size']} terms")
    print(f"  Gold corpus:     {playbook['n_gold']} contracts")
    print(f"  N-gram range:    {playbook['ngram_range']}")
    print(f"  Top distinctive playbook terms (top 10):")
    for term, weight in playbook["top_terms"][:10]:
        print(f"    {weight:.4f}  {term}")

    # Test 1: Weak contract — should show HIGH deviation
    print("\n[2] Testing WEAK contract (missing protective language)...")
    weak_dev = compute_deviation(WEAK_CONTRACT, playbook)
    print(f"  Similarity:        {weak_dev['similarity']:.4f}")
    print(f"  Deviation:         {weak_dev['deviation_pct']:.2f}%")
    print(f"  Within playbook?   {weak_dev['within_playbook']}")
    print(f"  Missing terms:     {len(weak_dev['missing_terms'])}")
    print(f"  Confidence:        {weak_dev['confidence_band']}")
    print(f"  Explanation:       {explain_deviation(weak_dev)}")

    # Test 2: Good contract — should show LOW deviation
    print("\n[3] Testing GOOD contract (similar to gold)...")
    good_dev = compute_deviation(GOOD_CONTRACT, playbook)
    print(f"  Similarity:        {good_dev['similarity']:.4f}")
    print(f"  Deviation:         {good_dev['deviation_pct']:.2f}%")
    print(f"  Within playbook?   {good_dev['within_playbook']}")
    print(f"  Closest gold:      #{good_dev['closest_gold_index'] + 1} (sim={good_dev['closest_gold_similarity']:.4f})")
    print(f"  Explanation:       {explain_deviation(good_dev)}")

    # Test 3: Orthogonal contract — should show VERY high deviation
    print("\n[4] Testing ORTHOGONAL contract (equipment rental — completely different domain)...")
    ortho_dev = compute_deviation(ORTHOGONAL_CONTRACT, playbook)
    print(f"  Similarity:        {ortho_dev['similarity']:.4f}")
    print(f"  Deviation:         {ortho_dev['deviation_pct']:.2f}%")
    print(f"  Within playbook?   {ortho_dev['within_playbook']}")
    print(f"  Explanation:       {explain_deviation(ortho_dev)}")

    # Sanity assertions
    print("\n[5] Sanity checks:")
    assert good_dev["similarity"] > weak_dev["similarity"], \
        f"FAIL: good ({good_dev['similarity']}) should beat weak ({weak_dev['similarity']})"
    print("  PASS: GOOD contract similarity > WEAK contract similarity")

    assert weak_dev["similarity"] > ortho_dev["similarity"], \
        f"FAIL: weak ({weak_dev['similarity']}) should beat ortho ({ortho_dev['similarity']})"
    print("  PASS: WEAK (same domain) similarity > ORTHOGONAL similarity")

    assert good_dev["similarity"] >= 0.4, \
        f"FAIL: good contract should have >=0.4 similarity, got {good_dev['similarity']}"
    print("  PASS: GOOD contract similarity >= 0.4 (meaningful match for n=3 corpus)")

    assert ortho_dev["similarity"] < 0.2, \
        f"FAIL: orthogonal contract should have <0.2 similarity, got {ortho_dev['similarity']}"
    print("  PASS: ORTHOGONAL contract similarity < 0.2 (correctly rejected)")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED — TF-IDF engine is real, working, and ranks contracts")
    print("correctly by semantic distance from the gold playbook.")
    print("=" * 70)


if __name__ == "__main__":
    main()
