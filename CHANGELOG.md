# Changelog

All notable changes to Libra Contract Guardian are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project uses [Semantic Versioning](https://semver.org/).

## [2.0.0] — 2026-06-26

Libra Contract Guardian v2.0 — a local-only legal-analysis application,
engineered to production-grade standards. All inference runs on-device via
Ollama; no document content ever leaves the machine.

### Architecture
- **Local-only by design.** All LLM inference is routed through a local Ollama
  instance (default `mistral:7b-instruct`) at `127.0.0.1`. No external API calls
  carry document content off-host.
- **Deterministic-first.** Each engine (contract, PRPP, TDM, trademark) produces
  a deterministic result; the LLM is used as a phraser over that result, never as
  the sole source of legal conclusions.
- **Citation provenance.** An output verifier rejects any citation that is not in
  the curated authority database, so generated text cannot introduce fabricated
  cases or statutes.

### Analysis engines
- Contract risk analysis with clause-level review and citation sanitisation.
- PRPP (Post-Report Provenance Procedure) civil-procedure assessment — a
  three-stage disclosure-viability framework, with deterministic scoring and an
  AI-phrased verified mode.
- TDM (text-and-data-mining) contract exposure analysis under UK/EU copyright law.
- Trademark conflict screening using phonetic (Double Metaphone) and
  edit-distance (Levenshtein) similarity, with a supplementary perceptual-hash
  visual signal; live lookups disabled in local-only mode.

### Security & privacy
- HTML-escaping of all user- and model-derived values rendered in the UI.
- DOCX decompression-bomb guard and a defence-in-depth character cap on text
  extraction.
- Privacy guard enforcing local-only network policy with an auditable control
  point; the audit log records destinations only, never document content.
- Privacy-safe application logging: events, timings, and error types are written
  to a rotating local log; a redaction guard ensures document content is never
  written to disk.
- All dependencies audited (`pip-audit`) — no known vulnerabilities.

### Packaging & setup
- Standalone Windows build via PyInstaller (`Build_Libra_EXE.bat` →
  `dist\Libra\Libra.exe`) — runs without a separate Python install. (Ollama is
  still installed separately for AI analysis.)
- Guided first-run setup checker (`check_setup.py`) and one-click launchers for
  Windows and macOS.
- Non-technical setup guide (`SETUP.md`).

### Reliability
- Startup stylesheet resolution works across normal, relocated, and frozen-build
  run modes, degrading gracefully if the stylesheet is absent.
- LLM call path degrades cleanly when Ollama is unavailable, the model is
  missing, or a call errors — clear messages, never a crash.
- ~390+ checks across 11 test suites covering the engines, verifier, privacy
  guard, history store, security hardening, and core helpers.

### Status
Libra Contract Guardian v2.0 implements the method described in the author's
forthcoming article in the *European Intellectual Property Review* (Thomson
Reuters), Issue 10, September 2026. It is a local-only legal-analysis
application, engineered to production-grade standards — hardened, tested across
~390+ checks, dependency-audited, and packaged as a standalone Windows build.
Developed and maintained by the author for local use.
