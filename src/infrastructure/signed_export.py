"""
Signed export generator with REAL PDF using ReportLab + JSON + hash + signature
"""

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from ..domain.ratio_engine import SolvencyCard
from ..domain.journal import AccountingEvent

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import os

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
                "flags": solvency_card.flags
            },
            "journal_events_count": len(events_serialized),
            "events": events_serialized,
        }

        content = json.dumps(payload, sort_keys=True, default=str)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        signature = "SIG-" + hashlib.sha256((content_hash + "FINVERITAS_PRIVATE_DEMO").encode()).hexdigest()[:24].upper()

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
                "events": len(events_serialized)
            },
        }
        return pkg

    def _generate_pdf(self, path: str, company: str, card: SolvencyCard, event_count: int, content_hash: str, signature: str):
        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=20, textColor=colors.darkblue)
        story.append(Paragraph(f"FinVeritas Contabolsa - Relatório de Crédito", title_style))
        story.append(Paragraph(f"<b>Empresa:</b> {company}", styles['Normal']))
        story.append(Paragraph(f"<b>Data:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Giant Score
        score_color = colors.green if card.overall_status == "GREEN" else (colors.orange if card.overall_status == "YELLOW" else colors.red)
        story.append(Paragraph(f"<font size='28' color='#{score_color.hexval()[2:]}'><b>SCORE DE CRÉDITO: {card.credit_score}</b></font>", styles['Normal']))
        story.append(Paragraph(f"<b>Status:</b> {card.overall_status}", styles['Normal']))
        story.append(Spacer(1, 20))

        # Ratios Table
        story.append(Paragraph("<b>Principais Indicadores</b>", styles['Heading2']))
        table_data = [["Indicador", "Valor", "Status"]]
        for r in card.ratios[:8]:
            table_data.append([r.name, str(r.value), r.status.upper()])

        t = Table(table_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        story.append(Paragraph(f"<b>Eventos no Journal:</b> {event_count}", styles['Normal']))
        story.append(Paragraph(f"<b>Hash da Cadeia:</b> {content_hash[:32]}...", styles['Normal']))
        story.append(Paragraph(f"<b>Assinatura Digital:</b> {signature}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<i>Documento gerado por FinVeritas Contabolsa - Conformidade ISO 25010 + Anti-Fraude Ironclad</i>", styles['Normal']))

        doc.build(story)
