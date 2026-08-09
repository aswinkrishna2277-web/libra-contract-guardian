"""
negation_guard.py — Libra Contract Guardian
============================================

PURPOSE
    Signal detection across the PRPP and TDM engines is substring matching:
    if the term "scrape" appears, the scraping signal fires. That is fast,
    deterministic and auditable — but it cannot tell a PERMISSION from a
    PROHIBITION. Two defects confirmed by stress testing:

      PRPP:  "NO evidence the work was in any training corpus ...
              nothing was deleted"            -> scored 71/100 "Moderate"
      TDM:   "expressly prohibits any dataset creation. There shall be
              no scraping, no crawling, no data mining"
                                              -> scored 36/100 "Medium risk"

    In both cases maximally EXCULPATORY or PROTECTIVE drafting was scored as
    risk. For a contract-analysis tool this is close to a core-competence
    failure: rewarding good drafting is the point.

APPROACH
    A term's signal is suppressed only when a negation genuinely GOVERNS it.
    Two precision rules keep this from over-suppressing:

      1. LOOK BACKWARD ONLY. A negation governs what follows it, not what
         precedes it. So "may scrape any source without restriction" is NOT
         suppressed — "without" attaches to "restriction", and it sits after
         "scrape" in any event.

      2. STOP AT THE SENTENCE BOUNDARY. A negation in a previous sentence
         does not govern this one. "The Company shall not be liable for loss.
         The Company may scrape data." must keep the scraping signal.

    Erring toward NOT suppressing is deliberate: a missed suppression costs
    a false positive the reviewer will notice, while an over-eager
    suppression hides real risk, which is the more dangerous direction.

AUDIT
    Every suppression is returned to the caller so it can be logged. If an
    assessment is ever questioned, the record shows precisely which signal
    was suppressed and on the strength of which negation.
"""

from __future__ import annotations

import re

# Words that genuinely negate what follows. Deliberately conservative:
# ambiguous quantifiers such as "without" are excluded, because "used
# without a licence for training" is a real risk, not a prohibition.
_NEGATION_WORDS = [
    "no", "not", "never", "neither", "nor", "none", "nothing",
    "cannot", "shall not", "may not", "must not", "will not",
    "prohibit", "prohibits", "prohibited", "prohibiting",
    "forbid", "forbids", "forbidden", "forbidding",
    "exclude", "excludes", "excluded", "excluding", "exclusion",
    "refrain", "prevented", "precluded", "barred",
    "disallow", "disallows", "disallowed",
]

# Passive prohibitions put the negation AFTER the term:
#   "Data mining is forbidden."      "Machine learning use is excluded."
#   "Scraping shall be prohibited."  "Training is not permitted."
# A backward-only scan cannot see these, so a tightly-bounded forward scan is
# needed. It is deliberately restricted to a copula followed by a prohibition
# word, so that ordinary following text cannot suppress a signal by accident.
_PASSIVE_PROHIBITION = re.compile(
    r"^[^.;:!?\n]{0,60}?\b(?:is|are|was|were|shall\s+be|will\s+be|may\s+be|being)\s+"
    r"(?:expressly\s+|strictly\s+|specifically\s+)?"
    r"(?:not\s+permitted|not\s+allowed|prohibited|forbidden|excluded|barred|"
    r"disallowed|precluded|impermissible)",
    re.IGNORECASE,
)

# Built once: word-boundary alternation, longest first so "shall not" wins
# over a bare "not".
_NEG_PATTERN = re.compile(
    r"\b(" + "|".join(
        re.escape(w) for w in sorted(_NEGATION_WORDS, key=len, reverse=True)
    ) + r")\b",
    re.IGNORECASE,
)

# A negation more than this many characters before the term is unlikely to
# govern it even within the same sentence.
_MAX_LOOKBACK = 80

# Sentence terminators: a negation before one of these is in a prior clause
# or sentence and does not govern the current term.
_BOUNDARY = re.compile(r"[.;:!?\n]")


def _governing_negation(text_lower: str, term_start: int,
                        term_end: int | None = None) -> str | None:
    """
    Return the negation word governing the term at `term_start`, or None.

    Checks two constructions:
      • ACTIVE  — a negation BEFORE the term ("there shall be no scraping"),
        found by looking backward to the nearest sentence boundary.
      • PASSIVE — a prohibition AFTER the term ("data mining is forbidden"),
        found by a tightly-bounded forward scan for a copula plus a
        prohibition word.
    """
    window_start = max(0, term_start - _MAX_LOOKBACK)
    window = text_lower[window_start:term_start]

    # Truncate at the last sentence boundary inside the window: anything
    # before it belongs to a previous sentence.
    boundaries = list(_BOUNDARY.finditer(window))
    if boundaries:
        window = window[boundaries[-1].end():]

    matches = list(_NEG_PATTERN.finditer(window))
    if matches:
        return matches[-1].group(1)

    # Passive construction: "<term> ... is prohibited"
    if term_end is not None:
        tail = text_lower[term_end:term_end + 80]
        m = _PASSIVE_PROHIBITION.search(tail)
        if m:
            return m.group(0).strip().split()[-1]

    return None


def term_is_negated(text: str, term: str) -> tuple[bool, str | None]:
    """
    Is EVERY occurrence of `term` in `text` governed by a negation?

    Returns (is_negated, example_negation_word).

    Requires ALL occurrences to be negated. One unnegated occurrence means
    the practice is permitted somewhere in the document, so the signal must
    stand — a contract that prohibits scraping in clause 3 but permits it in
    clause 9 is a risk, not a protection.
    """
    if not text or not term:
        return False, None

    tl = text.lower()
    t = term.lower()

    found_any = False
    example: str | None = None

    start = 0
    while True:
        idx = tl.find(t, start)
        if idx == -1:
            break
        found_any = True
        neg = _governing_negation(tl, idx, idx + len(t))
        if neg is None:
            # An unnegated occurrence exists — signal stands.
            return False, None
        example = example or neg
        start = idx + len(t)

    if not found_any:
        return False, None
    return True, example


def filter_negated_terms(text: str, terms: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    """
    Split matched terms into those that stand and those that are negated.

    Returns (surviving_terms, suppressed) where `suppressed` is a list of
    (term, negation_word) pairs suitable for an audit log.
    """
    surviving: list[str] = []
    suppressed: list[tuple[str, str]] = []
    for term in terms or []:
        negated, neg_word = term_is_negated(text, term)
        if negated:
            suppressed.append((term, neg_word or "negation"))
        else:
            surviving.append(term)
    return surviving, suppressed
