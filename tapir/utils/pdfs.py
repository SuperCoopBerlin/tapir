from typing import List

import weasyprint
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import translation
from django_weasyprint.utils import django_url_fetcher
from weasyprint import Document
from weasyprint.text.fonts import FontConfiguration

_WEASYPRINT_FONT_CONFIG = FontConfiguration()


def render_pdf(templates: List, context: dict, language: str) -> Document:
    with translation.override(language):
        rendered_html = render_to_string(
            template_name=templates,
            context=context,
        )
    document = weasyprint.HTML(
        string=rendered_html,
        base_url=settings.WEASYPRINT_BASEURL,
        url_fetcher=django_url_fetcher,
    )
    return document.render(font_config=_WEASYPRINT_FONT_CONFIG)
