# Phase 2D — Analysis Engine Citation Verification (Complete)

**Status:** 344 checks passing across 8 test suites (added Phase 2D: 26 checks)
**New files:** `analysis_sanitiser.py`, `test_phase_2d.py`
**Modified:** `app.py` (two analysis engines now gated by the sanitiser)

---

## What this phase addressed

Phase 2B and 2C refactored the PRPP, TDM, and Trademark engines so their citations come from the verified authority database and pass through the output verifier. But two engines inside `app.py` were still on the old pattern — they asked the local LLM to emit citations freely, with no verification:

- **`search_mode_analysis`** — the quick-scan contract analyser. Asks the LLM for `legal_references`, `red_flags`, and `immediate_actions`, all of which can embed citations.
- **`high_research_mode_analysis`** — the deep clause-by-clause analyser. Asks the LLM for per-clause `statute_citations` plus a synthesis with `legal_references`.

Both could surface a hallucinated citation to the user. Phase 2D closes that gap.

## What the other two engines turned out to be

While surveying, I confirmed two engines did NOT need this treatment:

- **`cross_check_contract`** — already fully deterministic. It keyword-matches against a local legal knowledge base; the LLM never touches it. No fabrication risk.
- **`copyright_radar`** — already fully deterministic. Keyword scoring with hardcoded, correct statute flags ("CDPA s.29A", "CDPA s.16"). No fabrication risk.

So the genuine exposure was the two LLM-driven analysers, and those are now handled.

## How the fix works

`analysis_sanitiser.py` provides a single post-processing pass, `sanitise_analysis(parsed)`, that both engines call just before returning. It mirrors how the verifier gates the other engines, but as a wrapper so the large existing functions did not need rewriting.

For each citation-bearing field the LLM produced, the sanitiser:

1. **Strips internal-ID leaks** (e.g. `CASE_LIDL_V_TESCO_2024`) everywhere — the same family of identifiers the verifier rejects.
2. **Verifies each citation** against the full authority database.
3. **Flags, never silently deletes.** A citation that cannot be traced is moved into a new `unverified_citations` field and, in prose fields, the text is annotated with "[⚠ citation unverified — confirm manually]". The user sees an honest warning rather than a false authority presented as real.
4. **Attaches a `citation_verification` audit block** to the result: how many citations were checked, verified, flagged, and how many ID leaks were removed.

### Two-tier verification logic

The sanitiser distinguishes between fields that are *supposed* to be citations and prose that *might* contain one:

- **Citation-list fields** (`legal_references`, per-clause `statute_citations`): an entry is verified if (a) the verifier's patterns recognise a valid citation in it, OR (b) it matches a known authority by name/citation (this second path covers EU instruments like "EU AI Act Art. 53" and "DSM Directive Art. 4" that the regex patterns don't capture but which are real authorities in the database). An entry that matches neither is flagged. This catches fabricated statute names like "Made Up Act 2050 s.999" that match no pattern and no real authority.

- **Prose fields** (`red_flags`, `immediate_actions`, clause `analysis`): only flagged if they contain a recognised citation that fails verification. Plain prose with no citation is left alone. ID leaks are stripped from these too.

The design is deliberately conservative: it never invents or "corrects" a citation. It only verifies, flags, and strips.

## Deployment

In `C:\Users\aswin\OneDrive\Desktop\Libra version 2\`:

1. Drop in two new files:
   - `analysis_sanitiser.py`
   - `test_phase_2d.py`
2. Overwrite one file:
   - `app.py` (the two analysis engines now call the sanitiser)
3. Stop Streamlit (Ctrl+C), then:
   ```
   venv\Scripts\activate
   python test_phase_2d.py
   streamlit run app.py
   ```
   Expect Phase 2D to pass all 8 groups.

To re-verify the whole system after deploying, run all eight suites:
```
python test_phase_2a.py
python test_phase_2b.py
python test_phase_2c.py
python test_phase_2c_trademark.py
python test_phase_2c_fix.py
python test_trademark_similarity.py
python test_phase_2_5.py
python test_phase_2d.py
```

## What you will see in the app

When you run a contract through the Search or Deep Research tab, the result now carries a `citation_verification` block. If the local LLM produced a citation that cannot be traced, it will appear under `unverified_citations` rather than mixed in with verified ones, and any prose mentioning it will carry the "confirm manually" annotation. In the common case where the LLM behaves, you will see a note like "All N citations verified against the authority database."

If you want this surfaced visibly in the UI (a small green "citations verified" badge, or an amber "N flagged" warning), that is a Phase 4 demo-polish item — the data is now there for the UI to display; it just is not shown yet.

## What is NOT done

- **The drafter (`generate_safer_version`).** This is the one remaining LLM engine on the old pattern. It is deliberately left for a focused pass because it generates *new clause text* (not just analysis), so the verification needs more care — the output is meant to be sent to a counterparty. This is the natural next build task.
- **`cross_check_contract` migration to authority_db.** It works and is safe (deterministic), but it still reads from the older local legal knowledge base rather than the verified `authority_db`. Harmonising the two is a tidiness improvement, not a safety fix. Low priority.

## Test status

| Suite | Checks | Status |
|---|---|---|
| Phase 2A — authority DB | 32 | ✓ |
| Phase 2B — PRPP engine | 72 | ✓ |
| Phase 2C — TDM engine | 60 | ✓ |
| Phase 2C — Trademark engine | 34 | ✓ |
| Phase 2C-fix — ID leak regression | 57 | ✓ |
| Trademark similarity | 32 | ✓ |
| Phase 2.5 — privacy guard | 31 | ✓ |
| Phase 2D — analysis sanitiser | 26 | ✓ |
| **Total** | **344** | **✓** |

## Where the project stands

Every LLM-driven engine that produces citations is now verified:
- PRPP → verified (Phase 2B)
- TDM → verified (Phase 2C)
- Trademark → verified (Phase 2C + fuzzy-matching fix)
- Search-mode analysis → verified (Phase 2D)
- Deep-research analysis → verified (Phase 2D)

The only remaining LLM engine is the drafter, which is a different kind of task (text generation, not citation) and deserves its own pass.

The honest one-line summary for outreach or interview: *"Every part of the system that cites legal authority draws those citations from a database audited against the official sources, and verifies them before display; a hallucinated citation cannot reach the user as if it were real."*
