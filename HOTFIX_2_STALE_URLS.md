# Phase 2C Hotfix #2 — Stale Legal Source URLs

## What you saw

In the Legal Database Status panel (the one showing ✅ / ❌ for each legal source), two sources were marked ❌:

- ❌ UK Govt March 2026 Report on Copyright & AI
- ❌ PD 57AD (Business & Property Courts)

The ❌ does **not** mean the authority is invalid or unverified. It means Libra's `refresh_legal_database()` function pinged the configured URL and got back something other than HTTP 200.

## Diagnosis

These were not bugs in the v2 engines. They were stale URLs in `PUBLIC_LEGAL_SOURCES` (in `app.py`) that pointed to old paths the gov sites had reorganised.

The verifier and engines themselves never used these URLs — they're purely for the "are these public sources reachable?" health check shown in the sidebar.

### The actual URL changes

**March 2026 Report:**
- Old (broken): `https://www.gov.uk/government/publications/copyright-and-artificial-intelligence`
- New (works): `https://www.gov.uk/government/publications/report-and-impact-assessment-on-copyright-and-artificial-intelligence`

The old URL pointed at the December 2024 *consultation* page. The actual *report* (published 18 March 2026) is at the `report-and-impact-assessment-on-` path.

**PD 57AD:**
- Old (broken): `https://www.justice.gov.uk/courts/procedure-rules/civil/rules/pd_part57ad`
- New (works): `https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-57a-business-and-property-courts/practice-direction-57ad-disclosure-in-the-business-and-property-courts`

The Civil Procedure Rules section of `justice.gov.uk` was reorganised in 2024. The old `pd_part57ad` shortcut now 404s. The canonical URL uses the longer path.

## What I changed

Two files were updated:

### 1. `app.py`

- `PUBLIC_LEGAL_SOURCES`: corrected both URLs (lines 697-698)
- `refresh_legal_database()`: made the ping more forgiving:
  - Tries HEAD first (less bandwidth), falls back to GET
  - Follows redirects (`allow_redirects=True`) — gov.uk often 301s to canonical URLs
  - Treats any 2xx or 3xx response as ✅ (was only treating 200 as ✅)
  - Bumped timeout from 8s to 12s — gov.uk and justice.gov.uk can be slow

### 2. `authority_db.py`

- Updated the two PD 57AD entries (`RULE_PD_57AD` and `RULE_PD_57AD_MODEL_C`) to use the new canonical justice.gov.uk URL
- The March 2026 Report entry already used the assets.publishing.service.gov.uk PDF URL, which is fine

## What this does NOT fix

The trademark dashboard returning "0 conflicts / LOW RISK" for `BURRBERY` is **still** an open issue. That's the upstream live UKIPO/TMview search not fuzzy-matching `BURRBERY` against `BURBERRY`. Not a citation issue, not a URL issue — a search-quality issue. Park for Phase 2D or 2.5.

## Deployment

In `C:\Users\aswin\OneDrive\Desktop\Libra version 2\`:

1. Stop Streamlit (Ctrl+C in the terminal)
2. Back up your current files (rename `app.py` → `app_pre_hotfix2.py` and `authority_db.py` → `authority_db_pre_hotfix2.py`)
3. Copy the new `app.py` and `authority_db.py` from Downloads into the project folder
4. Run the test suites (must all pass):
   ```
   venv\Scripts\activate
   python test_phase_2a.py
   python test_phase_2b.py
   python test_phase_2c.py
   python test_phase_2c_trademark.py
   python test_phase_2c_fix.py
   ```
   Expected: all 224 tests pass.
5. Restart Streamlit: `streamlit run app.py`
6. Open the sidebar, find the **Legal Database Status** panel
7. Click **⬆️ Update DB**
8. Both rows should now show ✅:
   - ✅ UK Govt March 2026 Report on Copyright & AI
   - ✅ PD 57AD (Business & Property Courts)

If they still show ❌, the issue is local — likely a corporate proxy or firewall blocking outbound requests. Try the URLs in your browser directly to confirm they work from your machine; if they do but the panel still shows ❌, the proxy is the problem and would need investigating separately.

## Why the v2 engine wasn't affected

The v2 engines (PRPP, TDM, Trademark) do not depend on `PUBLIC_LEGAL_SOURCES` or `refresh_legal_database()` at all. Those engines use `authority_db.py` directly — the citations and summaries come from the verified database, not from live URL pings.

The Legal Database Status panel is a separate "are these public sources reachable from this machine?" diagnostic. It's useful but cosmetic. Even if every URL in that list 404'd, your trademark opinions would still cite the correct authorities with the correct citations, because those come from the offline verified database.

## Status

| Suite | Tests | Status |
|---|---|---|
| Phase 2A | 28 | ✓ |
| Phase 2B | 47 | ✓ |
| Phase 2C TDM | 56 | ✓ |
| Phase 2C Trademark | 33 | ✓ |
| Phase 2C-fix ID leak | 60 | ✓ |
| **Total** | **224** | **✓** |

Open items for later:
1. Upstream UKIPO fuzzy-search (BURRBERY → BURBERRY) — Phase 2D
2. `cross_check_contract`, `copyright_radar`, `generate_safer_version` refactor — Phase 2D
3. Data-protection layer before real client data — Phase 2.5
