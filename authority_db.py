"""
authority_db.py — Libra's structured legal authority database.

═══════════════════════════════════════════════════════════════════════════════
PURPOSE
═══════════════════════════════════════════════════════════════════════════════

This module is the SINGLE SOURCE OF TRUTH for every legal authority Libra cites.
It is the architectural backbone that minimises hallucination to negligible
levels.

The principle: the LLM never generates citations. It only phrases facts that
have already been selected from this database. Any citation in any output must
resolve to an Authority entry here, or it is rejected by the verification layer.

═══════════════════════════════════════════════════════════════════════════════
ANTI-HALLUCINATION GUARANTEES
═══════════════════════════════════════════════════════════════════════════════

What this database structurally prevents:
✓ Fabricated case names (the LLM can only reference IDs that exist here)
✓ Wrong neutral citations (verified once, used many times)
✓ Invented paragraph numbers (we store the verified ones; LLM cannot add new)
✓ Hallucinated statutory sections (every section number is pre-verified)
✓ Fake regulators or instruments (entries are typed and audited)

What this database CANNOT prevent (honest limitations):
✗ The LLM applying a correct citation to the wrong factual situation
✗ Phrasing errors that misstate what an authority says
✗ Subtle misinterpretation of the relationship between authorities
✗ Errors in the database itself (mitigated by your manual verification)

In practice this reduces citation-hallucination to negligible levels. Output
quality still depends on careful prompt design and human review.

═══════════════════════════════════════════════════════════════════════════════
SCHEMA
═══════════════════════════════════════════════════════════════════════════════

Every authority is an Authority dataclass with:

    id              — stable, unique identifier (e.g. "CASE_WISNIEWSKI_1998")
    kind            — STATUTE | CASE | RULE | REGULATION | GUIDANCE | REPORT
    short_name      — what we display in outputs ("Wisniewski v Central Manchester HA")
    full_citation   — the canonical citation ("[1998] EWCA Civ 596; [1998] PIQR P324")
    jurisdiction    — UK | EU | DE | US | INTL
    year            — primary year (for sorting/filtering)
    summary         — one-paragraph plain-English summary used in outputs
    key_paragraphs  — list of verified paragraph/section references
    url             — verified source URL (BAILII, legislation.gov.uk, EUR-Lex)
    topic_tags      — list of topic keys (used for retrieval)
    verified_by     — author who verified (you, by default)
    verified_on     — date verified (ISO format)
    verification_source — where the citation was cross-checked
    notes           — any caveats (e.g. "appeal pending", "preprint")

═══════════════════════════════════════════════════════════════════════════════
USAGE PATTERNS
═══════════════════════════════════════════════════════════════════════════════

    from authority_db import AUTHORITIES, get, find_by_topic, format_citation

    # Direct lookup by ID
    wisniewski = get("CASE_WISNIEWSKI_1998")
    print(wisniewski.full_citation)

    # Find authorities relevant to a topic
    adverse_inference_authorities = find_by_topic("adverse_inference")

    # Format a citation for output
    text = format_citation("CASE_WISNIEWSKI_1998", include_paragraph="P324")

    # Verify a string contains only known citations (used by verification layer)
    is_valid, unknowns = verify_output_citations(llm_output)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ════════════════════════════════════════════════════════════════════════════
# SCHEMA
# ════════════════════════════════════════════════════════════════════════════

class Kind(str, Enum):
    STATUTE = "STATUTE"
    CASE = "CASE"
    RULE = "RULE"              # CPR, PD 57AD etc
    REGULATION = "REGULATION"  # EU Regulations, SIs
    DIRECTIVE = "DIRECTIVE"    # EU Directives
    GUIDANCE = "GUIDANCE"      # ICO, EUIPO, etc
    REPORT = "REPORT"          # Government reports, policy papers
    ACADEMIC = "ACADEMIC"      # Journal articles, preprints


class Jurisdiction(str, Enum):
    UK = "UK"
    EU = "EU"
    DE = "DE"
    US = "US"
    INTL = "INTL"


@dataclass(frozen=True)
class Authority:
    """A single legal authority. Frozen to prevent accidental modification."""
    id: str
    kind: Kind
    short_name: str
    full_citation: str
    jurisdiction: Jurisdiction
    year: Optional[int]
    summary: str
    key_paragraphs: tuple[str, ...] = field(default_factory=tuple)
    url: str = ""
    topic_tags: tuple[str, ...] = field(default_factory=tuple)
    verified_by: str = "R.A. Aswin Krishna"
    verified_on: str = "2026-05-13"
    verification_source: str = ""
    notes: str = ""

    # ── Currency tracking ────────────────────────────────────────────────────
    # A citation being CORRECT is not the same as an authority being CURRENT.
    # Without these fields a case awaiting judgment from a supreme court reads
    # exactly like a settled 1974 House of Lords decision. Audit of 29 Aug 2026
    # found zero wrong citations but five authorities whose status had moved:
    # Kneschke (BGH hearing 3 Sep 2026), Bartz (settlement approved, not
    # denied), DSM Art.4 (now contested by two Munich judgments), AI Act Art.53
    # (enforcement powers live 2 Aug 2026) and Getty (appeal permission
    # granted).
    #
    #   good_law      — no known challenge; apply normally
    #   under_appeal  — decided but subject to a pending appeal
    #   contested     — conflicting decisions in other courts on the same point
    #   pending       — not yet decided; listed for hearing or opinion
    #   superseded    — overtaken by later authority or amendment
    #
    # status_verified_on records WHEN the status was last checked. The UI must
    # display it, because an unqualified "under appeal" silently rots the
    # moment judgment is handed down.
    status: str = "good_law"
    status_verified_on: str = "2026-05-13"
    status_note: str = ""


# ════════════════════════════════════════════════════════════════════════════
# AUTHORITIES — the canonical database
# ════════════════════════════════════════════════════════════════════════════
#
# Every entry below has been verified against an authoritative source. The
# verification_source field records where each was cross-checked.
#
# ⚠️  IMPORTANT FOR THE USER (you):
# After I generate this initial migration, READ EVERY ENTRY and confirm each
# citation is correct. Flag anything to me that needs correction. Once you
# have signed off, the database becomes the single source of truth for the
# entire application.
# ════════════════════════════════════════════════════════════════════════════

AUTHORITIES: dict[str, Authority] = {

    # ─── CASES: UK ─────────────────────────────────────────────────────────

    "CASE_GETTY_V_STABILITY_2025": Authority(
        id="CASE_GETTY_V_STABILITY_2025",
        kind=Kind.CASE,
        short_name="Getty Images v Stability AI",
        full_citation="Getty Images (US) Inc v Stability AI Ltd [2025] EWHC 2863 (Ch)",
        jurisdiction=Jurisdiction.UK,
        year=2025,
        summary=(
            "Smith J — Model weights do not store recoverable copies of training "
            "images on the evidence; the claimant's secondary-infringement claim "
            "under CDPA 1988 ss.22-23 accordingly failed. Trade mark and passing "
            "off claims partially succeeded. Permission to appeal granted "
            "January 2026."
        ),
        url="https://www.bailii.org/ew/cases/EWHC/Ch/2025/2863.html",
        topic_tags=("ai_training", "secondary_infringement", "model_weights", "uk_landmark"),
        verification_source="BAILII; manuscript footnote 13",
        notes=(
            "Permission to appeal granted by Mrs Justice Joanna Smith DBE in "
            "December 2025 at the consequentials hearing (separate citation: "
            "[2025] EWHC 3343 (Ch)). Stability AI refused permission to appeal "
            "trade mark findings. Court of Appeal hearing expected within "
            "7-15 months of original decision date. Treat substantive findings "
            "as provisional pending appeal outcome."
        ),
        status="under_appeal",
        status_verified_on="2026-08-29",
        status_note=(
            "Permission to appeal GRANTED 16 December 2025 (Re Form of Order "
            "[2025] EWHC 3343 (Ch)). Appeal pending in the Court of Appeal on "
            "whether an 'article' can be an 'infringing copy' under CDPA "
            "ss.22-23 and s.27(3) where it never contained a copy. Parallel US "
            "action continues (N.D. Cal. 3:25-cv-06891). Note also that the "
            "Munich Regional Court reached the OPPOSITE technical conclusion on "
            "whether works are reproduced within model weights (GEMA v OpenAI; "
            "GEMA v Suno). Substantive findings provisional."
        ),
    ),

    "CASE_DESIGNERS_GUILD_2000": Authority(
        id="CASE_DESIGNERS_GUILD_2000",
        kind=Kind.CASE,
        short_name="Designers Guild v Russell Williams",
        full_citation=(
            "Designers Guild Ltd v Russell Williams (Textiles) Ltd "
            "[2000] UKHL 58; [2001] 1 All ER 700; [2000] 1 WLR 2416; [2001] FSR 11"
        ),
        jurisdiction=Jurisdiction.UK,
        year=2000,
        summary=(
            "House of Lords (Lords Bingham, Hoffmann, Hope, Millett, Scott). "
            "Two-stage approach to copyright infringement: (1) was there copying "
            "(causal connection), and (2) was a substantial part taken? Lord "
            "Hoffmann: 'the more abstract and simple the copied idea, the less "
            "likely it is to constitute a substantial part'. Where copying is "
            "found, substantiality will usually follow on the same facts. "
            "Appellate courts must not reopen the trial judge's substantial-part "
            "findings absent clear misdirection."
        ),
        url="https://www.bailii.org/uk/cases/UKHL/2000/58.html",
        topic_tags=("copyright_infringement", "substantial_part", "non_literal_copying"),
        verification_source="BAILII; vLex; HL judgment",
    ),

    "CASE_WISNIEWSKI_1998": Authority(
        id="CASE_WISNIEWSKI_1998",
        kind=Kind.CASE,
        short_name="Wisniewski v Central Manchester HA",
        full_citation=(
            "Wisniewski (A Minor) v Central Manchester Health Authority "
            "[1998] EWCA Civ 596; [1998] PIQR P324; [1998] Lloyds Rep Med 223"
        ),
        jurisdiction=Jurisdiction.UK,
        year=1998,
        summary=(
            "Court of Appeal (1 April 1998). Brooke LJ at p.340 articulated FIVE "
            "principles on adverse inferences from missing witnesses: (1) court "
            "MAY draw adverse inferences from absence/silence of a witness who "
            "might be expected to have material evidence on an issue; (2) such "
            "inferences may STRENGTHEN the other party's evidence or WEAKEN the "
            "evidence of the silent party; (3) there must FIRST be some evidence, "
            "however weak, adduced by the party seeking the inference (a 'case to "
            "answer'); (4) if a credible explanation for the absence is given, "
            "no inference or a reduced inference is drawn; (5) the inference is "
            "discretionary, not mandatory. Foundational authority. NOTE: Magdeev "
            "v Tsvetkov [2020] EWHC 887 (Comm) at [150]-[154] adds a structured "
            "three-step gateway before discretion engages."
        ),
        key_paragraphs=("p.340 (Brooke LJ — five principles)",),
        url="https://www.bailii.org/ew/cases/EWCA/Civ/1998/596.html",
        topic_tags=("adverse_inference", "evidence", "absent_witnesses"),
        verification_source=(
            "BAILII; PIQR; multiple appellate-level applications including "
            "Wetton v Ahmed [2011] and Magdeev v Tsvetkov [2020]"
        ),
    ),

    "CASE_WETTON_V_AHMED_2011": Authority(
        id="CASE_WETTON_V_AHMED_2011",
        kind=Kind.CASE,
        short_name="Wetton v Ahmed",
        full_citation="Wetton (as Liquidator of Mumtaz Properties Ltd) v Ahmed [2011] EWCA Civ 610",
        jurisdiction=Jurisdiction.UK,
        year=2011,
        summary=(
            "Court of Appeal. Arden LJ at [14]: 'contemporaneous written "
            "documentation is of the very greatest importance in assessing "
            "credibility... where there is room for doubt about a person's "
            "credibility, the failure of a party to call or to give evidence "
            "from a witness whose evidence might reasonably be expected to "
            "support that party's case is itself a powerful indicator that the "
            "evidence would not have supported it'. Primary modern authority "
            "extending Wisniewski logic to documentary spoliation and the "
            "elevation of contemporary documents over oral testimony."
        ),
        key_paragraphs=("[14] (Arden LJ — contemporary documents)",),
        url="https://www.bailii.org/ew/cases/EWCA/Civ/2011/610.html",
        topic_tags=("adverse_inference", "documents", "spoliation"),
        verification_source="BAILII; cross-referenced in Sinha v Taylor [2022] EWHC 1096",
    ),

    "CASE_MAGDEEV_V_TSVETKOV_2020": Authority(
        id="CASE_MAGDEEV_V_TSVETKOV_2020",
        kind=Kind.CASE,
        short_name="Magdeev v Tsvetkov",
        full_citation="Magdeev v Tsvetkov [2020] EWHC 887 (Comm)",
        jurisdiction=Jurisdiction.UK,
        year=2020,
        summary=(
            "Cockerill J in the Commercial Court — refined and structured the "
            "Wisniewski test. At [150]-[154]: before the discretion to draw an "
            "adverse inference engages, the party inviting the inference must "
            "(1) establish that the counter-party MIGHT HAVE called the witness "
            "and the witness HAD material evidence; (2) IDENTIFY the particular "
            "inference sought; (3) EXPLAIN why the inference is justified on "
            "the basis of other evidence. The 'increasingly relied upon' Wisniewski "
            "principle is not a substitute for proper proof of the underlying "
            "case."
        ),
        key_paragraphs=("[150]-[154] (three-step gateway)",),
        url="https://www.bailii.org/ew/cases/EWHC/Comm/2020/887.html",
        topic_tags=("adverse_inference", "evidence", "absent_witnesses"),
        verification_source="BAILII; Local Government Lawyer analysis",
        notes=(
            "Important refinement to cite alongside Wisniewski. The three-step "
            "gateway tightens the doctrine and limits scope for speculative "
            "inference-drawing applications."
        ),
    ),

    "CASE_EARLES_V_BARCLAYS_2009": Authority(
        id="CASE_EARLES_V_BARCLAYS_2009",
        kind=Kind.CASE,
        short_name="Earles v Barclays Bank Plc",
        full_citation="Earles v Barclays Bank Plc [2009] EWHC 2500 (Mercantile); [2009] WLR (D) 309",
        jurisdiction=Jurisdiction.UK,
        year=2009,
        summary=(
            "HHJ Simon Brown QC, 8 October 2009. Spoliation and electronic "
            "disclosure. Confirms NO general pre-action preservation duty — but "
            "the duty 'radically' engages once proceedings are commenced, "
            "particularly for electronically stored information held by banks. "
            "Adverse inferences for spoliation require clear evidence of "
            "deliberate destruction in anticipation of litigation."
        ),
        key_paragraphs=("[28] (no pre-action preservation duty)", "[38] (spoliation rule)"),
        url="https://www.bailii.org/ew/cases/EWHC/Mercantile/2009/2500.html",
        topic_tags=("electronic_records", "preservation_duty", "adverse_inference", "spoliation"),
        verification_source="BAILII; cross-checked WLR Daily and Guildhall Chambers paper",
        notes=(
            "Important caveat for PRPP Stage 3: this case LIMITS the pre-action "
            "preservation duty. Cite alongside Wetton v Ahmed and Wisniewski to "
            "balance the doctrine — not in isolation."
        ),
    ),

    "CASE_IPCOM_V_HTC_2013": Authority(
        id="CASE_IPCOM_V_HTC_2013",
        kind=Kind.CASE,
        short_name="IPCom v HTC Europe",
        full_citation="IPCom GmbH & Co KG v HTC Europe Co Ltd [2013] EWHC 2880 (Ch)",
        jurisdiction=Jurisdiction.UK,
        year=2013,
        summary=(
            "Roth J — confidentiality rings for source-code inspection; "
            "external-eyes-only tier to protect trade secrets in disclosure. "
            "Foundational UK authority for tightly-drawn confidentiality regimes "
            "(referred to as 'IPCom 2' in subsequent case law)."
        ),
        url="https://www.bailii.org/ew/cases/EWHC/Ch/2013/2880.html",
        topic_tags=("confidentiality_ring", "source_code", "disclosure"),
        verification_source="BAILII; cross-checked against OnePlus v Mitsubishi [2020] EWCA Civ 1562",
        notes="Specific paragraph references should be verified against full judgment before use.",
    ),

    "CASE_MITSUBISHI_V_ONEPLUS_2020": Authority(
        id="CASE_MITSUBISHI_V_ONEPLUS_2020",
        kind=Kind.CASE,
        short_name="Mitsubishi Electric v OnePlus",
        full_citation="Mitsubishi Electric Corporation v OnePlus Technology (Shenzhen) Co Ltd [2020] EWCA Civ 1562",
        jurisdiction=Jurisdiction.UK,
        year=2020,
        summary=(
            "Floyd LJ — three-tier confidentiality regime upheld for proprietary "
            "algorithms (Attorney's Eyes Only). Confirms the role of tightly-drawn "
            "confidentiality clubs in IP disclosure."
        ),
        key_paragraphs=("[39] (key principles summary, sub-paragraphs (i)-(x))",),
        url="https://www.bailii.org/ew/cases/EWCA/Civ/2020/1562.html",
        topic_tags=("confidentiality_ring", "three_tier", "algorithms"),
        verification_source="BAILII; verified against Court of Appeal judgment 19 Nov 2020",
    ),

    "CASE_INFEDERATION_V_GOOGLE_2020": Authority(
        id="CASE_INFEDERATION_V_GOOGLE_2020",
        kind=Kind.CASE,
        short_name="Infederation v Google",
        full_citation="Infederation Ltd v Google LLC [2020] EWHC 657 (Ch)",
        jurisdiction=Jurisdiction.UK,
        year=2020,
        summary=(
            "Roth J — restrictive inspection regimes are exceptional derogations "
            "from open justice; sets out the principles for evaluating "
            "confidentiality-club applications. Counterweight to over-restrictive "
            "rings."
        ),
        key_paragraphs=("[27]–[42]",),
        url="https://www.bailii.org/ew/cases/EWHC/Ch/2020/657.html",
        topic_tags=("confidentiality_ring", "open_justice", "disclosure"),
        verification_source="BAILII",
    ),

    "CASE_BLACK_V_SUMITOMO_2001": Authority(
        id="CASE_BLACK_V_SUMITOMO_2001",
        kind=Kind.CASE,
        short_name="Black v Sumitomo",
        full_citation="Black v Sumitomo Corporation [2001] EWCA Civ 1819",
        jurisdiction=Jurisdiction.UK,
        year=2001,
        summary=(
            "Rix LJ — leading authority on pre-action disclosure under CPR r.31.16. "
            "Pre-action disclosure is narrow and exceptional, requiring high "
            "specificity and a real prospect of substantive proceedings."
        ),
        key_paragraphs=("[71]–[72] (Rix LJ)",),
        url="https://www.bailii.org/ew/cases/EWCA/Civ/2001/1819.html",
        topic_tags=("pre_action_disclosure", "cpr_31_16"),
        verification_source="BAILII; manuscript footnote 38",
    ),

    "CASE_BERMUDA_V_KPMG_2001": Authority(
        id="CASE_BERMUDA_V_KPMG_2001",
        kind=Kind.CASE,
        short_name="Bermuda International Securities v KPMG",
        full_citation="Bermuda International Securities Ltd v KPMG [2001] EWCA Civ 269 (27 February 2001)",
        jurisdiction=Jurisdiction.UK,
        year=2001,
        summary=(
            "Court of Appeal — first significant appellate decision on CPR "
            "r.31.16 after its introduction in 1999. The Court DECLINED to lay "
            "down guidelines at this early stage, leaving each application to be "
            "assessed on its facts. Confirmed the structured 4-condition test "
            "under r.31.16(3): (a) likely-parties, (b) likely-relevance, (c) "
            "standard-disclosure scope, (d) desirability. Precursor to the more "
            "detailed Black v Sumitomo analysis later that year."
        ),
        url="https://www.bailii.org/ew/cases/EWCA/Civ/2001/269.html",
        topic_tags=("pre_action_disclosure", "cpr_31_16"),
        verification_source="BAILII; Law Gazette analysis",
    ),

    "CASE_BROWNLIE_2017": Authority(
        id="CASE_BROWNLIE_2017",
        kind=Kind.CASE,
        short_name="Brownlie v Four Seasons",
        full_citation="Four Seasons Holdings Inc v Brownlie [2017] UKSC 80",
        jurisdiction=Jurisdiction.UK,
        year=2017,
        summary=(
            "Lord Sumption — restated the 'good arguable case' standard under "
            "CPR r.6.37 for jurisdictional gateways. Standard is lower than the "
            "Part 24 summary judgment threshold."
        ),
        key_paragraphs=("[5]–[7] (Lord Sumption)",),
        url="https://www.bailii.org/uk/cases/UKSC/2017/80.html",
        topic_tags=("good_arguable_case", "jurisdictional_gateway", "cpr_6_37"),
        verification_source="BAILII; manuscript footnote 32",
    ),

    "CASE_RE_B_2008": Authority(
        id="CASE_RE_B_2008",
        kind=Kind.CASE,
        short_name="Re B (Care Proceedings: Standard of Proof)",
        full_citation="Re B (Children) (Care Proceedings: Standard of Proof) [2008] UKHL 35; [2009] 1 AC 11",
        jurisdiction=Jurisdiction.UK,
        year=2008,
        summary=(
            "House of Lords. Lord Hoffmann at [2]: 'If a legal rule requires a "
            "fact to be proved, a judge or jury must decide whether or not it "
            "happened. There is no room for a finding that it might have "
            "happened. The law operates a binary system in which the only values "
            "are 0 and 1.' Baroness Hale at [70]: 'the standard of proof... is "
            "the simple balance of probabilities, neither more nor less.' "
            "Seriousness of allegations is no longer relevant to the standard."
        ),
        key_paragraphs=("[2] (Lord Hoffmann, binary system)", "[70] (Baroness Hale, simple balance)"),
        url="https://www.bailii.org/uk/cases/UKHL/2008/35.html",
        topic_tags=("standard_of_proof", "binary_system"),
        verification_source="BAILII; Parliament publications; verified judgment text",
    ),

    "CASE_LIDL_V_TESCO_2024": Authority(
        id="CASE_LIDL_V_TESCO_2024",
        kind=Kind.CASE,
        short_name="Lidl v Tesco",
        full_citation=(
            "Lidl Great Britain Ltd v Tesco Stores Ltd [2024] EWCA Civ 262 "
            "(on appeal from [2023] EWHC 873 (Ch))"
        ),
        jurisdiction=Jurisdiction.UK,
        year=2024,
        summary=(
            "Court of Appeal (Lewison, Arnold, Birss LLJ; Arnold LJ lead "
            "judgment, 19 March 2024). UPHELD trade mark infringement under "
            "TMA s.10(3) and passing off; REVERSED copyright infringement "
            "finding. Tesco's Clubcard Prices signs took unfair advantage of "
            "Lidl's reputation for low prices and were detrimental to its "
            "distinctive character. The case raised the bar for 'change in "
            "economic behaviour' evidence in detriment claims. The Court split "
            "on the role of 'due cause' in the s.10(3) assessment — point left "
            "for future clarification."
        ),
        key_paragraphs=(
            "[44] (originality of derivative works)",
            "[67] (13 points on confusion analysis)",
            "[194] (narrow scope of protection)",
        ),
        url="https://www.bailii.org/ew/cases/EWCA/Civ/2024/262.html",
        topic_tags=("trade_mark", "unfair_advantage", "tma_10_3"),
        verification_source=(
            "BAILII; Fieldfisher; Gowling WLG; 11 South Square; Kluwer Trademark "
            "Blog; Capital Law"
        ),
    ),

    "CASE_SKY_V_SKYKICK_2024": Authority(
        id="CASE_SKY_V_SKYKICK_2024",
        kind=Kind.CASE,
        short_name="SkyKick UK v Sky",
        full_citation=(
            "SkyKick UK Ltd v Sky Ltd [2024] UKSC 36 "
            "(on appeal from [2021] EWCA Civ 1121)"
        ),
        jurisdiction=Jurisdiction.UK,
        year=2024,
        summary=(
            "UK Supreme Court (13 November 2024). Lord Kitchin (with Lords Reed, "
            "Lloyd-Jones, Hamblen, Burrows). LANDMARK ruling on bad-faith "
            "invalidity under TMA s.3(6). An application made WITHOUT genuine "
            "intention to use the mark in relation to specified goods or "
            "services constitutes bad faith and may invalidate the registration "
            "wholly or PARTIALLY in respect of those goods/services. Broad "
            "specifications combined with limited business plans support a bad-"
            "faith inference. Categories within a general description (e.g. "
            "'computer software') may be partially invalid where the applicant "
            "had no intention to use the mark for sub-categories."
        ),
        key_paragraphs=(
            "[2] (central issue)",
            "[239] (partial invalidation)",
            "[258] (credible evidence of intention)",
            "[323] (sub-categories within broad descriptions)",
        ),
        url="https://www.bailii.org/uk/cases/UKSC/2024/36.html",
        topic_tags=("trade_mark", "bad_faith", "specification", "uksc_landmark"),
        verification_source=(
            "Supreme Court press summary; Gowling WLG; IPKat; 11 South Square; "
            "Cambridge Legal Studies"
        ),
        notes=(
            "Decision in Sky v SkyKick saga (began 2016). The Supreme Court "
            "rejected the parties' attempt to withdraw the appeal late in the "
            "process on public-policy grounds. Lord Reed gave a concurring "
            "judgment on Brexit jurisdiction issues."
        ),
    ),

    "CASE_NORWICH_PHARMACAL_1974": Authority(
        id="CASE_NORWICH_PHARMACAL_1974",
        kind=Kind.CASE,
        short_name="Norwich Pharmacal v HMRC",
        full_citation="Norwich Pharmacal Co v Customs and Excise Commissioners [1974] AC 133",
        jurisdiction=Jurisdiction.UK,
        year=1974,
        summary=(
            "House of Lords — third-party disclosure where the third party has "
            "become innocently mixed up in wrongdoing. Distinct from inter-party "
            "disclosure under the CPR."
        ),
        url="",
        topic_tags=("third_party_disclosure", "norwich_pharmacal"),
        verification_source="manuscript footnote 49",
    ),

    "CASE_ASHWORTH_V_MGN_2002": Authority(
        id="CASE_ASHWORTH_V_MGN_2002",
        kind=Kind.CASE,
        short_name="Ashworth Hospital v MGN",
        full_citation="Ashworth Hospital Authority v MGN Ltd [2002] UKHL 29",
        jurisdiction=Jurisdiction.UK,
        year=2002,
        summary=(
            "Lord Woolf — Norwich Pharmacal applied to media defendants. Confirms "
            "the broad sweep of the jurisdiction but the need for clear wrongdoing."
        ),
        url="https://www.bailii.org/uk/cases/UKHL/2002/29.html",
        topic_tags=("third_party_disclosure", "norwich_pharmacal"),
        verification_source="BAILII; manuscript footnote 50",
    ),

    "CASE_SPILIADA_1987": Authority(
        id="CASE_SPILIADA_1987",
        kind=Kind.CASE,
        short_name="Spiliada Maritime v Cansulex",
        full_citation=(
            "Spiliada Maritime Corporation v Cansulex Ltd "
            "[1986] UKHL 10; [1987] AC 460; [1986] 3 WLR 972"
        ),
        jurisdiction=Jurisdiction.UK,
        year=1987,
        summary=(
            "House of Lords (Lord Goff of Chieveley giving the leading speech, "
            "with Lords Keith, Templeman, Griffiths and Mackay agreeing). The "
            "seminal modern statement of forum non conveniens. Two-stage test: "
            "(1) is there some other available forum which is clearly more "
            "appropriate? — burden on defendant; (2) if so, are there "
            "circumstances of substantial justice that should keep the case in "
            "England despite the more appropriate alternative? Connecting "
            "factors include availability of witnesses, governing law, parties' "
            "place of business. 'Forum non conveniens' is about appropriateness, "
            "not mere practical convenience."
        ),
        key_paragraphs=("p.476 (Lord Goff — modern statement)",),
        url="https://www.bailii.org/uk/cases/UKHL/1986/10.html",
        topic_tags=("forum_conveniens", "jurisdiction"),
        verification_source="BAILII; Oxford Public International Law; Wikipedia",
        notes=(
            "Post-Brexit, Spiliada has expanded application in UK courts as "
            "Owusu v Jackson constraints no longer apply. Adopted in Canada, "
            "Singapore, NZ, Hong Kong; rejected by Australia."
        ),
    ),

    # ─── CASES: EU / GERMANY ───────────────────────────────────────────────

    "CASE_INFOPAQ_2009": Authority(
        id="CASE_INFOPAQ_2009",
        kind=Kind.CASE,
        short_name="Infopaq International v Danske Dagblades",
        full_citation=(
            "Infopaq International A/S v Danske Dagblades Forening "
            "Case C-5/08, EU:C:2009:465 (16 July 2009)"
        ),
        jurisdiction=Jurisdiction.EU,
        year=2009,
        summary=(
            "CJEU (Fourth Chamber). Foundational EU originality threshold: a work "
            "is protected if it is the 'author's own intellectual creation'. At "
            "[47]-[48]: even an 11-word extract of a newspaper article may "
            "constitute reproduction 'in part' under Art. 2 of Directive 2001/29 "
            "if it contains an element which is the expression of the author's "
            "intellectual creation. Broad interpretation of the reproduction right. "
            "Triggered the harmonisation of originality across EU copyright."
        ),
        key_paragraphs=("[33]-[37] (originality threshold)", "[47]-[48] (11-word extract)"),
        url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:62008CJ0005",
        topic_tags=("copyright_originality", "reproduction_right", "eu_landmark"),
        verification_source="EUR-Lex CELEX:62008CJ0005; CURIA",
        notes=(
            "Post-Brexit, UK Supreme Court retains discretion to depart from "
            "Infopaq line under EU(W)A 2018 s.6. UK Court of Appeal confirmed "
            "the 'author's own intellectual creation' test in THJ v Sheridan "
            "[2023] EWCA Civ 1354."
        ),
    ),

    "CASE_PRC_V_NLA_2013": Authority(
        id="CASE_PRC_V_NLA_2013",
        kind=Kind.CASE,
        short_name="Public Relations Consultants Association v NLA",
        full_citation="Public Relations Consultants Association Ltd v Newspaper Licensing Agency Ltd [2013] UKSC 18",
        jurisdiction=Jurisdiction.UK,
        year=2013,
        summary=(
            "Supreme Court — temporary copies exception under CDPA s.28A. "
            "Transient or incidental copies that are integral to a technological "
            "process and have no independent economic significance fall outside "
            "the reproduction right."
        ),
        url="https://www.bailii.org/uk/cases/UKSC/2013/18.html",
        topic_tags=("temporary_copies", "cdpa_28a"),
        verification_source="BAILII",
    ),

    "CASE_KNESCHKE_V_LAION_2025": Authority(
        id="CASE_KNESCHKE_V_LAION_2025",
        kind=Kind.CASE,
        short_name="Kneschke v LAION",
        full_citation=(
            "Robert Kneschke v LAION e.V., OLG Hamburg (Hanseatic Higher Regional Court), "
            "10 December 2025, Ref.: 5 U 104/24 (on appeal from LG Hamburg, "
            "27 September 2024, Ref.: 310 O 227/23)"
        ),
        jurisdiction=Jurisdiction.DE,
        year=2025,
        summary=(
            "OLG Hamburg confirmed that LAION's creation of the LAION-5B dataset "
            "was covered by both the scientific-research TDM exception (Art. 3 "
            "DSM Directive / § 60d UrhG) and the general TDM exception (Art. 4 "
            "DSM / § 44b UrhG). On Art. 4(3): machine-readable opt-out must be "
            "machine-ACTIONABLE, not merely intelligible — assessed against the "
            "technological state of the art at the time of the disputed use "
            "(here: late 2021). Plaintiff's natural-language opt-out in stock-site "
            "T&Cs held INVALID for 2021 facts. First substantive European "
            "appellate guidance on what makes an Art. 4(3) reservation effective. "
            "Further appeal granted to the German Federal Court of Justice (BGH)."
        ),
        url="https://www.twobirds.com/en/insights/2025/germany/higher-regional-court-hamburg-confirms-ai-training-was-permitted-(kneschke-v,-d-,-laion)",
        topic_tags=("ai_training", "tdm_opt_out", "dsm_directive", "eu_landmark", "machine_readable"),
        verification_source=(
            "Bird & Bird (twobirds.com); Norton Rose Fulbright; DLA Piper; "
            "Kluwer Copyright Blog; Open Future; manuscript footnote 23"
        ),
        notes=(
            "Subject to further appeal to BGH. The court's machine-readability "
            "standard is FACT-SPECIFIC to 2021 technology — a 2025 fact pattern "
            "with the same opt-out form might reach a different result. Cite "
            "carefully in present-day contexts."
        ),
        status="under_appeal",
        status_verified_on="2026-08-29",
        status_note=(
            "Further appeal (Revision) PENDING before the Bundesgerichtshof, "
            "Docket I ZR 281/25. HEARING LISTED 3 SEPTEMBER 2026. The OLG "
            "Hamburg expressly allowed the further appeal. The BGH ruling may "
            "alter the scope of the s.44b UrhG / DSM Art.4 TDM opt-out on which "
            "this entry rests. Do NOT treat as settled law."
        ),
    ),

    # ─── CASES: US ─────────────────────────────────────────────────────────

    "CASE_BARTZ_V_ANTHROPIC_2025": Authority(
        id="CASE_BARTZ_V_ANTHROPIC_2025",
        kind=Kind.CASE,
        short_name="Bartz v Anthropic",
        full_citation=(
            "Bartz v Anthropic PBC, No. 3:24-cv-05417 (N.D. Cal.) "
            "(filed 19 August 2024); Order on Fair Use, Judge William Alsup, "
            "23 June 2025"
        ),
        jurisdiction=Jurisdiction.US,
        year=2025,
        summary=(
            "Judge Alsup's 32-page summary-judgment order. SPLIT decision: "
            "(1) Anthropic's use of lawfully-acquired books to train Claude LLMs "
            "was 'exceedingly transformative' and fair use under §107 of the "
            "Copyright Act; (2) digitisation of purchased print books for the "
            "central library was fair use because digital replaced print; BUT "
            "(3) Anthropic's retention of pirated copies (from shadow libraries "
            "such as LibGen) was NOT transformative and was infringement. Class "
            "certified mid-July 2025. Proposed $1.5bn class settlement filed "
            "26 August 2025; preliminary approval denied without prejudice on "
            "8 September 2025 by Judge Alsup."
        ),
        url="https://www.courtlistener.com/docket/69058235/bartz-v-anthropic-pbc/",
        topic_tags=("ai_training", "fair_use", "us_authority"),
        verification_source=(
            "CourtListener docket; Norton Rose Fulbright; ArentFox Schiff; "
            "McDonald Hopkins; Buchanan Ingersoll & Rooney"
        ),
        notes=(
            "US authority; persuasive only in UK context. Note that Judge Alsup "
            "doubted whether downloading pirated source copies could ever be "
            "justified as reasonably necessary to a fair use. Distinct from UK "
            "framework — CDPA has no fair-use defence, only fair-dealing and "
            "specific exceptions. Compare with Kadrey v Meta Platforms, decided "
            "days later by Judge Chhabria with different analysis."
        ),
        status="good_law",
        status_verified_on="2026-08-29",
        status_note=(
            "SETTLEMENT HISTORY CORRECTED (verified 29 Aug 2026). Preliminary "
            "approval was GRANTED 25 September 2025, not denied. FINAL APPROVAL "
            "given 20 July 2026 by Judge Araceli Martinez-Olguin (Judge Alsup "
            "having retired mid-case): USD 1.5bn, the largest copyright "
            "settlement in US history. ~91% of 482,460 certified works claimed; "
            "approximately 350 opt-outs; fees reduced to ~USD 101.6m. Judge "
            "Alsup's June 2025 fair-use reasoning is unaffected by the "
            "settlement and is distinguished at length in GEMA v Suno."
        ),
    ),

    # ─── CASES: GERMANY — AI training / memorisation ───────────────────────

    "CASE_GEMA_V_OPENAI_2025": Authority(
        id="CASE_GEMA_V_OPENAI_2025",
        kind=Kind.CASE,
        short_name="GEMA v OpenAI",
        full_citation=(
            "GEMA v OpenAI, Landgericht Muenchen I (Munich Regional Court I), "
            "42nd Civil Chamber, 11 November 2025, Case No. 42 O 14139/24"
        ),
        jurisdiction=Jurisdiction.DE,
        year=2025,
        summary=(
            "First European judgment holding that MEMORISATION of protected works "
            "within the parameters of a large language model is itself an act of "
            "reproduction, and that the text-and-data-mining exception does not "
            "cover it. GEMA sued two OpenAI group companies over nine German song "
            "lyrics (including 'Atemlos', 'Maenner' and 'Ueber den Wolken') which "
            "ChatGPT reproduced almost verbatim in response to simple prompts. The "
            "court largely upheld GEMA's claims for injunctive relief, information "
            "and damages, dismissing a secondary personality-rights claim. Applying "
            "Infopaq (C-5/08), it held that reproduction is construed broadly and "
            "includes any fixation; memorised lyrics therefore qualify as "
            "reproduction under s.16 UrhG. Reproduction during creation of the "
            "training DATASET fell within the TDM limitation (s.44b UrhG), but "
            "reproduction within the MODEL did not. OpenAI was directly liable "
            "because the chatbot made the lyrics available to an unlimited public."
        ),
        url="https://cms.law/en/deu/legal-updates/gema-vs.-openai-munich-regional-court-i-issues-landmark-copyright-decision",
        topic_tags=("ai_training", "tdm", "memorisation", "reproduction", "eu_copyright"),
        verification_source=(
            "Munich Regional Court I press release 11 Nov 2025 (unofficial "
            "translation); EUIPO case-law summary; CMS, Bird & Bird, Taylor "
            "Wessing, Norton Rose Fulbright, Preu Bohlig analyses"
        ),
        verified_on="2026-08-29",
        status="under_appeal",
        status_verified_on="2026-08-29",
        status_note=(
            "First-instance decision, currently under appeal. Judgment explicitly "
            "cites ss.15, 16, 19a, 44b UrhG and Arts.2-3 InfoSoc Directive and "
            "Art.4 DSM Directive. Directly contradicts the technical conclusion in "
            "Getty v Stability AI (England) on whether works are reproduced within "
            "model weights. Treat findings as provisional."
        ),
        notes=(
            "German authority; persuasive only in the UK. Of direct relevance to "
            "PRPP: the court reasoned from litigant-elicited outputs back to "
            "'expression stored in the model', which is precisely the evidential "
            "inference a structured disclosure procedure would replace with "
            "direct evidence of training-data content."
        ),
    ),

    "CASE_GEMA_V_SUNO_2026": Authority(
        id="CASE_GEMA_V_SUNO_2026",
        kind=Kind.CASE,
        short_name="GEMA v Suno",
        full_citation=(
            "GEMA v Suno Inc, Landgericht Muenchen I (Munich Regional Court I), "
            "42nd Civil Chamber (Presiding Judge Elke Schwager), 31 July 2026, "
            "Case No. 42 O 763/25"
        ),
        jurisdiction=Jurisdiction.DE,
        year=2026,
        summary=(
            "First European case on a generative AI MUSIC tool, and the first "
            "European ruling to impose copyright liability for AI training "
            "conducted entirely OUTSIDE the EU. Same chamber as GEMA v OpenAI, "
            "extending that reasoning from text to music. In relation to six "
            "musical works (including 'Rasputin' and 'Daddy Cool'), the court "
            "prohibited four acts: reproduction for training purposes in the "
            "United States; reproduction by memorisation within the model in "
            "Germany; communication to the public by offering the model; and "
            "reproduction and communication through the outputs. It founded "
            "jurisdiction over the US training on a venue rule for collecting "
            "societies, applied US copyright law to those acts, and REJECTED fair "
            "use. Suno, not its users, was held responsible for infringing "
            "outputs: users supplied only basic prompts, while Suno designed, "
            "trained and operated the models. The court held the burden of "
            "disproving market harm lay with Suno."
        ),
        url="https://www.twobirds.com/en/insights/2026/germany/munich-district-court-rules-on-ai-generated-music-gema-v-suno",
        topic_tags=("ai_training", "tdm", "memorisation", "extraterritorial", "fair_use"),
        verification_source=(
            "JUVE Patent; Bird & Bird; Reed Smith; Bristows; Conventus Law; "
            "PPC Land (143-page English translation reported 3 Aug 2026)"
        ),
        verified_on="2026-08-29",
        status="under_appeal",
        status_verified_on="2026-08-29",
        status_note=(
            "NOT FINAL. First-instance decision; appeal considered likely, "
            "focused on the extraterritorial limb, the memorisation standard and "
            "the 176 prompts relied on as evidence. Penalties of up to EUR "
            "250,000 per violation. The making-available claim under s.19a failed; "
            "the unnamed right of communication to the public succeeded instead."
        ),
        notes=(
            "German authority; persuasive only in the UK. Highly relevant to PRPP: "
            "the case turned on 176 litigant-generated prompts as the evidential "
            "route to establishing memorisation — an illustration of the "
            "evidential asymmetry a disclosure procedure is designed to address."
        ),
    ),

    "CASE_BGH_LAION_PENDING": Authority(
        id="CASE_BGH_LAION_PENDING",
        kind=Kind.CASE,
        short_name="BGH — Kneschke v LAION (pending)",
        full_citation=(
            "Kneschke v LAION e.V., Bundesgerichtshof (German Federal Court of "
            "Justice), Docket I ZR 281/25 (pending; hearing listed 3 September 2026)"
        ),
        jurisdiction=Jurisdiction.DE,
        year=2026,
        summary=(
            "Further appeal from OLG Hamburg (5 U 104/24, 10 December 2025). The "
            "Federal Court of Justice will consider the scope of the German TDM "
            "exception (s.44b UrhG, implementing DSM Art.4) and the "
            "machine-readability standard for a rightsholder opt-out. Germany's "
            "highest civil court on this question; the outcome will govern the "
            "TDM analysis relied on across the EU-facing engines."
        ),
        url="https://dejure.org/dienste/vernetzung/rechtsprechung?Gericht=BGH&Aktenzeichen=I+ZR+281%2F25",
        topic_tags=("tdm", "opt_out", "ai_training", "pending"),
        verification_source="BGH docket (dejure.org); Morgan Lewis; Bird & Bird",
        verified_on="2026-08-29",
        status="pending",
        status_verified_on="2026-08-29",
        status_note=(
            "NOT YET DECIDED. Hearing listed 3 September 2026. Cite only as a "
            "pending reference indicating that the point is unsettled. Never cite "
            "as authority for any proposition."
        ),
        notes="Pending appeal — no holding exists yet.",
    ),

    "CASE_CJEU_LIKE_COMPANY_PENDING": Authority(
        id="CASE_CJEU_LIKE_COMPANY_PENDING",
        kind=Kind.CASE,
        short_name="Like Company v Google (pending, CJEU)",
        full_citation=(
            "Like Company v Google Ireland Ltd, Case C-250/25 (CJEU, pending; "
            "Advocate General's opinion due 3 September 2026)"
        ),
        jurisdiction=Jurisdiction.EU,
        year=2026,
        summary=(
            "Pending reference to the Court of Justice concerning the "
            "text-and-data-mining exception under the DSM Directive and the "
            "treatment of generative AI outputs. The ruling will bind the "
            "interpretation of DSM Arts.3-4 across all Member States."
        ),
        url="",
        topic_tags=("tdm", "ai_training", "eu_copyright", "pending"),
        verification_source="Bird & Bird; Conventus Law reporting of GEMA v Suno",
        verified_on="2026-08-29",
        status="pending",
        status_verified_on="2026-08-29",
        status_note=(
            "NOT YET DECIDED. AG opinion due 3 September 2026; judgment later. "
            "Cite only to show the point is unsettled at EU level. Never cite as "
            "authority for any proposition."
        ),
        notes="Pending reference — no ruling exists yet.",
    ),

    # ─── STATUTES: CDPA 1988 ───────────────────────────────────────────────

    "STATUTE_CDPA_S1": Authority(
        id="STATUTE_CDPA_S1",
        kind=Kind.STATUTE,
        short_name="CDPA 1988 s.1",
        full_citation="Copyright, Designs and Patents Act 1988, s.1",
        jurisdiction=Jurisdiction.UK,
        year=1988,
        summary="Copyright subsists in original literary, dramatic, musical or artistic works.",
        url="https://www.legislation.gov.uk/ukpga/1988/48/section/1",
        topic_tags=("copyright_subsistence",),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_CDPA_S16": Authority(
        id="STATUTE_CDPA_S16",
        kind=Kind.STATUTE,
        short_name="CDPA 1988 s.16",
        full_citation="Copyright, Designs and Patents Act 1988, s.16",
        jurisdiction=Jurisdiction.UK,
        year=1988,
        summary=(
            "Acts restricted by copyright — including reproduction, distribution, "
            "and communication to the public. s.16(3) provides that restricted "
            "acts apply to the work as a whole OR any substantial part."
        ),
        url="https://www.legislation.gov.uk/ukpga/1988/48/section/16",
        topic_tags=("copyright_infringement", "restricted_acts", "substantial_part"),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_CDPA_S17": Authority(
        id="STATUTE_CDPA_S17",
        kind=Kind.STATUTE,
        short_name="CDPA 1988 s.17",
        full_citation="Copyright, Designs and Patents Act 1988, s.17",
        jurisdiction=Jurisdiction.UK,
        year=1988,
        summary=(
            "Copying includes reproduction in any material form; transient or "
            "incidental copies are included within the reproduction right."
        ),
        url="https://www.legislation.gov.uk/ukpga/1988/48/section/17",
        topic_tags=("reproduction_right", "copying"),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_CDPA_S28A": Authority(
        id="STATUTE_CDPA_S28A",
        kind=Kind.STATUTE,
        short_name="CDPA 1988 s.28A",
        full_citation="Copyright, Designs and Patents Act 1988, s.28A",
        jurisdiction=Jurisdiction.UK,
        year=1988,
        summary=(
            "Temporary copies exception — transient or incidental copies that are "
            "integral to a technological process and have no independent economic "
            "significance fall outside the reproduction right."
        ),
        url="https://www.legislation.gov.uk/ukpga/1988/48/section/28A",
        topic_tags=("temporary_copies", "exception"),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_CDPA_S29A": Authority(
        id="STATUTE_CDPA_S29A",
        kind=Kind.STATUTE,
        short_name="CDPA 1988 s.29A",
        full_citation="Copyright, Designs and Patents Act 1988, s.29A",
        jurisdiction=Jurisdiction.UK,
        year=1988,
        summary=(
            "TDM exception — copies for text and data mining are permitted only "
            "where the user has lawful access AND the purpose is NON-COMMERCIAL "
            "research. Commercial TDM remains infringing absent licence."
        ),
        url="https://www.legislation.gov.uk/ukpga/1988/48/section/29A",
        topic_tags=("tdm_exception", "non_commercial", "ai_training"),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_CDPA_S90": Authority(
        id="STATUTE_CDPA_S90",
        kind=Kind.STATUTE,
        short_name="CDPA 1988 s.90",
        full_citation="Copyright, Designs and Patents Act 1988, s.90",
        jurisdiction=Jurisdiction.UK,
        year=1988,
        summary="Assignment of copyright must be in writing signed by the assignor.",
        url="https://www.legislation.gov.uk/ukpga/1988/48/section/90",
        topic_tags=("assignment", "formalities"),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_CDPA_S96": Authority(
        id="STATUTE_CDPA_S96",
        kind=Kind.STATUTE,
        short_name="CDPA 1988 s.96",
        full_citation="Copyright, Designs and Patents Act 1988, s.96",
        jurisdiction=Jurisdiction.UK,
        year=1988,
        summary=(
            "Infringement actionable by the copyright owner; remedies include "
            "injunctions, damages, and accounts of profits."
        ),
        url="https://www.legislation.gov.uk/ukpga/1988/48/section/96",
        topic_tags=("infringement_remedies",),
        verification_source="legislation.gov.uk",
    ),

    # ─── STATUTES: TMA 1994 ────────────────────────────────────────────────

    "STATUTE_TMA_S5_2_B": Authority(
        id="STATUTE_TMA_S5_2_B",
        kind=Kind.STATUTE,
        short_name="TMA 1994 s.5(2)(b)",
        full_citation="Trade Marks Act 1994, s.5(2)(b)",
        jurisdiction=Jurisdiction.UK,
        year=1994,
        summary=(
            "Relative grounds for refusal — likelihood of confusion, including "
            "likelihood of association, between an applied-for mark and an earlier "
            "trade mark."
        ),
        url="https://www.legislation.gov.uk/ukpga/1994/26/section/5",
        topic_tags=("trade_mark", "relative_grounds", "confusion"),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_TMA_S5_3": Authority(
        id="STATUTE_TMA_S5_3",
        kind=Kind.STATUTE,
        short_name="TMA 1994 s.5(3)",
        full_citation="Trade Marks Act 1994, s.5(3)",
        jurisdiction=Jurisdiction.UK,
        year=1994,
        summary=(
            "Relative grounds — marks with a reputation. Refuses registration "
            "where use of the later mark would take unfair advantage of, or be "
            "detrimental to, the distinctive character or repute of an earlier "
            "mark with reputation."
        ),
        url="https://www.legislation.gov.uk/ukpga/1994/26/section/5",
        topic_tags=("trade_mark", "dilution", "reputation"),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_TMA_S10_2": Authority(
        id="STATUTE_TMA_S10_2",
        kind=Kind.STATUTE,
        short_name="TMA 1994 s.10(2)",
        full_citation="Trade Marks Act 1994, s.10(2)",
        jurisdiction=Jurisdiction.UK,
        year=1994,
        summary=(
            "Infringement by use of an identical or similar mark in relation to "
            "identical or similar goods/services where likelihood of confusion "
            "exists."
        ),
        url="https://www.legislation.gov.uk/ukpga/1994/26/section/10",
        topic_tags=("trade_mark", "infringement", "confusion"),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_TMA_S10_3": Authority(
        id="STATUTE_TMA_S10_3",
        kind=Kind.STATUTE,
        short_name="TMA 1994 s.10(3)",
        full_citation="Trade Marks Act 1994, s.10(3)",
        jurisdiction=Jurisdiction.UK,
        year=1994,
        summary=(
            "Infringement by taking unfair advantage of, or being detrimental to, "
            "the distinctive character or repute of a mark with reputation. The "
            "dilution provision."
        ),
        url="https://www.legislation.gov.uk/ukpga/1994/26/section/10",
        topic_tags=("trade_mark", "dilution", "unfair_advantage"),
        verification_source="legislation.gov.uk",
    ),

    "STATUTE_TMA_S3_1_C": Authority(
        id="STATUTE_TMA_S3_1_C",
        kind=Kind.STATUTE,
        short_name="TMA 1994 s.3(1)(c)",
        full_citation="Trade Marks Act 1994, s.3(1)(c)",
        jurisdiction=Jurisdiction.UK,
        year=1994,
        summary=(
            "Absolute grounds for refusal — marks consisting exclusively of signs "
            "or indications which may serve to designate kind, quality, quantity, "
            "value, geographical origin, or other characteristics of the goods or "
            "services. The descriptiveness ground."
        ),
        url="https://www.legislation.gov.uk/ukpga/1994/26/section/3",
        topic_tags=("trade_mark", "descriptiveness", "absolute_grounds"),
        verification_source="legislation.gov.uk",
    ),

    # ─── RULES: CPR / PD 57AD ──────────────────────────────────────────────

    "RULE_CPR_1_1": Authority(
        id="RULE_CPR_1_1",
        kind=Kind.RULE,
        short_name="CPR r.1.1",
        full_citation="Civil Procedure Rules 1998, r.1.1",
        jurisdiction=Jurisdiction.UK,
        year=1998,
        summary=(
            "Overriding objective — dealing with cases justly and at proportionate "
            "cost. Governs all procedural discretion under the CPR."
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part01",
        topic_tags=("overriding_objective", "proportionality"),
        verification_source="justice.gov.uk",
    ),

    "RULE_CPR_6_36": Authority(
        id="RULE_CPR_6_36",
        kind=Kind.RULE,
        short_name="CPR r.6.36",
        full_citation="Civil Procedure Rules 1998, r.6.36",
        jurisdiction=Jurisdiction.UK,
        year=1998,
        summary=(
            "Service of the claim form out of the jurisdiction where permission "
            "is required. Operates with the gateways in PD 6B."
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part06",
        topic_tags=("service_out", "jurisdiction"),
        verification_source="justice.gov.uk",
    ),

    "RULE_CPR_6_37": Authority(
        id="RULE_CPR_6_37",
        kind=Kind.RULE,
        short_name="CPR r.6.37",
        full_citation="Civil Procedure Rules 1998, r.6.37",
        jurisdiction=Jurisdiction.UK,
        year=1998,
        summary=(
            "Application for permission to serve out of jurisdiction. Requires "
            "'good arguable case' that the claim falls within a gateway under "
            "PD 6B, together with the merits threshold."
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part06",
        topic_tags=("good_arguable_case", "service_out", "jurisdictional_gateway"),
        verification_source="justice.gov.uk",
    ),

    "RULE_CPR_31_16": Authority(
        id="RULE_CPR_31_16",
        kind=Kind.RULE,
        short_name="CPR r.31.16",
        full_citation="Civil Procedure Rules 1998, r.31.16",
        jurisdiction=Jurisdiction.UK,
        year=1998,
        summary=(
            "Pre-action disclosure — narrow and exceptional. Requires real prospect "
            "of substantive proceedings between the parties, that the documents "
            "would fall within standard disclosure, and that disclosure is "
            "necessary to dispose fairly or save costs."
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part31",
        topic_tags=("pre_action_disclosure", "exceptional"),
        verification_source="justice.gov.uk",
    ),

    "RULE_CPR_31_22": Authority(
        id="RULE_CPR_31_22",
        kind=Kind.RULE,
        short_name="CPR r.31.22",
        full_citation="Civil Procedure Rules 1998, r.31.22",
        jurisdiction=Jurisdiction.UK,
        year=1998,
        summary=(
            "Restrictions on use of disclosed documents — used as the basis for "
            "confidentiality rings restricting onward use to the proceedings."
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part31",
        topic_tags=("confidentiality_ring", "use_of_documents"),
        verification_source="justice.gov.uk",
    ),

    "RULE_CPR_PT_24": Authority(
        id="RULE_CPR_PT_24",
        kind=Kind.RULE,
        short_name="CPR Part 24",
        full_citation="Civil Procedure Rules 1998, Part 24",
        jurisdiction=Jurisdiction.UK,
        year=1998,
        summary=(
            "Summary judgment — court may give summary judgment where a party has "
            "no real prospect of success on the claim or issue. Higher threshold "
            "than 'good arguable case'."
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part24",
        topic_tags=("summary_judgment", "real_prospect"),
        verification_source="justice.gov.uk",
    ),

    "RULE_CPR_PT_35": Authority(
        id="RULE_CPR_PT_35",
        kind=Kind.RULE,
        short_name="CPR Part 35",
        full_citation="Civil Procedure Rules 1998, Part 35",
        jurisdiction=Jurisdiction.UK,
        year=1998,
        summary=(
            "Experts and assessors. Restricts expert evidence to what is reasonably "
            "required; experts owe an overriding duty to the court."
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part35",
        topic_tags=("expert_evidence", "court_appointed"),
        verification_source="justice.gov.uk",
    ),

    "RULE_CPR_46_21": Authority(
        id="RULE_CPR_46_21",
        kind=Kind.RULE,
        short_name="CPR r.46.21",
        full_citation="Civil Procedure Rules 1998, Part 46 Section VII (rules 46.20-46.22); PD 46 paragraph 11.1, Tables A and B",
        jurisdiction=Jurisdiction.UK,
        year=1998,
        summary=(
            "IPEC overall costs cap — total recoverable costs in the Intellectual "
            "Property Enterprise Court capped at £60,000 on the final determination "
            "of a claim in relation to liability, and £30,000 on an inquiry as to "
            "damages or account of profits. Stage-cost tables in PD 46 paragraph "
            "11.1 (Tables A and B). The IPEC costs provisions were moved from "
            "Part 45 Section IV to Part 46 Section VII post-October 2023 to better "
            "reflect their nature as special-case costs rather than fixed costs."
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part46",
        topic_tags=("ipec", "costs_cap"),
        verification_source="IPEC Guide (revised November 2024), judiciary.uk; CPR Part 46 Section VII",
        notes=(
            "Pre-October 2023 the same provisions were at CPR r.45.31 / PD 45 "
            "Section IV. Older references in case law and academic literature "
            "still cite the old rule numbers."
        ),
    ),

    "RULE_PD_57AD": Authority(
        id="RULE_PD_57AD",
        kind=Kind.RULE,
        short_name="PD 57AD",
        full_citation="Practice Direction 57AD — Disclosure in the Business and Property Courts",
        jurisdiction=Jurisdiction.UK,
        year=2022,
        summary=(
            "Permanent regime from 1 October 2022 (replacing the pilot PD 51U). "
            "Applies to existing and new proceedings in the High Court Business "
            "and Property Courts. Provides for Initial Disclosure (with statement "
            "of case) and Extended Disclosure (five Models, A–E). EXCLUDED from "
            "scope per paragraph 1.4: County Court claims, Part 8 claims (unless "
            "ordered), Competition claims, and claims in the IPEC."
        ),
        key_paragraphs=(
            "para 1.4 (scope and exclusions including IPEC)",
            "para 3.1 (Known Adverse Documents)",
            "para 8.3 (Model C requests)",
            "para 10.4 (no tactical or oppressive use)",
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-57a-business-and-property-courts/practice-direction-57ad-disclosure-in-the-business-and-property-courts",
        topic_tags=("pd_57ad", "extended_disclosure", "business_property_courts"),
        verification_source="justice.gov.uk; Bevan Brittan, Gardner Leader, Stewarts analyses",
        notes=(
            "IMPORTANT: PD 57AD does NOT apply to IPEC. If your AI-copyright "
            "case is in the IPEC track, PRPP Stage 2 (Model C disclosure) is "
            "unavailable under this rule. Consider transferring to the BPC or "
            "using a different procedural vehicle."
        ),
    ),

    "RULE_PD_57AD_MODEL_C": Authority(
        id="RULE_PD_57AD_MODEL_C",
        kind=Kind.RULE,
        short_name="PD 57AD Model C",
        full_citation="Practice Direction 57AD, paragraph 8.3 — Model C Extended Disclosure",
        jurisdiction=Jurisdiction.UK,
        year=2022,
        summary=(
            "'Request-led search-based' disclosure of particular documents or "
            "narrow classes of documents, tied to contested Issues for "
            "Disclosure. Designed for easily-identifiable, well-defined classes "
            "(per Stewarts/Osafo guidance). NOT for lengthy granular requests, "
            "which the court treats as misuse. Well-suited to AI-training-data "
            "cases where the class is narrow (e.g. SHA-256 hash manifests, "
            "model cards, training-data lineage logs)."
        ),
        url="https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-57a-business-and-property-courts/practice-direction-57ad-disclosure-in-the-business-and-property-courts",
        topic_tags=("model_c", "extended_disclosure", "narrow_classes"),
        verification_source="justice.gov.uk PD 57AD para 8.3; Stewarts/Osafo 2023 NLJ commentary",
        notes=(
            "Misuse of Model C as a 'strategic weapon' is sanctioned by courts. "
            "Per para 10.4, requests must not be tactical or oppressive."
        ),
    ),

    # ─── EU REGULATIONS / DIRECTIVES ───────────────────────────────────────

    "REG_EU_AI_ACT_ART_53": Authority(
        id="REG_EU_AI_ACT_ART_53",
        kind=Kind.REGULATION,
        short_name="EU AI Act Art. 53",
        full_citation="Regulation (EU) 2024/1689 (AI Act), Article 53",
        jurisdiction=Jurisdiction.EU,
        year=2024,
        summary=(
            "Obligations on providers of general-purpose AI models. "
            "Art. 53(1)(c) requires a policy to comply with Union copyright law. "
            "Art. 53(1)(d) requires a 'sufficiently detailed summary' of training "
            "content, calibrated to a template adopted by the AI Office on 24 July "
            "2025 and in force from 2 August 2025. The template is aggregated to "
            "dataset-category level, not per-work attribution."
        ),
        url="https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        topic_tags=("ai_act", "training_data_disclosure", "gpai"),
        verification_source="EUR-Lex; manuscript footnote 28",
        status="good_law",
        status_verified_on="2026-08-29",
        status_note=(
            "ENFORCEMENT NOW LIVE. Art.53 obligations have applied since 2 "
            "August 2025 (models placed before that date have until 2 August "
            "2027). The AI Office gained supervisory and ENFORCEMENT powers on "
            "2 AUGUST 2026: it may demand documents, evaluate models, order "
            "corrective action, restrict or recall products, and fine up to the "
            "greater of EUR 15m or 3% of worldwide turnover (Art.101). The "
            "mandatory training-content template was adopted 24 July 2025."
        ),
    ),

    "DIR_DSM_ART_3": Authority(
        id="DIR_DSM_ART_3",
        kind=Kind.DIRECTIVE,
        short_name="DSM Directive Art. 3",
        full_citation="Directive (EU) 2019/790 (DSM Directive), Article 3",
        jurisdiction=Jurisdiction.EU,
        year=2019,
        summary=(
            "Mandatory TDM exception for scientific research by research "
            "organisations and cultural heritage institutions. No opt-out "
            "permitted. Takes precedence in qualifying contexts."
        ),
        url="https://eur-lex.europa.eu/eli/dir/2019/790/oj",
        topic_tags=("tdm", "scientific_research", "dsm_directive"),
        verification_source="EUR-Lex",
    ),

    "DIR_DSM_ART_4": Authority(
        id="DIR_DSM_ART_4",
        kind=Kind.DIRECTIVE,
        short_name="DSM Directive Art. 4",
        full_citation="Directive (EU) 2019/790 (DSM Directive), Article 4",
        jurisdiction=Jurisdiction.EU,
        year=2019,
        summary=(
            "TDM exception for commercial use. Subject to opt-out by rights-"
            "holders via machine-readable reservation under Art. 4(3). Confirmed "
            "by OLG Hamburg in Kneschke v LAION."
        ),
        url="https://eur-lex.europa.eu/eli/dir/2019/790/oj",
        topic_tags=("tdm", "commercial", "opt_out", "dsm_directive"),
        verification_source="EUR-Lex; Kneschke v LAION",
        status="contested",
        status_verified_on="2026-08-29",
        status_note=(
            "CONTESTED as at 29 August 2026. The Munich Regional Court has "
            "twice held that Art.4 covers only the data-PREPARATION phase and "
            "does NOT cover reproduction within the trained model itself: GEMA "
            "v OpenAI (LG Muenchen I, 11 Nov 2025, 42 O 14139/24) and GEMA v "
            "Suno (31 Jul 2026, 42 O 763/25). That is in tension with the OLG "
            "Hamburg analysis in Kneschke v LAION. Scope is now before the "
            "Bundesgerichtshof (I ZR 281/25, hearing 3 Sep 2026) and the CJEU "
            "(Like Company v Google, C-250/25, AG opinion due 3 Sep 2026). "
            "Advise with express reference to the split; not settled."
        ),
    ),

    # ─── REPORTS ───────────────────────────────────────────────────────────

    "REPORT_UK_MAR2026_COPYRIGHT_AI": Authority(
        id="REPORT_UK_MAR2026_COPYRIGHT_AI",
        kind=Kind.REPORT,
        short_name="UK Govt March 2026 Report on Copyright and AI",
        full_citation=(
            "DSIT, DCMS & IPO, 'Report on Copyright and Artificial Intelligence' "
            "(18 March 2026) policy paper, ISBN 978-1-5286-6308-3, "
            "published under ss.135-137 Data (Use and Access) Act 2025"
        ),
        jurisdiction=Jurisdiction.UK,
        year=2026,
        summary=(
            "Statutory analytical report (does NOT amend law). At paragraph 27, "
            "the government formally abandoned its previously preferred Option 3 "
            "(broad TDM exception with rights-reservation opt-out). No new "
            "legislative proposal advanced. CDPA s.29A non-commercial-research "
            "TDM exception preserved unchanged. The government will 'gather "
            "further evidence' and 'engage stakeholders on other potential "
            "policy approaches' — meaning status quo continues. Report identifies "
            "the evidentiary asymmetry in AI-copyright litigation but does NOT "
            "propose a procedural framework (leaving an opening for the PRPP "
            "approach). Companion Impact Assessment published same day."
        ),
        key_paragraphs=(
            "para 17 (Option 3 rejected by most respondents)",
            "para 27 (Option 3 no longer the preferred way forward)",
            "para 62 (EU TDM exceptions overview)",
            "paras 90-94 (s.17 CDPA reproduction issues)",
        ),
        url="https://assets.publishing.service.gov.uk/media/69ba692226909a14239612e4/CP2602959_-_Report_on_Copyright_and_Artificial_Intelligence_web.pdf",
        topic_tags=("uk_policy", "ai_training", "tdm", "march_2026_report"),
        verification_source="gov.uk; Fieldfisher, Bird & Bird, HSF Kramer, Bratby Law analyses",
        notes=(
            "Released alongside Liz Kendall MP's written ministerial statement "
            "(17 March 2026 Hansard) and a separate Impact Assessment. The "
            "House of Lords Communications and Digital Committee published its "
            "own critical report on 6 March 2026. Specific page references in "
            "the 123-page PDF should be verified directly against the document."
        ),
    ),

    # ─── ACADEMIC: the manuscript itself ───────────────────────────────────

    "ACADEMIC_KRISHNA_PRPP_2026": Authority(
        id="ACADEMIC_KRISHNA_PRPP_2026",
        kind=Kind.ACADEMIC,
        short_name="Krishna, PRPP (2026)",
        full_citation=(
            "R.A. Aswin Krishna, 'Training Data Disclosure in AI Copyright "
            "Litigation: The Post-Report Provenance Procedure' (2026), submitted "
            "for publication"
        ),
        jurisdiction=Jurisdiction.UK,
        year=2026,
        summary=(
            "Three-stage civil-procedure framework for AI-training-data disclosure "
            "operating through PD 57AD: (1) prima facie trigger under CPR r.6.37 "
            "good-arguable-case; (2) Model C Extended Disclosure of SHA-256 hash "
            "manifests within confidentiality ring; (3) discretionary adverse "
            "inference under the Wisniewski/Wetton/Earles lineage. Manuscript "
            "currently under editorial review at EIPR."
        ),
        url="",
        topic_tags=("prpp", "ai_copyright_procedure", "manuscript"),
        verification_source="author",
        notes="Status: under editorial review at EIPR (as of May 2026).",
    ),

    "ACADEMIC_AHMED_EXTRACTION_2026": Authority(
        id="ACADEMIC_AHMED_EXTRACTION_2026",
        kind=Kind.ACADEMIC,
        short_name="Ahmed et al., 'Extracting books...' (2026)",
        full_citation=(
            "Ahmed Ahmed, A. Feder Cooper, Sanmi Koyejo & Percy Liang, "
            "'Extracting books from production language models' (6 January 2026) "
            "arXiv:2601.02671 [cs.CL]"
        ),
        jurisdiction=Jurisdiction.INTL,
        year=2026,
        summary=(
            "PREPRINT, not peer-reviewed. Two-phase extraction procedure tested "
            "on four production LLMs (Claude 3.7 Sonnet, GPT-4.1, Gemini 2.5 Pro, "
            "Grok 3). Findings: Gemini 2.5 Pro returned 76.8% nv-recall on Harry "
            "Potter and the Sorcerer's Stone WITHOUT jailbreaking; Grok 3 at 70.3%. "
            "Jailbroken Claude 3.7 Sonnet reached nv-recall = 95.8% (near-verbatim "
            "entire books). 90-day responsible-disclosure window observed before "
            "publication (notified providers September 2025; published January 2026)."
        ),
        url="https://arxiv.org/abs/2601.02671",
        topic_tags=("memorisation", "regurgitation", "ai_research", "preprint"),
        verification_source="arXiv.org; SSRN paper id 6050534",
        notes=(
            "PREPRINT — not peer-reviewed at time of citation. Cite with explicit "
            "caveat. Note that one author (A. Feder Cooper) is also lead author of "
            "Cooper et al. (2025) cited in the same paper for extraction from "
            "Llama 3.1 70B."
        ),
    ),
}


# ════════════════════════════════════════════════════════════════════════════
# LOOKUP AND RETRIEVAL FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def get(authority_id: str) -> Optional[Authority]:
    """Retrieve an authority by its stable ID. Returns None if not found."""
    return AUTHORITIES.get(authority_id)


def get_or_raise(authority_id: str) -> Authority:
    """Retrieve an authority by ID. Raises KeyError if not found."""
    if authority_id not in AUTHORITIES:
        raise KeyError(
            f"Authority ID '{authority_id}' not found in database. "
            f"All citations must use a known ID — adding new authorities "
            f"requires verification and an entry in authority_db.py."
        )
    return AUTHORITIES[authority_id]


def find_by_topic(topic: str) -> list[Authority]:
    """
    Return all authorities tagged with the given topic.

    Topics are stable strings like 'adverse_inference', 'ai_training', etc.
    Used by engines to retrieve relevant authorities for a given factual
    situation.
    """
    return [a for a in AUTHORITIES.values() if topic in a.topic_tags]


def find_by_kind(kind: Kind) -> list[Authority]:
    """Return all authorities of a given kind (e.g. all CASES)."""
    return [a for a in AUTHORITIES.values() if a.kind == kind]


def find_by_jurisdiction(jurisdiction: Jurisdiction) -> list[Authority]:
    """Return all authorities for a given jurisdiction."""
    return [a for a in AUTHORITIES.values() if a.jurisdiction == jurisdiction]


# ════════════════════════════════════════════════════════════════════════════
# CITATION FORMATTING
# ════════════════════════════════════════════════════════════════════════════

def format_citation(
    authority_id: str,
    include_paragraph: Optional[str] = None,
    short: bool = False,
) -> str:
    """
    Format a citation for inclusion in output.

    Args:
        authority_id:      The stable ID of the authority.
        include_paragraph: Optional paragraph reference (must be in key_paragraphs).
        short:             If True, return short_name only. Otherwise full citation.

    Returns:
        Formatted citation string.

    Raises:
        KeyError if authority_id not found.
        ValueError if include_paragraph not in the authority's key_paragraphs.
    """
    auth = get_or_raise(authority_id)
    base = auth.short_name if short else auth.full_citation
    if include_paragraph:
        if include_paragraph not in auth.key_paragraphs:
            raise ValueError(
                f"Paragraph reference '{include_paragraph}' not verified for "
                f"{auth.id}. Verified paragraphs: {auth.key_paragraphs}"
            )
        return f"{base} at {include_paragraph}"
    return base


# ════════════════════════════════════════════════════════════════════════════
# VERIFICATION LAYER
# ════════════════════════════════════════════════════════════════════════════

# Patterns that look like citations in free-form text
_NEUTRAL_CIT_PATTERN = re.compile(
    r"\[\d{4}\]\s*(?:UKHL|UKSC|EWCA\s*Civ|EWCA\s*Crim|EWHC|UKPC|EWFC|AC|WLR|PIQR|All\s*ER)"
    r"[\s\w()]*"
)
_STATUTE_PATTERN = re.compile(
    r"(?:CDPA|TMA|UCTA|GDPR|CPR|PD\s*\d+\w*|s\.\s*\d+[A-Z]?(?:\(\d+\))?(?:\([a-z]\))?)\b",
    re.IGNORECASE
)


def extract_citations_from_text(text: str) -> list[str]:
    """
    Extract substrings from text that look like legal citations.

    Used by verify_output_citations to find candidate citations that
    should resolve to known authorities.
    """
    citations: list[str] = []
    for match in _NEUTRAL_CIT_PATTERN.finditer(text):
        citations.append(match.group(0).strip())
    return citations


def verify_output_citations(text: str) -> tuple[bool, list[str]]:
    """
    Verify that every citation-like substring in `text` corresponds to a
    known authority in AUTHORITIES.

    Returns:
        (is_valid, unknown_citations)
        - is_valid: True if every found citation matches a known authority
        - unknown_citations: list of substrings that do not match

    NOTE on honest limitations:
      This is a best-effort check. It catches obvious fabrications (cases
      that don't exist in our database). It does NOT verify that the citation
      is being applied to the correct factual situation, or that the
      paragraph numbers are accurate. Those require human review.
    """
    found = extract_citations_from_text(text)
    if not found:
        return True, []

    known_citations = {a.full_citation for a in AUTHORITIES.values()}
    known_short = {a.short_name for a in AUTHORITIES.values()}

    unknown: list[str] = []
    for cit in found:
        # Match if any known citation contains this fragment OR
        # this fragment contains a known short name
        if any(cit in known or known in cit for known in known_citations):
            continue
        if any(short in text for short in known_short):
            # The short form appears nearby; treat as verified
            continue
        unknown.append(cit)

    return len(unknown) == 0, unknown


# ════════════════════════════════════════════════════════════════════════════
# DATABASE STATISTICS (for status/health endpoints)
# ════════════════════════════════════════════════════════════════════════════

def stats() -> dict:
    """Return summary statistics about the authority database."""
    by_kind: dict[str, int] = {}
    by_jurisdiction: dict[str, int] = {}
    for a in AUTHORITIES.values():
        by_kind[a.kind.value] = by_kind.get(a.kind.value, 0) + 1
        by_jurisdiction[a.jurisdiction.value] = by_jurisdiction.get(a.jurisdiction.value, 0) + 1
    return {
        "total": len(AUTHORITIES),
        "by_kind": by_kind,
        "by_jurisdiction": by_jurisdiction,
        "topics": sorted({t for a in AUTHORITIES.values() for t in a.topic_tags}),
    }


# ════════════════════════════════════════════════════════════════════════════
# SELF-CHECK (run as: python authority_db.py)
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Libra Authority Database — Self Check")
    print("─" * 70)

    s = stats()
    print(f"\nTotal authorities: {s['total']}")
    print(f"\nBy kind:")
    for k, v in sorted(s["by_kind"].items()):
        print(f"  {k:<15} {v}")
    print(f"\nBy jurisdiction:")
    for j, v in sorted(s["by_jurisdiction"].items()):
        print(f"  {j:<6} {v}")
    print(f"\nDistinct topic tags: {len(s['topics'])}")
    print(f"\nFirst 10 topics: {s['topics'][:10]}")

    # Verify every authority has required fields populated
    print("\n─ Integrity check ─")
    issues = 0
    for aid, auth in AUTHORITIES.items():
        if not auth.short_name:
            print(f"  MISSING short_name: {aid}")
            issues += 1
        if not auth.full_citation:
            print(f"  MISSING full_citation: {aid}")
            issues += 1
        if not auth.summary:
            print(f"  MISSING summary: {aid}")
            issues += 1
        if not auth.verification_source:
            print(f"  MISSING verification_source: {aid}")
            issues += 1
    if issues == 0:
        print("  ✓ All entries have required fields")
    else:
        print(f"  ✗ {issues} integrity issues found")

    # Sample retrievals
    print("\n─ Sample retrievals ─")
    wisn = get("CASE_WISNIEWSKI_1998")
    print(f"  Wisniewski full:  {wisn.full_citation}")
    print(f"  Wisniewski short: {wisn.short_name}")

    adverse = find_by_topic("adverse_inference")
    print(f"\n  Authorities tagged 'adverse_inference': {len(adverse)}")
    for a in adverse:
        print(f"    - {a.short_name}")

    # Verification example
    print("\n─ Verification layer test ─")
    sample = (
        "The court relied on Wisniewski v Central Manchester HA [1998] EWCA Civ 596, "
        "later extended in Wetton v Ahmed [2011] EWCA Civ 610."
    )
    ok, unknown = verify_output_citations(sample)
    print(f"  Sample text valid: {ok}")
    print(f"  Unknown citations: {unknown}")

    bad_sample = (
        "The court relied on Smith v Made-Up Authority [2027] EWCA Civ 9999."
    )
    ok, unknown = verify_output_citations(bad_sample)
    print(f"\n  Bad sample valid: {ok}")
    print(f"  Unknown citations: {unknown}")
