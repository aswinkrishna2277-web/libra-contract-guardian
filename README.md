# Libra Contract Guardian v2.0

A local-first legal analysis prototype for UK AI-copyright matters. It maps a
contract or fact pattern onto the relevant law and civil-procedure mechanics,
draws every citation from a database audited against the official sources, and
verifies those citations before display — so a hallucinated authority cannot
reach the user as if it were real.

**This is a private research repository.** It accompanies a forthcoming article
in the *European Intellectual Property Review* (Thomson Reuters). It is a
working prototype and a research demonstration, not a commercial product, and
does not constitute legal advice.

---

## What it does

Five analysis engines, each with citations verified against the authority
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

## Tests

Eight integration suites, 344 checks:

```powershell
python test_phase_2a.py            # authority DB, selector, verifier
python test_phase_2b.py            # PRPP engine
python test_phase_2c.py            # TDM engine
python test_phase_2c_trademark.py  # trademark engine
python test_phase_2c_fix.py        # authority-ID leak regression
python test_trademark_similarity.py# fuzzy matching
python test_phase_2_5.py           # privacy guard
python test_phase_2d.py            # analysis citation sanitiser
```

## Known limitations

- The live trademark-register feed (UKIPO/EUIPO/WIPO) has no open real-time
  API; conflict analysis runs on the local similarity engine, and the official
  registers are linked for manual verification.
- The model phrases; it does not decide. All substantive scoring is
  deterministic and all citations are verified.

---

*R.A. Aswin Krishna — independent research prototype, 2026.*
