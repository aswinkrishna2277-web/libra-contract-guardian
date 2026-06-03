# ================================================================
#  LIBRA CONTRACT GUARDIAN v2.0 – Trademark Similarity Module
#  Phonetic + edit-distance similarity scoring for mark conflicts
#
#  PURPOSE
#    The live UKIPO/TMview search returns exact-token matches only.
#    It does NOT flag that "BURRBERY" is one edit away from the famous
#    "BURBERRY". This module adds the similarity layer that turns a raw
#    list of marks (from any source: live search, uploaded competitor
#    list, or local register) into scored conflicts.
#
#  ARCHITECTURE
#    Deterministic. No LLM. Pure scoring functions.
#    Three signals combined into a single conflict score (0-100):
#      1. Visual / edit-distance similarity (Levenshtein ratio)
#      2. Phonetic similarity (Double Metaphone agreement)
#      3. Containment / substring signal (one mark inside the other)
#    Plus goods/services overlap (Nice class match) as a multiplier.
#
#  DEPENDENCIES
#    rapidfuzz is used if available (fast C implementation).
#    If not installed, a pure-Python Levenshtein fallback is used.
#    Phonetic matching is pure-Python (no library needed).
#
#  PRODUCTION BUILD — R.A. Aswin Krishna, IP-AI Practitioner
# ================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ─── Optional rapidfuzz acceleration ──────────────────────────────────────
try:
    from rapidfuzz.distance import Levenshtein as _RFLevenshtein
    _HAS_RAPIDFUZZ = True
except Exception:
    _HAS_RAPIDFUZZ = False


# ═══════════════════════════════════════════════════════════════════════════
#  EDIT DISTANCE
# ═══════════════════════════════════════════════════════════════════════════

def _levenshtein_pure(a: str, b: str) -> int:
    """Pure-Python Levenshtein edit distance. Used when rapidfuzz absent."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur.append(min(
                prev[j] + 1,        # deletion
                cur[j - 1] + 1,     # insertion
                prev[j - 1] + cost, # substitution
            ))
        prev = cur
    return prev[-1]


def edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance, accelerated by rapidfuzz if available."""
    if _HAS_RAPIDFUZZ:
        return _RFLevenshtein.distance(a, b)
    return _levenshtein_pure(a, b)


def edit_ratio(a: str, b: str) -> float:
    """
    Normalised similarity in [0, 1] derived from edit distance.
    1.0 = identical, 0.0 = completely different.
    """
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    dist = edit_distance(a, b)
    max_len = max(len(a), len(b))
    return 1.0 - (dist / max_len)


# ═══════════════════════════════════════════════════════════════════════════
#  PHONETIC MATCHING (pure-Python Double Metaphone, simplified)
# ═══════════════════════════════════════════════════════════════════════════

def _metaphone(word: str) -> str:
    """
    Simplified Metaphone phonetic encoding. Pure Python, no dependencies.

    This is not a full Double Metaphone implementation, but it captures the
    common phonetic equivalences that matter for trademark confusion:
      - silent letters, vowel reduction
      - PH->F, CK->K, doubled consonants collapsed
      - similar-sounding consonant groups normalised

    For trademark purposes, the goal is that "BURRBERY" and "BURBERRY"
    produce the same or near-identical codes.
    """
    if not word:
        return ""
    w = "".join(ch for ch in word.upper() if ch.isalpha())
    if not w:
        return ""

    # Common phonetic normalisations applied in order
    replacements = [
        ("PH", "F"),
        ("CK", "K"),
        ("SCH", "SK"),
        ("TH", "0"),   # voiced/unvoiced th -> placeholder
        ("GH", "G"),
        ("WR", "R"),
        ("KN", "N"),
        ("GN", "N"),
        ("WH", "W"),
        ("QU", "KW"),
        ("X", "KS"),
        ("Z", "S"),
        ("C", "K"),    # hard-c approximation
        ("V", "F"),
        ("Y", "I"),
    ]
    for old, new in replacements:
        w = w.replace(old, new)

    # Collapse doubled letters (BURRBERY -> BURBERY)
    collapsed = []
    prev = ""
    for ch in w:
        if ch != prev:
            collapsed.append(ch)
        prev = ch
    w = "".join(collapsed)

    # Drop vowels except a leading one (keeps the consonant skeleton)
    vowels = set("AEIOU")
    skeleton = []
    for i, ch in enumerate(w):
        if ch in vowels:
            if i == 0:
                skeleton.append(ch)
        else:
            skeleton.append(ch)
    return "".join(skeleton)


def phonetic_ratio(a: str, b: str) -> float:
    """
    Phonetic similarity in [0, 1] based on Metaphone-code edit ratio.
    1.0 = phonetically identical, 0.0 = completely different sounding.
    """
    ca = _metaphone(a)
    cb = _metaphone(b)
    if not ca and not cb:
        return 1.0
    if not ca or not cb:
        return 0.0
    if ca == cb:
        return 1.0
    return edit_ratio(ca, cb)


# ═══════════════════════════════════════════════════════════════════════════
#  CONTAINMENT
# ═══════════════════════════════════════════════════════════════════════════

def containment_signal(a: str, b: str) -> float:
    """
    Returns a [0, 1] signal for whether one mark contains the other.
    'SMOOTH' inside 'SMOOTH COFFEE' is a strong containment signal.
    """
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if shorter in longer:
        # Strength scales with how much of the longer mark the shorter covers
        return len(shorter) / len(longer)
    return 0.0


# ═══════════════════════════════════════════════════════════════════════════
#  COMBINED CONFLICT SCORE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SimilarityResult:
    """Result of comparing a proposed mark against one existing mark."""
    proposed_mark: str
    existing_mark: str
    existing_owner: str
    existing_class: str
    edit_ratio: float
    phonetic_ratio: float
    containment: float
    class_match: bool
    conflict_score: float          # 0-100
    risk_band: str                 # HIGH / MEDIUM / LOW / MINIMAL
    rationale: str


def score_pair(
    proposed_mark: str,
    existing_mark: str,
    proposed_class: str = "",
    existing_class: str = "",
    existing_owner: str = "",
) -> SimilarityResult:
    """
    Score a single proposed-vs-existing mark pair.

    Weights (sum to 1.0 before class multiplier):
      visual/edit:   0.45
      phonetic:      0.40
      containment:   0.15
    Same-class overlap applies a 1.0 multiplier; different class applies 0.65
    (conflict is still possible across classes for famous marks, but the base
    likelihood-of-confusion risk is lower).
    """
    er = edit_ratio(proposed_mark, existing_mark)
    pr = phonetic_ratio(proposed_mark, existing_mark)
    cm = containment_signal(proposed_mark, existing_mark)

    base = (er * 0.45) + (pr * 0.40) + (cm * 0.15)

    class_match = bool(
        proposed_class and existing_class
        and str(proposed_class).strip() == str(existing_class).strip()
    )
    multiplier = 1.0 if class_match else 0.65
    score = base * multiplier * 100

    # Legal booster: marks that are phonetically (near-)identical AND in the
    # same Nice class present a strong likelihood-of-confusion case under
    # TMA s.10(2). "Aural similarity" is an established head of confusion in
    # UK/EU trade mark law. Boost these into the HIGH band where the base
    # score lands just below it.
    if class_match and pr >= 0.95 and er >= 0.6:
        score = max(score, 78.0)
    elif class_match and pr >= 0.85 and er >= 0.7:
        score = max(score, 72.0)

    score = round(min(100.0, score), 1)

    band = (
        "HIGH" if score >= 75 else
        "MEDIUM" if score >= 50 else
        "LOW" if score >= 25 else
        "MINIMAL"
    )

    # Build a human-readable rationale
    parts = []
    if er >= 0.8:
        parts.append(f"very close spelling (edit similarity {er:.0%})")
    elif er >= 0.6:
        parts.append(f"similar spelling (edit similarity {er:.0%})")
    if pr >= 0.85:
        parts.append(f"phonetically near-identical ({pr:.0%})")
    elif pr >= 0.65:
        parts.append(f"phonetically similar ({pr:.0%})")
    if cm >= 0.5:
        parts.append("one mark substantially contains the other")
    if class_match:
        parts.append(f"same Nice class ({proposed_class})")
    else:
        parts.append("different Nice class (cross-class risk only)")
    rationale = "; ".join(parts) if parts else "low similarity on all signals"

    return SimilarityResult(
        proposed_mark=proposed_mark,
        existing_mark=existing_mark,
        existing_owner=existing_owner,
        existing_class=str(existing_class),
        edit_ratio=round(er, 3),
        phonetic_ratio=round(pr, 3),
        containment=round(cm, 3),
        class_match=class_match,
        conflict_score=score,
        risk_band=band,
        rationale=rationale,
    )


def score_against_list(
    proposed_mark: str,
    proposed_class: str,
    existing_marks: list[dict],
    min_score: float = 25.0,
) -> list[dict]:
    """
    Score a proposed mark against a list of existing marks.

    Each existing mark dict may have: mark, owner, niceClass.
    Returns a list of conflict dicts (compatible with the trademark engine's
    expected shape: mark, owner, niceClass, conflict_score) sorted by score
    descending. Only conflicts at or above min_score are returned.

    This is the key function: it converts ANY list of marks into scored
    conflicts, fixing the gap where the live search returned 0 conflicts
    for near-miss marks like BURRBERY vs BURBERRY.
    """
    results = []
    for em in existing_marks or []:
        existing_mark = em.get("mark", "") or em.get("name", "")
        if not existing_mark:
            continue
        r = score_pair(
            proposed_mark=proposed_mark,
            existing_mark=existing_mark,
            proposed_class=proposed_class,
            existing_class=em.get("niceClass", em.get("class", "")),
            existing_owner=em.get("owner", em.get("proprietor", "")),
        )
        if r.conflict_score >= min_score:
            results.append({
                "mark": r.existing_mark,
                "owner": r.existing_owner,
                "niceClass": r.existing_class,
                "conflict_score": r.conflict_score,
                "risk_band": r.risk_band,
                "edit_ratio": r.edit_ratio,
                "phonetic_ratio": r.phonetic_ratio,
                "containment": r.containment,
                "class_match": r.class_match,
                "rationale": r.rationale,
            })
    results.sort(key=lambda d: d["conflict_score"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════════════
#  WELL-KNOWN UK MARKS (small built-in watchlist)
# ═══════════════════════════════════════════════════════════════════════════
# A tiny built-in list of famous UK marks so that even with ZERO live-search
# results and ZERO uploaded competitors, an obvious near-miss like "BURRBERY"
# still flags. This is NOT a substitute for a proper register search — it is
# a safety net that prevents the embarrassing "0 conflicts" result for marks
# that are near-identical to household-name brands. The UI must make clear
# this is an indicative watchlist, not an authoritative register.

WELL_KNOWN_UK_MARKS: list[dict] = [
    {"mark": "BURBERRY", "owner": "Burberry Limited", "niceClass": "25"},
    {"mark": "TESCO", "owner": "Tesco Stores Limited", "niceClass": "35"},
    {"mark": "BARCLAYS", "owner": "Barclays Bank PLC", "niceClass": "36"},
    {"mark": "VODAFONE", "owner": "Vodafone Group PLC", "niceClass": "38"},
    {"mark": "CADBURY", "owner": "Cadbury UK Limited", "niceClass": "30"},
    {"mark": "ROLLS ROYCE", "owner": "Rolls-Royce PLC", "niceClass": "12"},
    {"mark": "MARKS SPENCER", "owner": "Marks and Spencer PLC", "niceClass": "25"},
    {"mark": "SAINSBURY", "owner": "Sainsbury's Supermarkets Ltd", "niceClass": "35"},
    {"mark": "LLOYDS", "owner": "Lloyds Bank PLC", "niceClass": "36"},
    {"mark": "HSBC", "owner": "HSBC Group", "niceClass": "36"},
    {"mark": "DYSON", "owner": "Dyson Limited", "niceClass": "07"},
    {"mark": "JAGUAR", "owner": "Jaguar Land Rover Ltd", "niceClass": "12"},
    {"mark": "HARRODS", "owner": "Harrods Limited", "niceClass": "35"},
    {"mark": "BBC", "owner": "British Broadcasting Corporation", "niceClass": "38"},
    {"mark": "SKY", "owner": "Sky Limited", "niceClass": "38"},
]


def check_against_well_known(
    proposed_mark: str,
    proposed_class: str,
    min_score: float = 60.0,
) -> list[dict]:
    """
    Check a proposed mark against the built-in famous-marks watchlist.

    Higher default threshold (60) because this is a safety-net check meant
    to catch only strong near-misses to household names, not to generate
    noise. Returns conflicts in the same shape as score_against_list.
    """
    return score_against_list(
        proposed_mark=proposed_mark,
        proposed_class=proposed_class,
        existing_marks=WELL_KNOWN_UK_MARKS,
        min_score=min_score,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  TOP-LEVEL HELPER FOR THE TRADEMARK TAB
# ═══════════════════════════════════════════════════════════════════════════

def enrich_conflicts(
    proposed_mark: str,
    proposed_class: str,
    live_results: Optional[list[dict]] = None,
    uploaded_competitors: Optional[list[dict]] = None,
    include_well_known_safety_net: bool = True,
) -> dict:
    """
    The single entry point the trademark tab should call.

    Combines three sources into one scored, deduplicated conflict list:
      1. live_results       — whatever the live UKIPO/TMview search returned
      2. uploaded_competitors — marks from a user-uploaded competitor file
      3. well-known watchlist — built-in famous-marks safety net

    Returns:
      {
        "conflicts": [ ...scored conflict dicts, sorted desc... ],
        "sources_used": [...],
        "well_known_hits": [...],
        "note": "..."
      }

    This fixes the BURRBERY gap: even if live_results is empty, the
    well-known safety net flags BURRBERY vs BURBERRY at HIGH risk.
    """
    all_existing: list[dict] = []
    sources_used = []

    if live_results:
        all_existing.extend(live_results)
        sources_used.append(f"live search ({len(live_results)} marks)")
    if uploaded_competitors:
        all_existing.extend(uploaded_competitors)
        sources_used.append(f"uploaded competitors ({len(uploaded_competitors)} marks)")

    # Score the live + uploaded marks (lower threshold, the user supplied them)
    scored = score_against_list(
        proposed_mark, proposed_class, all_existing, min_score=25.0
    )

    # Safety-net check against famous marks
    well_known_hits = []
    if include_well_known_safety_net:
        well_known_hits = check_against_well_known(
            proposed_mark, proposed_class, min_score=60.0
        )
        if well_known_hits:
            sources_used.append("famous-marks safety net")

    # Merge, deduplicating by (mark, owner)
    seen = set()
    merged = []
    for c in scored + well_known_hits:
        key = (c["mark"].strip().lower(), c.get("owner", "").strip().lower())
        if key not in seen:
            seen.add(key)
            merged.append(c)
    merged.sort(key=lambda d: d["conflict_score"], reverse=True)

    note = (
        "Conflict scores combine edit-distance, phonetic, and containment "
        "similarity, weighted by Nice-class overlap. The famous-marks safety "
        "net is indicative only and is NOT a substitute for an authoritative "
        "UKIPO/EUIPO/WIPO register search. Verify all conflicts in the "
        "official registers before relying on this assessment."
    )

    return {
        "conflicts": merged,
        "sources_used": sources_used,
        "well_known_hits": well_known_hits,
        "note": note,
    }
