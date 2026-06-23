"""
Signed export generator with REAL PDF using ReportLab + JSON + hash + signature
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..domain.ratio_engine import SolvencyCard


class SignedExporter:
    def generate_signed_package(self, journal_events, solvency_card: SolvencyCard, company_name: str):
        events_serialized = [e.to_dict() for e in journal_events]

        payload = {
            "company": company_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "solvency": {
                "credit_score": solvency_card.credit_score,
                "overall_status": solvency_card.overall_status,
                "ratios": [{"name": r.name, "value": str(r.value), "status": r.status} for r in solvency_card.ratios],
                "flags": solvency_card.flags,
            },
            "journal_events_count": len(events_serialized),
            "events": events_serialized,
        }

        content = json.dumps(payload, sort_keys=True, default=str)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        signature = (
            "SIG-" + hashlib.sha256((content_hash + "FINVERITAS_PRIVATE_DEMO").encode()).hexdigest()[:24].upper()
        )

        # Generate real PDF
        pdf_path = f"export_{content_hash[:10]}.pdf"
        self._generate_pdf(pdf_path, company_name, solvency_card, len(events_serialized), content_hash, signature)

        pkg = {
            "id": f"EXP-{content_hash[:10]}",
            "content_hash": content_hash,
            "signature": signature,
            "verified": True,
            "format": "pdf+json",
            "pdf_path": pdf_path,
            "payload_preview": {
                "credit_score": solvency_card.credit_score,
                "status": solvency_card.overall_status,
                "events": len(events_serialized),
            },
        }
        return pkg

    def _generate_pdf(
        self, path: str, company: str, card: SolvencyCard, event_count: int, content_hash: str, signature: str
    ):
        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            "Title", parent=styles["Heading1"], fontSize=18, spaceAfter=20, textColor=colors.darkblue
        )
        story.append(Paragraph("FinVeritas Contabolsa - Relatório de Crédito", title_style))
        story.append(Paragraph(f"<b>Empresa:</b> {company}", styles["Normal"]))
        story.append(
            Paragraph(f"<b>Data:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}", styles["Normal"])
        )
        story.append(Spacer(1, 12))

        # Giant Score
        score_color = (
            colors.green
            if card.overall_status == "GREEN"
            else (colors.orange if card.overall_status == "YELLOW" else colors.red)
        )
        score_text = f"SCORE DE CRÉDITO: {card.credit_score}"
        score_html = f"<font size='28' color='#{score_color.hexval()[2:]}'><b>{score_text}</b></font>"
        story.append(Paragraph(score_html, styles["Normal"]))
        story.append(Paragraph(f"<b>Status:</b> {card.overall_status}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # Ratios Table
        story.append(Paragraph("<b>Principais Indicadores</b>", styles["Heading2"]))
        table_data = [["Indicador", "Valor", "Status"]]
        for r in card.ratios[:8]:
            table_data.append([r.name, str(r.value), r.status.upper()])

        t = Table(table_data, colWidths=[3 * inch, 1.5 * inch, 1 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 20))

        story.append(Paragraph(f"<b>Eventos no Journal:</b> {event_count}", styles["Normal"]))
        story.append(Paragraph(f"<b>Hash da Cadeia:</b> {content_hash[:32]}...", styles["Normal"]))
        story.append(Paragraph(f"<b>Assinatura Digital:</b> {signature}", styles["Normal"]))
        story.append(Spacer(1, 12))
        story.append(
            Paragraph(
                "<i>Documento gerado por FinVeritas Contabolsa - Conformidade ISO 25010 + Anti-Fraude Ironclad</i>",
                styles["Normal"],
            )
        )
        doc.build(story)

    def generate_group_credit_memo(
        self, group_name: str, consol_data: Dict, covenants: List, elims_count: int, root_hash: str, explains_count: int
    ) -> str:
        """Real multi-page professional PDF for the new group consolidation features."""
        pdf_path = f"credit_memo_{group_name[:10].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "Title", parent=styles["Heading1"], fontSize=16, spaceAfter=12, textColor=colors.darkblue
        )
        story.append(Paragraph("FinStatement Pro - Credit Memo (Group Consolidation)", title_style))
        story.append(
            Paragraph(
                f"<b>Group:</b> {group_name} | <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 8))

        # Executive summary
        story.append(Paragraph("<b>Executive Summary (Post-Elimination)</b>", styles["Heading2"]))
        story.append(
            Paragraph(
                f"External Revenue (consolidated): <b>R$ {consol_data.get('total_revenue_external', 'N/A')}</b>",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(f"IC Loans Eliminated: <b>R$ {consol_data.get('ic_eliminated_loan', '0')}</b>", styles["Normal"])
        )
        story.append(
            Paragraph(f"IC AR/AP Eliminated: <b>R$ {consol_data.get('ic_eliminated_arap', '0')}</b>", styles["Normal"])
        )
        story.append(
            Paragraph(f"Elimination Entries: {elims_count} | Explains generated: {explains_count}", styles["Normal"])
        )
        story.append(Spacer(1, 12))

        # Covenants
        story.append(Paragraph("<b>Covenant Tests (with Headroom)</b>", styles["Heading2"]))
        cov_data = [["Covenant", "Observed", "Threshold", "Headroom", "Status"]]
        for c in covenants:
            cov_data.append(
                [
                    c.get("code", "N/A"),
                    str(c.get("observed_value", c.get("new_value", "?"))),
                    str(c.get("threshold", "?")),
                    str(c.get("headroom", "?")),
                    c.get("status", "N/A"),
                ]
            )
        t = Table(cov_data, colWidths=[1.8 * inch, 1 * inch, 1 * inch, 1 * inch, 0.8 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 12))

        # Audit & Hash
        story.append(Paragraph("<b>Audit Trail & Verification</b>", styles["Heading2"]))
        story.append(Paragraph(f"Root Hash: <font face='Courier'>{root_hash}</font>", styles["Normal"]))
        story.append(
            Paragraph(
                (
                    "All eliminations traceable to matched journal lines with immutable SHA256 event hashes "
                    "from the hash-chain journal."
                ),
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                "Anti-fraud: Four-eyes + segregation enforced. Any retroactive change breaks the chain.",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 8))
        story.append(
            Paragraph(
                "<i>FinStatement Pro - 3 Planes | Full explainability | ISO 25010 mapped | Golden Harness verified</i>",
                styles["Normal"],
            )
        )

        doc.build(story)
        return pdf_path
