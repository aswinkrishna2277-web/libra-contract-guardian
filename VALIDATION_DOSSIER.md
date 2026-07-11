# Libra Contract Guardian — Validation Dossier

**For independent expert reviewers (IP practitioners, legal academics, and
technically-qualified auditors).**

**Author:** R.A. Aswin Krishna
**Date:** 2026
**Purpose of this document:** to make it as easy as possible for a qualified
reviewer to evaluate whether this software does what it claims — and to be
explicit about what has, and has not, been independently validated.

---

## 0. How to read this dossier (and what it is *not*)

This is not a marketing document and it is not a claim that the software is
proven. It is the opposite: a structured invitation to scrutinise the software,
with the author's own honest assessment of where the claims are strong and where
they are not yet externally validated.

**What "validated" means here.** A claim is *validated* only when someone
independent of the author has checked it against a ground truth the author did
not create. By that standard, as of this document's date, **the software's legal
correctness has not yet been independently validated.** The author's own test
suite (≈390 checks) confirms the code behaves as the author intended — it does
*not* confirm that what the author intended is legally correct. Those are
different things, and this dossier keeps them separate throughout.

The purpose of circulating this dossier is to obtain the independent review that
would change that status.

---

## 1. What the software is (and is not)

**Is:** a local-only application that assists IP-risk analysis under UK/EU
copyright and trademark law. It implements, in code, the procedural method set
out in the author's forthcoming article in the *European Intellectual Property
Review* (Thomson Reuters), Issue 10, 2026 (the "PRPP" — Post-Report Provenance
Procedure), alongside several other analysis modules.

**Is not:** a decision-maker, a substitute for qualified legal advice, or a
validated legal instrument. It produces structured assessments a lawyer must
independently verify.

**Relationship to the EIPR paper — stated precisely.** The paper advances a
*legal-procedural argument* about how courts should approach disclosure of AI
training data. Peer review of that paper assessed the *argument*. The software
*implements* that argument as one module among several. **Acceptance of the
paper does not validate the software.** A reviewer evaluating the software is
evaluating a different object from the one the journal evaluated.

---

## 2. Claims, tiered by how defensible they are

A reviewer's time is best spent where the claims are weakest. This section ranks
the software's claims by strength so scrutiny can be directed efficiently.

### Tier A — Structurally strong (verifiable by inspection)

These do not depend on contested legal judgement; a reviewer can confirm them by
reading the code and running it.

- **Local-only operation.** No document content is transmitted off-host. The
  privacy guard blocks non-local network calls and audits every attempt.
  *Reviewer can verify:* inspect `privacy_guard.py`; monitor network traffic
  during a run.
- **Citation provenance / anti-fabrication.** Every citation in output is
  checked against a fixed authority database; unrecognised citations are
  rejected or flagged. The system claims *negligible citation-fabrication risk,
  not zero hallucination* — an important, honest distinction the code itself
  makes.
  *Reviewer can verify:* inspect `output_verifier.py`; attempt to induce a
  fabricated citation and confirm it is caught.
- **Determinism.** Given the same input, scoring is reproducible; it is computed
  in code, not sampled from the model.
  *Reviewer can verify:* run the same input repeatedly; confirm identical output.

### Tier B — Defensible but reflect authored legal judgement

These encode the author's reading of the law. They are reasonable, but they are
*interpretations*, and a reviewer may legitimately disagree.

- **Authority database contents.** The cases, statutes, and rules selected as
  relevant, and their stated propositions. *A reviewer should check these against
  the primary sources (BAILII, legislation.gov.uk, EUR-Lex, CURIA).*
- **The mapping from facts to legal stages.** e.g. that certain factual signals
  establish a prima facie disclosure trigger. *This tracks the paper's argument;
  a reviewer who disputes the paper may dispute this.*
- **Which authorities are selected for which fact pattern.** *A reviewer should
  check that the software surfaces the authorities a competent lawyer would.*

### Tier C — Weakest; require external justification (scrutinise hardest)

These are the claims most vulnerable to challenge, and the author flags them
proactively.

- **The specific numeric weights in the scoring.** The scoring uses chosen
  constants — e.g. a prima facie trigger floors at 20 and rises by fixed
  increments; UK jurisdiction scores 60 vs 35 for non-UK; an IPEC track reduces a
  stage score by 30. **These magnitudes are the author's calibration, not values
  derived from an external, validated dataset.** They are internally consistent
  and directionally defensible (e.g. spoliation *should* raise adverse-inference
  exposure), but the *exact numbers* have no external ground truth. This is the
  single point a rigorous reviewer should press hardest, and the author does not
  claim otherwise.
- **Score-to-label thresholds** (e.g. what counts as "Strong" vs "Weak"
  viability). Same caveat: sensible cut-offs, not externally validated ones.

**The honest summary:** the software's *architecture* (Tier A) is strong and
checkable. Its *legal content* (Tier B) is defensible interpretation. Its
*quantitative calibration* (Tier C) is reasonable but unvalidated, and should be
treated as a structured aid to reasoning, not as an authoritative score.

---

## 3. What a reviewer is asked to do

To convert "unvalidated" into "independently reviewed," a qualified reviewer is
asked to assess, on real or realistic fact patterns:

1. **Legal correctness of outputs.** Are the authorities cited correct, current,
   and apposite? Is the procedural reasoning sound? Would you, as a practitioner,
   stand behind the analysis?
2. **Directional soundness of scoring.** Ignoring the exact numbers, does the
   scoring move in the right direction for the right reasons?
3. **Failure modes.** Where does it mislead? What would a careless user wrongly
   rely on? (See §5, the reviewer's adversarial checklist.)
4. **Fitness for stated purpose.** Is it a sound *assistant* to a competent
   lawyer (its actual claim), even though it is not a decision-maker?

A reviewer who completes this and is willing to be named provides exactly the
external credibility the author is seeking. A reviewer who finds faults provides
something equally valuable: a corrective.

---

## 4. Worked examples (to be completed with reviewer)

*[This section is a template. For each example: the input fact pattern, the
software's full output, and space for the reviewer's independent assessment.
These should be built from real decided cases where the "right answer" is known
independently of the software — so the comparison is against external ground
truth, not the author's expectation.]*

- Example 1 — PRPP assessment on [a decided disclosure case]: software output vs
  the actual procedural outcome.
- Example 2 — TDM exposure on [a real training-data contract]: software output vs
  practitioner assessment.
- Example 3 — Trademark clearance on [a mark with a known conflict outcome]:
  software opinion vs the actual registry/decision result.

*(The author should not fill in the "correct answer" column. The reviewer, or a
decided case, should.)*

---

## 5. Reviewer's adversarial checklist (please try to break it)

The strongest validation is a genuine attempt to make the software fail. A
reviewer is invited to:

- [ ] Feed a contract whose correct risk level you already know; check the score.
- [ ] Feed a fact pattern from a *decided* case; compare the software's
      procedural assessment to what the court actually did.
- [ ] Try to induce a fabricated or wrong citation in the output.
- [ ] Check every authority the software cites against the primary source.
- [ ] Give it an edge case (empty, malformed, adversarial, out-of-scope input)
      and see whether it fails safely or misleads.
- [ ] Probe the scoring: construct two fact patterns you believe should score
      very differently and confirm the software agrees — and two that should
      score similarly.
- [ ] Judge whether a non-expert user could be *misled* by any output into a
      wrong conclusion.

---

## 6. Current validation status (honest register)

| Object | Status | Validated by whom |
|---|---|---|
| The legal-procedural argument (PRPP) | Peer-reviewed, accepted | EIPR reviewers |
| The software architecture (local-only, verifier, determinism) | Verifiable by inspection; author-tested | Author only (to date) |
| The software's legal correctness | **Not yet independently validated** | — (this dossier seeks it) |
| The numeric scoring calibration | **Not externally validated** | — |

The author's position is that the top row is done, the second row is
demonstrable, and rows three and four are the work this dossier is meant to
begin. Nothing in the author's materials should be read as claiming rows three or
four are already complete.

---

## 7. How to proceed

The most credible validation available to this project is expert review by
qualified IP practitioners and academics — realistically accessible once the
paper is published (September 2026) and through the author's academic network at
Queen's University Belfast. A reviewer willing to assess the software against the
above, and to be acknowledged, converts an author-built tool into an
independently-reviewed one.

Contact: R.A. Aswin Krishna (aswinkrishna2277@gmail.com).
