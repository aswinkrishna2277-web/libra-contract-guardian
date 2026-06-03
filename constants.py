# ================================================================
#  LIBRA CONTRACT GUARDIAN v1.0 – Shared Constants
#  Production Build | UK/EU IP Law
#  R.A. Aswin Krishna — IP-AI Practitioner
# ================================================================

APP_TITLE    = "Libra Contract Guardian"
APP_SUBTITLE = "AI Legal Intelligence System"
APP_VERSION  = "1.0"
APP_BUILD    = "Production Release — April 2026"

DISCLAIMER   = (
    "Libra Contract Guardian is a personal legal-intelligence tool developed by "
    "R.A. Aswin Krishna (advocate, India; IP-AI practitioner) for his own professional use. "
    "It produces preliminary analysis to support, not replace, the judgment of a qualified legal "
    "practitioner. The PRPP (Post-Report Provenance Procedure) framework implemented here is an "
    "original civil-procedure proposal by the author, accepted for publication in the European "
    "Intellectual Property Review (Thomson Reuters), and derived from the UK Government's March 2026 "
    "Report on Copyright and Artificial Intelligence, Practice Direction 57AD, and the judgment in "
    "Getty Images (US) Inc v Stability AI Ltd [2025] EWHC 2863 (Ch). A relationship of "
    "advocate/solicitor and client arises only where the author is separately and expressly engaged "
    "to provide professional services; use of this tool alone does not create one. The author may "
    "use this tool in connection with paid professional engagements."
)

SYSTEM_LEGAL = """You are an expert UK/EU commercial, IP and AI lawyer specialising in:
- Copyright, Designs and Patents Act 1988 (CDPA), especially ss.16, 17, 28A, 29A
- UK/EU GDPR and Data Protection Act 2018
- EU AI Act 2024, DSM Directive (EU) 2019/790, Art. 3–4 TDM provisions
- UK Government's March 2026 Report on Copyright and Artificial Intelligence
- Practice Direction 57AD (disclosure in the Business and Property Courts)
- Trade Marks Act 1994, Trade Marks Directive (EU) 2015/2436
- NIS2 Directive, Computer Misuse Act 1990
- SaaS, licensing, tech transfer contracts, NDAs, DPAs, IP assignments
- ADR: LCIA, ICC, Arbitration Act 1996
- UCTA 1977, Consumer Rights Act 2015

CRITICAL SCORING RULE — Risk vs Mitigation Intelligence:
- Raw risk keywords (training data, dataset, scraping) raise risk scores ONLY when unaccompanied by mitigation language.
- Protective clauses (provenance warranties, TDM exclusions, audit rights, opt-out clauses, statute citations, indemnities) LOWER risk and RAISE compliance_strength_score.
- A contract that expressly EXCLUDES AI training use is SAFER than one silent on the topic.
- Statute citations in the contract body indicate compliance awareness — reduce risk.

Jurisdiction: UK and EU law first. Cite specific Acts, sections, articles, and leading cases.
Be precise; flag risks clearly; quote protective language where present."""

# ════════════════════════════════════════════════════════════════════════════
# LEGAL KNOWLEDGE BASE
# ════════════════════════════════════════════════════════════════════════════
LEGAL_KB = {
    "CDPA 1988": {
        "url": "https://www.legislation.gov.uk/ukpga/1988/48/contents",
        "sections": {
            "s.1":    "Copyright subsists in original literary, dramatic, musical or artistic works.",
            "s.11":   "First ownership of copyright — generally the author.",
            "s.16":   "Acts restricted by copyright — reproduction, distribution, communication.",
            "s.16(3)":"Restricted acts applied to the work as a whole OR any substantial part.",
            "s.17":   "Copying includes reproduction in any material form; transient or incidental copies included.",
            "s.28A":  "Temporary copies exception — transient/incidental copies that are integral to a technological process and have no independent economic significance.",
            "s.29A":  "TDM exception — copies for text and data mining limited to lawful access and NON-COMMERCIAL research purposes. Commercial TDM remains infringing absent licence.",
            "s.50A":  "Lawful users may make backup copies of computer programs.",
            "s.77-89":"Moral rights — paternity, integrity, false attribution.",
            "s.90":   "Assignment of copyright must be in writing signed by the assignor.",
            "s.96":   "Infringement actionable by the copyright owner; injunctions, damages, accounts.",
        }
    },
    "UK GDPR / DPA 2018": {
        "url": "https://www.legislation.gov.uk/ukpga/2018/12/contents",
        "sections": {
            "Art.5":    "Principles — lawfulness, fairness, transparency, purpose limitation, data minimisation, accuracy, storage limitation, integrity.",
            "Art.6":    "Lawful bases for processing personal data.",
            "Art.13-14":"Transparency obligations — information to data subjects.",
            "Art.17":   "Right to erasure.",
            "Art.20":   "Right to data portability.",
            "Art.25":   "Data protection by design and default.",
            "Art.28":   "Processor acts only on documented instructions; written DPA required.",
            "Art.32":   "Security of processing — appropriate technical and organisational measures.",
            "Art.35":   "DPIA required for high-risk processing.",
            "Art.44-49":"International transfers — adequacy, SCCs, BCRs.",
        }
    },
    "UCTA 1977": {
        "url": "https://www.legislation.gov.uk/ukpga/1977/50/contents",
        "sections": {
            "s.2(1)": "Cannot exclude liability for death or personal injury caused by negligence.",
            "s.2(2)": "Exclusion for other negligent loss subject to reasonableness.",
            "s.3":    "Standard-form exclusion clauses subject to reasonableness.",
            "s.11":   "Reasonableness test — fair and reasonable having regard to circumstances.",
        }
    },
    "Consumer Rights Act 2015": {
        "url": "https://www.legislation.gov.uk/ukpga/2015/15/contents",
        "sections": {
            "s.62": "Unfair terms — not binding if contrary to good faith and cause significant imbalance.",
            "s.65": "Cannot exclude liability for death or personal injury.",
            "s.68": "Transparency requirement — terms must be transparent and prominent.",
        }
    },
    "Arbitration Act 1996": {
        "url": "https://www.legislation.gov.uk/ukpga/1996/23/contents",
        "sections": {
            "s.1":    "Arbitration agreement is binding; arbitral award is final.",
            "s.33":   "Tribunal must act fairly and impartially.",
            "s.67-68":"Challenging award — jurisdiction or serious irregularity.",
        }
    },
    "Trade Marks Act 1994": {
        "url": "https://www.legislation.gov.uk/ukpga/1994/26/contents",
        "sections": {
            "s.5(2)(b)": "Relative grounds — likelihood of confusion, including likelihood of association.",
            "s.5(3)":    "Relative grounds — marks with a reputation (dilution).",
            "s.10(2)":   "Infringement by use of a similar mark where likelihood of confusion exists.",
            "s.10(3)":   "Infringement by taking unfair advantage of, or being detrimental to, distinctive character or repute of mark with reputation.",
        }
    },
    "UK Govt March 2026 Report on Copyright & AI": {
        "url": "https://www.gov.uk/government/publications/copyright-and-artificial-intelligence",
        "sections": {
            "Policy Stance":    "Government declined to enact statutory transparency or a broad commercial TDM opt-out; enforcement relegated to private civil litigation.",
            "Procedural Costs": "Identifies procedural costs as a primary barrier to SME market entry.",
            "CCE Pilot":        "Prospective Creative Content Exchange — voluntary licensing hub for public collections; no retroactive relief.",
        }
    },
    "PD 57AD (Business & Property Courts)": {
        "url": "https://www.justice.gov.uk/courts/procedure-rules/civil/rules/pd_part57ad",
        "sections": {
            "Model C Extended Disclosure": "Narrow, issue-based disclosure of specified documents or classes on the Disclosure Review Document.",
            "Disclosure Review Document":  "Parties identify Issues for Disclosure; court selects appropriate Disclosure Model.",
            "Preservation Duty (para 3.1)":"Parties must preserve documents once litigation is contemplated; breach may trigger sanctions.",
            "Proportionality (para 6.4)":  "Disclosure limited to what is necessary to resolve issues justly and at proportionate cost.",
        }
    },
    "Civil Procedure Rules": {
        "url": "https://www.justice.gov.uk/courts/procedure-rules/civil",
        "sections": {
            "r.1.1":   "Overriding objective — dealing with cases justly and at proportionate cost.",
            "r.3.4(2)(a)":"Strike out of statements of case disclosing no reasonable grounds.",
            "r.6.37":  "Good arguable case threshold for service out of jurisdiction.",
            "r.31.16": "Pre-action disclosure — narrow, non-iterative; insufficient for AI ingestion cases.",
            "r.31.22": "Restrictions on use of disclosed documents (confidentiality rings).",
            "Pt 24":   "Summary judgment — real prospect of success.",
            "Pt 35":   "Experts and assessors — duty to restrict expert evidence.",
            "r.44.2":  "Costs jurisdiction — conduct of the parties before and during proceedings.",
        }
    },
    "EU AI Act (Reg. 2024/1689)": {
        "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        "sections": {
            "Art.53(1)(c)": "Provider policy to comply with Union copyright law.",
            "Art.53(1)(d)": "Sufficiently detailed summary of training content — aggregated, macro-level only.",
        }
    },
    "DSM Directive (EU) 2019/790": {
        "url": "https://eur-lex.europa.eu/eli/dir/2019/790/oj",
        "sections": {
            "Art.3": "TDM exception for scientific research — no opt-out permitted.",
            "Art.4": "TDM exception for commercial use — opt-out via machine-readable reservation required.",
        }
    },
    "ICO AI Guidance": {
        "url": "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/",
        "sections": {
            "Explainability": "AI systems must be explainable to data subjects upon request.",
            "Bias Audits":    "Regular bias audits required where automated decision-making affects individuals.",
            "Lawful Basis":   "Training on personal data requires a valid lawful basis under Art.6 UK GDPR.",
        }
    },
    "Leading Cases": {
        "url": "https://www.bailii.org",
        "sections": {
            "Getty Images v Stability AI [2025] EWHC 2863 (Ch)":
                "Model weights do not store recoverable copies of training images; secondary infringement requires proof that model IS an infringing copy — not established on the evidence. Appeal pending.",
            "Designers Guild v Russell Williams [2000] UKHL 58":
                "Two-stage substantial-part test for non-literal copying — identify original elements, then test causal reproduction.",
            "Infopaq International v Danske Dagblades (C-5/08)":
                "Even very short extracts can engage the reproduction right if they contain the author's own intellectual creation.",
            "Wisniewski v Central Manchester HA [1998] EWCA Civ 596; [1998] PIQR P324":
                "Brooke LJ — adverse inference doctrine. Court may infer that absent evidence is adverse to the withholding party where (i) party has evidence within its control; (ii) fails to produce; (iii) no credible explanation. Originally framed for absent witnesses.",
            "Wetton v Ahmed [2011] EWCA Civ 610":
                "Arden LJ at [14] — extended Wisniewski adverse-inference logic to absent documents. Primary authority for documentary spoliation in modern practice.",
            "Earles v Barclays Bank Plc [2009] EWHC 2500 (Mercantile)":
                "HHJ Simon Brown QC — Wisniewski applied to electronic records. Confirms no general pre-action preservation duty; duty engages once proceedings are contemplated.",
            "IPCom v HTC Europe [2013] EWHC 2880 (Ch)":
                "Roth J at [360]–[377] — confidentiality rings for source-code inspection; external-eyes-only tier to protect trade secrets.",
            "Mitsubishi Electric v OnePlus [2020] EWCA Civ 1562":
                "Floyd LJ at [18]–[23] — three-tier confidentiality regime upheld for proprietary algorithms (Attorney's Eyes Only).",
            "Infederation v Google [2020] EWHC 657 (Ch)":
                "Roth J at [27]–[42] — restrictive inspection regimes are exceptional derogations from open justice; principles for evaluating confidentiality-club applications.",
            "Kneschke v LAION (OLG Hamburg, 5 U 104/24, 10 Dec 2025)":
                "Machine-readable reservation required under Art.4(3) DSM Directive; scientific research exception (Art.3) takes precedence.",
            "Lidl v Tesco [2024] EWCA Civ 262":
                "Infringement and passing off — Tesco's Clubcard Prices logo infringed Lidl's mark; takes unfair advantage of Lidl's reputation under s.10(3) TMA 1994.",
            "Sky v SkyKick [2020] UKSC 17":
                "Bad faith and overbreadth of specification can invalidate trade mark registrations.",
        }
    },
}

# ════════════════════════════════════════════════════════════════════════════
# RISK CATEGORIES
# ════════════════════════════════════════════════════════════════════════════
RISK_CATEGORIES = {
    "tdm_training_data": {"label":"TDM / AI Training Data Risk","icon":"🧠","color":"#ff7f50",
        "keywords":["training data","dataset","datasets","corpus","model training","machine learning","llm","foundation model","scrape","scraping","crawl","data mining","text and data mining","tdm","provenance","lineage","source data","licensed data","opt-out","attribution","ingest","ingestion","semantic dilution"]},
    "ip_ownership":     {"label":"IP Ownership Risk","icon":"©️","color":"#ffa94d",
        "keywords":["ownership","assign","transfer","copyright","patent","trademark","moral rights","work for hire"]},
    "data_privacy":     {"label":"Data Privacy Risk","icon":"🔒","color":"#da77f2",
        "keywords":["personal data","gdpr","uk gdpr","controller","processor","breach","transfer","consent","data subject"]},
    "saas_licensing":   {"label":"SaaS / Licensing Risk","icon":"☁️","color":"#74c0fc",
        "keywords":["license","subscription","saas","software","api","seat","user","auto-renew","uptime","sla"]},
    "cyber_security":   {"label":"Cyber Security Risk","icon":"🛡️","color":"#63e6be",
        "keywords":["security","cyber","hack","vulnerability","encryption","incident","audit","penetration","access control"]},
    "tech_transfer":    {"label":"Tech Transfer Risk","icon":"🔄","color":"#a9e34b",
        "keywords":["technology transfer","know-how","trade secret","export control","dual use","source code","escrow"]},
    "adr":              {"label":"ADR / Dispute Risk","icon":"⚖️","color":"#ffd43b",
        "keywords":["arbitration","dispute","mediation","governing law","jurisdiction","litigation","forum","lcia","icc"]},
    "liability":        {"label":"Liability Risk","icon":"⚡","color":"#ff8787",
        "keywords":["limitation of liability","indemnif","consequential","indirect","cap","damages","warranty","hold harmless"]},
    "semantic_dilution": {"label":"Semantic Dilution Risk","icon":"🔮","color":"#845ef7",
        "keywords":["dilution","blurring","tarnishment","reputation","distinctiveness","fame","encroachment"]},
}

# ════════════════════════════════════════════════════════════════════════════
# PRPP — Post-Report Provenance Procedure (Aswin Krishna, 2026)
# Source: Author's own civil-procedure framework, accepted for publication
#         in the European Intellectual Property Review (Thomson Reuters)
# NOT a contractual checklist — a litigation-disclosure procedure
# ════════════════════════════════════════════════════════════════════════════
PRPP_FRAMEWORK_NOTE = (
    "The Post-Report Provenance Procedure (PRPP) is a civil-procedure framework proposed by "
    "R.A. Aswin Krishna in his article 'Training Data Disclosure in AI Copyright "
    "Litigation: The Post-Report Provenance Procedure', accepted for publication in the "
    "European Intellectual Property Review (Thomson Reuters / Sweet & Maxwell), 2026. The PRPP operates "
    "through Practice Direction 57AD in the Business and Property Courts of England and Wales, "
    "providing a three-stage disclosure mechanism in response to the evidentiary vacuum left by "
    "the UK Government's March 2026 Report on Copyright and AI. It does NOT replace or alter "
    "substantive copyright law — it is a procedural adaptation of existing disclosure tools."
)

# PRPP Three-Step Structure (from the manuscript)
PRPP_STEPS = {
    "step_1_prima_facie": {
        "title": "Step 1: The Prima Facie Trigger",
        "summary": "Claimant must establish a plausible inference of ingestion — calibrated to the 'good arguable case' standard (CPR r.6.37), not the higher 'real prospect of success' (CPR Pt 24).",
        "routes": [
            {
                "name": "Hosted Repository Evidence",
                "detail": "Claimant adduces factual evidence that protected portfolio was hosted on a domain comprehensively scraped by a known dataset (e.g. Common Crawl, LAION-5B, Books3), cross-referenced with developer's public model cards.",
                "strength": "Strongest — objective, publicly verifiable.",
            },
            {
                "name": "Circumstantial Regurgitation",
                "detail": "Model reproduces protected content near-verbatim under targeted prompting. Establish through a reproducible, documented extraction protocol supported by CPR Part 35 expert evidence; near-verbatim reproduction of a substantial part is probative of ingestion.",
                "strength": "Strong — objective black-box forensic evidence.",
            },
            {
                "name": "Membership Inference Attack (MIA)",
                "detail": "Statistical methodology querying model outputs to determine, with probabilistic confidence, whether a specific data point was in the training set. Requires CPR Pt 35 expert evidence; black-box variants less reliable.",
                "strength": "Contingent — admissible as statistical indicator, not definitive proof.",
            },
        ],
    },
    "step_2_disclosure": {
        "title": "Step 2: Hash Manifests & Confidentiality Ring",
        "summary": "Upon satisfying the prima facie threshold, claimant seeks Model C Extended Disclosure under PD 57AD of narrow classes: cryptographic hash manifests (SHA-256) or deduplication logs. Production occurs within a confidentiality ring, typically external-eyes-only per IPCom and Mitsubishi.",
        "mechanism": [
            "Include 'Algorithmic Ingestion' as contested Issue for Disclosure on the DRD",
            "Court orders Model C Extended Disclosure — narrow, issue-based",
            "Developer produces SHA-256 manifests in confidentiality ring (CPR r.31.22(2))",
            "Jointly-instructed IT expert under CPR Pt 35 queries hashes and reports binary match result",
            "Proportionality governed by PD 57AD para 6.4 and CPR r.1.1",
        ],
    },
    "step_3_adverse_inference": {
        "title": "Step 3: Evidentiary Spoliation & the Adverse Inference",
        "summary": "Where developer fails to preserve or produce records without credible non-culpable explanation, court may exercise discretion to draw adverse inference on factual issue of ingestion. Foundational doctrine: Wisniewski v Central Manchester HA [1998] EWCA Civ 596; [1998] PIQR P324 (witnesses); extended to documents in Wetton v Ahmed [2011] EWCA Civ 610; applied to electronic records in Earles v Barclays Bank Plc [2009] EWHC 2500 (Mercantile).",
        "threshold": [
            "Distinguish deliberate suppression from routine data-minimisation practices",
            "Non-retention after formal notice of claim = deliberate spoliation",
            "Refusal to comply with disclosure order without credible justification triggers inference",
            "Inference is discretionary, not mandatory; supports factual ingestion, does not discharge ultimate burden of proof",
        ],
    },
}
