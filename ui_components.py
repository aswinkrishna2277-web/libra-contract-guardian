# ================================================================
#  LIBRA CONTRACT GUARDIAN v2.2 – UI Components Module
#  Extracted UI rendering functions from app.py
#  All functions reference shared constants via app-level import.
# ================================================================

import streamlit as st
import re

from constants import LEGAL_KB, RISK_CATEGORIES, DISCLAIMER, APP_TITLE, APP_SUBTITLE
from app import check_ollama_available, refresh_legal_database


# ── render_header ─────────────────────────────────────────────────────────────
def render_header():
    kb_statutes = len(LEGAL_KB)
    kb_sections = sum(len(v["sections"]) for v in LEGAL_KB.values())
    st.markdown(f"""
    <div class="app-header">
        <div class="app-header-icon">⚖️</div>
        <div>
            <h1>Libra Contract Guardian</h1>
            <p>AI Legal Intelligence System · UK / EU Law · Evidence-Backed Analysis</p>
        </div>
        <div class="app-header-badge">
            {kb_statutes} Statutes · {kb_sections} Provisions
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── render_disclaimer ─────────────────────────────────────────────────────────
def render_disclaimer():
        st.markdown(
        f'<div class="disclaimer-banner">⚠️ <strong>DISCLAIMER:</strong> {DISCLAIMER}</div>',
        unsafe_allow_html=True)


# ── render_risk_score ─────────────────────────────────────────────────────────
def render_risk_score(score: int, level: str):
    colors = {"Low": "#52c97a", "Medium": "#e8a838", "High": "#e05252", "Critical": "#cc0000"}
    color  = colors.get(level, "#e05252")
    st.markdown(f"""
    <div class="risk-score-ring">
        <div class="risk-number" style="color:{color};">{score}</div>
        <div style="font-size:.9rem;color:{color};font-weight:700;margin:.15rem 0;">{level} Risk</div>
        <div class="risk-label">Overall Score / 100</div>
    </div>
    """, unsafe_allow_html=True)


# ── render_compliance_strength ────────────────────────────────────────────────
def render_compliance_strength(score: int):
    color = "#52c97a" if score >= 70 else "#e8a838" if score >= 40 else "#e05252"
    st.markdown(f"""
    <div class="compliance-bar-wrap">
      <div class="compliance-bar-label">
        <span>Compliance Strength</span>
        <strong style="color:{color};">{score}/100</strong>
      </div>
      <div class="compliance-bar-track">
        <div class="compliance-bar-fill" style="width:{score}%;background:linear-gradient(90deg,{color}99,{color});"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── render_confidence_badge ───────────────────────────────────────────────────
def render_confidence_badge(confidence_score: int, reasoning: str = ""):
    if confidence_score >= 80:
        cls, label = "confidence-high",   "HIGH CONFIDENCE"
    elif confidence_score >= 55:
        cls, label = "confidence-medium", "MEDIUM CONFIDENCE"
    else:
        cls, label = "confidence-low",    "LOW CONFIDENCE"
    st.markdown(f'<div class="{cls} confidence-badge">🎯 {label} — {confidence_score}%</div>',
                unsafe_allow_html=True)
    if reasoning:
        st.caption(reasoning)


# ── render_risk_bars ──────────────────────────────────────────────────────────
def render_risk_bars(key_risks: dict):
    for key, score in key_risks.items():
        cat = RISK_CATEGORIES.get(key, {"label": key, "icon": "•", "color": "#888"})
        col = "#e05252" if score >= 70 else "#e8a838" if score >= 40 else "#52c97a"
        st.markdown(f"""
        <div style="margin-bottom:.85rem;">
          <div style="display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:.25rem;">
            <span>{cat["icon"]} {cat["label"]}</span>
            <span style="color:{col};font-weight:700;">{score}</span>
          </div>
          <div style="background:rgba(255,255,255,.07);border-radius:99px;height:8px;overflow:hidden;">
            <div style="height:100%;width:{score}%;background:linear-gradient(90deg,{cat['color']}99,{cat['color']});border-radius:99px;transition:width .6s;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── render_red_flags ──────────────────────────────────────────────────────────
def render_red_flags(flags: list):
    for f in flags:
        st.markdown(f'<div class="flag-chip">🚩 {f}</div>', unsafe_allow_html=True)


# ── render_statute_panel ──────────────────────────────────────────────────────
def render_statute_panel(statute_hits: list):
    if not statute_hits:
        st.caption("No statute cross-matches found for this contract content.")
        return
    for hit in statute_hits:
        url_html = (f'<a href="{hit["url"]}" target="_blank" style="color:#4da3ff;font-size:.72rem;">🔗 View Statute</a>'
                    if hit.get("url") else "")
        st.markdown(f"""
        <div class="statute-card">
            <div class="statute-name">✔ {hit.get('statute','')} — {hit.get('section','')}</div>
            <div class="statute-extract">"{hit.get('extract', hit.get('text',''))}"</div>
            <div class="statute-section" style="margin-top:.35rem;">📌 Relevance: {hit.get('reason','')}</div>
            {f'<div style="margin-top:.35rem;">{url_html}</div>' if url_html else ''}
        </div>
        """, unsafe_allow_html=True)


# ── render_clause_card ────────────────────────────────────────────────────────
def render_clause_card(clause: dict):
    level     = clause.get("risk_level", "Medium")
    cls       = {"Low": "risk-low", "Medium": "risk-medium", "High": "risk-high", "Critical": "risk-high"}.get(level, "risk-medium")
    cat       = RISK_CATEGORIES.get(clause.get("risk_category", ""), {"icon": "•", "label": clause.get("risk_category", "")})
    citations = clause.get("statute_citations", [])
    cit_html  = " ".join(f'<span class="source-chip">{c}</span>' for c in citations) if citations else ""
    excerpt   = clause.get("excerpt", "")
    is_protective = clause.get("is_protective_clause", False)
    prot_badge = (
        '<span style="background:rgba(82,201,122,.15);border:1px solid rgba(82,201,122,.3);'
        'color:#52c97a;border-radius:5px;padding:.15rem .45rem;font-size:.72rem;margin-left:.5rem;">✓ Protective</span>'
        if is_protective else ""
    )
    st.markdown(f"""
    <div class="clause-card {cls}">
      <div class="clause-header">{cat["icon"]} {cat["label"]} · {level} Risk ({clause.get("risk_score",0)}/100){prot_badge}</div>
      <div class="clause-text">"{excerpt[:500]}{'…' if len(excerpt) > 500 else ''}"</div>
      <div class="clause-analysis"><strong>Legal Analysis:</strong> {clause.get("analysis","")}</div>
      <div class="clause-analysis" style="margin-top:.45rem;border-color:rgba(224,82,82,.3);color:#ffb3b3;"><strong>Specific Concern:</strong> {clause.get("specific_concern","")}</div>
      {f'<div style="margin-top:.5rem;">{cit_html}</div>' if cit_html else ''}
    </div>
    """, unsafe_allow_html=True)


# ── render_legal_document ─────────────────────────────────────────────────────
def render_legal_document(title: str, draft_text: str):
    from app import render_numbered_draft
    txt  = render_numbered_draft(draft_text)
    html = f"<div class='legal-document'><h1>{title}</h1>"
    html += "<div class='legal-meta'>Prepared for review and customisation. UK / EU style drafting. Statute references included.</div>"
    for para in txt.split("\n"):
        p = para.strip()
        if not p:
            html += "<br>"
        elif re.match(r"^\d+(\.\d+)*\.\s", p):
            html += f"<p><strong>{p}</strong></p>"
        elif p.isupper() and len(p) < 80:
            html += f"<h2>{p}</h2>"
        else:
            html += f"<p>{p}</p>"
    html += """
    <div class="legal-signature">
      <div class="sig-box">Signed for and on behalf of Party A<br><br>Name: ____________________<br>Title: ____________________<br>Date: ____________________</div>
      <div class="sig-box">Signed for and on behalf of Party B<br><br>Name: ____________________<br>Title: ____________________<br>Date: ____________________</div>
    </div></div>"""
    st.markdown(html, unsafe_allow_html=True)


# ── render_prpp_checklist ─────────────────────────────────────────────────────
def render_prpp_checklist(checklist: list):
    for item in checklist:
        status = item.get("status", "fail")
        icon   = "✅" if status == "pass" else "⚠️" if status == "partial" else "❌"
        cls    = "pass" if status == "pass" else "fail"
        st.markdown(f"""
        <div class="prpp-check {cls}">
          <div class="prpp-check-icon">{icon}</div>
          <div>
            <strong>{item.get('item','')}</strong>
            <span style="color:var(--muted);font-size:.76rem;"> (weight: {item.get('weight',0)})</span><br>
            <span style="color:var(--muted);font-size:.79rem;">{item.get('detail','')}</span><br>
            <span style="color:#7ec8e3;font-size:.77rem;">📖 {item.get('statute','')}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── render_tdm_issues ─────────────────────────────────────────────────────────
def render_tdm_issues(tdm_issues: list):
    for issue in tdm_issues:
        sev   = issue.get("severity", "Medium")
        color = "#cc0000" if sev == "Critical" else "#e05252" if sev == "High" else "#e8a838" if sev == "Medium" else "#52c97a"
        st.markdown(f"""
        <div class="tdm-exposure">
          <div class="tdm-exposure-title">⚡ {issue.get('issue','')}
            <span style="color:{color};font-size:.76rem;margin-left:.5rem;">[{sev}]</span></div>
          <div class="tdm-exposure-body">{issue.get('detail','')}</div>
          <div style="margin-top:.35rem;">
            <span class="source-chip">{issue.get('statute','')}</span>
            <span style="color:var(--muted);font-size:.76rem;margin-left:.5rem;">Exposure: {issue.get('exposure_type','')}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── render_litigation_risks ───────────────────────────────────────────────────
def render_litigation_risks(litigation_risks: list):
    for lr in litigation_risks:
        lik   = lr.get("likelihood", "Medium")
        color = "#e05252" if lik == "High" else "#e8a838" if lik == "Medium" else "#52c97a"
        st.markdown(f"""
        <div class="statute-card" style="border-color:rgba(224,82,82,.25);">
          <div class="statute-name" style="color:{color};">⚖️ {lr.get('risk','')}</div>
          <div class="statute-section">Statute: {lr.get('statute','')} · Likelihood: {lik}</div>
          <div class="statute-extract">Remedy: {lr.get('remedy','')}</div>
        </div>
        """, unsafe_allow_html=True)


# ── render_legal_references_panel ────────────────────────────────────────────
def render_legal_references_panel(refs: list, title: str = "📚 Legal References Used"):
    if not refs:
        return
    with st.expander(title, expanded=False):
        cols = st.columns(2)
        for i, ref in enumerate(refs):
            stat = LEGAL_KB.get(ref)
            with cols[i % 2]:
                if stat:
                    st.markdown(f"""
                    <div class="db-status">
                      <div style="color:var(--gold);font-weight:700;font-size:.84rem;">📖 {ref}</div>
                      <a href="{stat['url']}" target="_blank" style="color:#4da3ff;font-size:.72rem;">🔗 View Statute</a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div class="db-status"><div style="color:var(--gold);font-size:.84rem;">📖 {ref}</div></div>',
                        unsafe_allow_html=True)


# ── render_score_comparison ───────────────────────────────────────────────────
def render_score_comparison(orig_risk: int, new_risk: int, orig_cs: int, new_cs: int):
    """Render the side-by-side score comparison panel."""
    risk_delta = orig_risk - new_risk   # positive = improvement
    cs_delta   = new_cs - orig_cs       # positive = improvement

    rc_orig = "#cc0000" if orig_risk >= 75 else "#e05252" if orig_risk >= 50 else "#e8a838" if orig_risk >= 25 else "#52c97a"
    rc_new  = "#cc0000" if new_risk  >= 75 else "#e05252" if new_risk  >= 50 else "#e8a838" if new_risk  >= 25 else "#52c97a"

    if risk_delta > 0:
        risk_delta_html = f'<span class="score-compare-delta delta-better">▼ {risk_delta} pts safer</span>'
    elif risk_delta < 0:
        risk_delta_html = f'<span class="score-compare-delta delta-worse">▲ {abs(risk_delta)} pts higher</span>'
    else:
        risk_delta_html = '<span class="score-compare-delta delta-same">Unchanged</span>'

    if cs_delta > 0:
        cs_delta_html = f'<span class="score-compare-delta delta-better">▲ +{cs_delta} pts</span>'
    elif cs_delta < 0:
        cs_delta_html = f'<span class="score-compare-delta delta-worse">▼ {abs(cs_delta)} pts</span>'
    else:
        cs_delta_html = '<span class="score-compare-delta delta-same">Unchanged</span>'

    st.markdown(f"""
    <div style="margin:.7rem 0;">
      <div style="font-family:'DM Serif Display',serif;color:var(--gold);font-size:1rem;margin-bottom:.6rem;">
        📊 Score Comparison: Original vs Safer Draft
      </div>
      <div class="score-compare">
        <div class="score-compare-col">
          <div class="score-compare-label">Original Risk Score</div>
          <div class="score-compare-num" style="color:{rc_orig};">{orig_risk}</div>
          {risk_delta_html}
        </div>
        <div class="score-compare-arrow">→</div>
        <div class="score-compare-col">
          <div class="score-compare-label">Safer Draft Risk Score</div>
          <div class="score-compare-num" style="color:{rc_new};">{new_risk}</div>
          <div style="font-size:.72rem;color:var(--muted);margin-top:.2rem;">After mitigation</div>
        </div>
      </div>
      <div class="score-compare" style="margin-top:.5rem;">
        <div class="score-compare-col">
          <div class="score-compare-label">Original Compliance Strength</div>
          <div class="score-compare-num" style="color:#8a9bb0;">{orig_cs}</div>
          {cs_delta_html}
        </div>
        <div class="score-compare-arrow">→</div>
        <div class="score-compare-col">
          <div class="score-compare-label">Safer Draft Compliance Strength</div>
          <div class="score-compare-num" style="color:#52c97a;">{new_cs}</div>
          <div style="font-size:.72rem;color:var(--muted);margin-top:.2rem;">Protective language detected</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── render_verification_banner ────────────────────────────────────────────────
def render_verification_banner(orig_risk: int, new_risk: int, orig_cs: int, new_cs: int):
    """Render the post-draft auto-verification banner."""
    risk_delta = orig_risk - new_risk
    cs_delta   = new_cs - orig_cs

    if risk_delta > 0 and cs_delta > 0:
        icon  = "✅"
        title = "Safer draft verified"
        msg   = f"Overall risk reduced by <strong>{risk_delta} points</strong> · Compliance strength increased by <strong>+{cs_delta} points</strong>"
        extra = "The safer draft contains more protective language and fewer unmitigated risk exposures than the original."
    elif risk_delta > 0:
        icon  = "✅"
        title = "Safer draft verified — risk reduced"
        msg   = f"Overall risk reduced by <strong>{risk_delta} points</strong> · Compliance strength: {new_cs}/100"
        extra = "Risk reduction confirmed. Consider adding more protective schedule references to further increase compliance strength."
    elif cs_delta > 0:
        icon  = "✅"
        title = "Safer draft — compliance strengthened"
        msg   = f"Compliance strength increased by <strong>+{cs_delta} points</strong> · Risk score: {new_risk}/100"
        extra = "Protective language detected in the draft. Risk score may reduce further on re-analysis with more context."
    else:
        icon  = "⚠️"
        title = "Draft generated — manual review recommended"
        msg   = f"Risk score: {new_risk}/100 · Compliance strength: {new_cs}/100"
        extra = "Scores similar to original. The AI may need more context about the contract type. Review the draft and add specific protective clauses as needed."

    st.markdown(f"""
    <div class="verify-banner">
      <div class="verify-banner-title">{icon} {title}</div>
      <div>{msg}</div>
      <div style="font-size:.8rem;color:#7ecfb3;margin-top:.35rem;">{extra}</div>
    </div>
    """, unsafe_allow_html=True)


# ── render_sidebar ────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:.8rem 0 .4rem;">
            <div style="font-size:2.6rem;filter:drop-shadow(0 0 12px rgba(201,168,76,.5));">⚖️</div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.15rem;color:var(--gold);">Contract Guardian</div>
            <div style="font-size:.68rem;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;">AI Legal Intelligence</div>
        </div>
        <hr style="border-color:var(--border);margin:.8rem 0;">
        """, unsafe_allow_html=True)

        # v2.0 — local-only. No backend selection.
        st.markdown("<p style='font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.4rem;'>Local LLM</p>", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:rgba(82,201,122,0.10);border:1px solid rgba(82,201,122,0.30);border-radius:6px;padding:.55rem .8rem;font-size:.77rem;color:#b3ffd4;margin:.4rem 0;">
        🔒 <strong>Local-only mode.</strong> All inference runs on this machine.
        </div>""", unsafe_allow_html=True)

        try:
            import local_llm as _local_llm
            status = _local_llm.check_status(st.session_state.get("local_model", "mistral:7b-instruct"))
            if status.available:
                st.success(f"✅ Ollama connected · {st.session_state.get('local_model', 'mistral:7b-instruct')}")
                if status.models_installed:
                    pick = st.selectbox(
                        "Active model",
                        status.models_installed,
                        index=(
                            status.models_installed.index(st.session_state.get("local_model", "mistral:7b-instruct"))
                            if st.session_state.get("local_model", "mistral:7b-instruct") in status.models_installed
                            else 0
                        ),
                    )
                    st.session_state.local_model = pick
            else:
                st.error(f"❌ Ollama not reachable: {status.error or 'unknown'}")
        except Exception as _e:
            st.error(f"local_llm module unavailable: {_e}")

        st.markdown("---")
        # Rest of the sidebar (Cache/Update DB) remains the same...

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Clear Cache", use_container_width=True):
                for k in [
                    "analysis_cache", "crosscheck_cache", "document_cache",
                    "analysis_result", "crosscheck_result", "safer_version",
                    "safer_version_analysis", "original_risk_score",
                    "original_compliance_strength",
                    "prpp_result", "tdm_result",
                ]:
                    if isinstance(st.session_state.get(k), dict):
                        st.session_state[k] = {}
                    else:
                        st.session_state[k] = None if k not in ("safer_version",) else ""
                st.success("Cache cleared.")
        with c2:
            if st.button("⬆️ Update DB", use_container_width=True):
                with st.spinner("Refreshing…"):
                    r = refresh_legal_database()
                st.success(f"Updated at {r['updated_at']}")

        if st.session_state.legal_reference_snapshot:
            with st.expander("🗄️ Legal Database Status", expanded=False):
                st.markdown(
                    f"<div style='font-size:.72rem;color:var(--muted);margin-bottom:.4rem;'>Last updated: {st.session_state.legal_reference_updated_at}</div>",
                    unsafe_allow_html=True)
                for item in st.session_state.legal_reference_snapshot:
                    icon = "✅" if item["status"] == "ok" else "❌"
                    cls  = "db-ok" if item["status"] == "ok" else "db-fail"
                    st.markdown(f"""
                    <div class="db-status-row">
                      <span class="{cls}">{icon}</span>
                      <span style="font-size:.77rem;">{item['title']}</span>
                    </div>""", unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='font-size:.74rem;color:var(--muted);margin-top:.5rem;'>Click <strong>Update DB</strong> to ping legal sources.</div>",
                unsafe_allow_html=True)

        with st.expander("📚 Legal Scope", expanded=False):
            st.markdown("""
            <div style="font-size:.76rem;color:var(--muted);line-height:1.75;">
            <strong style="color:var(--gold);">UK/EU Focus:</strong><br>
            • CDPA 1988 (s.29A TDM) &nbsp;• UK/EU GDPR / DPA 2018<br>
            • UCTA 1977 &nbsp;• CRA 2015 &nbsp;• Arbitration Act 1996<br>
            • UKIPO TDM Report 2026 &nbsp;• PD 57AD &nbsp;• ICO AI Guidance<br><br>
            <strong style="color:var(--gold);">Contract Types:</strong><br>
            Commercial · IP · SaaS · NDA · DPA · Tech Transfer · ADR
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-size:.69rem;color:var(--muted);margin-top:1rem;text-align:center;">
        Legal KB: {len(LEGAL_KB)} statutes embedded<br>
        {sum(len(v['sections']) for v in LEGAL_KB.values())} statutory provisions
        </div>""", unsafe_allow_html=True)