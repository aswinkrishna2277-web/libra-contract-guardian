# Libra Contract Guardian v2.0

A local-only legal-analysis application for UK AI-copyright matters, engineered
to production-grade standards. It maps a contract or fact pattern onto the
relevant law and civil-procedure mechanics, draws every citation from a database
audited against the official sources, and verifies those citations before
display — so a hallucinated authority cannot reach the user as if it were real.

**This is a private repository.** It accompanies a forthcoming article in the
*European Intellectual Property Review* (Thomson Reuters), Issue 10, September
2026. It is developed and maintained by the author for his own professional use,
is not a commercial product, and does not constitute legal advice.

---

## What it does

Four analysis engines, each with citations verified against the authority
database:

- **Contract analysis (Quick and Deep Research modes)** — risk scoring across
  TDM, IP, data-privacy, SaaS, cyber, ADR, and liability categories, with a
  clause-by-clause breakdown in Deep Research mode.
- **TDM / text-and-data-mining** — risk and mitigation scoring against
  CDPA 1988 s.29A, the DSM Directive, and the EU AI Act.
- **PRPP procedure** — the three-stage Post-Report Provenance Procedure
  (prima facie trigger under CPR r.6.37; Model C disclosure under PD 57AD;
  adverse inference under the *Wisniewski* line).
- **Trademark clearance** — fuzzy conflict detection (edit-distance + phonetic)
  with a structured clearance opinion.

## Architecture (why the citations are trustworthy)

1. **Deterministic scoring.** Scores are computed in code from structured
   signals — not by the language model.
2. **Authority database.** A 50-entry database of UK and EU cases, statutes,
   civil procedure rules, directives, and policy instruments, each cross-checked
   against the official source (BAILII, legislation.gov.uk, EUR-Lex, CURIA).
3. **LLM as phraser only.** A local model (Mistral 7B via Ollama) phrases a
   result that has already been determined.
4. **Output verification.** Every citation in the output is checked against the
   database; anything that does not trace to a real authority is rejected or
   flagged.
5. **Local-only by default.** No cloud, no third-party API, no document content
   leaving the device. Every network attempt is audited locally.

## Privacy & security

- **No document content leaves the device.** All inference is local; the privacy
  guard blocks non-local network calls and audits every attempt (destinations
  only, never content).
- **Privacy-safe logging.** Application events, timings, and error types are
  written to a rotating local log; a redaction guard ensures document content is
  never written to disk.
- **Hardened extraction.** HTML escaping of rendered values, a DOCX
  decompression-bomb guard, and a character cap on text extraction.
- **Dependencies audited** with `pip-audit` — no known vulnerabilities.

## Running locally

Requires Python 3.11+, and [Ollama](https://ollama.com) with a model pulled
(e.g. `ollama pull mistral:7b-instruct`) for the phrasing layer. The engines
fall back to deterministic output if no model is available.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

A standalone Windows build is also available via `Build_Libra_EXE.bat`
(produces `dist\Libra\Libra.exe`, which runs without a separate Python install;
Ollama is still installed separately for AI analysis). See `SETUP.md` for the
non-technical setup guide.

## Tests

Eleven integration suites, ~390+ checks:

```powershell
python test_phase_2a.py             # authority DB, selector, verifier
python test_phase_2b.py             # PRPP engine
python test_phase_2c.py             # TDM engine
python test_phase_2c_trademark.py   # trademark engine
python test_phase_2c_fix.py         # authority-ID leak regression
python test_trademark_similarity.py # fuzzy matching
python test_phase_2_5.py            # privacy guard
python test_phase_2d.py             # analysis citation sanitiser
python test_history_store.py        # local analysis history
python test_security.py             # HTML escaping + docx bomb guard
python test_phase_e_core.py         # core scoring/helper functions
```

## Known limitations

- The live trademark-register feed (UKIPO/EUIPO/WIPO) has no open real-time
  API; conflict analysis runs on the local similarity engine, and the official
  registers are linked for manual verification.
- The model phrases; it does not decide. All substantive scoring is
  deterministic and all citations are verified.

---

*R.A. Aswin Krishna — local-only legal-analysis application, engineered to
production-grade standards, 2026.*
