# The 90-Second Demo Script

The hardest skill in legal-tech presentation is brevity under pressure. A partner with three minutes between meetings does not want a tour of your software. They want to understand, in under two minutes, whether what you have built is intellectually serious. This script is calibrated for that.

Practice it until you can say it without thinking. The pauses are deliberate — they let the listener catch up. The transitions are signposted because cognitive load on the listener should be zero; all the work happens in your delivery.

---

## The script (memorise this — verbatim or close to it)

**[0:00 — 0:15  Frame the problem]**

> "The UK Government's March 2026 Report on Copyright and AI identified a gap that the substantive law doesn't fill. A copyright owner who suspects her work was used to train a generative model cannot, by ordinary means, prove ingestion. The corpus is held internally, the weights are a black box, and the EU AI Act Article 53 disclosures are aggregated to dataset-category level. Getty v Stability confirmed the limits of the secondary-infringement route on the same evidentiary problem."

*Pause briefly. Look up. Wait for them to nod or interject.*

**[0:15 — 0:35  State the framework, headline first]**

> "I propose a procedural response. Three stages, all built from tools that already exist in our civil procedure. Stage one: a prima facie trigger calibrated to the good-arguable-case threshold under CPR 6.37, with three evidentiary routes — hosted-repository evidence, circumstantial regurgitation, and Membership Inference Attack as Part 35 expert evidence. Stage two: Model C Extended Disclosure under PD 57AD — narrow, hash-manifests only, in a confidentiality ring. Stage three: Wisniewski adverse inference if the developer fails to preserve."

*This is where the listener's posture changes. Either they engage or they don't.*

**[0:35 — 0:55  The clever bit — anticipate the objection]**

> "The framework is deliberately conservative. It requires no rule change. It does not change what counts as infringement under section 16. It changes how the factual element of ingestion can be established. And it has a self-certified confidentiality tier specifically for SME defendants, responding directly to the cost concerns the Government Report flagged."

*This signals you have anticipated the natural objection (overreach / chilling investment) before they raise it.*

**[0:55 — 1:15  The software, briefly]**

> "I built a working demonstrator that operationalises the framework. Three engines: PRPP, TDM, and a Playbook engine that does TF-IDF cosine similarity against a firm's gold-standard corpus. The Playbook component ships with a verification test that proves the ranking is correct on synthetic IP/AI clauses. The whole thing runs against a curated knowledge base — CDPA, DSM Directive, EU AI Act, PD 57AD, leading cases including Kneschke v LAION from December 2025."

**[1:15 — 1:30  Close — what you want]**

> "The white paper is under journal review. The framework is the contribution; the software is the demonstration. I'd value your reaction to the framework — whether as a comment on its proportionality or as a sceptic of the Stage 1 thresholds."

*Stop talking. Do not fill silence. Let them speak.*

---

## The four questions you will be asked

Prepare answers to these. They are predictable.

### Q1: "How is this different from existing disclosure?"

> "It is existing disclosure, applied to a discrete Issue for Disclosure that hasn't yet been recognised as one. Algorithmic ingestion is the Issue. Hash manifests are the document class. Both fit naturally inside PD 57AD; the framework is what surfaces them as a coherent procedural pathway."

### Q2: "Won't this chill UK AI investment?"

> "The opposite, I argue. The status quo produces uncertainty for both rights-holders and developers. PRPP creates a defined procedural pathway with proportionality safeguards built in — the SME tier specifically. Well-advised developers prefer defined procedures to ad-hoc disclosure battles. And maintaining hash records of training corpora is cheap, doesn't compromise trade secrecy, and substantially reduces a developer's exposure to a Stage 3 inference."

### Q3: "Has any court actually done this?"

> "Not in this synthesised form, no. Each component is judicially settled — CPR 6.37 thresholds in *Brownlie*, Model C since 2019, Wisniewski since 1998. What hasn't been done is the recognition that algorithmic ingestion is a discrete Issue for Disclosure, and that hash manifests are a document class within PD 57AD para 6.5. That is the contribution."

### Q4: "Why should I take this seriously from someone pre-LLM?"

> "Because the work stands on its own. The white paper is fully cited, the framework is conservative in form, the software is verified by a test harness anyone can run in 30 seconds. I'm not asking for credit on credentials. I'm asking for a reaction to the substance."

*This is the most important answer in the deck. Deliver it without defensiveness. Confident, measured, eye contact.*

---

## What NOT to do

**Do not** start with "Hi, I'm Aswin." They know who you are; that's why you're in the room. Start with the problem.

**Do not** lead with the software. The framework is the asset. The software is proof you can execute. Software-first reads like a SaaS pitch; framework-first reads like research.

**Do not** apologise for being pre-qualification or pre-LLM. The work either stands or it doesn't. Defensive framing tells the listener to look for weaknesses they would not otherwise have noticed.

**Do not** say "I think" or "I believe" repeatedly. State the framework. The listener can disagree if they want to; let them.

**Do not** mention the Magic Circle, dream firms, or your career goals. Talk about the work. The career conversation is a separate one and it follows from the substance, not the other way around.

**Do not** rush. The pauses are not gaps — they are the listener's processing time.

---

## One last thing

The 90 seconds is a ceiling, not a floor. If they want to engage at minute 0:30 — let them. Drop the rest of the script. The script exists to ensure that *if you are uninterrupted*, you say everything that matters in the time allotted. The moment a real conversation starts, the script is over.

The interview where you delivered all 90 seconds without interruption is, on average, the interview where the listener was being polite. The interview where they cut in at 0:25 is the one where they were interested.

Both outcomes are useful information.
