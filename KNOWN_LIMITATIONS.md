# Known Limitations

This document records what each component of Libra does **not** do. It exists because a research deliverable that is honest about its scope is more credible than one that overstates its capabilities. Anyone evaluating Libra for use in practice — academic supervisor, hiring partner, IP boutique innovation team, EUIPO Observatory reviewer — should read this alongside the README.

---

## PRPP Engine (`prpp.py`)

### What it does
Assesses a litigation scenario against the three-stage Post-Report Provenance Procedure framework: prima facie trigger (CPR r.6.37), Model C Extended Disclosure (PD 57AD), and adverse inference (*Wisniewski* [1998] EWCA Civ 596 / *Wetton v Ahmed* [2011] EWCA Civ 610 / *Earles v Barclays* [2009] EWHC 2500 (Mercantile)).

### What it does NOT do
- **It does not predict case outcomes.** PRPP is a procedural framework; whether a court orders Model C disclosure depends on facts, judicial discretion, and proportionality assessments that no automated tool can substitute for.
- **It does not establish that PRPP has been adopted.** No reported decision has yet ordered training-data disclosure in the form PRPP proposes. The framework synthesises existing CPR / PD 57AD tools but its judicial reception is untested.
- **It does not replace legal advice.** A practitioner must independently assess whether PRPP applies in any given matter.

### Confidence framing
Where AI-backend analysis succeeds, confidence is reported by the model (typically 70–90%). Where AI fails or is unavailable, the keyword-fallback path runs and confidence is capped at 70% by design.

---

## TDM Engine (`tdm.py`)

### What it does
Reviews contract text for TDM and AI-training liability under CDPA 1988 s.29A, DSM Directive Arts 3–4, EU AI Act Art.53. Mitigation-aware: protective clauses reduce risk.

### What it does NOT do
- **It is not a substitute for clause-level legal review.** The engine flags issues; a practitioner must read the contract and apply judgment.
- **The keyword-fallback mode (when AI is unavailable) uses rule-based scoring with hardcoded weights.** It is a screening tool, not a definitive risk assessment. Confidence is capped at 68% in this mode.
- **It does not perform jurisdictional conflict-of-laws analysis.** Statutes cited assume UK governing law unless the contract specifies otherwise; the engine notes EU exposures but does not compute their interaction with UK law in detail.

---

## Playbook Engine (`playbook.py`) — v1.1

### What it does (v1.1)
Real TF-IDF vector-space cosine similarity. A new contract is transformed into the same vector space as the firm's gold corpus, and similarity to the centroid is computed.

### What it does NOT do
- **It is not a semantic embedding model.** TF-IDF captures lexical co-occurrence, not meaning. Two clauses that say the same thing in different vocabulary will appear dissimilar. For semantic matching, an embedding model (e.g. `sentence-transformers`) would be required — left as a future enhancement.
- **It is meaningful only when n_gold ≥ 5.** Smaller corpora produce noisier centroids; the engine reports a confidence band ("low" for n_gold < 5; "medium" for 5–9; "high" for ≥10).
- **It does not classify clauses by type.** The deviation result tells you the new contract is unlike your playbook; it does not tell you whether the divergence is in indemnity drafting vs governing-law selection vs liability caps. That remains a human judgment.

---

## Trademark Module

### What it does
Word-mark similarity scoring using edit-distance + n-gram overlap + (optional) phonetic metrics. Three-source search fallback: DuckDuckGo → Wikipedia → curated DB. The "semantic dilution" category implements the author's TMA s.10(3) academic theory.

### What it does NOT do
- **The "visual similarity" component on word marks is a coarse character-pixel hash.** It renders the mark text as image pixels and hashes the result. This is not perceptual hashing on a real logo. For logo-to-logo comparison, the image-upload path uses real perceptual hashing on actual image bytes — that path is correct; the text path is a fallback signal only.
- **It does not perform classification under the Nice classification system.** Mark similarity is computed in the abstract; whether marks conflict in a specific class requires further analysis.
- **It does not access the live UKIPO or EUIPO registers.** Search results are from public web sources, not the official trade-mark registers.

---

## Live Source Verification

### What it does
HTTP availability checks against `legislation.gov.uk` and other authoritative URLs cited in the legal knowledge base.

### What it does NOT do
- **It does not retrieve and parse statutory text.** A 200 OK response means the URL is reachable; it does not verify that the cited section reads as the knowledge base claims.
- **For statute verification, follow the URL manually.**

---

## AI Backend Layer

### What it does
Routes prompts to one of: Anthropic Claude, OpenAI GPT-4, or local Ollama. Falls back to keyword analysis if the AI call fails or returns unparseable JSON.

### What it does NOT do
- **It does not eliminate hallucination risk.** The system prompts constrain output to UK/EU statute citations and require JSON, but the underlying model may still produce inaccurate citations. Every output should be verified against the source.
- **It does not store conversations.** Session state is in-memory only and cleared on app restart.

---

## General

- **No solicitor-client relationship is created by use of this tool.**
- **Users assume full responsibility for reliance on outputs.**
- **The author is an IP-AI practitioner-researcher, not a qualified solicitor in England & Wales.** The PRPP framework is academic research; its application in practice requires qualified UK legal counsel.

---

*Last updated: v1.1 release, 2026.*
