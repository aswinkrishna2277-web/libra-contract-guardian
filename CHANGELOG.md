# CHANGELOG

## v1.1 — 2026 release

### Added
- **`playbook.py`** — A genuine TF-IDF vector-space playbook engine using `scikit-learn`'s `TfidfVectorizer` (1- and 2-grams, sublinear TF, L2-normalised) and cosine similarity against the centroid of the gold-standard corpus.
- **`test_playbook.py`** — Verification test that proves the TF-IDF engine correctly ranks contracts by semantic distance from the playbook (synthetic IP/AI clauses; sanity assertions on similarity ordering).
- **`KNOWN_LIMITATIONS.md`** — Explicit statement of where each engine's claims do and do not apply.
- **`CHANGELOG.md`** — This file.
- **`build_real_playbook` / `compute_real_deviation` / `explain_real_deviation`** — New entry points for callers that want the full TF-IDF output (similarity, closest-gold-index, missing/novel terms, confidence band).

### Changed
- **`compute_playbook_vector`** is now a backwards-compatible shim that returns both the legacy per-category keys AND a new `_tfidf_playbook` key holding the real TF-IDF model.
- **`playbook_deviation`** is now a backwards-compatible shim that returns both legacy-shaped keys (`risk_gaps`, `fix_suggestions`) and the new richer output (`similarity`, `missing_terms`, `novel_terms`, `confidence_band`, `explanation`).
- **README rewritten** to describe the tool as a research demonstrator, not an "AI-Powered Legal Intelligence System." The tool is good enough that it doesn't need the marketing layer; calling it what it is improves credibility with technically and legally literate readers.

### Fixed
- **The single largest credibility gap in v1.0**: the function named `compute_playbook_vector` no longer averages keyword counts and call them a "vector." It now produces an actual vector-space model.

### Preserved (backwards compatibility)
- All v1.0 UI code that called `compute_playbook_vector(texts)` and `playbook_deviation(text, vec)` continues to work without modification. The shims expose both legacy and new keys.
- Legacy per-category gap analysis is now derived from TF-IDF top terms rather than direct keyword averaging — the per-category output is more meaningful, not less.

---

## v1.0 — earlier 2026 release (baseline)

- PRPP engine rewritten as three-stage civil procedure (was misaligned as contractual checklist in v0.x).
- Mitigation-aware risk scoring (protective clauses reduce risk).
- Three-source trademark search fallback (DuckDuckGo → Wikipedia → curated DB).
- Confidence scoring honesty (keyword fallback capped at 68%).
- Empty-contract guard in TDM engine.
- Circular-import fix via lazy imports.
