import os

from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_pdf_font():
    font_name = 'FamilyDentPDF'
    if font_name in pdfmetrics.getRegisteredFontNames():
        return font_name
    candidates = [
        getattr(settings, 'PRICE_LIST_FONT_PATH', ''),
        os.getenv('DJANGO_PRICE_LIST_FONT_PATH', ''),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    ]
    for path in candidates:
        if path and os.path.exists(path):
            pdfmetrics.registerFont(TTFont(font_name, path))
            return font_name
    return 'Helvetica'
