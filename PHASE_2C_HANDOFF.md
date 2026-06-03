# Phase 2C — TDM & Trademark Engine Refactor (Complete)

**Status:** All 164 integration tests pass (28 Phase 2A + 47 Phase 2B + 56 + 33 Phase 2C)
**Engine version:** 2.0-phase-2c
**Files delivered:** `tdm_v2.py`, `trademark_v2.py`, `test_phase_2c.py`, `test_phase_2c_trademark.py`

---

## What changed

Phase 2C applies the same deterministic-first / LLM-as-phraser architecture from Phase 2B to the **TDM engine** and the **Trademark clearance opinion engine**.

### TDM Engine (`tdm_v2.py`)

Replaces `tdm.py`. Same drop-in signature: `tdm_risk_engine(text, analysis)`.

**Architecture:**
1. `detect_tdm_signals(text)` — pure function: contract text → 13 risk triggers + 28 mitigation signals
2. `score_tdm(signals, ...)` — pure function: signals → risk/compliance scores (0-100)
3. `select_authorities_for_tdm(text, signals)` — picks authority IDs from `CONTRACT_TDM` and `CONTRACT_AI_TRAINING` selectors
4. `render_deterministic_tdm(...)` — produces full output dict with citations from `format_citation()`
5. Optional `_try_llm_phrasing(...)` — LLM gets allowed authority IDs only; output is verified before display
6. If LLM strays → deterministic render stands unchanged

**Citation rule:** every statute and case in the output is drawn from `authority_db.AUTHORITIES`. No string-templated citations anywhere.

### Trademark Engine (`trademark_v2.py`)

Replaces `generate_trademark_ai_opinion()` in `app.py`. Same drop-in signature.

**Critical fix from v1:** The old engine cited **Sky v SkyKick [2020] UKSC 17** — this is wrong. The correct citation is **[2024] UKSC 36**, decided 13 November 2024 by Lord Kitchin. The wrong citation appeared in:
- Line 1440 of `app.py` (in the LLM prompt's "Legal Framework" instruction)
- Line 1477 of `app.py` (in the deterministic fallback template)

The v2 engine **structurally cannot** reproduce this error: every authority comes from the verified database, where Sky v SkyKick is filed under `CASE_SKY_V_SKYKICK_2024` with citation `[2024] UKSC 36`. There is no `CASE_SKY_V_SKYKICK_2020` ID. We tested this with 20 varied profiles — zero contained the wrong citation.

**Architecture:**
1. `compute_trademark_risk(...)` — pure function: search results → risk profile (HIGH/MEDIUM/LOW)
2. `select_authorities_for_trademark(profile)` — picks IDs from `TRADEMARK_CONFUSION`, `TRADEMARK_DILUTION`, plus `TRADEMARK_BAD_FAITH` when famous-mark threshold is hit
3. `render_deterministic_opinion(profile, allowed_ids)` — produces the full ~3,500-word opinion with verified citations
4. Optional `_try_llm_trademark_opinion(...)` — LLM is given allowed IDs and explicit instruction not to use `[2020] UKSC 17`
5. If LLM output fails verification → deterministic template stands

---

## Drop-in deployment

### TDM engine

On your Windows machine:
1. Back up your current `tdm.py` → `tdm_v1_backup.py`
2. Rename `tdm_v2.py` → `tdm.py`
3. Run `python test_phase_2c.py` → expect 56/56
4. Restart Streamlit. The TDM tab will use the new engine; UI is unchanged because the output shape matches v1 exactly.

### Trademark engine

The trademark engine lives **inside `app.py`** (lines 1410–1502 in `generate_trademark_ai_opinion`), so the deployment is slightly different:

**Option A — Quickest (recommended for now):**
1. Drop `trademark_v2.py` into the project folder
2. In `app.py`, find line 1410 (`def generate_trademark_ai_opinion(`)
3. Above that function, add:
   ```python
   from trademark_v2 import generate_trademark_ai_opinion as _v2_trademark_opinion
   ```
4. Replace the old function body with:
   ```python
   def generate_trademark_ai_opinion(your_mark, nice_class, description,
                                      ukipo_results, dilution_rows):
       return _v2_trademark_opinion(your_mark, nice_class, description,
                                     ukipo_results, dilution_rows)
   ```
5. Restart Streamlit.

**Option B — Cleaner (when you have time):** Move `generate_trademark_ai_opinion` and `trademark_dilution_scanner` into their own module (`trademark.py`), import from there in `app.py`. This is a refactor task, not urgent.

---

## Behavioural changes

### TDM engine

1. **Empty-text guard preserved** — empty input produces `risk_score=0, level="N/A", compliance=0` (not the misleading "100% compliance" that the pure complement-of-risk formula would give).

2. **Mitigation signals expanded** — 28 mitigation phrases now detected (v1 had 21). New additions include "machine-readable reservation", "article 4(3)", "section 29a", "ai act".

3. **Citation precision improved** — every statute citation in the output now uses the exact form from the verified authority database. No more risk of "CDPA s.29A" vs "CDPA section 29A" vs "Section 29A CDPA 1988" inconsistency.

4. **Confidence cap raised to 85 (from 68) when LLM phrasing verifies** — but only when verification passes. Deterministic-only mode is still capped at 68.

### Trademark engine

1. **Sky v SkyKick citation is now correct** — `[2024] UKSC 36`, not `[2020] UKSC 17`.

2. **Lidl v Tesco [2024] EWCA Civ 262 is referenced explicitly** for unfair-advantage analysis. The v1 prompt mentioned "Lidl v Tesco [2024] UKCA" with incorrect format; the v2 always uses the verified citation.

3. **Famous-mark threshold (>85) now triggers TRADEMARK_BAD_FAITH and TRADEMARK_DESCRIPTIVE selectors** — broader authority pool when reputation is at stake.

4. **Recommendation logic is structured** — Proceed to file / Proceed with clearance review / Proceed with modifications / Conduct further clearance / Abandon, mapped deterministically from the conflict counts. No LLM "vibes" classification.

5. **LLM prompt now explicitly forbids `[2020] UKSC 17`** — belt-and-braces in case the verifier missed an edge case. (It won't, but defence in depth.)

---

## What this means for your manuscript

Your EIPR manuscript footnote that cites Sky v SkyKick should use **[2024] UKSC 36**. If you cited it as `[2020] UKSC 17` anywhere, that's wrong and should be corrected before publication. Lord Kitchin's leading judgment, decided 13 November 2024, is the controlling authority.

The other corrections from Phase 2A (CPR 46.21 IPEC cap, etc.) are unchanged. Refer back to `SELF_AUDIT_REPORT_FINAL.md` if you need the complete list.

---

## Test coverage

| Suite | Tests | Status |
|---|---|---|
| Phase 2A (authority database) | 28 | ✓ all pass |
| Phase 2B (PRPP engine) | 47 | ✓ all pass |
| Phase 2C TDM | 56 | ✓ all pass |
| Phase 2C Trademark | 33 | ✓ all pass |
| **Total** | **164** | **✓** |

The trademark suite includes a stress test that generates 20 varied profiles (different mark names, conflict counts, score thresholds) and verifies that none of them produce the wrong `[2020] UKSC 17` citation. This is the kind of test you can defensibly point to when explaining the "negligible hallucination" claim: it's not aspirational, it's enforced by test infrastructure.

---

## What's NOT yet refactored

The following still use older patterns and should be addressed in later phases:

| Engine | Location | Phase | Notes |
|---|---|---|---|
| `cross_check_contract` | `app.py` ~723 | Phase 2D | Contract analyser; touches several other paths |
| `high_research_mode_analysis` | `app.py` ~882 | Phase 2D | Deep-research mode for documents |
| `copyright_radar` | `app.py` ~995 | Phase 2D | Clause-level copyright analysis |
| `generate_safer_version` | `app.py` ~1882 | Phase 2D | Drafter — delicate; touches generated content quality |
| `playbook.py` | Standalone | Phase 2D (light) | TF-IDF only; no LLM citation hallucination risk |
| `build_brief.py` / `build_paper.py` | Standalone | Phase 2D (light) | PDF builders; some hardcoded citations to check |

The high-priority items are `cross_check_contract` and `generate_safer_version` — both call the LLM with hardcoded prompt content that could fabricate citations. The drafter especially needs care because the output is meant for the user to send to a counterparty.

---

## What's next

Phase 2C is done. You have three choices:

**A. Deploy and test before going further.** Drop the two new files into your project, swap the old `tdm.py`, wire up the trademark import in `app.py`, restart Streamlit, run a real client matter through it. See what surprises you. This is the safest path.

**B. Continue to Phase 2D.** Refactor the remaining engines in `app.py`. Same architecture, more surface area. Estimated 10-15 hours Claude work.

**C. Skip ahead to Phase 2.5 (data protection).** If you're getting close to using Libra on real client data, the data-protection layer matters more than refactoring the drafter. This is the regulatory-lawyer consultation we flagged earlier.

My recommendation: do A first. Even with the tests passing, the proof is in actually using it on the test scenarios in `test_documents_docx/`. If you find issues, we fix them before adding more refactored engines on top.

Ready when you are.
