# Phase 2C Hotfix — Authority-ID Leak Prevention

## What you found

When you ran the trademark tab with `BURRBERY`, the opinion contained this line:

> "consult case law such as Lidl v Tesco ([CASE_LIDL_V_TESCO_2024]) for guidance"

That `[CASE_LIDL_V_TESCO_2024]` is an internal authority identifier from `authority_db.py`. It should never appear in user-facing output. The bug: the LLM prompt was showing the IDs to the LLM in the "ALLOWED AUTHORITIES" block, and Mistral 7B copied them verbatim.

## What also happened (worth understanding)

The trademark tab also showed `0 conflicts / LOW RISK` for `BURRBERY` in class 25. That is NOT a fix-needed issue with the v2 engine — it's a separate problem with the upstream live API search not finding `BURBERRY` as a fuzzy near-match to `BURRBERY`. The v2 engine correctly produced a LOW-risk opinion because the upstream search told it there were zero conflicts.

That dashboard issue is real but separate. It's a UKIPO-search-fuzziness problem, not a citation problem. Park it for now — we'll fix it later. The headline issue today is the citation/ID leak, and that's what this hotfix solves.

## What changed

Five files were modified, in defence-in-depth order:

### 1. `authority_selector.py` — IDs no longer shown to LLM

The `authorities_to_prompt_block()` function used to render each authority with its internal ID visible (`[CASE_LIDL_V_TESCO_2024]`). The LLM saw this and copied it into its output as if it were a citation form.

The function now renders only the human-facing forms: `short_name` and `full_citation`. The LLM never sees internal IDs in the prompt, so it can never copy them.

### 2. `output_verifier.py` — verifier now rejects ID leaks defensively

Added a regex pattern that detects any text matching `CASE_*`, `STATUTE_*`, `RULE_*`, `REG_*`, `DIR_*`, `REPORT_*`, or `ACADEMIC_*` (the seven kinds of authorities in the database).

If `verify()` finds any of these patterns in LLM output, it rejects the output immediately with `is_valid=False` and a diagnostic reason. This is the second line of defence — if a future engine or future LLM somehow gets an ID into the prompt, the verifier will catch it before the user sees it.

### 3. `prpp_v2.py` — prompt strengthened

The PRPP phrasing prompt was rewritten to:
- explicitly forbid bracket-tag forms like `[CASE_FOO]`
- explicitly forbid ALL_CAPS_WITH_UNDERSCORES author names
- show citation examples ("PD 57AD", "Wisniewski v Central Manchester HA [1998] EWCA Civ 596")
- explicitly ban the seven ID prefixes in the JSON output instruction

### 4. `tdm_v2.py` — prompt strengthened

Same treatment as PRPP. The TDM phrasing prompt now explicitly bans ID leaks and shows correct citation form examples for CDPA, DSM, EU AI Act, and Kneschke.

### 5. `trademark_v2.py` — prompt strengthened

Same treatment, plus an explicit instruction:
> Do NOT cite Sky v SkyKick as "[2020] UKSC 17". The correct citation is "[2024] UKSC 36" (Lord Kitchin, 13 November 2024).

### 6. `test_phase_2a.py` — one test corrected

There was a Phase 2A test that asserted the prompt block CONTAINED IDs. After this fix, the prompt block does NOT contain IDs — so the test was inverted to assert the opposite. Same test, opposite truth condition. This was a documentation/test fix, not a code regression.

### 7. NEW: `test_phase_2c_fix.py` — 60 regression tests

A new test suite locks in the fix. It tests:
- The prompt block contains no internal IDs
- The verifier rejects all seven kinds of ID leaks
- Clean output (with proper citations) still passes
- 20 stress-test trademark profiles produce zero ID leaks
- 20 stress-test profiles produce zero `[2020] UKSC 17` wrong citations

This regression suite prevents the bug from coming back silently.

## Deployment

Same procedure as Phase 2C, just more files to swap.

### On your Windows machine

In `C:\Users\aswin\OneDrive\Desktop\Libra version 2\`:

**Files to replace (drop in, overwrite):**
1. `authority_selector.py` (prompt block no longer leaks IDs)
2. `output_verifier.py` (rejects ID leaks defensively)
3. `prpp_v2.py` — if you renamed it to `prpp.py`, overwrite that too
4. `tdm_v2.py` — if you renamed it to `tdm.py`, overwrite that too
5. `trademark_v2.py` (stronger prompt instructions)

**Files to back up first (rename `_old.py`) just in case:**
- Same as above. Keep the previous versions safely so you can roll back.

**Files to add:**
6. `test_phase_2a.py` (overwrites — has corrected assertion)
7. `test_phase_2c_fix.py` (new — regression test for this fix)

### Order of operations

1. Stop Streamlit if it's running (Ctrl+C in the terminal)
2. Back up any of the 5 files you're replacing (rename to `<filename>_pre_hotfix.py`)
3. Drop in the new versions from Downloads
4. Activate venv: `venv\Scripts\activate`
5. Run all five test suites:
   ```
   python test_phase_2a.py
   python test_phase_2b.py
   python test_phase_2c.py
   python test_phase_2c_trademark.py
   python test_phase_2c_fix.py
   ```
   Expected: every one says `✓ ALL TESTS PASSED`. Total: 224 tests.
6. Restart Streamlit: `streamlit run app.py`
7. Test the trademark tab again with `BURRBERY` / class 25 / clothing description

## What to look for after deployment

Run the trademark test again. The opinion should now contain:

- **Section 3:** "SkyKick UK Ltd v Sky Ltd [2024] UKSC 36" (full citation on first mention) and "Sky v SkyKick" (short form on later mentions)
- **Section 3 or 7:** "Lidl Great Britain Ltd v Tesco Stores Ltd [2024] EWCA Civ 262" or "Lidl v Tesco" — NOT `[CASE_LIDL_V_TESCO_2024]`
- **Anywhere:** NO occurrences of `CASE_*`, `STATUTE_*`, `RULE_*`, `REG_*`, `DIR_*`, `REPORT_*`, or `ACADEMIC_*`

If you DO see any of those patterns, something didn't deploy correctly — go back and check that all five replaced files are the new versions.

## What this means

The leak you found was a real bug that the previous test suite missed because the test only checked "do the citations match allowed authorities" — and the leaked ID happened to be a valid allowed authority. The fix has two layers: (1) the LLM no longer sees IDs to copy from, and (2) even if it somehow did, the verifier would catch and reject them.

This is the kind of bug that's only catchable by running the system on real inputs, which is exactly what you did. Good catch.

## Separately: the upstream search problem

The fact that `BURRBERY` returned zero UKIPO conflicts is a separate issue worth tracking:

- The live API (TMview / UKIPO) probably searches exact-token matches and won't fuzzy-match `BURRBERY` against `BURBERRY`
- The v2 trademark engine includes a phonetic-similarity scorer (`trademark_dilution_scanner`) that WOULD have flagged this — but it only runs when competitor files are uploaded; it doesn't run against UKIPO search results

This is fixable but not urgent for the citation-fix testing. The opinion engine itself is now leak-free; the upstream search quality is a separate workstream we can pick up in Phase 2D or 2.5.

## Status after hotfix

| Suite | Tests | Status |
|---|---|---|
| Phase 2A — authority database | 28 | ✓ |
| Phase 2B — PRPP engine | 47 | ✓ |
| Phase 2C — TDM engine | 56 | ✓ |
| Phase 2C — Trademark engine | 33 | ✓ |
| Phase 2C-fix — ID leak regression | 60 | ✓ |
| **Total** | **224** | **✓** |
