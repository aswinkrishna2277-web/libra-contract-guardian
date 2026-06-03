"""
Executive Brief — one-page PDF generator.

This is the document that arrives in a partner's inbox before they
click any links. It must stand alone, look professional, and convey
the legal substance of the project in under 60 seconds of reading.

Layout: A4, 2-column for the body, with a strong masthead.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, KeepInFrame
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ── Colours (matching the editorial landing-page palette) ─────────────────
INK         = colors.HexColor("#1a1814")
INK_SOFT    = colors.HexColor("#3d3830")
INK_MUTE    = colors.HexColor("#6b6354")
ACCENT      = colors.HexColor("#8b1a1a")
GOLD        = colors.HexColor("#a88533")
RULE_SOFT   = colors.HexColor("#c9bfa8")
PAPER       = colors.HexColor("#f4ede0")


def build_brief(out_path: str = "Libra_Executive_Brief.pdf"):
    # ── Page geometry ────────────────────────────────────────────────────
    page_w, page_h = A4
    margin = 18 * mm
    gutter = 6 * mm
    col_w = (page_w - 2 * margin - gutter) / 2

    # Top masthead frame (full-width)
    head_frame = Frame(
        margin, page_h - margin - 42*mm,
        page_w - 2*margin, 42*mm,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0
    )
    # Two-column body frames
    body_top = page_h - margin - 42*mm - 4*mm
    body_height = body_top - margin - 22*mm  # leave room for footer
    left_col = Frame(
        margin, margin + 22*mm, col_w, body_height,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0
    )
    right_col = Frame(
        margin + col_w + gutter, margin + 22*mm, col_w, body_height,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0
    )
    # Footer frame (full-width)
    footer_frame = Frame(
        margin, margin, page_w - 2*margin, 18*mm,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0
    )

    def on_page(canvas, doc):
        # subtle paper tone (very light)
        canvas.setFillColor(PAPER)
        canvas.rect(0, 0, page_w, page_h, stroke=0, fill=1)

        # Top accent rule
        canvas.setStrokeColor(INK)
        canvas.setLineWidth(0.6)
        canvas.line(margin, page_h - margin, page_w - margin, page_h - margin)

        # Masthead label (top corners)
        canvas.setFont("Times-Italic", 9)
        canvas.setFillColor(INK_MUTE)
        canvas.drawString(margin, page_h - margin + 2*mm, "R.A. Aswin Krishna · Research")
        canvas.drawRightString(page_w - margin, page_h - margin + 2*mm,
                               "EXECUTIVE BRIEF · v1.1 · 2026")

        # Bottom rule above footer
        canvas.line(margin, margin + 20*mm, page_w - margin, margin + 20*mm)

        # Page number / footer text drawn directly by canvas
        canvas.setFont("Times-Italic", 8)
        canvas.setFillColor(INK_MUTE)

    doc = BaseDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=margin,
        title="Libra — Executive Brief",
        author="R.A. Aswin Krishna",
        subject="Post-Report Provenance Procedure (PRPP) — research demonstrator",
    )
    doc.addPageTemplates([
        PageTemplate(id="brief",
                     frames=[head_frame, left_col, right_col, footer_frame],
                     onPage=on_page),
    ])

    # ── Styles ───────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    s_volume = ParagraphStyle(
        "volume", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=8.4, leading=10,
        textColor=ACCENT, spaceAfter=2,
        alignment=TA_LEFT,
        # we'll set tracking via a hack — uppercase+spacing in markup
    )
    s_title = ParagraphStyle(
        "title", parent=styles["Title"],
        fontName="Times-Bold", fontSize=34, leading=36,
        textColor=INK, spaceAfter=4, alignment=TA_LEFT,
    )
    s_deck = ParagraphStyle(
        "deck", parent=styles["Italic"],
        fontName="Times-Italic", fontSize=12.5, leading=16.2,
        textColor=INK_SOFT, spaceAfter=2, alignment=TA_LEFT,
    )
    s_byline = ParagraphStyle(
        "byline", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=8.5, leading=10,
        textColor=INK_MUTE, alignment=TA_LEFT,
    )
    s_section = ParagraphStyle(
        "section", parent=styles["Heading2"],
        fontName="Times-Bold", fontSize=10.5, leading=12,
        textColor=ACCENT, spaceBefore=6, spaceAfter=4, alignment=TA_LEFT,
    )
    s_body = ParagraphStyle(
        "body", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=9.4, leading=12.6,
        textColor=INK_SOFT, spaceAfter=5, alignment=TA_JUSTIFY,
    )
    s_body_lead = ParagraphStyle(
        "body_lead", parent=s_body,
        fontName="Times-Roman", fontSize=9.6, leading=13.2,
        textColor=INK,
    )
    s_cite = ParagraphStyle(
        "cite", parent=styles["Italic"],
        fontName="Times-Italic", fontSize=8.4, leading=11,
        textColor=INK_MUTE, alignment=TA_LEFT, spaceAfter=4,
    )
    s_pull = ParagraphStyle(
        "pull", parent=styles["Italic"],
        fontName="Times-Italic", fontSize=11, leading=14.5,
        textColor=ACCENT, alignment=TA_LEFT, spaceBefore=4, spaceAfter=4,
        leftIndent=8, borderColor=ACCENT, borderWidth=0,
    )
    s_footer = ParagraphStyle(
        "footer", parent=styles["Normal"],
        fontName="Times-Italic", fontSize=8, leading=10.5,
        textColor=INK_MUTE, alignment=TA_LEFT,
    )

    # ── Build the story ──────────────────────────────────────────────────
    story = []

    # ── HEADER (full-width frame) ────────────────────────────────────────
    story.append(Paragraph(
        '<font color="#8b1a1a">VOL. I &nbsp;&middot;&nbsp; A RESEARCH DELIVERABLE</font>',
        s_volume
    ))
    story.append(Spacer(1, 2))

    title_para = Paragraph(
        '<font color="#1a1814">Libra<font color="#8b1a1a">.</font></font>',
        s_title
    )
    story.append(title_para)

    story.append(Paragraph(
        'A research demonstrator for the <i>Post-Report Provenance Procedure</i> — '
        'a three-stage civil-procedure framework for AI-copyright disclosure under '
        'PD 57AD, England &amp; Wales.',
        s_deck
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        '<b>R.A. ASWIN KRISHNA</b> &nbsp;&middot;&nbsp; '
        'IP-AI Practitioner &nbsp;&middot;&nbsp; '
        'Companion to manuscript under journal review, 2026',
        s_byline
    ))
    story.append(HRFlowable(width="100%", thickness=0.7, color=INK,
                            spaceBefore=8, spaceAfter=0, hAlign='LEFT'))

    # FrameBreak — move to left column
    from reportlab.platypus import FrameBreak
    story.append(FrameBreak())

    # ── LEFT COLUMN ──────────────────────────────────────────────────────
    story.append(Paragraph("§ I &nbsp;&middot;&nbsp; THE PROBLEM", s_section))

    story.append(Paragraph(
        "The UK Government's <i>March 2026 Report on Copyright and Artificial "
        "Intelligence</i> identified an evidentiary asymmetry at the heart of "
        "AI-copyright litigation: claimants cannot inspect training corpora, "
        "while EU AI Act Art.53 disclosures are aggregated to a level that does "
        "not establish causal nexus for individual works.",
        s_body_lead
    ))

    story.append(Paragraph(
        "<i>Getty v Stability AI</i> [2025] EWHC 2863 (Ch) confirmed the limits of "
        "the secondary-infringement route in the UK. The substantive law has not "
        "moved; the procedural toolkit has not been adapted to the asymmetry. "
        "PRPP responds to this gap.",
        s_body
    ))

    story.append(Paragraph("§ II &nbsp;&middot;&nbsp; THE FRAMEWORK", s_section))

    story.append(Paragraph(
        "<b>Stage 1 — Prima Facie Trigger.</b> Three evidentiary routes "
        "calibrated to the good-arguable-case threshold under CPR r.6.37: "
        "(a) hosted-repository evidence cross-referenced with Common Crawl / "
        "LAION-5B and the developer's model card; (b) circumstantial "
        "regurgitation per Ahmed et al. (2026) arXiv:2601.02671 (preprint); "
        "(c) Membership Inference Attack as CPR Pt 35 expert evidence.",
        s_body
    ))

    story.append(Paragraph(
        "<b>Stage 2 — Model C Extended Disclosure.</b> Under PD 57AD, narrow "
        "disclosure of cryptographic hash manifests (SHA-256) and deduplication "
        "logs, produced within a confidentiality ring. External-eyes-only per "
        "<i>IPCom v HTC</i> [2013] EWHC 2880 (Ch) at [360]–[377]; three-tier per "
        "<i>Mitsubishi v OnePlus</i> [2020] EWCA Civ 1562 at [18]–[23]; "
        "self-certified for SME defendants per the March 2026 Report.",
        s_body
    ))

    story.append(Paragraph(
        "<b>Stage 3 — Adverse Inference.</b> Where the developer fails to "
        "preserve or produce records without credible non-culpable explanation, "
        "the court may draw an adverse inference on the factual issue of "
        "ingestion: <i>Wisniewski</i> [1998] EWCA Civ 596; [1998] PIQR P324 "
        "(witnesses), extended to documents in <i>Wetton v Ahmed</i> [2011] "
        "EWCA Civ 610 [14], applied to electronic records in <i>Earles v "
        "Barclays</i> [2009] EWHC 2500 (Mercantile). Distinguishes deliberate "
        "spoliation from routine data-minimisation.",
        s_body
    ))

    story.append(Paragraph(
        '<i>"PRPP is a procedural mechanism, not a substantive copyright doctrine. '
        'It does not change what counts as infringement. It changes how the factual '
        'element of ingestion can be established."</i>',
        s_pull
    ))

    # FrameBreak — move to right column
    story.append(FrameBreak())

    # ── RIGHT COLUMN ─────────────────────────────────────────────────────
    story.append(Paragraph("§ III &nbsp;&middot;&nbsp; THE SOFTWARE", s_section))

    story.append(Paragraph(
        "The demonstrator implements the framework against a curated UK/EU "
        "knowledge base. Three engines, each defensible:",
        s_body_lead
    ))

    story.append(Paragraph(
        "<b>PRPP Engine</b> &mdash; computes prima facie trigger strength across "
        "all three routes; assesses Model C feasibility under proportionality "
        "(PD 57AD para 6.4 + CPR r.1.1); applies the Wisniewski test with auto "
        "tier-downgrade for SME defendants.",
        s_body
    ))

    story.append(Paragraph(
        "<b>TDM Engine</b> &mdash; reviews commercial contracts for liability under "
        "CDPA 1988 s.29A, DSM Directive Arts 3-4, and EU AI Act Art.53. Risk "
        "scoring is mitigation-aware: TDM exclusions, provenance warranties, and "
        "audit rights <i>reduce</i> risk rather than being ignored.",
        s_body
    ))

    story.append(Paragraph(
        "<b>Playbook Engine (v1.1)</b> &mdash; real TF-IDF vector-space cosine "
        "similarity against the centroid of a firm's gold-standard corpus. "
        "Returns similarity score, closest-precedent identification, missing "
        "protective terms, and confidence band. Ships with a verification "
        "harness that proves correct ranking on synthetic IP/AI clauses.",
        s_body
    ))

    story.append(Paragraph("§ IV &nbsp;&middot;&nbsp; KNOWLEDGE BASE", s_section))

    story.append(Paragraph(
        "CDPA 1988 (ss.16, 17, 28A, 29A, 90, 96), UK GDPR &amp; DPA 2018, "
        "UCTA 1977, Trade Marks Act 1994, Arbitration Act 1996, EU AI Act "
        "Reg.2024/1689, DSM Directive 2019/790, the March 2026 UK Government "
        "Report, and PD 57AD.",
        s_body
    ))

    story.append(Paragraph(
        "Leading cases include <i>Getty v Stability AI</i> [2025] EWHC 2863 (Ch); "
        "<i>Designers Guild v Russell Williams</i>; <i>Wisniewski</i>; "
        "<i>Wetton v Ahmed</i>; <i>Earles v Barclays</i>; <i>IPCom v HTC</i>; "
        "<i>Mitsubishi v OnePlus</i>; <i>Infederation v Google</i>; "
        "<i>Kneschke v LAION</i> (OLG Hamburg, 10 Dec 2025); "
        "<i>Lidl v Tesco</i>; <i>Sky v SkyKick</i>.",
        s_body
    ))

    story.append(Paragraph("§ V &nbsp;&middot;&nbsp; LIMITATIONS", s_section))

    story.append(Paragraph(
        "PRPP is a proposal; no court has yet ordered Model C disclosure for AI "
        "training corpora in this form. The framework synthesises existing CPR / "
        "PD 57AD tools; its judicial reception is untested. The manuscript is "
        "under journal review. No solicitor-client relationship is created by "
        "use of this tool.",
        s_body
    ))

    # FrameBreak — into footer
    story.append(FrameBreak())

    # ── FOOTER ───────────────────────────────────────────────────────────
    footer_table = Table([[
        Paragraph(
            "<b>R.A. Aswin Krishna</b> &nbsp;&middot;&nbsp; aswinkrishna2277@gmail.com "
            "&nbsp;&middot;&nbsp; Incoming LLM (IP Law), Queen's University Belfast "
            "&nbsp;&middot;&nbsp; Prior practice: K&amp;S Partners; Saikrishna &amp; "
            "Associates; KRIA Law (India)",
            s_footer
        ),
        Paragraph(
            '<i>Cite: R.A. Aswin Krishna, Libra Contract Guardian v1.1: '
            'A research demonstrator for the Post-Report Provenance Procedure (2026).</i>',
            ParagraphStyle("cite_r", parent=s_footer, alignment=TA_RIGHT)
        ),
    ]], colWidths=[(page_w - 2*margin) * 0.55, (page_w - 2*margin) * 0.45])
    footer_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(footer_table)

    doc.build(story)
    return out_path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/libra/Libra_Executive_Brief.pdf"
    path = build_brief(out)
    print(f"Generated: {path}")
