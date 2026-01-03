import io
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle
from .pdf_utils import register_pdf_font


def _format_variant_label(variant):
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


def _format_price(value):
    if value is None:
        return '-'
    return f'{value:.2f} TJS'


def build_price_list_pdf(products):
    buffer = io.BytesIO()
    font_name = register_pdf_font()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'PriceListTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=18,
        leading=22,
    )
    subtitle_style = ParagraphStyle(
        'PriceListSubtitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#666666'),
    )
    cell_style = ParagraphStyle(
        'PriceListCell',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=9,
        leading=11,
    )
    header_style = ParagraphStyle(
        'PriceListHeader',
        parent=cell_style,
        alignment=1,
    )
    elements = [
        Paragraph('Прайс-лист', title_style),
        Spacer(1, 6),
        Paragraph(f'Сформировано: {timezone.localdate():%d.%m.%Y}', subtitle_style),
        Spacer(1, 12),
    ]
    rows = [
        [
            Paragraph('№', header_style),
            Paragraph('Категория', header_style),
            Paragraph('Товар', header_style),
            Paragraph('Вариант', header_style),
            Paragraph('Цена', header_style),
        ]
    ]
    index = 1
    for product in products:
        variants = list(product.variants.all())
        if variants:
            for variant in variants:
                price = variant.price if variant.price is not None else product.price
                rows.append(
                    [
                        str(index),
                        Paragraph(product.category.name, cell_style),
                        Paragraph(product.name, cell_style),
                        Paragraph(_format_variant_label(variant), cell_style),
                        Paragraph(_format_price(price), cell_style),
                    ]
                )
                index += 1
        else:
            rows.append(
                [
                    str(index),
                    Paragraph(product.category.name, cell_style),
                    Paragraph(product.name, cell_style),
                    Paragraph('-', cell_style),
                    Paragraph(_format_price(product.price), cell_style),
                ]
            )
            index += 1
    table = LongTable(
        rows,
        repeatRows=1,
        colWidths=[30, 120, 195, 115, 63],
    )
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
