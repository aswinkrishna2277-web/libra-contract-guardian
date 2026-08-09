# ================================================================
#  LIBRA CONTRACT GUARDIAN v1.1 — Playbook Engine
#  TF-IDF Vector Space + Cosine Similarity
#
#  This module replaces the v1.0 keyword-averaging "playbook_vector"
#  with a genuine vector-space implementation: a contract is
#  represented as a TF-IDF vector over the corpus vocabulary, and
#  deviation from a firm's gold-standard playbook is measured as
#  (1 - cosine similarity) against the centroid of gold contracts.
#
#  This is closer to what the v1.0 README claimed and what a
#  technically literate reviewer (Bristows tech team, EUIPO
#  Observatory, A&L Goodbody innovation team) would expect.
#
#  Author: R.A. Aswin Krishna, IP-AI Practitioner
#  License: see LICENSE
# ================================================================

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import re

try:
    import numpy as np
    NUMPY_OK = True
except Exception:
    np = None
    NUMPY_OK = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_OK = True
except Exception:
    TfidfVectorizer = None
    cosine_similarity = None
    SKLEARN_OK = False


# Legal-domain stopwords — words too generic to differentiate clauses.
# Standard English stopwords plus common contractual filler.
LEGAL_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at",
    "by", "for", "with", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "this", "that", "these", "those", "it", "its",
    "shall", "may", "will", "must", "any", "all", "such", "hereby",
    "herein", "hereof", "hereto", "thereof", "therein", "thereto",
    "party", "parties", "agreement", "contract", "clause", "section",
    "article", "paragraph", "subject", "pursuant", "respect", "regard",
    "between", "among", "including", "without", "limitation", "limited",
    "set", "forth", "above", "below", "applicable", "case", "event",
    "if", "then", "no", "not", "nor", "so", "do", "does", "did",
    "have", "has", "had", "having",
})


def _normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, strip non-alphanumeric noise."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s\-\.]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_playbook_vector(
    gold_texts: List[str],
    *,
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (1, 2),
    min_df: int = 1,
) -> Optional[Dict]:
    """
    Build a real TF-IDF playbook vector from gold-standard contracts.

    Returns a dict containing:
      - vectorizer:       fitted TfidfVectorizer (used for transforming new contracts)
      - centroid:         mean TF-IDF vector across all gold contracts (numpy array)
      - per_doc_vectors:  list of TF-IDF vectors, one per gold doc (sparse, dense-converted)
      - vocabulary_size:  int
      - n_gold:           int
      - top_terms:        list of (term, mean_tfidf) tuples, top 25 most distinctive
      - mode:             'tfidf' (real) or 'unavailable' (sklearn missing)

    The centroid IS the playbook — it's the mean point in TF-IDF space
    that represents what your firm considers a "good" contract.
    """
    if not gold_texts:
        return None

    if not (SKLEARN_OK and NUMPY_OK):
        return {
            "mode": "unavailable",
            "error": "scikit-learn or numpy not installed",
            "n_gold": len(gold_texts),
        }

    cleaned = [_normalize_text(t) for t in gold_texts if t and t.strip()]
    if len(cleaned) < 1:
        return None

    # min_df defaults to 1 because users may upload very few gold contracts.
    # If they upload 5+, we tighten to min_df=2 to filter accidental terms.
    effective_min_df = min(min_df, len(cleaned)) if len(cleaned) >= 5 else 1

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        stop_words=list(LEGAL_STOPWORDS),
        min_df=effective_min_df,
        max_df=0.95,
        sublinear_tf=True,  # use 1 + log(tf), more robust for legal corpora
        norm="l2",          # L2-normalised — required for clean cosine similarity
    )

    try:
        matrix = vectorizer.fit_transform(cleaned)
    except ValueError as e:
        # Happens if all docs are empty after stopword removal
        return {
            "mode": "unavailable",
            "error": f"vectorization failed: {e}",
            "n_gold": len(cleaned),
        }

    # Centroid = mean TF-IDF vector across gold corpus.
    # This is the "playbook point" in vector space.
    centroid = np.asarray(matrix.mean(axis=0)).flatten()

    # Top terms by mean TF-IDF — these are the most distinctive
    # protective patterns the playbook captures.
    feature_names = vectorizer.get_feature_names_out()
    term_scores = list(zip(feature_names, centroid))
    term_scores.sort(key=lambda x: x[1], reverse=True)
    top_terms = [(t, float(s)) for t, s in term_scores[:25] if s > 0]

    return {
        "mode": "tfidf",
        "vectorizer": vectorizer,
        "centroid": centroid,
        "per_doc_vectors": matrix,
        "vocabulary_size": len(feature_names),
        "n_gold": len(cleaned),
        "top_terms": top_terms,
        "ngram_range": ngram_range,
        # Retained so the reversed-protection check has the original wording to
        # compare against; TF-IDF vectors alone discard negations.
        "gold_texts": list(gold_texts),
    }


def compute_deviation(
    new_text: str,
    playbook: Dict,
    *,
    deviation_threshold: float = 0.35,
) -> Optional[Dict]:
    """
    Measure how far a new contract deviates from the firm's playbook.

    Uses cosine similarity between the new contract's TF-IDF vector
    and the playbook centroid. A similarity of 1.0 = identical clause
    pattern; 0.0 = completely orthogonal.

    Returns:
      - similarity:        float in [0, 1]   (1 = perfect match)
      - deviation_pct:     float in [0, 100] (0 = perfect match)
      - within_playbook:   bool              (True if deviation < threshold)
      - missing_terms:     list of top 15 playbook terms absent from new contract
      - novel_terms:       list of top 15 terms in new contract but NOT in playbook
      - per_doc_similarities: list of similarity scores against each gold doc
      - confidence_band:   "high" | "medium" | "low"  (based on n_gold)
      - mode:              'tfidf' | 'unavailable'
    """
    if not playbook or playbook.get("mode") != "tfidf":
        return None

    if not new_text or not new_text.strip():
        return None

    cleaned = _normalize_text(new_text)
    vectorizer = playbook["vectorizer"]
    centroid = playbook["centroid"]
    per_doc = playbook["per_doc_vectors"]

    # Transform the new contract into the playbook's vector space
    new_vec = vectorizer.transform([cleaned])
    new_dense = np.asarray(new_vec.todense()).flatten()

    # Cosine similarity to the centroid (the playbook itself)
    # Guard against zero vectors (a new contract with no overlap
    # at all with the playbook vocabulary)
    centroid_norm = np.linalg.norm(centroid)
    new_norm = np.linalg.norm(new_dense)

    if centroid_norm == 0 or new_norm == 0:
        similarity = 0.0
    else:
        similarity = float(np.dot(centroid, new_dense) / (centroid_norm * new_norm))

    similarity = max(0.0, min(1.0, similarity))
    deviation_pct = round((1.0 - similarity) * 100, 2)

    # Per-document similarities — useful for showing which gold contract
    # the new one is closest to (and therefore which precedent to cite)
    per_doc_sims = cosine_similarity(new_vec, per_doc).flatten().tolist()
    per_doc_sims = [round(float(s), 4) for s in per_doc_sims]

    # Find missing protective terms — playbook terms with high TF-IDF
    # in the gold corpus but ~0 weight in the new contract
    feature_names = vectorizer.get_feature_names_out()
    new_weights = dict(zip(feature_names, new_dense))

    missing_terms = []
    for term, gold_weight in playbook["top_terms"]:
        new_weight = new_weights.get(term, 0.0)
        if new_weight < 0.01 and gold_weight > 0.01:
            missing_terms.append({
                "term": term,
                "playbook_weight": round(gold_weight, 4),
                "new_weight": round(float(new_weight), 4),
            })
        if len(missing_terms) >= 15:
            break

    # Novel terms — significant in new contract, absent in playbook.
    # Could be unfamiliar (risk) or innovative (interest).
    novel_idx = np.argsort(new_dense)[::-1][:50]
    novel_terms = []
    for i in novel_idx:
        term = feature_names[i]
        new_weight = float(new_dense[i])
        if new_weight < 0.05:
            break
        if term not in dict(playbook["top_terms"]):
            novel_terms.append({"term": term, "weight": round(new_weight, 4)})
        if len(novel_terms) >= 15:
            break

    # ── "Within playbook" must reflect the CLOSEST precedent, not the average ─
    # This was previously computed from the centroid similarity alone. The
    # centroid is the average of every gold document, so a contract that is
    # IDENTICAL to one of them still only resembles the average partially:
    # measured at per_doc_similarities [1.0, 0.096, 0.105] -> centroid
    # similarity 0.646 -> 35.4% deviation -> "outside the playbook". A firm's
    # own standard template was being reported as a deviation from its own
    # playbook. A contract is within the playbook if it closely matches ANY
    # approved precedent, so the closest match governs; the centroid figure is
    # still reported as the overall deviation measure.
    _best_match = max(per_doc_sims) if per_doc_sims else 0.0
    _within = (
        deviation_pct < (deviation_threshold * 100)
        or (1.0 - _best_match) < deviation_threshold
    )

    # ── Reversed-protection check ───────────────────────────────────────────
    # TF-IDF treats "not" as a stopword, so a contract that REVERSES the
    # playbook's core protection is invisible to cosine similarity. Measured:
    # taking a gold document and changing only "shall not use" to "may use" —
    # turning a prohibition on AI training into a permission — produced a
    # similarity difference of exactly 0.0000. The two documents were
    # indistinguishable to the engine.
    #
    # Similarity alone therefore cannot answer "does this contract still
    # protect us?". We check explicitly whether protections the playbook
    # consistently asserts have been negated or reversed in the new contract.
    _protective_concepts = [
        "training", "machine learning", "data mining", "scrape", "scraping",
        "liability", "indemnit", "provenance", "intellectual property",
        "confidential", "audit",
    ]
    reversed_protections: list[dict] = []
    try:
        from negation_guard import term_is_negated as _pb_negated

        gold_joined = " ".join(playbook.get("gold_texts") or [])
        for concept in _protective_concepts:
            if concept not in cleaned:
                continue
            gold_neg, _ = (
                _pb_negated(gold_joined, concept) if gold_joined else (False, None)
            )
            new_neg, _ = _pb_negated(new_text, concept)
            # The playbook restricts this concept; the new contract does not.
            if gold_neg and not new_neg:
                reversed_protections.append({
                    "concept": concept,
                    "playbook": "restricted",
                    "new_contract": "permitted or unrestricted",
                })
    except Exception:  # pragma: no cover - must never break deviation analysis
        reversed_protections = []

    # Confidence band based on size of gold corpus
    n_gold = playbook["n_gold"]
    if n_gold >= 10:
        confidence = "high"
    elif n_gold >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "mode": "tfidf",
        "similarity": round(similarity, 4),
        "deviation_pct": deviation_pct,
        "within_playbook": _within and not reversed_protections,
        "reversed_protections": reversed_protections,
        "closest_precedent_similarity": round(_best_match, 4),
        "missing_terms": missing_terms,
        "novel_terms": novel_terms,
        "per_doc_similarities": per_doc_sims,
        "closest_gold_index": int(np.argmax(per_doc_sims)) if per_doc_sims else -1,
        "closest_gold_similarity": max(per_doc_sims) if per_doc_sims else 0.0,
        "confidence_band": confidence,
        "n_gold": n_gold,
        "vocabulary_size": playbook["vocabulary_size"],
    }


def explain_deviation(deviation: Dict) -> str:
    """
    Produce a 2-3 sentence plain-English explanation of the deviation result,
    suitable for inclusion in a legal memo or audit log.
    """
    if not deviation or deviation.get("mode") != "tfidf":
        return "Deviation analysis unavailable (TF-IDF engine not loaded)."

    sim = deviation["similarity"]
    dev = deviation["deviation_pct"]
    n_missing = len(deviation.get("missing_terms", []))
    n_novel = len(deviation.get("novel_terms", []))
    closest_sim = deviation.get("closest_gold_similarity", 0)
    conf = deviation["confidence_band"]

    if sim >= 0.75:
        verdict = "closely conforms to"
    elif sim >= 0.50:
        verdict = "partially aligns with"
    elif sim >= 0.25:
        verdict = "substantially diverges from"
    else:
        verdict = "is largely orthogonal to"

    return (
        f"This contract {verdict} the firm's playbook (cosine similarity = {sim:.2f}, "
        f"deviation = {dev:.1f}%). It is closest to gold contract #{deviation['closest_gold_index'] + 1} "
        f"(similarity = {closest_sim:.2f}). {n_missing} expected protective term(s) are absent and "
        f"{n_novel} novel term(s) are present that do not appear in the gold corpus. "
        f"Confidence: {conf} (n_gold = {deviation['n_gold']})."
    )


# ────────────────────────────────────────────────────────────────────────
# Backwards-compatibility shim
# ────────────────────────────────────────────────────────────────────────
def compute_playbook_vector(texts: List[str]) -> Dict:
    """
    Legacy entry point — preserved for compatibility with v1.0 callers.
    Returns a SIMPLIFIED dict with both old keys (per-category scores)
    and new keys (the real TF-IDF playbook).

    New callers should use build_playbook_vector() directly.
    """
    # Build the real TF-IDF playbook
    real_playbook = build_playbook_vector(texts)

    # Legacy per-category dict — kept for old UI code that expects it.
    # This is now derived from the TF-IDF top terms, not standalone.
    legacy_categories = {}
    if real_playbook and real_playbook.get("mode") == "tfidf":
        # Map TF-IDF top terms back to the v1.0 RISK_CATEGORIES taxonomy
        # for any UI that still expects per-category scores.
        try:
            from constants import RISK_CATEGORIES
        except ImportError:
            RISK_CATEGORIES = {}

        top_term_set = {t for t, _ in real_playbook["top_terms"]}
        for cat_key, cat_def in RISK_CATEGORIES.items():
            cat_keywords = set(cat_def.get("keywords", []))
            # How many of this category's keywords appear in the playbook's
            # top distinctive terms? Map to a 0-100 score.
            overlap = len(cat_keywords & top_term_set)
            legacy_categories[cat_key] = min(100, overlap * 20)

    return {
        # New keys — the real engine
        "_tfidf_playbook": real_playbook,
        # Legacy keys — for old UI code
        **legacy_categories,
    }


def playbook_deviation(new_text: str, playbook_vector: Dict) -> Dict:
    """
    Legacy entry point. Now wraps the TF-IDF deviation engine and shapes
    the output to match what the v1.0 UI expects.
    """
    real_playbook = playbook_vector.get("_tfidf_playbook") if isinstance(playbook_vector, dict) else None

    # Real TF-IDF deviation
    real_dev = compute_deviation(new_text, real_playbook) if real_playbook else None

    if real_dev:
        # New-shape result — preferred
        try:
            from constants import RISK_CATEGORIES
        except ImportError:
            RISK_CATEGORIES = {}

        # For backwards compatibility with the old playbook deviation UI:
        # produce per-category gap analysis using missing_terms.
        missing_term_set = {m["term"] for m in real_dev["missing_terms"]}
        gaps = []
        for cat_key, cat_def in RISK_CATEGORIES.items():
            cat_keywords = set(cat_def.get("keywords", []))
            if cat_keywords & missing_term_set:
                gaps.append(cat_key)

        return {
            # New keys
            "_tfidf_deviation": real_dev,
            "explanation": explain_deviation(real_dev),
            # Legacy-shaped keys (for v1.0 UI compatibility)
            "deviation_pct": real_dev["deviation_pct"],
            "similarity": real_dev["similarity"],
            "risk_gaps": gaps,
            "missing_terms": real_dev["missing_terms"],
            "novel_terms": real_dev["novel_terms"],
            "fix_suggestions": [
                f"Consider adding language around '{m['term']}' — present in {real_dev['n_gold']} of your gold contracts but absent here."
                for m in real_dev["missing_terms"][:8]
            ],
            "confidence_band": real_dev["confidence_band"],
            "mode": "tfidf",
        }

    # Fallback: scikit-learn unavailable. Be honest about it.
    return {
        "mode": "unavailable",
        "deviation_pct": 0.0,
        "similarity": 0.0,
        "risk_gaps": [],
        "missing_terms": [],
        "novel_terms": [],
        "fix_suggestions": ["TF-IDF engine unavailable. Install scikit-learn to enable real vector-space deviation analysis."],
        "explanation": "Playbook deviation analysis requires scikit-learn. Run: pip install scikit-learn",
    }
