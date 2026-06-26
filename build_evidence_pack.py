"""Build the one-page evidence pack PDF for outreach."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Palette — restrained, legal-professional
INK = HexColor("#1a1a2e")
ACCENT = HexColor("#7a5c2e")   # muted gold/bronze
MUTED = HexColor("#555555")
RULE = HexColor("#c9b88a")

doc = SimpleDocTemplate(
    "/home/claude/libra/Evidence_Pack.pdf",
    pagesize=A4,
    topMargin=18 * mm,
    bottomMargin=16 * mm,
    leftMargin=22 * mm,
    rightMargin=22 * mm,
    title="AI-Copyright Litigation Procedure — Summary",
    author="R.A. Aswin Krishna",
    subject="PRPP framework and software",
)

styles = getSampleStyleSheet()

name_st = ParagraphStyle(
    "name", parent=styles["Title"], fontName="Times-Bold",
    fontSize=18, leading=21, textColor=INK, spaceAfter=2, alignment=TA_LEFT,
)
sub_st = ParagraphStyle(
    "sub", parent=styles["Normal"], fontName="Times-Italic",
    fontSize=10, leading=13, textColor=ACCENT, spaceAfter=2, alignment=TA_LEFT,
)
h_st = ParagraphStyle(
    "h", parent=styles["Heading2"], fontName="Times-Bold",
    fontSize=11.5, leading=14, textColor=ACCENT, spaceBefore=9, spaceAfter=3,
)
body_st = ParagraphStyle(
    "body", parent=styles["Normal"], fontName="Times-Roman",
    fontSize=9.6, leading=13, textColor=INK, spaceAfter=4, alignment=TA_LEFT,
)
bullet_st = ParagraphStyle(
    "bullet", parent=body_st, fontSize=9.6, leading=12.5, spaceAfter=3,
)
foot_st = ParagraphStyle(
    "foot", parent=styles["Normal"], fontName="Times-Italic",
    fontSize=8, leading=10, textColor=MUTED, spaceBefore=6,
)
contact_st = ParagraphStyle(
    "contact", parent=body_st, fontName="Times-Bold", fontSize=10, leading=13,
)

def rule():
    return HRFlowable(width="100%", thickness=0.8, color=RULE,
                      spaceBefore=4, spaceAfter=6)

story = []

story.append(Paragraph("AI-Copyright Litigation Procedure", name_st))
story.append(Paragraph(
    "R.A. Aswin Krishna &nbsp;·&nbsp; Forthcoming, <i>European Intellectual "
    "Property Review</i> (Thomson Reuters) &nbsp;·&nbsp; Incoming LLM in IP "
    "Law, Queen's University Belfast, September 2026", sub_st))
story.append(rule())

story.append(Paragraph("The problem", h_st))
story.append(Paragraph(
    "UK AI-copyright claims face a structural evidentiary asymmetry. A "
    "rights-holder who suspects their work was used to train a model cannot, "
    "at the outset, prove ingestion: the training data, the dataset "
    "composition, and the model's provenance all sit with the developer. "
    "Existing legal-AI tools summarise contracts and flag risk in general "
    "terms; they do not map a fact pattern onto the civil-procedure mechanics "
    "that decide whether such a claim can proceed.", body_st))

story.append(Paragraph("The research", h_st))
story.append(Paragraph(
    "My forthcoming article in the <i>European Intellectual Property Review</i> "
    "proposes the <b>Post-Report Provenance Procedure (PRPP)</b> — a "
    "civil-procedure framework for managing that asymmetry within the existing "
    "UK Civil Procedure Rules, requiring no legislative change. It operates "
    "across three stages: the prima facie trigger (good arguable case under "
    "CPR r.6.37); Model C request-led Extended Disclosure under Practice "
    "Direction 57AD, including the IPEC carve-out at paragraph 1.4; and the "
    "adverse-inference analysis under the <i>Wisniewski</i> line as refined in "
    "<i>Magdeev v Tsvetkov</i> [2020] EWHC 887 (Comm). The framework is "
    "anchored in current authority: the March 2026 UK Government Report on "
    "Copyright and AI, the <i>Kneschke v LAION</i> decision of the OLG Hamburg "
    "(December 2025), and the EU AI Act Article 53 training-data-summary "
    "template adopted in July 2025.", body_st))

story.append(Paragraph("The software", h_st))
story.append(Paragraph(
    "Alongside the research I have built its operational form: software that "
    "takes a UK AI-copyright fact pattern, maps it to the three PRPP stages, "
    "and produces a structured procedural assessment. Three design choices "
    "distinguish it from general-purpose legal-AI tools:", body_st))

bullets = [
    Paragraph(
        "<b>Citations are verified, not generated.</b> Every authority the "
        "system cites is drawn from a 50-entry database — UK and EU case law, "
        "statutes, civil procedure rules, directives, and policy instruments — "
        "each cross-checked against the official source (BAILII, "
        "legislation.gov.uk, EUR-Lex, CURIA). The model cannot invent or "
        "substitute citations; an output verifier rejects any citation that "
        "does not trace to the database, reducing citation-fabrication risk to "
        "a negligible level.", bullet_st),
    Paragraph(
        "<b>Scoring is deterministic.</b> The procedural scoring is computed "
        "in code from structured signals, not by the model. The model's role "
        "is limited to phrasing a result already determined and verified.", bullet_st),
    Paragraph(
        "<b>It runs entirely on the user's own machine.</b> No cloud, no "
        "third-party API, no client data leaving the device — the design "
        "choice that makes it deployable on confidential matters, not only on "
        "demonstrations.", bullet_st),
]
story.append(ListFlowable(
    [ListItem(b, leftIndent=6, value="–") for b in bullets],
    bulletType="bullet", start="–", leftIndent=10, bulletColor=ACCENT,
))

story.append(Paragraph("Status", h_st))
story.append(Paragraph(
    "The framework is accepted for publication (forthcoming, <i>European "
    "Intellectual Property Review</i>, Thomson Reuters). The "
    "software is operational, with the procedural engine, a text-and-data-"
    "mining contract analyser, and a trademark clearance module each covered "
    "by an automated test suite. It is a local-only application the author "
    "maintains for his own professional use, offered here as a demonstration "
    "of the research in operational form.", body_st))

story.append(rule())
story.append(Paragraph(
    "R.A. Aswin Krishna &nbsp;·&nbsp; aswinkrishna2277@gmail.com", contact_st))
story.append(Paragraph(
    "This summary describes original research and independent software. "
    "The software is a research demonstration and does not constitute legal "
    "advice.", foot_st))

doc.build(story)
print("PDF built successfully")
