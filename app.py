"""
FinVeritas Contabolsa - Beautiful, Intuitive Dashboard
Giant Solvency Card + Full Indicators + Ironclad Anti-Fraud + Export
"""

import streamlit as st
from decimal import Decimal
import json

from src.application.finveritas_service import FinVeritasService
from src.domain.journal import JournalLine

st.set_page_config(page_title="FinVeritas • Contabolsa", layout="wide", page_icon="🏦")

# Custom CSS for giant card
st.markdown("""
<style>
.giant-card {
    padding: 30px;
    border-radius: 20px;
    text-align: center;
    margin: 20px 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}
.GREEN { background: linear-gradient(135deg, #22c55e, #16a34a); color: white; }
.YELLOW { background: linear-gradient(135deg, #eab308, #ca8a04); color: black; }
.RED { background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; }
.ratio-good { color: #22c55e; font-weight: bold; }
.ratio-warning { color: #eab308; font-weight: bold; }
.ratio-danger { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🏦 FinVeritas Contabolsa")
st.caption("Transforme qualquer empresa em padrão B3 • Análise de Crédito & Solvência para Bancos")

if "service" not in st.session_state:
    st.session_state.service = FinVeritasService()

service = st.session_state.service

# ===================== GIANT SOLVENCY CARD =====================
st.header("📊 Card Gigante de Solvência & Qualidade de Crédito")

try:
    card = service.calculate_solvency()
except Exception as e:
    st.error(f"Erro ao calcular: {e}")
    card = None

if card:
    color_class = card.overall_status
    st.markdown(f"""
    <div class="giant-card {color_class}">
        <h1 style="font-size: 72px; margin:0;">{card.credit_score}</h1>
        <h2 style="margin:0;">SCORE DE QUALIDADE DE CRÉDITO</h2>
        <h3 style="margin-top:10px;">{card.overall_status}</h3>
        <p style="margin-top:15px; font-size:18px;">{card.traceability_note}</p>
    </div>
    """, unsafe_allow_html=True)

    if card.flags:
        for f in card.flags:
            st.warning(f"⚠️ {f}")

# ===================== KEY INDICATORS =====================
st.subheader("Indicadores Principais (Liquidez • Solvência • Rentabilidade)")

if card:
    cols = st.columns(4)
    for i, ratio in enumerate(card.ratios[:8]):  # top 8
        col = cols[i % 4]
        css_class = f"ratio-{ratio.status}"
        with col:
            st.markdown(f"""
            <div style="padding:12px; border:1px solid #ddd; border-radius:12px; margin-bottom:10px;">
                <div style="font-size:13px; color:#666;">{ratio.name}</div>
                <div style="font-size:28px; font-weight:700;" class="{css_class}">{ratio.value}</div>
                <div style="font-size:12px;">{ratio.explanation[:90]}...</div>
            </div>
            """, unsafe_allow_html=True)

# ===================== JOURNAL & IMPORT =====================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📥 Importar Pix + NF-e (Fiscal)")
    with st.form("fiscal_import"):
        txid = st.text_input("Pix TXID", "PIX-20250619-8821")
        amount = st.number_input("Valor (R$)", value=45230.5, step=100.0)
        has_sig = st.checkbox("Possui assinatura digital válida", value=True)
        submitted = st.form_submit_button("Importar e Lançar no Diário")
        if submitted:
            try:
                pix = {"txid": txid, "amount": amount, "has_digital_signature": has_sig}
                result = service.import_fiscal(pix, actor="analista")
                st.success(f"Importado com sucesso! Lançamento gerado. Valor: R$ {amount:,.2f}")
                st.rerun()
            except Exception as ex:
                st.error(str(ex))

with col2:
    st.subheader("📒 Lançar no Diário (Journal)")
    with st.form("journal"):
        desc = st.text_input("Descrição", "Recebimento de cliente")
        amount = st.number_input("Valor (R$)", value=15000.0)
        submitted = st.form_submit_button("Lançar Partida Dobrada")
        if submitted:
            lines = [
                JournalLine("1.1.01 - Caixa/Bancos", debit=Decimal(str(amount))),
                JournalLine("3.1.01 - Receita", credit=Decimal(str(amount))),
            ]
            try:
                ev = service.post_journal_entry(desc, lines)
                st.success(f"Lançamento {ev.id[:8]} registrado. Hash: {ev.current_hash[:16]}...")
                st.rerun()
            except Exception as ex:
                st.error(str(ex))

# ===================== EXPORT + FRAUD =====================
st.divider()

colA, colB = st.columns(2)
with colA:
    if st.button("📤 EXPORTAR PARA BANCO (PDF + JSON Assinado)", type="primary"):
        try:
            pkg = service.export_to_bank()
            st.success(f"Pacote gerado: {pkg['id']}")
            st.json({
                "hash": pkg["content_hash"][:32] + "...",
                "signature": pkg["signature"],
                "verified": pkg["verified"],
                "score": pkg["payload_preview"]
            })
            st.download_button("Baixar manifesto JSON", data=json.dumps(pkg, indent=2, default=str), file_name=f"{pkg['id']}.json")
        except Exception as e:
            st.error(str(e))

with colB:
    st.subheader("🔒 Teste Anti-Fraude Ironclad")
    if st.button("Simular importação de alto valor SEM assinatura"):
        dec = service.force_fraud_test(Decimal("125000"), has_sig=False)
        st.error(f"Decisão: {dec.value} — Bloqueado conforme política")

# ===================== AUDIT LOG =====================
with st.expander("📜 Log Anti-Fraude (Eterno)"):
    attempts = service.get_fraud_log()
    if attempts:
        for a in reversed(attempts[-10:]):
            st.text(f"{a.timestamp[:19]} | {a.action} | {a.decision} | {a.reason}")
    else:
        st.caption("Nenhuma tentativa registrada ainda.")

st.caption("FinVeritas Contabolsa • ISO 25010 compliant • Hash Chain + Guardrails • SDD")
