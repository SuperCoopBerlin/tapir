from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from tapir import settings


def generate_share_request_pdf(
    share_owner, num_shares, additional_information, request
):

    context = {
        "share_owner": share_owner,
        "num_shares": num_shares,
        "additional_information": additional_information,
        "date": timezone.now(),
        "COOP_NAME": settings.COOP_NAME,
        "EMAIL_ADDRESS_MEMBER_OFFICE": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
        "COOP_FULL_NAME": settings.COOP_FULL_NAME,
        "COOP_STREET": settings.COOP_STREET,
        "COOP_PLACE": settings.COOP_PLACE,
    }

    html_string = render_to_string(
        "coop/pdf/extra_shares_request_pdf.html", context, request=request
    )

    pdf_bytes = HTML(string=html_string).write_pdf()

    return pdf_bytes
