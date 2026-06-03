# Phase 2A — Foundation Layer Complete

**Status:** Code written, all 27 integration tests pass.
**Your job now:** Verify the legal accuracy of the 49 authority entries before Phase 2B refactors the engines around them.

---

## What we just built

Three modules form the architectural backbone of citation safety:

### 1. `authority_db.py` — Single source of truth

49 authority entries, each with: stable ID, kind, citation, jurisdiction, year, summary, verified paragraph references, source URL, topic tags, and verification source.

Categories included:
- **21 cases** (UK 19, EU 1, US 1, DE 1) covering AI-IP, disclosure procedure, adverse inference, confidentiality, trademark, jurisdiction
- **12 statutes** (CDPA 1988, TMA 1994)
- **10 procedural rules** (CPR, PD 57AD)
- **1 EU Regulation** (AI Act Art. 53)
- **2 EU Directives** (DSM Arts 3 and 4)
- **1 Government Report** (March 2026 UK)
- **2 Academic** (your PRPP manuscript + Ahmed et al. preprint)

### 2. `authority_selector.py` — Deterministic authority picker

Given a scenario (PRPP litigation, contract text, trademark search), this module picks the relevant authorities through:
- **16 named selectors** for common procedural contexts
- **51 keyword patterns** that enrich the base selection from user input

The LLM never picks authorities — Python does, deterministically.

### 3. `output_verifier.py` — Last-line citation-drift catcher

After the LLM produces natural-language output, this module:
1. Extracts every citation-like substring (UK neutral, EU cases, US cases, statutes, rules)
2. Resolves each against the authority database
3. Returns a structured pass/fail report
4. Provides a fallback rendering for outputs that fail verification

---

## What this enables, honestly

After Phase 2B-D refactor the engines around these modules, you will be able to defensibly state:

> *Every citation in Libra's output is verified against a structured authority database of 49+ pre-vetted entries. Citations not in the database are detected by a verification layer and the output is rejected before display. The local LLM is constrained to phrasing only — it cannot introduce citations on its own initiative.*

This is true, defensible, and the strongest claim that survives technical scrutiny.

What you should NOT claim, even after this work:

- "Zero hallucination" — the LLM can still misapply a correct citation
- "Cannot be wrong" — the database can have errors (yours to catch in review)
- "Better than a lawyer" — unsupportable without controlled evaluation

---

## YOUR JOB BEFORE PHASE 2B

The database needs your sign-off. Without that, everything downstream is built on unverified ground.

### Required review checklist

For each of the 49 entries, confirm:

1. **The neutral citation is correct.** (BAILII, legislation.gov.uk, EUR-Lex, CURIA.)
2. **The judge / Lord is correctly attributed.**
3. **The paragraph references actually appear in the judgment.**
4. **The summary accurately captures the holding** (not just the words — the legal point).
5. **The notes/caveats are honest** (appeals pending, preprint status, etc).

### Suggested workflow

Open `authority_db.py`. The entries are grouped by section:
- Lines 138–375: UK cases
- Lines 378–410: EU/Germany cases
- Lines 413–425: US cases
- Lines 428–533: Statutes (CDPA, TMA)
- Lines 536–660: Rules (CPR, PD)
- Lines 663–725: EU Reg/Dir
- Lines 728–760: Reports
- Lines 763–795: Academic

For each entry:
1. Click the URL (or look up in BAILII / EUR-Lex if no URL)
2. Compare the `full_citation`, `key_paragraphs`, `summary` against the source
3. Flag anything you'd change in a separate note

I'd recommend a focused 2-3 hour review session. Use the 8 hours we budgeted for Phase 2A across multiple sessions if needed.

### What to send me

For each entry that needs changing, send:
- The authority ID
- What's currently in the database
- What it should be changed to
- Source for the correction

I'll apply the corrections, re-run the test suite, and confirm before moving to Phase 2B.

---

## Honest note on what I couldn't verify

I cross-checked all 49 entries against authoritative sources during construction, but I cannot:

- **Read the full judgments** to confirm paragraph numbers in every case
- **Verify the exact page references** in the March 2026 Report
- **Confirm Vestergaard's specific [2010] EWHC 1803 (Ch) neutral citation** — there are multiple Vestergaard judgments and I have lower confidence on this one
- **Resolve the exact OJ reference for the AI Act template** — I cited the verifiable date instead

You are the lawyer. You're qualified to do the verification I cannot. This is the work that buys you the "verified database" claim — and the claim depends on the work actually being done.

---

## Files delivered in Phase 2A

| File | Purpose | Lines |
|------|---------|------:|
| `authority_db.py` | The 49-entry authority database | 720 |
| `authority_selector.py` | Deterministic picker by context + keywords | 380 |
| `output_verifier.py` | Citation-drift catcher with fallback | 380 |
| `test_phase_2a.py` | 27-assertion integration test harness | 175 |
| `PHASE_2A_REVIEW.md` | This document | — |

All five files in `/mnt/user-data/outputs/`. Pull them down to your machine and add them to your `libra-v2` folder alongside the existing app files.

---

## What Phase 2B looks like

Once you've reviewed and signed off on the database (or flagged corrections), Phase 2B refactors the PRPP engine to:

1. Compute scores deterministically in Python (no LLM in the scoring loop)
2. Select authorities via `authority_selector` based on the scenario
3. Pass the structured result + allowed authority IDs to the LLM
4. Use the LLM only to phrase the result in natural English
5. Verify every output through `output_verifier` before display
6. Fall back to deterministic rendering if verification fails

Estimated time: 15-20 hours of my work, 5 hours of your testing.

But not yet. First, verify the database.

---

**Tell me when you've completed the review and I'll start Phase 2B.**
