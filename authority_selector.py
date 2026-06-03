"""
authority_selector.py — Deterministic authority selection.

═══════════════════════════════════════════════════════════════════════════════
PURPOSE
═══════════════════════════════════════════════════════════════════════════════

Given a factual situation (PRPP scenario, contract analysis, TDM assessment,
trademark search), this module DETERMINISTICALLY selects the relevant
authorities from authority_db.py.

The LLM never sees authorities that haven't been pre-selected by this module.
This is the architectural guarantee that prevents the model from "remembering"
cases that don't exist in our database.

═══════════════════════════════════════════════════════════════════════════════
HOW IT WORKS
═══════════════════════════════════════════════════════════════════════════════

Two-layer selection:

1. EXPLICIT TOPIC SELECTORS — pre-defined sets of authority IDs for each
   procedural or substantive context (e.g. "PRPP_STAGE_3" → adverse-inference
   authorities). These are curated by humans and immune to LLM drift.

2. KEYWORD-DRIVEN ENRICHMENT — given the user's input text, scan for keywords
   that indicate additional relevant topics, and add those authorities to the
   selection. Keyword lists are explicit Python data, not LLM judgements.

Both layers operate on Authority IDs only. The final output is a list of
verified Authority objects from authority_db.py.

═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import re
from typing import Optional

from authority_db import (
    AUTHORITIES,
    Authority,
    Kind,
    Jurisdiction,
    get,
    get_or_raise,
    find_by_topic,
)


# ════════════════════════════════════════════════════════════════════════════
# EXPLICIT SELECTORS BY ENGINE/CONTEXT
# ════════════════════════════════════════════════════════════════════════════
#
# These are the authorities each engine context ALWAYS considers. They are the
# "core" — anchored to your published framework and the leading authorities.
#
# Additional authorities can be added by keyword-driven enrichment below.
# ════════════════════════════════════════════════════════════════════════════

SELECTORS: dict[str, list[str]] = {

    # ─── PRPP ENGINE ───────────────────────────────────────────────────────

    "PRPP_STAGE_1_TRIGGER": [
        # Stage 1 — prima facie trigger under CPR r.6.37
        "RULE_CPR_6_37",
        "RULE_CPR_6_36",
        "RULE_CPR_PT_35",          # expert evidence (MIA, prompting tests)
        "STATUTE_CDPA_S16",        # primary infringement basis
        "REG_EU_AI_ACT_ART_53",    # training-data summary (Art 53(1)(d))
        "CASE_BROWNLIE_2017",
        "CASE_GETTY_V_STABILITY_2025",
        "CASE_KNESCHKE_V_LAION_2025",
        "ACADEMIC_KRISHNA_PRPP_2026",
    ],

    "PRPP_STAGE_2_DISCLOSURE": [
        # Stage 2 — Model C Extended Disclosure
        "RULE_PD_57AD",
        "RULE_PD_57AD_MODEL_C",
        "RULE_CPR_31_22",
        "RULE_CPR_1_1",
        "STATUTE_CDPA_S16",        # substantive cause-of-action backdrop
        "CASE_IPCOM_V_HTC_2013",
        "CASE_MITSUBISHI_V_ONEPLUS_2020",
        "CASE_INFEDERATION_V_GOOGLE_2020",
        "CASE_DESIGNERS_GUILD_2000",  # substantial-part test
        "ACADEMIC_KRISHNA_PRPP_2026",
    ],

    "PRPP_STAGE_3_INFERENCE": [
        # Stage 3 — adverse inference
        "CASE_WISNIEWSKI_1998",
        "CASE_WETTON_V_AHMED_2011",
        "CASE_EARLES_V_BARCLAYS_2009",
        "CASE_MAGDEEV_V_TSVETKOV_2020",
        "CASE_RE_B_2008",
        "ACADEMIC_KRISHNA_PRPP_2026",
    ],

    "PRPP_PRE_ACTION_ALT": [
        # Alternative considered and distinguished — pre-action disclosure
        "RULE_CPR_31_16",
        "CASE_BLACK_V_SUMITOMO_2001",
        "CASE_BERMUDA_V_KPMG_2001",
        "CASE_NORWICH_PHARMACAL_1974",
        "CASE_ASHWORTH_V_MGN_2002",
    ],

    "PRPP_CROSS_BORDER": [
        # Cross-border enforcement
        "RULE_CPR_6_36",
        "RULE_CPR_6_37",
        "CASE_BROWNLIE_2017",
        "CASE_SPILIADA_1987",
    ],

    "PRPP_IPEC_CAVEAT": [
        # IPEC limitation
        "RULE_CPR_46_21",
        "RULE_PD_57AD",
    ],

    # ─── CONTRACT ANALYSER ────────────────────────────────────────────────

    "CONTRACT_AI_TRAINING": [
        "STATUTE_CDPA_S29A",
        "STATUTE_CDPA_S16",
        "STATUTE_CDPA_S17",
        "STATUTE_CDPA_S28A",
        "DIR_DSM_ART_3",
        "DIR_DSM_ART_4",
        "REG_EU_AI_ACT_ART_53",
        "CASE_GETTY_V_STABILITY_2025",
        "CASE_KNESCHKE_V_LAION_2025",
        "REPORT_UK_MAR2026_COPYRIGHT_AI",
    ],

    "CONTRACT_TDM": [
        "STATUTE_CDPA_S29A",
        "DIR_DSM_ART_3",
        "DIR_DSM_ART_4",
        "CASE_KNESCHKE_V_LAION_2025",
        "REG_EU_AI_ACT_ART_53",
    ],

    "CONTRACT_ASSIGNMENT": [
        "STATUTE_CDPA_S90",
        "STATUTE_CDPA_S1",
        "STATUTE_CDPA_S11",
    ] if "STATUTE_CDPA_S11" in AUTHORITIES else [
        "STATUTE_CDPA_S90",
        "STATUTE_CDPA_S1",
    ],

    "CONTRACT_INFRINGEMENT_REMEDIES": [
        "STATUTE_CDPA_S96",
        "STATUTE_CDPA_S16",
        "CASE_DESIGNERS_GUILD_2000",
        "CASE_INFOPAQ_2009",
    ],

    "CONTRACT_TEMPORARY_COPIES": [
        "STATUTE_CDPA_S28A",
        "CASE_PRC_V_NLA_2013",
    ],

    # ─── TRADEMARK ENGINE ─────────────────────────────────────────────────

    "TRADEMARK_CONFUSION": [
        "STATUTE_TMA_S5_2_B",
        "STATUTE_TMA_S10_2",
    ],

    "TRADEMARK_DILUTION": [
        "STATUTE_TMA_S5_3",
        "STATUTE_TMA_S10_3",
        "CASE_LIDL_V_TESCO_2024",
    ],

    "TRADEMARK_DESCRIPTIVE": [
        "STATUTE_TMA_S3_1_C",
        "CASE_SKY_V_SKYKICK_2024",
    ],

    "TRADEMARK_BAD_FAITH": [
        "CASE_SKY_V_SKYKICK_2024",
    ],

    # ─── DISCLOSURE / CONFIDENTIALITY ─────────────────────────────────────

    "CONFIDENTIALITY_RING": [
        "CASE_IPCOM_V_HTC_2013",
        "CASE_MITSUBISHI_V_ONEPLUS_2020",
        "CASE_INFEDERATION_V_GOOGLE_2020",
        "RULE_CPR_31_22",
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# KEYWORD → TOPIC ENRICHMENT
# ════════════════════════════════════════════════════════════════════════════
#
# Each keyword (case-insensitive) maps to a list of authority IDs that become
# relevant when that keyword appears in user input. Keywords are matched as
# whole-word patterns.
#
# This is deterministic and auditable: no LLM judgement involved.
# ════════════════════════════════════════════════════════════════════════════

KEYWORD_ENRICHMENT: dict[str, list[str]] = {
    # AI training / model
    r"\btraining\s+data\b": ["STATUTE_CDPA_S29A", "CASE_GETTY_V_STABILITY_2025", "REG_EU_AI_ACT_ART_53"],
    r"\bmodel\s+training\b": ["STATUTE_CDPA_S29A", "CASE_GETTY_V_STABILITY_2025"],
    r"\bfoundation\s+model\b": ["REG_EU_AI_ACT_ART_53", "CASE_GETTY_V_STABILITY_2025"],
    r"\bgenerative\s+AI\b": ["CASE_GETTY_V_STABILITY_2025", "REG_EU_AI_ACT_ART_53"],
    r"\blarge\s+language\s+model\b": ["REG_EU_AI_ACT_ART_53"],

    # TDM
    r"\btext[- ]and[- ]data[- ]mining\b": ["STATUTE_CDPA_S29A", "DIR_DSM_ART_3", "DIR_DSM_ART_4"],
    r"\bTDM\b": ["STATUTE_CDPA_S29A", "DIR_DSM_ART_4"],
    r"\bscraping\b": ["STATUTE_CDPA_S29A", "DIR_DSM_ART_4", "CASE_KNESCHKE_V_LAION_2025"],
    r"\bweb[- ]crawl(?:ing)?\b": ["STATUTE_CDPA_S29A", "DIR_DSM_ART_4"],
    r"\bopt[- ]out\b": ["DIR_DSM_ART_4", "CASE_KNESCHKE_V_LAION_2025"],
    r"\bmachine[- ]readable\b": ["DIR_DSM_ART_4", "CASE_KNESCHKE_V_LAION_2025"],
    r"\bArticle\s+4\(3\)\b": ["DIR_DSM_ART_4", "CASE_KNESCHKE_V_LAION_2025"],

    # Disclosure / procedure
    r"\bdisclosure\b": ["RULE_PD_57AD", "RULE_PD_57AD_MODEL_C"],
    r"\bPD\s*57AD\b": ["RULE_PD_57AD", "RULE_PD_57AD_MODEL_C"],
    r"\bModel\s+C\b": ["RULE_PD_57AD_MODEL_C"],
    r"\bpre[- ]action\b": ["RULE_CPR_31_16", "CASE_BLACK_V_SUMITOMO_2001", "CASE_BERMUDA_V_KPMG_2001"],
    r"\bgood\s+arguable\s+case\b": ["RULE_CPR_6_37", "CASE_BROWNLIE_2017"],
    r"\bjurisdiction(?:al)?\b": ["RULE_CPR_6_36", "RULE_CPR_6_37", "CASE_BROWNLIE_2017", "CASE_SPILIADA_1987"],
    r"\bservice\s+out\b": ["RULE_CPR_6_36", "RULE_CPR_6_37"],

    # Adverse inference / spoliation
    r"\badverse\s+inference\b": ["CASE_WISNIEWSKI_1998", "CASE_WETTON_V_AHMED_2011", "CASE_EARLES_V_BARCLAYS_2009", "CASE_MAGDEEV_V_TSVETKOV_2020"],
    r"\bspoliation\b": ["CASE_WETTON_V_AHMED_2011", "CASE_EARLES_V_BARCLAYS_2009"],
    r"\bpreservation\b": ["CASE_EARLES_V_BARCLAYS_2009", "RULE_PD_57AD"],
    r"\bWisniewski\b": ["CASE_WISNIEWSKI_1998"],
    r"\bWetton\b": ["CASE_WETTON_V_AHMED_2011"],
    r"\bEarles\b": ["CASE_EARLES_V_BARCLAYS_2009"],

    # Confidentiality
    r"\bconfidentiality\s+ring\b": ["CASE_IPCOM_V_HTC_2013", "CASE_MITSUBISHI_V_ONEPLUS_2020", "RULE_CPR_31_22"],
    r"\bsource\s+code\b": ["CASE_IPCOM_V_HTC_2013"],
    r"\bexternal[- ]eyes[- ]only\b": ["CASE_IPCOM_V_HTC_2013", "CASE_MITSUBISHI_V_ONEPLUS_2020"],

    # Copyright substantive
    r"\bsubstantial\s+part\b": ["STATUTE_CDPA_S16", "CASE_DESIGNERS_GUILD_2000"],
    r"\boriginality\b": ["STATUTE_CDPA_S1", "CASE_INFOPAQ_2009"],
    r"\bcopying\b": ["STATUTE_CDPA_S17", "STATUTE_CDPA_S16"],
    r"\btransient\s+cop(?:y|ies)\b": ["STATUTE_CDPA_S28A", "CASE_PRC_V_NLA_2013"],

    # Trademark
    r"\bdilution\b": ["STATUTE_TMA_S5_3", "STATUTE_TMA_S10_3", "CASE_LIDL_V_TESCO_2024"],
    r"\bunfair\s+advantage\b": ["STATUTE_TMA_S10_3", "CASE_LIDL_V_TESCO_2024"],
    r"\bconfusion\b": ["STATUTE_TMA_S5_2_B", "STATUTE_TMA_S10_2"],
    r"\bdescriptive\b": ["STATUTE_TMA_S3_1_C", "CASE_SKY_V_SKYKICK_2024"],
    r"\bbad\s+faith\b": ["CASE_SKY_V_SKYKICK_2024"],
    r"\breputation\b": ["STATUTE_TMA_S5_3", "STATUTE_TMA_S10_3"],

    # Standard of proof
    r"\bbalance\s+of\s+probabilities\b": ["CASE_RE_B_2008"],
    r"\bstandard\s+of\s+proof\b": ["CASE_RE_B_2008"],

    # Norwich Pharmacal
    r"\bNorwich\s+Pharmacal\b": ["CASE_NORWICH_PHARMACAL_1974", "CASE_ASHWORTH_V_MGN_2002"],
    r"\bthird[- ]party\s+disclosure\b": ["CASE_NORWICH_PHARMACAL_1974"],

    # AI Act
    r"\bAI\s+Act\b": ["REG_EU_AI_ACT_ART_53"],
    r"\bArticle\s+53\b": ["REG_EU_AI_ACT_ART_53"],

    # March 2026 Report
    r"\bMarch\s+2026\s+Report\b": ["REPORT_UK_MAR2026_COPYRIGHT_AI"],
    r"\bGovernment\s+Report\b": ["REPORT_UK_MAR2026_COPYRIGHT_AI"],

    # IPEC
    r"\bIPEC\b": ["RULE_CPR_46_21"],
    r"\bIntellectual\s+Property\s+Enterprise\s+Court\b": ["RULE_CPR_46_21"],

    # Memorisation / regurgitation
    r"\bregurgitation\b": ["CASE_GETTY_V_STABILITY_2025", "RULE_CPR_PT_35"],
    r"\bmemorisation\b": ["CASE_GETTY_V_STABILITY_2025", "RULE_CPR_PT_35"],
    r"\bverbatim\b": ["CASE_GETTY_V_STABILITY_2025", "STATUTE_CDPA_S16"],
}


# ════════════════════════════════════════════════════════════════════════════
# CORE SELECTION FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def select_from_selectors(selector_keys: list[str]) -> list[Authority]:
    """
    Select authorities from one or more named selectors.

    Args:
        selector_keys: List of SELECTORS keys (e.g. ["PRPP_STAGE_1_TRIGGER"]).

    Returns:
        Deduplicated list of Authority objects, in selector order.

    Raises:
        KeyError if any selector_key or its IDs are unknown.
    """
    seen: set[str] = set()
    out: list[Authority] = []
    for key in selector_keys:
        if key not in SELECTORS:
            raise KeyError(
                f"Unknown selector '{key}'. Available: {sorted(SELECTORS.keys())}"
            )
        for aid in SELECTORS[key]:
            if aid in seen:
                continue
            seen.add(aid)
            out.append(get_or_raise(aid))
    return out


def enrich_by_keywords(text: str, base: Optional[list[Authority]] = None) -> list[Authority]:
    """
    Scan input text for keywords and return additional authorities.

    Args:
        text: User input (scenario description, contract text, query).
        base: Optional pre-selected authorities to extend (deduplicated).

    Returns:
        Combined list of authorities, deduplicated.
    """
    out: list[Authority] = list(base) if base else []
    seen: set[str] = {a.id for a in out}

    text_lower = text.lower()
    for pattern, aids in KEYWORD_ENRICHMENT.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            for aid in aids:
                if aid in seen:
                    continue
                auth = get(aid)
                if auth is None:
                    # Skip authorities that don't yet exist in the DB
                    continue
                seen.add(aid)
                out.append(auth)
    return out


def select_for_prpp(scenario_text: str, stage: Optional[int] = None) -> list[Authority]:
    """
    Convenience: select authorities for a PRPP scenario.

    Args:
        scenario_text: The user's scenario description.
        stage:         If 1/2/3, focus on that stage; otherwise include all.

    Returns:
        Deduplicated list of relevant authorities.
    """
    if stage == 1:
        selectors = ["PRPP_STAGE_1_TRIGGER", "PRPP_CROSS_BORDER"]
    elif stage == 2:
        selectors = ["PRPP_STAGE_2_DISCLOSURE", "CONFIDENTIALITY_RING"]
    elif stage == 3:
        selectors = ["PRPP_STAGE_3_INFERENCE"]
    else:
        selectors = [
            "PRPP_STAGE_1_TRIGGER",
            "PRPP_STAGE_2_DISCLOSURE",
            "PRPP_STAGE_3_INFERENCE",
            "PRPP_CROSS_BORDER",
            "PRPP_IPEC_CAVEAT",
        ]
    base = select_from_selectors(selectors)
    return enrich_by_keywords(scenario_text, base)


def select_for_contract(contract_text: str) -> list[Authority]:
    """
    Convenience: select authorities for contract analysis.

    Pure keyword-driven — no base selector — because contracts vary widely.
    """
    return enrich_by_keywords(contract_text, base=[])


def select_for_trademark(mark: str, context: str = "") -> list[Authority]:
    """
    Convenience: select authorities for trademark assessment.

    Always includes confusion and dilution baselines; enriches via context.
    """
    base = select_from_selectors(["TRADEMARK_CONFUSION", "TRADEMARK_DILUTION"])
    return enrich_by_keywords(context or mark, base)


# ════════════════════════════════════════════════════════════════════════════
# STRUCTURED EXPORT (for handing to the LLM as prompt context)
# ════════════════════════════════════════════════════════════════════════════

def authorities_to_prompt_block(authorities: list[Authority]) -> str:
    """
    Render a list of authorities as a structured prompt block for the LLM.

    CRITICAL: this format must NOT expose the internal authority IDs (like
    `CASE_LIDL_V_TESCO_2024`) because LLMs occasionally copy them verbatim
    into output text. The LLM should only see the human-facing forms:
    short_name (for in-text use) and full_citation (for first reference).
    """
    if not authorities:
        return "(no authorities selected for this query)"

    lines = [
        "AVAILABLE AUTHORITIES — you may cite ONLY these. Use the citation",
        "forms shown below. Do NOT invent, substitute, or rephrase citations.",
        "When introducing an authority, use the full citation; in subsequent",
        "references, the short form is acceptable.",
        "",
    ]
    for i, a in enumerate(authorities, start=1):
        lines.append(f"  [{i}] {a.short_name}")
        lines.append(f"      Full citation: {a.full_citation}")
        lines.append(f"      Short form (for subsequent refs): {a.short_name}")
        lines.append(f"      Summary: {a.summary}")
        if a.key_paragraphs:
            lines.append(f"      Verified paragraphs: {', '.join(a.key_paragraphs)}")
        if a.notes:
            lines.append(f"      Note: {a.notes}")
        lines.append("")
    return "\n".join(lines)


def authorities_to_json(authorities: list[Authority]) -> list[dict]:
    """JSON-serialisable representation for structured LLM prompts."""
    return [
        {
            "id": a.id,
            "citation": a.full_citation,
            "short_name": a.short_name,
            "summary": a.summary,
            "key_paragraphs": list(a.key_paragraphs),
            "notes": a.notes or None,
        }
        for a in authorities
    ]


# ════════════════════════════════════════════════════════════════════════════
# SELF-CHECK
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Libra Authority Selector — Self Check")
    print("─" * 70)

    # 1. Verify every selector resolves to known IDs
    print("\n[1] Selector integrity check")
    issues = 0
    for sel_key, ids in SELECTORS.items():
        for aid in ids:
            if aid not in AUTHORITIES:
                print(f"  MISSING: selector '{sel_key}' references unknown ID '{aid}'")
                issues += 1
    if issues == 0:
        print(f"  ✓ All {len(SELECTORS)} selectors reference valid authorities")

    # 2. Verify every keyword enrichment resolves
    print("\n[2] Keyword enrichment integrity check")
    issues = 0
    for pattern, ids in KEYWORD_ENRICHMENT.items():
        for aid in ids:
            if aid not in AUTHORITIES:
                print(f"  MISSING: keyword '{pattern}' references unknown ID '{aid}'")
                issues += 1
    if issues == 0:
        print(f"  ✓ All {len(KEYWORD_ENRICHMENT)} keyword patterns reference valid authorities")

    # 3. PRPP scenario test (Strong Claimant style input)
    print("\n[3] PRPP scenario test — Strong Claimant")
    strong = (
        "The defendant operates a generative AI service trained on Common Crawl "
        "and LAION-5B. The claimant has hosted-repository evidence and "
        "circumstantial regurgitation. A pre-action preservation letter was sent. "
        "Defendant claims routine data minimisation. Jurisdictional gateway via "
        "CPR r.6.36."
    )
    auths = select_for_prpp(strong)
    print(f"  Selected {len(auths)} authorities:")
    for a in auths[:8]:
        print(f"    - {a.short_name}")
    if len(auths) > 8:
        print(f"    ... and {len(auths) - 8} more")

    # 4. Contract test — AI training agreement
    print("\n[4] Contract test — AI training agreement")
    contract = (
        "The Licensee may use the data for training generative AI models. "
        "No machine-readable opt-out applies."
    )
    auths = select_for_contract(contract)
    print(f"  Selected {len(auths)} authorities:")
    for a in auths:
        print(f"    - {a.short_name}")

    # 5. Trademark test
    print("\n[5] Trademark test — dilution claim")
    auths = select_for_trademark("BURRBERY", context="similarity to mark with reputation, unfair advantage")
    print(f"  Selected {len(auths)} authorities:")
    for a in auths:
        print(f"    - {a.short_name}")

    # 6. Prompt block render
    print("\n[6] Prompt block render (Stage 3 only)")
    auths = select_for_prpp("", stage=3)
    block = authorities_to_prompt_block(auths)
    print(block[:600] + "...")
