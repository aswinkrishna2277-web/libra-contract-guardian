# Libra Contract Guardian

**A research demonstrator for the Post-Report Provenance Procedure (PRPP) — a civil-procedure framework for AI-copyright disclosure under PD 57AD, England & Wales.**

Author: **R.A. Aswin Krishna**
Status: Research deliverable | UK/EU IP & AI Law focus | v1.1

---

## What this is

Libra is a working software demonstrator that operationalises the **Post-Report Provenance Procedure (PRPP)** — a three-stage civil-procedure framework for AI-copyright litigation, set out in the author's manuscript *Training Data Disclosure in AI Copyright Litigation: The Post-Report Provenance Procedure* (under journal review, 2026).

The tool implements the PRPP framework against a curated UK/EU IP-AI legal knowledge base (CDPA 1988, DSM Directive, EU AI Act, PD 57AD, March 2026 UK Government Report on Copyright and AI, and leading cases including *Getty v Stability AI* [2025] EWHC 2863 (Ch), *Wisniewski v Central Manchester HA* [1998] EWCA Civ 596; [1998] PIQR P324, *Wetton v Ahmed* [2011] EWCA Civ 610, *Earles v Barclays* [2009] EWHC 2500 (Mercantile), *IPCom v HTC*, *Infederation v Google*, and *Kneschke v LAION* (OLG Hamburg, 10 Dec 2025)).

It is **not** an autonomous legal-advice system. It produces structured analysis to support, not replace, the judgment of a qualified practitioner.

---

## What the engines do

### PRPP Engine (`prpp.py`)

A three-stage civil-procedure assessor:

1. **Stage 1 — Prima facie trigger** (good-arguable-case, CPR r.6.37). Three evidentiary routes: (a) hosted-repository evidence (Common Crawl / LAION-5B cross-reference); (b) circumstantial regurgitation (Ahmed et al., *Extracting books from production language models* (2026) arXiv:2601.02671 — preprint, not peer-reviewed); (c) Membership Inference Attack as CPR Pt 35 expert evidence.
2. **Stage 2 — Model C Extended Disclosure** under PD 57AD: cryptographic hash manifests (SHA-256), deduplication logs, within a confidentiality ring (*IPCom v HTC* external-eyes-only; *Mitsubishi v OnePlus* three-tier; self-certified tier for SME defendants per March 2026 Report p.66).
3. **Stage 3 — Adverse inference** (*Wisniewski v Central Manchester HA* [1998] EWCA Civ 596; [1998] PIQR P324, extended to documents in *Wetton v Ahmed* [2011] EWCA Civ 610 and applied to electronic records in *Earles v Barclays Bank Plc* [2009] EWHC 2500 (Mercantile)) on non-preservation, distinguishing deliberate spoliation from routine data-minimisation.

### TDM Engine (`tdm.py`)

Reviews commercial contracts (SaaS, data licensing, training-data procurement, research collaborations) for liability under CDPA 1988 s.29A, DSM Directive Arts 3–4, and EU AI Act Art.53. Risk scoring is **mitigation-aware** — protective clauses (TDM exclusions, provenance warranties, audit rights, opt-out reservations) reduce risk rather than being ignored.

### Playbook Engine (`playbook.py`) — v1.1

Real **TF-IDF vector-space cosine similarity** against a firm's gold-standard contract corpus. Returns:
- Cosine similarity (0–1) between new contract and the playbook centroid
- Closest gold contract identification (which precedent to cite)
- Missing protective terms and novel terms in the new contract
- Confidence band based on gold-corpus size

### Trademark Module

Hybrid scoring on word marks: edit-distance + n-gram overlap + phonetic similarity. The "visual similarity" component on word marks is a coarse character-pixel hash and is a fallback signal only — it is not a substitute for image-based similarity on actual logo files. See `KNOWN_LIMITATIONS.md` for the exact methodology and where it does and does not apply.

---

## Methodology in one paragraph

PRPP is a procedural mechanism, not a substantive copyright doctrine. It does not change what counts as infringement under CDPA 1988 s.16; it changes how a claimant can establish the factual element of ingestion in litigation. The framework exists because of the evidentiary asymmetry described in the UK Government's March 2026 Report on Copyright and AI: claimants cannot inspect training corpora, while the EU AI Act Art.53 disclosures are aggregated to a level that does not establish causal nexus for individual works. PRPP responds with three procedural levers (CPR r.6.37, PD 57AD Model C, Wisniewski) that already exist in the Business and Property Courts but have not been applied to AI-copyright disclosure as a coherent system.

---

## Running it

### Prerequisites

```
Python 3.10+
pip install -r requirements.txt
```

### Local

```bash
streamlit run app.py
```

Opens at http://localhost:8501. Configure backend in the sidebar (Anthropic Claude, OpenAI, or local Ollama).

### Verifying the engines

The TF-IDF engine ships with a verification test:

```bash
python test_playbook.py
```

Output confirms TF-IDF playbook ranks similar contracts higher than dissimilar ones, cosine similarity scores align with legal-domain expectations, and orthogonal (out-of-domain) contracts are correctly rejected (similarity < 0.2).

---

## What changed in v1.1

The v1.0 README claimed a "playbook vector" but the implementation averaged keyword counts. v1.1 replaces this with genuine TF-IDF vector-space analysis using `scikit-learn`'s `TfidfVectorizer` (1- and 2-grams, sublinear TF, L2-normalised) against the centroid of the gold corpus. The legacy entry points (`compute_playbook_vector`, `playbook_deviation`) are preserved as backwards-compatible shims so existing UI code continues to work; they now wrap the real engine and return both legacy-shaped keys and the new richer output (`similarity`, `closest_gold_index`, `missing_terms`, `novel_terms`, `confidence_band`).

This was the single largest gap between what v1.0's labels promised and what its code did. v1.1 closes it. See `CHANGELOG.md` for the complete list.

---

## File structure

```
libra/
├── app.py                 Streamlit application
├── prpp.py                PRPP three-stage civil-procedure engine
├── tdm.py                 TDM contract-review engine (mitigation-aware)
├── playbook.py            TF-IDF cosine-similarity engine (v1.1)
├── constants.py           Legal knowledge base + risk taxonomy
├── ui_components.py       Streamlit rendering helpers
├── style.css              Theme
├── test_playbook.py       Verification test for the TF-IDF engine
├── requirements.txt       Python dependencies
├── CHANGELOG.md           Version history
├── KNOWN_LIMITATIONS.md   Honest scope of every engine
└── README.md              This file
```

---

## Limitations

- **The PRPP framework is a proposal, not adopted procedure.** No court has yet ordered Model C Extended Disclosure for AI training corpora in the form proposed. The framework synthesises existing CPR/PD 57AD tools; its judicial reception is untested. The manuscript is under journal review.
- **The trademark "visual similarity" component on word marks is a coarse character-pixel hash, not image similarity.** Use the image-upload path for real logo comparison.
- **Confidence in keyword-fallback mode is capped at 68%.** The tool will not present keyword-only outputs as high-confidence.
- **No solicitor-client relationship is created by use of this tool.** Users assume full responsibility for any reliance placed on outputs.

See `KNOWN_LIMITATIONS.md` for the full catalogue.

---

## Citation

> R.A. Aswin Krishna, *Libra Contract Guardian v1.1*: A research demonstrator for the Post-Report Provenance Procedure (2026). Companion software to the manuscript *Training Data Disclosure in AI Copyright Litigation: The Post-Report Provenance Procedure* (under journal review).

---

## Licence

All rights reserved. Contact the author for licensing enquiries.
