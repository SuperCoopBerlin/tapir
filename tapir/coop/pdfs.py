import weasyprint
from django.conf import settings
from django.template.loader import render_to_string
from django_weasyprint.utils import django_url_fetcher


def get_shareowner_membership_confirmation_pdf(owner):
    doc = weasyprint.HTML(
        string=render_to_string(
            "coop/membership_confirmation_pdf.html",
            {
                "owner": owner,
                "owner_data": owner.user if hasattr(owner, "user") else owner,
            },
        ),
        base_url=settings.WEASYPRINT_BASEURL,
        url_fetcher=django_url_fetcher,
    )
    return doc.render(font_config=weasyprint.fonts.FontConfiguration())
