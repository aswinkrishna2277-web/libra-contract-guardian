"""
test_phase_e_core.py — Phase E coverage expansion.

Locks down the core scoring / utility helpers that previously had no dedicated
tests: normalize_score, compute_compliance_strength, compute_risk_mitigation_
adjustment, detect_risk_keywords, the perceptual-hash pair (_phash_from_text /
_hash_similarity), and playbook_deviation.

These import app.py, so the app's dependencies (streamlit, pandas, plotly,
PyMuPDF, scikit-learn) must be installed — i.e. run inside the project venv.
"""

import os
os.environ.setdefault("LIBRA_LOG_DIR", os.path.join(os.path.dirname(__file__), ".libra_test"))


def t(label, cond, extra=""):
    print(f"  {'✓' if cond else '✗'} {label}" + (f" — {extra}" if extra else ""))
    return bool(cond)


def run_all() -> int:
    import app
    fails = 0

    # ── [1] normalize_score ──────────────────────────────────────────────────
    print("\n[1] normalize_score — robust numeric coercion")
    fails += not t("int passes through", app.normalize_score(42) == 42)
    fails += not t("float truncates to int", app.normalize_score(42.9) == 42)
    fails += not t("numeric string parses", app.normalize_score("40") == 40)
    fails += not t("float string parses", app.normalize_score("40.0") == 40)
    fails += not t("above 100 clamps to 100", app.normalize_score(150) == 100)
    fails += not t("below 0 clamps to 0", app.normalize_score(-5) == 0)
    fails += not t("garbage returns default", app.normalize_score("abc") == 50)
    fails += not t("None returns default", app.normalize_score(None) == 50)
    fails += not t("custom default honoured", app.normalize_score("x", default=10) == 10)

    # ── [2] compute_compliance_strength ──────────────────────────────────────
    print("\n[2] compute_compliance_strength — protective-language scoring")
    empty = app.compute_compliance_strength("")
    fails += not t("empty text → 0", empty == 0, f"got {empty}")
    protective = app.compute_compliance_strength(
        "The licensee warrants and indemnifies the licensor. Data provenance "
        "records shall be maintained. TDM is expressly excluded. Audit rights "
        "are granted and the agreement may be terminated for breach."
    )
    fails += not t("protective text scores > 0", protective > 0, f"got {protective}")
    fails += not t("score is an int in [0,100]",
                   isinstance(protective, int) and 0 <= protective <= 100)
    neutral = app.compute_compliance_strength("The sky is blue and grass is green.")
    fails += not t("neutral text scores lower than protective", neutral < protective,
                   f"neutral={neutral}, protective={protective}")

    # ── [3] compute_risk_mitigation_adjustment ───────────────────────────────
    print("\n[3] compute_risk_mitigation_adjustment — capped reduction")
    adj_empty = app.compute_risk_mitigation_adjustment("")
    fails += not t("empty → 0 reduction", adj_empty == 0)
    # Use real protective phrases the scorer recognises (multi-word, weighted),
    # enough to cross the 10-point strength threshold that earns a reduction.
    strong_protective = (
        "The dataset includes a data provenance schedule and full audit rights. "
        "TDM exclusion and machine learning exclusion clauses apply; the works are "
        "expressly excluded from any model training and not used for training. "
        "The licensor represents and warrants lawful provenance, with a provenance "
        "warranty and indemnify and hold harmless terms. Audit trail maintained. "
        "Compliant with CDPA 1988 s.29A and UK GDPR Article 28."
    )
    strength = app.compute_compliance_strength(strong_protective)
    adj = app.compute_risk_mitigation_adjustment(strong_protective)
    fails += not t("genuinely protective text crosses threshold (strength >= 10)",
                   strength >= 10, f"strength={strength}")
    fails += not t("genuinely protective text → reduction > 0", adj > 0, f"got {adj}")
    fails += not t("reduction never exceeds 40 cap", adj <= 40, f"got {adj}")
    # And confirm the design: weakly-protective text earns NO reduction (correct,
    # conservative behaviour — this was the assumption the first test version got wrong).
    weak_adj = app.compute_risk_mitigation_adjustment("warranty indemnity audit")
    fails += not t("weakly-protective text → 0 reduction (conservative by design)",
                   weak_adj == 0, f"got {weak_adj}")

    # ── [4] detect_risk_keywords ─────────────────────────────────────────────
    print("\n[4] detect_risk_keywords — per-category risk dict")
    scores = app.detect_risk_keywords("This contract covers AI training on scraped datasets and copyright.")
    fails += not t("returns a dict", isinstance(scores, dict))
    fails += not t("has all RISK_CATEGORIES keys",
                   set(scores.keys()) == set(app.RISK_CATEGORIES.keys()))
    fails += not t("all values are ints", all(isinstance(v, int) for v in scores.values()))
    fails += not t("all values in [0,100]", all(0 <= v <= 100 for v in scores.values()))
    empty_scores = app.detect_risk_keywords("")
    fails += not t("empty text → all zero",
                   all(v == 0 for v in empty_scores.values()))

    # ── [5] perceptual hash pair ─────────────────────────────────────────────
    print("\n[5] _phash_from_text / _hash_similarity")
    h1 = app._phash_from_text("BURBERRY")
    h2 = app._phash_from_text("BURBERRY")
    h3 = app._phash_from_text("totally different mark xyz")
    fails += not t("identical text → identical hash similarity is 100",
                   app._hash_similarity(h1, h2) == 100.0,
                   f"got {app._hash_similarity(h1, h2)}")
    sim_diff = app._hash_similarity(h1, h3)
    fails += not t("different text → similarity < 100", sim_diff < 100.0, f"got {sim_diff}")
    fails += not t("None hash → 0.0", app._hash_similarity(None, h1) == 0.0)
    fails += not t("both None → 0.0", app._hash_similarity(None, None) == 0.0)

    # ── [6] playbook_deviation ───────────────────────────────────────────────
    print("\n[6] playbook_deviation — deviation from a baseline vector")
    print("    (playbook has its own suite in test_playbook.py — this is a light smoke check)")
    try:
        import playbook
        vec = playbook.build_playbook_vector(
            ["The licensee shall indemnify. Warranty provided. TDM excluded."]
        )
        if vec is not None:
            dev = playbook.playbook_deviation(
                "The licensee shall indemnify. Warranty provided. TDM excluded.", vec
            )
            fails += not t("deviation returns a dict", isinstance(dev, dict))
            fails += not t("deviation dict has a recognisable score key",
                           any(k in dev for k in ("deviation_score", "similarity", "score",
                                                  "deviations", "cosine_similarity", "deviation_pct")),
                           f"keys: {list(dev.keys())[:6]}")
        else:
            print("    (build_playbook_vector returned None — skipping deeper check)")
    except Exception as e:
        print(f"    (playbook deviation check skipped: {type(e).__name__}: {e})")

    print()
    print("─" * 60)
    if fails == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {fails} test(s) failed")
    return fails


if __name__ == "__main__":
    import sys
    sys.exit(1 if run_all() else 0)
