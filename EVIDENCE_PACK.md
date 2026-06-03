# R.A. Aswin Krishna — AI-Copyright Litigation Procedure

**Forthcoming publication, *European Intellectual Property Review* (Thomson Reuters)** · Incoming LLM, IP Law, Queen's University Belfast (September 2026)

---

## The problem

UK AI-copyright claims face a structural evidentiary asymmetry. A rights-holder who suspects their work was used to train a model cannot, at the outset, prove ingestion: the training data, the dataset composition, and the model's provenance all sit with the developer. Existing legal-AI tools do not engage with this. They summarise contracts and flag risk in general terms; they do not map a fact pattern onto the civil-procedure mechanics that actually decide whether such a claim can proceed.

## The research

My forthcoming article in the *European Intellectual Property Review* proposes the **Post-Report Provenance Procedure (PRPP)** — a civil-procedure framework for managing that asymmetry within the existing UK Civil Procedure Rules. It does not call for legislative change. It works within three procedural stages:

1. **Prima facie trigger** — establishing a good arguable case under CPR r.6.37, using hosted-repository evidence, regurgitation evidence, and statistical-attack evidence.
2. **Model C disclosure** — the feasibility of request-led Extended Disclosure under Practice Direction 57AD, including the IPEC carve-out at paragraph 1.4 that excludes such claims from the disclosure regime.
3. **Adverse inference** — the availability of an inference at trial under the *Wisniewski* line as refined by Cockerill J in *Magdeev v Tsvetkov* [2020] EWHC 887 (Comm).

The framework is anchored in current authority: the March 2026 UK Government Report on Copyright and AI, the *Kneschke v LAION* decision of the OLG Hamburg (December 2025), and the EU AI Act Article 53 training-data-summary template adopted in July 2025.

## The software

Alongside the research I have built its operational form: software that takes a UK AI-copyright fact pattern, maps it to the three PRPP stages, and produces a structured procedural assessment. Three design choices distinguish it from general-purpose legal-AI tools:

- **Citations are verified, not generated.** Every authority the system cites is drawn from a database of 50 entries — UK and EU case law, statutes, civil procedure rules, EU directives, and policy instruments — each cross-checked against the official source (BAILII, legislation.gov.uk, EUR-Lex, CURIA). The language model is not permitted to invent or substitute citations; an output verifier rejects any citation that does not trace to the database. This reduces the risk of citation fabrication to a negligible level.

- **Scoring is deterministic.** The procedural scoring is computed in code from structured signals, not by the language model. The model's role is limited to phrasing a result that has already been determined and verified.

- **It runs entirely on the user's own machine.** No cloud, no third-party API, no client data leaving the device. This is the design choice that makes it deployable on confidential matters rather than only on demonstrations.

## Status

The framework is accepted for publication (forthcoming, *European Intellectual Property Review*, Thomson Reuters). The software is operational, with the procedural engine, a text-and-data-mining contract analyser, and a trademark clearance module each covered by an automated test suite. It is a working prototype the author maintains for his own professional use; it is offered here as a demonstration of the research in operational form.

## Contact

R.A. Aswin Krishna · aswinkrishna2277@gmail.com

*This summary describes original research and an independent prototype. The software is a research demonstration and does not constitute legal advice.*
