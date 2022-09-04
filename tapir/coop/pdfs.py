import weasyprint
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import translation
from django_weasyprint.utils import django_url_fetcher
from weasyprint import Document
from weasyprint.text.fonts import FontConfiguration

from tapir.coop.config import COOP_SHARE_PRICE, COOP_ENTRY_AMOUNT
from tapir.coop.models import ShareOwner

_WEASYPRINT_FONT_CONFIG = FontConfiguration()


def get_shareowner_membership_confirmation_pdf(owner):
    doc = weasyprint.HTML(
        string=render_to_string(
            [
                "coop/pdf/membership_confirmation_pdf.html",
                "coop/pdf/membership_confirmation_pdf.default.html",
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
        "share_price": COOP_SHARE_PRICE,
        "entry_amount": COOP_ENTRY_AMOUNT,
    }
    context.update(kwargs)

    # render membership agreement with German locale
    with translation.override("de"):
        doc = weasyprint.HTML(
            string=render_to_string(
                [
                    "coop/pdf/membership_agreement_pdf.html",
                    "coop/pdf/membership_agreement_pdf.default.html",
                ],
                context,
            ),
            base_url=settings.WEASYPRINT_BASEURL,
            url_fetcher=django_url_fetcher,
        )
        return doc.render(font_config=_WEASYPRINT_FONT_CONFIG)


def get_confirmation_extra_shares_pdf(
    share_owner: ShareOwner, num_shares: int
) -> Document:
    context = {
        "member_infos": share_owner.get_info(),
        "num_shares": num_shares,
        "member_number": share_owner.id,
    }

    with translation.override(share_owner.get_info().preferred_language):
        doc = weasyprint.HTML(
            string=render_to_string(
                [
                    "coop/pdf/extra_shares_confirmation_pdf.html",
                    "coop/pdf/extra_shares_confirmation_pdf.default.html",
                ],
                context,
            ),
            base_url=settings.WEASYPRINT_BASEURL,
            url_fetcher=django_url_fetcher,
        )
        return doc.render(font_config=_WEASYPRINT_FONT_CONFIG)
