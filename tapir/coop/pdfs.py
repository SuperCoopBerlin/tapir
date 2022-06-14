import weasyprint
from django.conf import settings
from django.template.loader import render_to_string
from django_weasyprint.utils import django_url_fetcher
from weasyprint.text.fonts import FontConfiguration

_WEASYPRINT_FONT_CONFIG = FontConfiguration()


def get_shareowner_membership_confirmation_pdf(owner):
    doc = weasyprint.HTML(
        string=render_to_string(
            [
                "coop/membership_confirmation_pdf.html",
                "coop/membership_confirmation_pdf.default.html",
            ],
            {
                "owner": owner,
            },
        ),
        base_url=settings.WEASYPRINT_BASEURL,
        url_fetcher=django_url_fetcher,
    )
    return doc.render(font_config=_WEASYPRINT_FONT_CONFIG)


def get_membership_agreement_pdf(owner=None, **kwargs):
    context = {
        "owner": owner,
    }
    context.update(kwargs)
    doc = weasyprint.HTML(
        string=render_to_string(
            [
                "coop/membership_agreement_pdf.html",
                "coop/membership_agreement_pdf.default.html",
            ],
            context,
        ),
        base_url=settings.WEASYPRINT_BASEURL,
        url_fetcher=django_url_fetcher,
    )
    return doc.render(font_config=_WEASYPRINT_FONT_CONFIG)
