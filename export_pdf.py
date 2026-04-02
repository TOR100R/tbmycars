"""
PDF export using only built-in Python + reportlab (free, no paid services).
Falls back to plain text if reportlab not available.
"""
import os
import io
from datetime import datetime
from database import Database

db = Database()


def generate_pdf(car_id: int) -> bytes:
    """Generate PDF report for a car. Returns bytes."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        return _generate_with_reportlab(car_id)
    except ImportError:
        return _generate_plain_text(car_id)


def _generate_with_reportlab(car_id: int) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    car = db.get_car(car_id)
    events = db.get_events(car_id, limit=500)
    insurance = db.get_insurance(car_id)
    claims = db.get_claims(car_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=2*cm, leftMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, spaceAfter=6)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=4)
    normal_style = styles['Normal']

    story = []

    # Title
    story.append(Paragraph(f"Mi Garaje — Historial de {car['brand']} {car['model']}", title_style))
    story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    story.append(Spacer(1, 0.5*cm))

    # Car info
    story.append(Paragraph("Datos del vehículo", heading_style))
    car_data = [
        ["Marca / Modelo", f"{car['brand']} {car['model']}"],
        ["Matrícula", car['plate']],
        ["Año", str(car['year'])],
        ["Kilómetros", f"{car['km']:,} km"],
        ["Combustible", car['fuel']],
    ]
    t = Table(car_data, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # Insurance
    if insurance:
        story.append(Paragraph("Seguro", heading_style))
        ins = insurance[0]
        ins_data = [
            ["Compañía", ins['company'] or '-'],
            ["Póliza", ins['policy'] or '-'],
            ["Vencimiento", ins['expiry'] or '-'],
            ["Prima", f"{ins['cost']}€" if ins['cost'] else '-'],
        ]
        t = Table(ins_data, colWidths=[5*cm, 11*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

    # Events
    if events:
        story.append(Paragraph(f"Historial de mantenimiento ({len(events)} registros)", heading_style))
        ev_data = [["Fecha", "Operación", "Km", "Coste", "Notas"]]
        for e in events:
            ev_data.append([
                e['date'],
                e['event_type'][:35],
                f"{e['km']:,}" if e['km'] else '-',
                f"{e['cost']}€" if e['cost'] else '-',
                (e['notes'] or '')[:30],
            ])
        t = Table(ev_data, colWidths=[2.5*cm, 6*cm, 2.5*cm, 2*cm, 3*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightyellow]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

    # Claims
    if claims:
        story.append(Paragraph(f"Partes al seguro ({len(claims)})", heading_style))
        cl_data = [["Fecha", "Descripción", "Expediente", "Estado"]]
        for c in claims:
            cl_data.append([
                c['date'] or '-',
                (c['description'] or '')[:40],
                c['claim_number'] or '-',
                c['status'] or '-',
            ])
        t = Table(cl_data, colWidths=[2.5*cm, 7*cm, 3*cm, 3.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t)

    doc.build(story)
    return buffer.getvalue()


def _generate_plain_text(car_id: int) -> bytes:
    """Fallback: plain text export as .txt"""
    car = db.get_car(car_id)
    events = db.get_events(car_id, limit=500)
    insurance = db.get_insurance(car_id)

    lines = []
    lines.append(f"MI GARAJE — {car['brand']} {car['model']}")
    lines.append(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append("=" * 50)
    lines.append(f"Matrícula: {car['plate']} | Año: {car['year']} | Km: {car['km']:,} | Combustible: {car['fuel']}")
    lines.append("")

    if insurance:
        ins = insurance[0]
        lines.append(f"SEGURO: {ins['company']} | Póliza: {ins['policy']} | Vence: {ins['expiry']}")
        lines.append("")

    lines.append("HISTORIAL DE MANTENIMIENTO:")
    lines.append("-" * 50)
    for e in events:
        line = f"{e['date']} | {e['event_type']}"
        if e['km']:
            line += f" | {e['km']:,} km"
        if e['cost']:
            line += f" | {e['cost']}€"
        if e['notes']:
            line += f" | {e['notes']}"
        lines.append(line)

    return "\n".join(lines).encode('utf-8')
