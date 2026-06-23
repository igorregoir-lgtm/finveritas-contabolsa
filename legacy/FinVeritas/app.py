"""
FinVeritas — Clara Contábil (Padrão B3)
Real modules demo: Journal + RatioEngine + Guardrails + FiscalIntegrator + Bank Export
"""

import streamlit as st
from decimal import Decimal
from datetime import datetime
import json

from src.application.use_cases import FinVeritasService
from src.infrastructure.fraud_log import InMemoryFraudLog  # for type hints only

st.set_page_config(page_title="FinVeritas • Clara Contábil", layout="wide")

st.title("🏦 FinVeritas • Clara Contábil • Padrão B3")
st.caption("Módulos reais • Anti-Fraude Ironclad • ISO 25010 • Rastreabilidade total")

# Singleton service in session
if "service" not in st.session_state:
    st.session_state.service = FinVeritasService()
    # Seed initial demo data on first load
    svc = st.session_state.service
    journal = svc.get_journal()
    if journal.entry_count == 0:
        svc.post_manual_entry("Aporte inicial de sócios", "1.1.01", "3.1.01", Decimal("250000"))

service: FinVeritasService = st.session_state.service

# ====================== TOP METRICS ======================
col1, col2, col3, col4 = st.columns(4)

journal = service.get_journal()
solvency = service.calculate_solvency()

with col1:
    st.metric("Lançamentos no Diário", journal.entry_count)
with col2:
    st.metric("Qualidade de Crédito", f"{solvency.credit_score}/100", 
              "↑ Excelente" if solvency.credit_score >= 85 else "Atenção")
with col3:
    blocked = len(service.get_blocked_attempts())
    st.metric("Tentativas de Fraude Bloqueadas", blocked, delta_color="inverse")
with col4:
    st.metric("Total Movimentado (demo)", f"R$ {float(sum(e.total for e in journal.get_entries())):,.2f}")

st.divider()

# ====================== SOLVENCY CARD ======================
st.subheader("📊 Card de Solvência (SolvencyCard)")

with st.container(border=True):
    st.markdown(f"**Score:** {solvency.credit_score}/100  —  **Recomendação:** {solvency.recommendation}")
    
    if solvency.flags:
        for flag in solvency.flags:
            st.warning(f"⚠️ {flag}")
    else:
        st.success("Nenhum alerta de risco identificado.")

    ratio_cols = st.columns(len(solvency.ratios) or 1)
    for i, ratio in enumerate(solvency.ratios):
        with ratio_cols[i]:
            color = "normal" if ratio.status == "good" else ("inverse" if ratio.status == "warning" else "normal")
            st.metric(ratio.name, f"{ratio.value}", delta=ratio.status.upper())

st.divider()

# ====================== JOURNAL ======================
st.subheader("📒 Diário (Journal) — Lançamentos de Partida Dobrada")

with st.expander("Lançar manualmente (demonstração)"):
    with st.form("manual_entry"):
        desc = st.text_input("Descrição", value="Pagamento de fornecedor")
        col_d, col_c = st.columns(2)
        with col_d:
            debit = st.selectbox("Conta Débito", ["1.1.01", "2.1.01", "4.1.01"])
        with col_c:
            credit = st.selectbox("Conta Crédito", ["3.1.01", "1.1.01"])
        amount = st.number_input("Valor (R$)", min_value=100.0, value=8500.0, step=100.0)
        
        submitted = st.form_submit_button("Lançar no Diário")
        if submitted:
            try:
                entry = service.post_manual_entry(desc, debit, credit, Decimal(str(amount)))
                st.success(f"Lançamento {entry.id[:8]} registrado com sucesso.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

# Show recent entries
entries = journal.get_entries()
if entries:
    for e in reversed(entries[-6:]):
        with st.container(border=True):
            st.write(f"**{e.timestamp.strftime('%Y-%m-%d %H:%M')}** — {e.description}  |  Total: R$ {e.total:,.2f}")
            for line in e.lines:
                st.text(f"   {line.account.code} {line.account.name:20}  D {line.debit:>12}   C {line.credit:>12}")
else:
    st.info("Nenhum lançamento ainda.")

st.divider()

# ====================== FISCAL IMPORT ======================
st.subheader("📥 Importar Pix + NF-e (FiscalIntegrator + Guardrails)")

with st.form("import_fiscal"):
    st.caption("Tente com e sem assinatura digital para testar o guardrail antifraude.")
    pix_txid = st.text_input("Pix TXID", value="PIX9876543210")
    pix_amount = st.number_input("Valor Pix (R$)", value=45230.75)
    has_sig = st.checkbox("Documento com assinatura digital", value=True)

    nfe_chave = st.text_input("Chave NF-e (opcional)", value="35250600000000000000550010000000011234567890")

    import_submitted = st.form_submit_button("Importar e Lançar no Diário")
    if import_submitted:
        pix_data = {
            "txid": pix_txid,
            "amount": pix_amount,
            "payer": "12345678000190",
            "payee": "98765432000100",
            "timestamp": datetime.utcnow().isoformat(),
            "has_digital_signature": has_sig,
            "description": "Recebimento de cliente",
        }
        nfe_data = None
        if nfe_chave:
            nfe_data = {
                "chave_acesso": nfe_chave,
                "numero": "000000001",
                "emitente": "12345678000190",
                "destinatario": "98765432000100",
                "valor_total": pix_amount,
                "data_emissao": datetime.utcnow().isoformat(),
                "has_digital_signature": has_sig,
            }
        try:
            rec, jentry = service.import_fiscal(pix_data, nfe_data)
            st.success(f"Importação validada. Reconciliado: R$ {rec.reconciled_amount}. Lançamento gerado: {jentry.id[:8] if jentry else 'N/A'}")
            if rec.warnings:
                for w in rec.warnings:
                    st.warning(w)
            st.rerun()
        except Exception as ex:
            st.error(f"Bloqueado / erro: {ex}")

st.divider()

# ====================== BANK EXPORT ======================
st.subheader("📤 Exportar para Banco (BankExporter + Hash + Assinatura)")

if st.button("Gerar Pacote de Exportação (PDF + Assinatura)"):
    try:
        pkg = service.export_to_bank(reference="DEMO-2026-06-19")
        st.success(f"Pacote gerado: {pkg.id}")
        st.json({
            "id": pkg.id,
            "total": str(pkg.total_amount),
            "entries": pkg.entry_count,
            "content_hash": pkg.content_hash,
            "signature": pkg.signature[:20] + "...",
            "verified": service.verify_export(pkg),
        })
        with st.expander("Manifesto completo"):
            st.code(json.dumps(pkg.manifest, indent=2, ensure_ascii=False), language="json")
    except Exception as e:
        st.error(str(e))

st.divider()

# ====================== FRAUD LOG ======================
st.subheader("🔒 Log de Guardrails (Anti-Fraude)")

attempts = service.get_fraud_attempts()
if attempts:
    for a in reversed(attempts[-8:]):
        icon = "🚫" if a.blocked else "✅"
        st.text(f"{icon} {a.timestamp.strftime('%H:%M:%S')} | {a.action} | {a.amount} | {a.reason} | blocked={a.blocked}")
else:
    st.caption("Nenhuma tentativa registrada ainda.")

st.divider()
st.caption("Módulos reais implementados: Journal • RatioEngine • AntiFraudPolicy • FiscalIntegrator • BankExporter • UseCases")
st.caption("Todo caminho sensível passa pelo guardrail. Lançamentos são imutáveis. Hash + assinatura verificáveis.")
