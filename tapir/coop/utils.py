from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML


def generate_share_request_pdf(share_owner, num_shares, request):

    context = {
        "share_owner": share_owner,
        "num_shares": num_shares,
        "date": timezone.now(),
    }

    html_string = render_to_string(
        "coop/pdf/extra_shares_request_pdf.html", context, request=request
    )

    pdf_bytes = HTML(string=html_string).write_pdf()

    return pdf_bytes
