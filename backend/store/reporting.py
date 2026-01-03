import io

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

from .models import Order
from .pdf_utils import register_pdf_font


STATUS_LABELS = {
    Order.STATUS_PENDING: 'Ожидает',
    Order.STATUS_PAID: 'Оплачен',
    Order.STATUS_SHIPPED: 'В пути',
    Order.STATUS_RECEIVED: 'Получен',
    Order.STATUS_CANCELED: 'Отменен',
}


def build_orders_report_pdf(orders, period_label, summary, status_counts):
    buffer = io.BytesIO()
    font_name = register_pdf_font()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=18,
        leading=22,
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#666666'),
    )
    cell_style = ParagraphStyle(
        'ReportCell',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=9,
        leading=11,
    )
    header_style = ParagraphStyle(
        'ReportHeader',
        parent=cell_style,
        alignment=1,
    )

    elements = [
        Paragraph('Отчет по заказам', title_style),
        Spacer(1, 6),
        Paragraph(period_label, subtitle_style),
        Paragraph(f'Сформировано: {timezone.localdate():%d.%m.%Y}', subtitle_style),
        Spacer(1, 10),
    ]

    summary_lines = [
        f'Количество заказов: {summary.get("total_orders", 0)}',
        f'Сумма заказов: {summary.get("total_amount", 0)} c.',
    ]
    if status_counts:
        status_text = ', '.join(
            f'{STATUS_LABELS.get(item["status"], item["status"])}: {item["count"]}'
            for item in status_counts
        )
        summary_lines.append(f'Статусы: {status_text}')
    for line in summary_lines:
        elements.append(Paragraph(line, subtitle_style))
    elements.append(Spacer(1, 12))

    rows = [
        [
            Paragraph('№', header_style),
            Paragraph('Дата', header_style),
            Paragraph('Заказ', header_style),
            Paragraph('Клиент', header_style),
            Paragraph('Статус', header_style),
            Paragraph('Сумма', header_style),
        ]
    ]

    if not orders:
        rows.append(
            [
                '1',
                Paragraph('-', cell_style),
                Paragraph('-', cell_style),
                Paragraph('Нет данных', cell_style),
                Paragraph('-', cell_style),
                Paragraph('-', cell_style),
            ]
        )
    else:
        for index, order in enumerate(orders, start=1):
            profile = getattr(order.user, 'profile', None)
            client_name = profile.full_name if profile and profile.full_name else order.user.username
            created_at = timezone.localtime(order.created_at).strftime('%d.%m.%Y')
            rows.append(
                [
                    str(index),
                    Paragraph(created_at, cell_style),
                    Paragraph(f'#{order.id}', cell_style),
                    Paragraph(client_name, cell_style),
                    Paragraph(STATUS_LABELS.get(order.status, order.status), cell_style),
                    Paragraph(f'{order.total} c.', cell_style),
                ]
            )

    table = LongTable(rows, repeatRows=1, colWidths=[30, 70, 50, 190, 75, 70])
    table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#efefef')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111111')),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cccccc')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 14))
    elements.append(Paragraph('Купленные позиции', title_style))
    elements.append(Spacer(1, 6))

    item_rows = [
        [
            Paragraph('Заказ', header_style),
            Paragraph('Товар', header_style),
            Paragraph('Вариант', header_style),
            Paragraph('Кол-во', header_style),
            Paragraph('Цена', header_style),
            Paragraph('Сумма', header_style),
        ]
    ]
    has_items = False
    for order in orders:
        for item in order.items.all():
            has_items = True
            variant_label = _format_variant_label(getattr(item, 'variant', None))
            item_total = item.price * item.quantity
            item_rows.append(
                [
                    Paragraph(f'#{order.id}', cell_style),
                    Paragraph(item.product.name, cell_style),
                    Paragraph(variant_label, cell_style),
                    Paragraph(str(item.quantity), cell_style),
                    Paragraph(f'{item.price} c.', cell_style),
                    Paragraph(f'{item_total} c.', cell_style),
                ]
            )
    if not has_items:
        item_rows.append(
            [
                Paragraph('-', cell_style),
                Paragraph('Нет данных', cell_style),
                Paragraph('-', cell_style),
                Paragraph('-', cell_style),
                Paragraph('-', cell_style),
                Paragraph('-', cell_style),
            ]
        )
    items_table = LongTable(item_rows, repeatRows=1, colWidths=[45, 185, 120, 45, 60, 60])
    items_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#efefef')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111111')),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cccccc')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
            ]
        )
    )
    elements.append(items_table)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    doc.build(elements)
    return buffer.getvalue()


def _format_variant_label(variant):
    if not variant:
        return '-'
    label = (variant.name or '').strip()
    attributes = variant.attributes or {}
    parts = []
    if label:
        parts.append(label)
    if attributes:
        attr_items = []
        for key, value in attributes.items():
            if value is None or value == '':
                continue
            key_label = str(key).strip()
            if key_label.lower() in {'color', 'цвет'}:
                attr_items.append(f'Цвет: {value}')
            else:
                attr_items.append(f'{key_label}: {value}')
        if attr_items:
            parts.append(', '.join(attr_items))
    return ' / '.join(parts) if parts else '-'
