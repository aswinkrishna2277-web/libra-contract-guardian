# Trademark Fuzzy-Matching Fix — Deployment Note

## What this fixes

When you tested `BURRBERY` in class 25, the trademark tab returned **0 conflicts, LOW RISK** — because the live UKIPO search does exact-token matching and never connected `BURRBERY` to the famous `BURBERRY`.

After this fix, the same input returns:
- **Risk Level: HIGH**
- **1 conflict: BURBERRY (Burberry Limited, Class 25) — 78%**
- Correct statutory provision cited (TMA 1994 s.10(2))
- Correct case citations throughout ([2024] UKSC 36, not [2020] UKSC 17)

## How it works

A new module, `trademark_similarity.py`, scores any proposed mark against any list of existing marks using three signals:

1. **Edit-distance similarity** — how many character changes separate the two marks (`BURRBERY` is 2 edits from `BURBERRY`)
2. **Phonetic similarity** — do they sound the same? (`BURRBERY` and `BURBERRY` both encode to the phonetic skeleton `BRBR` — identical)
3. **Containment** — is one mark inside the other? (`SMOOTH` inside `SMOOTH COFFEE`)

These combine into a 0-100 conflict score, weighted by whether the marks are in the same Nice class. A legal booster recognises that marks which are phonetically near-identical in the same class present a strong likelihood-of-confusion case under TMA s.10(2) — "aural similarity" is an established head of confusion in UK/EU trade mark law.

### The famous-marks safety net

Even with **zero** live-search results and **zero** uploaded competitors, the module checks the proposed mark against a small built-in watchlist of famous UK marks (Burberry, Tesco, Barclays, Vodafone, etc). This is the layer that catches `BURRBERY` when the live search finds nothing.

**Important honesty point:** this watchlist is indicative only. It is NOT a substitute for an authoritative register search. The module's output includes a note saying exactly this, and the UI should surface that note. The watchlist exists to prevent the embarrassing "0 conflicts" result for obvious near-misses to household names — not to replace a proper clearance search.

## Dependencies

The module uses `rapidfuzz` if it is installed (fast C implementation), but falls back to a pure-Python edit-distance implementation if not. **You do not have to install anything.** If you want the faster version:

```
venv\Scripts\activate
pip install rapidfuzz
```

But it works fine without it. The phonetic matching is entirely pure-Python with no dependencies.

## Deployment

In `C:\Users\aswin\OneDrive\Desktop\Libra version 2\`:

1. Drop in two new files:
   - `trademark_similarity.py` (the new module)
   - `test_trademark_similarity.py` (its test suite)
2. Overwrite one file:
   - `trademark_v2.py` (now calls the similarity module)
3. Stop Streamlit (Ctrl+C), then:
   ```
   venv\Scripts\activate
   python test_trademark_similarity.py
   python test_phase_2c_trademark.py
   streamlit run app.py
   ```
   Expect both test suites to pass.
4. Retest the trademark tab with `BURRBERY` / class 25.

## What you should see now

The dashboard at the top may still show "Live API search returned no results" — that is the upstream UKIPO API, which we have not changed. But the **opinion** below it will now correctly identify BURBERRY as a HIGH-risk conflict, because the similarity layer runs regardless of what the live API returns.

This is the right architecture: the live API is one input among several (live results + uploaded competitors + famous-marks safety net), and the similarity layer scores all of them. The opinion no longer depends solely on the live API working.

## Calibration reference

How the scorer bands example pairs (same class):

| Proposed | Existing | Score | Band |
|---|---|---|---|
| BURRBERY | BURBERRY | 78% | HIGH |
| GOOG3L | GOOGLE | 78% | HIGH |
| TESC0 | TESCO | ~78% | HIGH |
| NEXFLIX | NETFLIX | 67% | MEDIUM |
| SMOOTH COFFEE | SMOOTH | 52% | MEDIUM |
| LINNEBORG | LINDBERG | 63% | MEDIUM |
| XYZQVOR | BURBERRY | 12% | MINIMAL |

Note that identical marks in *different* classes score lower (e.g. BURBERRY/BURBERRY across class 25 vs 18 = 65% MEDIUM), correctly reflecting that cross-class conflict is weaker than same-class conflict for non-famous marks.

## What this does NOT do

- It does not search the live UKIPO/EUIPO/WIPO registers. That is the separate API/firewall question we discussed and parked.
- The famous-marks watchlist is 15 entries — it catches household names, not the full register.
- For authoritative clearance, the manual search links to UKIPO/EUIPO/WIPO remain the source of truth.

The honest framing for a demo: "Libra runs phonetic and edit-distance similarity against live-search results, any competitor list you upload, and a built-in famous-marks safety net. For an authoritative clearance, it points you to the official registers. The similarity layer means it won't miss an obvious near-miss like a one-letter variation on a household brand — which most exact-match tools do miss."

## Test status

| Suite | Tests | Status |
|---|---|---|
| Phase 2A | 28 | ✓ |
| Phase 2B | 47 | ✓ |
| Phase 2C TDM | 56 | ✓ |
| Phase 2C Trademark | 33 | ✓ |
| Phase 2C-fix (ID leak) | 60 | ✓ |
| Trademark similarity | 31 | ✓ |
| **Total** | **255** | **✓** |
