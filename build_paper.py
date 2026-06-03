"""
PRPP White Paper — standalone PDF generator.

8-10 page research white paper formatted to journal-grade typographic
standards. Designed to stand alone if the EIPR submission is rejected.

Structure:
  Title page          (cover with abstract)
  I.   Introduction   (the evidentiary asymmetry)
  II.  Background     (March 2026 Report; Getty; the gap)
  III. The PRPP Framework (three stages, in detail)
  IV.  Anticipated Objections
  V.   Practical Implications
  VI.  Conclusion
  Footnotes / Endnotes
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, PageBreak, KeepTogether
)


# ── Palette (matching landing page + brief) ───────────────────────────────
INK         = colors.HexColor("#1a1814")
INK_SOFT    = colors.HexColor("#3d3830")
INK_MUTE    = colors.HexColor("#6b6354")
ACCENT      = colors.HexColor("#8b1a1a")
GOLD        = colors.HexColor("#a88533")
RULE_SOFT   = colors.HexColor("#c9bfa8")
PAPER       = colors.HexColor("#fdfaf3")  # slightly cleaner for a paper-document feel


# ── Page geometry ─────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN_X = 24 * mm
MARGIN_TOP = 22 * mm
MARGIN_BOTTOM = 22 * mm


def _on_cover_page(canvas, doc):
    """Cover page: subtle paper tone + accent rules. No header/footer."""
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Top double rule
    canvas.setStrokeColor(INK)
    canvas.setLineWidth(0.7)
    canvas.line(MARGIN_X, PAGE_H - MARGIN_TOP,
                PAGE_W - MARGIN_X, PAGE_H - MARGIN_TOP)
    canvas.setLineWidth(0.3)
    canvas.line(MARGIN_X, PAGE_H - MARGIN_TOP - 1.5*mm,
                PAGE_W - MARGIN_X, PAGE_H - MARGIN_TOP - 1.5*mm)

    # Bottom rule
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_X, MARGIN_BOTTOM, PAGE_W - MARGIN_X, MARGIN_BOTTOM)


def _on_body_page(canvas, doc):
    """Body pages: header line, page number, paper background."""
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Header line
    canvas.setStrokeColor(RULE_SOFT)
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN_X, PAGE_H - MARGIN_TOP + 6*mm,
                PAGE_W - MARGIN_X, PAGE_H - MARGIN_TOP + 6*mm)

    # Header text — running title left, author right
    canvas.setFont("Times-Italic", 8.5)
    canvas.setFillColor(INK_MUTE)
    canvas.drawString(MARGIN_X, PAGE_H - MARGIN_TOP + 9*mm,
                      "Training Data Disclosure in AI Copyright Litigation")
    canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - MARGIN_TOP + 9*mm,
                           "Aswin Krishna · 2026")

    # Footer rule
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN_X, MARGIN_BOTTOM - 6*mm,
                PAGE_W - MARGIN_X, MARGIN_BOTTOM - 6*mm)

    # Page number — centred, italic
    canvas.setFont("Times-Italic", 9)
    canvas.setFillColor(INK_MUTE)
    canvas.drawCentredString(PAGE_W / 2, MARGIN_BOTTOM - 11*mm, str(doc.page))


def build_paper(out_path: str = "PRPP_White_Paper.pdf"):
    body_frame = Frame(
        MARGIN_X, MARGIN_BOTTOM,
        PAGE_W - 2*MARGIN_X, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0
    )

    # Tighter cover frame
    cover_frame = Frame(
        MARGIN_X, MARGIN_BOTTOM + 4*mm,
        PAGE_W - 2*MARGIN_X, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM - 4*mm,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0
    )

    doc = BaseDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title="Training Data Disclosure in AI Copyright Litigation: The Post-Report Provenance Procedure",
        author="R.A. Aswin Krishna",
        subject="A civil-procedure framework for AI-copyright disclosure under PD 57AD, England & Wales",
        keywords="PRPP, AI, copyright, PD 57AD, CPR, Wisniewski, Getty v Stability AI, training data disclosure",
    )
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=_on_cover_page),
        PageTemplate(id="body", frames=[body_frame], onPage=_on_body_page),
    ])

    # ── Styles ───────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    # Cover
    s_cover_label = ParagraphStyle(
        "cover_label", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=9, leading=11,
        textColor=ACCENT, alignment=TA_LEFT,
        spaceAfter=3,
    )
    s_cover_title = ParagraphStyle(
        "cover_title", parent=styles["Title"],
        fontName="Times-Bold", fontSize=26, leading=30,
        textColor=INK, spaceAfter=10, alignment=TA_LEFT,
    )
    s_cover_subtitle = ParagraphStyle(
        "cover_subtitle", parent=styles["Italic"],
        fontName="Times-Italic", fontSize=14, leading=18,
        textColor=INK_SOFT, spaceAfter=24, alignment=TA_LEFT,
    )
    s_cover_author = ParagraphStyle(
        "cover_author", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=11, leading=14,
        textColor=INK, alignment=TA_LEFT, spaceAfter=2,
    )
    s_cover_affil = ParagraphStyle(
        "cover_affil", parent=styles["Italic"],
        fontName="Times-Italic", fontSize=10, leading=13,
        textColor=INK_MUTE, alignment=TA_LEFT, spaceAfter=14,
    )
    s_cover_abstract_label = ParagraphStyle(
        "cover_abs_label", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=10, leading=12,
        textColor=ACCENT, alignment=TA_LEFT, spaceAfter=4,
    )
    s_cover_abstract = ParagraphStyle(
        "cover_abstract", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=10.2, leading=14.4,
        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=8,
    )
    s_cover_keywords = ParagraphStyle(
        "cover_kw", parent=styles["Italic"],
        fontName="Times-Italic", fontSize=9, leading=12,
        textColor=INK_MUTE, alignment=TA_LEFT, spaceAfter=8,
    )

    # Body
    s_section_num = ParagraphStyle(
        "sec_num", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=9, leading=11,
        textColor=ACCENT, alignment=TA_LEFT,
        spaceBefore=10, spaceAfter=2,
    )
    s_section = ParagraphStyle(
        "section", parent=styles["Heading2"],
        fontName="Times-Bold", fontSize=14, leading=17,
        textColor=INK, alignment=TA_LEFT,
        spaceBefore=2, spaceAfter=8,
    )
    s_subsection = ParagraphStyle(
        "subsection", parent=styles["Heading3"],
        fontName="Times-Italic", fontSize=11.5, leading=14,
        textColor=INK, alignment=TA_LEFT,
        spaceBefore=8, spaceAfter=4,
    )
    s_body = ParagraphStyle(
        "body", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=10.2, leading=14.4,
        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6,
        firstLineIndent=14,
    )
    s_body_first = ParagraphStyle(
        "body_first", parent=s_body, firstLineIndent=0,
    )
    s_quote = ParagraphStyle(
        "quote", parent=styles["Italic"],
        fontName="Times-Italic", fontSize=9.8, leading=14,
        textColor=INK_SOFT, alignment=TA_JUSTIFY,
        leftIndent=18, rightIndent=18,
        spaceBefore=4, spaceAfter=8,
    )
    s_footnote = ParagraphStyle(
        "footnote", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=8.4, leading=11,
        textColor=INK_MUTE, alignment=TA_JUSTIFY, spaceAfter=3,
    )

    story = []

    # ════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 38*mm))
    story.append(Paragraph(
        "WHITE PAPER &nbsp;&middot;&nbsp; UK / EU IP &amp; AI LAW &nbsp;&middot;&nbsp; v1.0 &nbsp;&middot;&nbsp; 2026",
        s_cover_label
    ))
    story.append(HRFlowable(width="32%", thickness=0.7, color=INK,
                            spaceBefore=2, spaceAfter=10, hAlign='LEFT'))

    story.append(Paragraph(
        "Training Data Disclosure in AI Copyright Litigation",
        s_cover_title
    ))
    story.append(Paragraph(
        "The Post-Report Provenance Procedure: a three-stage civil-procedure "
        "framework operating through PD&nbsp;57AD in the Business and Property "
        "Courts of England and Wales.",
        s_cover_subtitle
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph("R.A. Aswin Krishna", s_cover_author))
    story.append(Paragraph(
        "IP-AI Practitioner &nbsp;&middot;&nbsp; "
        "Incoming LLM (Intellectual Property Law), Queen's University Belfast",
        s_cover_affil
    ))

    story.append(HRFlowable(width="100%", thickness=0.4, color=RULE_SOFT,
                            spaceBefore=2, spaceAfter=10))

    story.append(Paragraph("ABSTRACT", s_cover_abstract_label))
    story.append(Paragraph(
        "The UK Government's <i>March 2026 Report on Copyright and Artificial "
        "Intelligence</i> identified an evidentiary asymmetry at the heart of "
        "AI-copyright litigation: claimants cannot inspect training corpora, "
        "while EU AI Act Article 53 disclosures are aggregated to a level that "
        "does not establish causal nexus for individual works. <i>Getty Images "
        "(US) Inc v Stability AI Ltd</i> [2025] EWHC 2863 (Ch) confirmed the "
        "limits of the secondary-infringement route in the United Kingdom. "
        "The substantive law has not moved to fill the gap; the procedural "
        "toolkit has not been adapted to the asymmetry.",
        s_cover_abstract
    ))
    story.append(Paragraph(
        "This paper proposes the <i>Post-Report Provenance Procedure</i> "
        "(PRPP) — a three-stage civil-procedure framework operating through "
        "Practice Direction 57AD in the Business and Property Courts. PRPP "
        "synthesises three procedural levers that already exist (CPR r.6.37 "
        "good-arguable-case; PD 57AD Model C Extended Disclosure; and the "
        "Wisniewski adverse-inference doctrine) and applies them to AI-copyright "
        "disclosure as a coherent system. PRPP does not change the substantive "
        "test for infringement under CDPA 1988 s.16; it changes how the factual "
        "element of ingestion can be established in litigation.",
        s_cover_abstract
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Keywords:</b> AI &amp; copyright; training data disclosure; "
        "PD 57AD; CPR Pt 31; Model C Extended Disclosure; <i>Wisniewski</i>; "
        "<i>Getty v Stability AI</i>; civil procedure; UK IP law.",
        s_cover_keywords
    ))

    story.append(HRFlowable(width="100%", thickness=0.3, color=RULE_SOFT,
                            spaceBefore=4, spaceAfter=4))

    story.append(Paragraph(
        "<b>Suggested citation:</b> <i>R.A. Aswin Krishna, Training Data "
        "Disclosure in AI Copyright Litigation: The Post-Report Provenance "
        "Procedure (White Paper, 2026)</i>. Companion software: Libra "
        "Contract Guardian v1.1.",
        s_cover_keywords
    ))

    # ════════════════════════════════════════════════════════════════════
    # BODY — switch template
    # ════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    from reportlab.platypus import NextPageTemplate
    story.insert(-1, NextPageTemplate("body"))

    # ── I. INTRODUCTION ─────────────────────────────────────────────────
    story.append(Paragraph("§ I", s_section_num))
    story.append(Paragraph("Introduction: An Evidentiary Asymmetry", s_section))

    story.append(Paragraph(
        "Generative artificial-intelligence systems are trained on corpora "
        "the contents of which are, in any meaningful sense, unknowable to the "
        "rights-holders whose works they may contain. This asymmetry is not "
        "an incidental feature of the technology; it is a defining one. Modern "
        "foundation models ingest hundreds of billions of tokens drawn from "
        "common-crawl scrapes, licensed corpora, and curated datasets that the "
        "developer alone holds in fully-attributed form.",
        s_body_first
    ))

    story.append(Paragraph(
        "When a copyright owner suspects that her works have been ingested "
        "without licence, she encounters a problem that no traditional copyright "
        "case has had to confront: she cannot, by any ordinarily-available means, "
        "test whether the suspected ingestion in fact occurred. The training "
        "corpus is held internally; the model weights are a probabilistic "
        "compression of an unknown distribution; the EU AI Act Article 53(1)(d) "
        "obligation to publish a 'sufficiently detailed summary' is calibrated "
        "to aggregated transparency rather than per-work disclosure.<sup>1</sup>",
        s_body
    ))

    story.append(Paragraph(
        "The UK Government's <i>March 2026 Report on Copyright and Artificial "
        "Intelligence</i><sup>2</sup> identified this asymmetry without resolving "
        "it. The Report formally abandoned the previously preferred broad TDM "
        "exception with opt-out (Option 3), deferred decision on alternative "
        "reforms pending further evidence, and expressly preserved the "
        "pre-existing balance struck by CDPA 1988 s.29A. What it did not do — "
        "and what this paper takes up — is propose a procedural framework by "
        "which the asymmetry can be addressed within existing law while the "
        "policy debate continues.",
        s_body
    ))

    story.append(Paragraph(
        "The argument advanced here is that the Civil Procedure Rules and "
        "Practice Direction 57AD already contain the tools required. They have "
        "not been applied to AI-copyright disclosure as a coherent system, but "
        "their constituent elements — the good-arguable-case threshold, "
        "Model C Extended Disclosure, the confidentiality ring, and the "
        "discretionary adverse inference under <i>Wisniewski v Central "
        "Manchester HA</i> — are doctrinally settled and judicially familiar. "
        "Their synthesis into a three-stage procedure is what this paper calls "
        "the <i>Post-Report Provenance Procedure</i> (PRPP).",
        s_body
    ))

    # ── II. BACKGROUND ──────────────────────────────────────────────────
    story.append(Paragraph("§ II", s_section_num))
    story.append(Paragraph("Background: The State of AI-Copyright Litigation", s_section))

    story.append(Paragraph("II.1  <i>Getty v Stability AI</i> and the limits of the secondary route",
                            s_subsection))

    story.append(Paragraph(
        "<i>Getty Images (US) Inc v Stability AI Ltd</i> [2025] EWHC 2863 (Ch)<sup>3</sup> "
        "is the most consequential decision yet rendered by an English court on "
        "the AI-copyright question. The claimant pursued, among other heads, a "
        "secondary-infringement claim on the footing that the trained model "
        "weights themselves constituted an infringing copy under CDPA 1988 ss.22-23. "
        "Joanna Smith J rejected this theory on the evidence: the weights were "
        "not, on the technical findings, a recoverable copy of the training "
        "images.",
        s_body_first
    ))

    story.append(Paragraph(
        "The decision is presently under appeal, and a contrary view at appellate "
        "level cannot be excluded. But the more important point for present "
        "purposes is structural rather than doctrinal: even if the secondary "
        "route is reinstated, it does nothing to address the prior, factual "
        "question of whether the protected works were in fact ingested. That "
        "question remains an evidentiary problem first, and a doctrinal problem "
        "second.",
        s_body
    ))

    story.append(Paragraph("II.2  The aggregation problem in EU AI Act Article 53",
                           s_subsection))

    story.append(Paragraph(
        "The EU AI Act, Regulation (EU) 2024/1689, requires providers of "
        "general-purpose AI models to publish a 'sufficiently detailed summary' "
        "of the content used for training (Art. 53(1)(d)). The implementing "
        "template prescribes summary disclosures at the level of dataset "
        "categories — public web crawl, licensed text, etc. — rather than at "
        "the level of individual works.<sup>4</sup>",
        s_body_first
    ))

    story.append(Paragraph(
        "From a regulatory-transparency perspective this is intelligible: the "
        "Article was drafted to balance copyright awareness against trade-secrecy "
        "and competitive concerns. From a litigation-evidence perspective, "
        "however, an aggregate disclosure does not establish causal nexus. A "
        "claimant cannot prove that <i>her particular work</i> was ingested by "
        "pointing to a published summary stating that 'public web data' was "
        "used — even if her work was undeniably available on the public web. "
        "The aggregation level forecloses precisely the inferential step the "
        "claimant must make.",
        s_body
    ))

    story.append(Paragraph("II.3  The procedural vacuum",
                           s_subsection))

    story.append(Paragraph(
        "What the rights-holder requires, and what neither the UK March 2026 "
        "Report nor the EU AI Act provides, is a procedural mechanism by which "
        "she may, on adequate prima facie evidence, compel disclosure of "
        "information sufficient to confirm or refute the factual proposition "
        "that her works were ingested. PRPP fills that vacuum.",
        s_body_first
    ))

    # ── III. THE FRAMEWORK ──────────────────────────────────────────────
    story.append(Paragraph("§ III", s_section_num))
    story.append(Paragraph("The PRPP Framework", s_section))

    story.append(Paragraph(
        "PRPP is staged. Each stage corresponds to a distinct procedural lever "
        "in the existing CPR / PD 57AD architecture, and each must be cleared "
        "before the next is reached. The staging is what makes PRPP "
        "proportionate: it ensures that costly disclosure is not ordered without "
        "antecedent evidence sufficient to justify it.",
        s_body_first
    ))

    story.append(Paragraph("III.1  Stage One — The Prima Facie Trigger",
                           s_subsection))

    story.append(Paragraph(
        "The claimant must clear a threshold of plausible inference of "
        "ingestion, calibrated to the 'good arguable case' standard articulated "
        "in CPR r.6.37 and the jurisdictional gateway authorities — not the "
        "higher 'real prospect of success' standard under CPR Part 24.<sup>5</sup> "
        "Three evidentiary routes are recognised:",
        s_body_first
    ))

    story.append(Paragraph(
        "<b>(a) Hosted-repository evidence.</b> The claimant adduces factual "
        "evidence that her protected portfolio was hosted on a domain "
        "comprehensively scraped by a known dataset (Common Crawl, LAION-5B, "
        "Books3 are the most common candidates), and cross-references this with "
        "the developer's public model-card disclosures. This route is the "
        "strongest because it is objective and publicly verifiable.",
        s_body
    ))

    story.append(Paragraph(
        "<b>(b) Circumstantial regurgitation.</b> The model, under targeted "
        "prompting, reproduces protected content near-verbatim. The "
        "Stanford-Yale study by Ahmed et al. (2026) provides the methodology "
        "and a calibration baseline: nv-recall of 95.8% on protected books "
        "for Claude 3.7 Sonnet under BoN=258 jailbreak conditions; "
        "76.8% on Harry Potter content for Gemini 2.5 Pro without "
        "jailbreaking.<sup>6</sup> This is forensic evidence in the "
        "black-box model: it does not require access to weights or corpus.",
        s_body
    ))

    story.append(Paragraph(
        "<b>(c) Membership Inference Attack (MIA).</b> A statistical "
        "methodology, deployed via CPR Part 35 expert evidence, that queries "
        "model outputs to determine — with probabilistic confidence — whether "
        "a specific data point was in the training set. White-box MIA (full "
        "model access) is highly reliable but unavailable to the claimant; "
        "black-box variants are admissible as a statistical indicator but not "
        "as definitive proof. PRPP treats Stage One MIA as supportive evidence, "
        "not as a stand-alone trigger.",
        s_body
    ))

    story.append(Paragraph("III.2  Stage Two — Model C Extended Disclosure",
                           s_subsection))

    story.append(Paragraph(
        "Once Stage One is cleared, the claimant seeks Model C Extended "
        "Disclosure under PD 57AD of narrow classes of material: cryptographic "
        "hash manifests (SHA-256) and deduplication logs of the training "
        "corpus.<sup>7</sup> The disclosure is narrow because the question is "
        "narrow: did the developer's training set contain a hash matching the "
        "claimant's work? A binary match — established in seconds by a "
        "jointly-instructed expert — answers it.",
        s_body_first
    ))

    story.append(Paragraph(
        "Production occurs within a confidentiality ring. The choice of tier "
        "is fact-sensitive:",
        s_body
    ))

    story.append(Paragraph(
        "&bull; <b>External-eyes-only</b>, per <i>IPCom v HTC Europe</i> "
        "[2013] EWHC 2880 (Ch),<sup>8</sup> where trade-secrecy concerns "
        "predominate and the developer is well-resourced.<br/>"
        "&bull; <b>Three-tier</b>, per <i>Mitsubishi Electric v OnePlus</i> "
        "[2020] EWCA Civ 1562, for proprietary-algorithm cases where "
        "internal counsel involvement is appropriate.<br/>"
        "&bull; <b>Self-certified (SME)</b>, where the developer is a small "
        "or medium enterprise. The March 2026 Report at p.66 expressly "
        "identified disproportionate cost as a barrier to innovation; PRPP "
        "responds with a lower-cost tier that preserves the procedural "
        "architecture without imposing external-counsel costs.",
        s_body
    ))

    story.append(Paragraph(
        "Proportionality is governed by PD 57AD para 6.4 and CPR r.1.1. The "
        "narrowness of the disclosure — hash manifests, not full corpora — is "
        "what makes the procedure proportionate even in lower-value claims.",
        s_body
    ))

    story.append(Paragraph("III.3  Stage Three — Adverse Inference",
                           s_subsection))

    story.append(Paragraph(
        "Where the developer fails to preserve or to produce hash records "
        "without credible non-culpable explanation, the court may exercise its "
        "discretion to draw an adverse inference on the factual issue of "
        "ingestion. The foundational principle is set out in <i>Wisniewski v "
        "Central Manchester Health Authority</i> [1998] EWCA Civ 596; "
        "[1998] PIQR P324 (Brooke LJ),<sup>9</sup> with the doctrinal extension "
        "to absent documents articulated in <i>Wetton v Ahmed</i> [2011] EWCA "
        "Civ 610 (Arden LJ at [14]) and applied to electronic records in "
        "<i>Earles v Barclays Bank Plc</i> [2009] EWHC 2500 (Mercantile).",
        s_body_first
    ))

    story.append(Paragraph(
        "PRPP requires the court at Stage Three to distinguish two situations, "
        "consistent with the Earles principle that the duty to preserve "
        "engages once proceedings are contemplated, not before:",
        s_body
    ))

    story.append(Paragraph(
        "&bull; <b>Deliberate spoliation</b>: non-retention <i>after</i> formal "
        "notice of claim, or refusal to comply with a disclosure order without "
        "credible justification. The Wisniewski / Wetton inference is "
        "appropriate.<br/>"
        "&bull; <b>Routine data-minimisation</b>: pre-litigation overwrites in "
        "the ordinary course of business, server-optimisation deletions, and "
        "data-protection-compliant minimisation regimes adopted before any "
        "knowledge of contemplated proceedings. The inference should not be "
        "drawn from these alone — Earles confirms there is no general "
        "pre-action preservation duty.",
        s_body
    ))

    story.append(Paragraph(
        "The discretion is not mandatory and supports the factual finding of "
        "ingestion; it does not discharge the claimant's ultimate burden on "
        "the substantive infringement question. PRPP is, throughout, a "
        "procedural mechanism — not a substantive doctrine.",
        s_body
    ))

    # ── IV. ANTICIPATED OBJECTIONS ──────────────────────────────────────
    story.append(Paragraph("§ IV", s_section_num))
    story.append(Paragraph("Anticipated Objections", s_section))

    story.append(Paragraph("IV.1  'This is disclosure overreach.'",
                           s_subsection))

    story.append(Paragraph(
        "PRPP does not order disclosure of the training corpus. It orders "
        "disclosure of cryptographic hashes — fixed-length strings that "
        "reveal nothing about the underlying content other than whether a "
        "specific known input was present. The mechanism is more analogous "
        "to a forensic hash-comparison in computer-misuse litigation than to "
        "a corpus-wide data-room exercise.",
        s_body_first
    ))

    story.append(Paragraph("IV.2  'It will chill UK AI investment.'",
                           s_subsection))

    story.append(Paragraph(
        "The opposite. The status quo — under which UK courts have no "
        "settled procedure for handling training-data evidence — produces "
        "uncertainty for both rights-holders and developers. PRPP creates "
        "a defined procedural pathway with proportionality safeguards, which "
        "is precisely what well-advised developers prefer to ad-hoc "
        "disclosure battles. The SME tier is designed to ensure smaller "
        "developers are not priced out.",
        s_body_first
    ))

    story.append(Paragraph("IV.3  'The substantive law has not been settled.'",
                           s_subsection))

    story.append(Paragraph(
        "Correct, and PRPP does not require it to be. The framework operates "
        "at the procedural layer: it allows the factual question of ingestion "
        "to be answered. Whether that answer entails infringement is a "
        "separate question, governed by the existing substantive tests in "
        "CDPA 1988 ss.16-17 and the leading cases (<i>Designers Guild v "
        "Russell Williams</i>; <i>Infopaq</i>). The two questions are "
        "logically separable; PRPP separates them.",
        s_body_first
    ))

    # ── V. PRACTICAL IMPLICATIONS ───────────────────────────────────────
    story.append(Paragraph("§ V", s_section_num))
    story.append(Paragraph("Practical Implications", s_section))

    story.append(Paragraph(
        "PRPP has implications for three constituencies.",
        s_body_first
    ))

    story.append(Paragraph(
        "<b>For rights-holders and their advisers</b>, PRPP provides a "
        "pleadable procedural pathway. A claim particularised under PRPP "
        "should: (i) plead Stage One evidence in the Particulars of Claim; "
        "(ii) include 'algorithmic ingestion' as a contested Issue for "
        "Disclosure on the Disclosure Review Document; (iii) seek a Stage Two "
        "Model C order at the first Case Management Conference; and (iv) "
        "preserve the Stage Three argument by sending a pre-action "
        "preservation letter at the earliest opportunity.",
        s_body
    ))

    story.append(Paragraph(
        "<b>For AI developers and in-house counsel</b>, PRPP creates an "
        "incentive to maintain hash-manifest records of training corpora "
        "as a matter of good practice. Such records are inexpensive to "
        "create, do not compromise trade secrecy (a hash reveals nothing "
        "about content), and substantially reduce the developer's exposure "
        "to a Stage Three adverse inference if they are produced when "
        "called for.",
        s_body
    ))

    story.append(Paragraph(
        "<b>For courts and the Disclosure Working Group</b>, PRPP offers "
        "a worked-through application of PD 57AD to a problem the Practice "
        "Direction was not specifically designed for but accommodates "
        "naturally. The framework requires no rule-change; it requires only "
        "the recognition that 'algorithmic ingestion' is a discrete Issue "
        "for Disclosure susceptible to Model C treatment, and that hash-manifest "
        "records are a discrete class of documents within the meaning of "
        "PD 57AD para 6.5.",
        s_body
    ))

    # ── VI. CONCLUSION ──────────────────────────────────────────────────
    story.append(Paragraph("§ VI", s_section_num))
    story.append(Paragraph("Conclusion", s_section))

    story.append(Paragraph(
        "The argument of this paper is conservative in form and ambitious only "
        "in its synthesis. The CPR r.6.37 threshold has been settled for two "
        "decades. PD 57AD has been operating in the Business and Property Courts "
        "since 2019. The <i>Wisniewski</i> doctrine is older still. What is new "
        "is the proposition that these three settled procedural tools, applied "
        "in sequence to the discrete problem of AI-training-data disclosure, "
        "constitute a coherent and proportionate response to the evidentiary "
        "asymmetry the March 2026 Report identified.",
        s_body_first
    ))

    story.append(Paragraph(
        "The Post-Report Provenance Procedure does not change what counts as "
        "infringement. It changes how the factual element of ingestion can be "
        "established. That is sufficient. The substantive questions — what "
        "constitutes a substantial part; whether transient copies engage s.17; "
        "the proper construction of CDPA 1988 s.29A in commercial settings — "
        "remain open, as they should. PRPP exists to ensure those questions "
        "can be reached, on a properly-developed factual record, in the courts "
        "of England and Wales.",
        s_body
    ))

    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="40%", thickness=0.4, color=RULE_SOFT,
                            spaceBefore=2, spaceAfter=8, hAlign='CENTER'))

    # ── ENDNOTES ────────────────────────────────────────────────────────
    story.append(Paragraph("§ &nbsp; Endnotes", s_section))

    notes = [
        ("1", "Regulation (EU) 2024/1689 (the EU AI Act), Article 53(1)(d). "
         "The European AI Office's implementing template (2025) calibrates "
         "disclosure to dataset-category level."),
        ("2", "UK Government, <i>Report on Copyright and Artificial Intelligence</i> "
         "(March 2026), available at gov.uk."),
        ("3", "<i>Getty Images (US) Inc v Stability AI Ltd</i> [2025] EWHC 2863 "
         "(Ch). The judgment of Smith J holds that, on the technical evidence "
         "adduced, the trained model weights did not store recoverable copies "
         "of the training images; the claimant's secondary-infringement claim "
         "under CDPA 1988 ss.22-23 accordingly failed. Appeal pending."),
        ("4", "European Commission, <i>Template for the Public Summary of "
         "Training Content for General-Purpose AI Models</i>, adopted by the "
         "AI Office on 24 July 2025, in force for new models from 2 August "
         "2025. The template is calibrated to dataset-category, source-domain, "
         "and approximate-volume disclosure, rather than per-work attribution. "
         "See also EU AI Act Code of Practice on Transparency, Copyright, and "
         "Safety (10 July 2025)."),
        ("5", "The good-arguable-case standard is articulated in <i>Brownlie "
         "v Four Seasons Holdings Inc</i> [2017] UKSC 80 and is the relevant "
         "threshold under CPR r.6.37 for jurisdictional gateways. It is "
         "lower than the CPR Part 24 standard and is the appropriate "
         "calibration for a Stage One PRPP trigger. For Disclosure under "
         "PD 57AD the threshold is gating-by-Issue rather than gating-by-merits, "
         "but the structural analogy holds."),
        ("6", "Ahmed Ahmed et al., <i>Extracting books from production "
         "language models</i> (2026) arXiv:2601.02671 [cs.CL]. <b>Preprint, "
         "not peer-reviewed at time of writing</b>; institutional affiliations "
         "as stated by the authors. Headline figures: Claude 3.7 Sonnet at "
         "95.8% nv-recall under Best-of-N jailbreak (BoN=258); Gemini 2.5 Pro "
         "at 76.8% on Harry Potter and the Sorcerer's Stone without "
         "jailbreaking. The methodology is black-box and reproducible via "
         "prompt-only access. Cited here as preliminary empirical evidence of "
         "verbatim-memorisation capacity in production models, not as proof "
         "of infringement."),
        ("7", "PD 57AD Model C is the 'request-led search-based' disclosure "
         "model, in which parties identify narrow classes of documents tied "
         "to the contested Issues for Disclosure. It is well-suited to "
         "AI-training-data disclosure precisely because the relevant class "
         "(hash manifests of ingested content) is narrow and defined."),
        ("8", "<i>IPCom GmbH &amp; Co KG v HTC Europe Co Ltd</i> [2013] EWHC "
         "2880 (Ch) at [360]–[377] (Roth J), establishing a tightly-drawn "
         "confidentiality ring restricting source-code inspection to external "
         "lawyers and independent experts. <i>Mitsubishi Electric Corporation "
         "v OnePlus Technology (Shenzhen) Co Ltd</i> [2020] EWCA Civ 1562 at "
         "[18]–[23] upholds three-tier rings for proprietary algorithms; see "
         "also <i>TQ Delta v Zyxel</i> [2018] EWHC 1515 (Ch) (external-eyes-only "
         "is exceptional) and <i>Infederation Ltd v Google LLC</i> [2020] EWHC "
         "657 (Ch) at [27]–[42] (Roth J) on the principles applicable to "
         "confidentiality rings."),
        ("9", "<i>Wisniewski v Central Manchester Health Authority</i> "
         "[1998] EWCA Civ 596; [1998] PIQR P324 (Brooke LJ at p340) — the "
         "foundational principles for adverse inferences from absent witnesses. "
         "The doctrinal extension to absent documents was articulated in "
         "<i>Wetton v Ahmed</i> [2011] EWCA Civ 610 (Arden LJ at [14]); see "
         "also <i>Earles v Barclays Bank Plc</i> [2009] EWHC 2500 (Mercantile) "
         "(electronic records; preservation duty engages once proceedings are "
         "contemplated). The inference is discretionary, not mandatory: see "
         "<i>Magdeev v Tsvetkov</i> [2020] EWHC 887 (Comm) (Cockerill J) for "
         "the modern restatement of the structured test."),
    ]
    for n, text in notes:
        story.append(Paragraph(f"<b>{n}.</b> &nbsp; {text}", s_footnote))

    # ── COMPANION SOFTWARE ──────────────────────────────────────────────
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.4, color=RULE_SOFT,
                            spaceBefore=2, spaceAfter=6))
    story.append(Paragraph(
        "<b>Companion software:</b> <i>Libra Contract Guardian</i> v1.1 (2026) "
        "operationalises the PRPP framework as a Streamlit demonstrator, "
        "with three engines (PRPP, TDM, Playbook) running against a curated "
        "UK/EU IP-AI knowledge base. The Playbook engine implements TF-IDF "
        "vector-space cosine similarity against gold-standard contract corpora; "
        "verification harness in <i>test_playbook.py</i>. Source available on "
        "request.",
        s_footnote
    ))

    story.append(Paragraph(
        "<b>Author contact:</b> R.A. Aswin Krishna · "
        "aswinkrishna2277@gmail.com · "
        "Incoming LLM (Intellectual Property Law), Queen's University Belfast.",
        s_footnote
    ))

    doc.build(story)
    return out_path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/libra/PRPP_White_Paper.pdf"
    path = build_paper(out)
    print(f"Generated: {path}")
