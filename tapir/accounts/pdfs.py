from tapir.accounts.models import TapirUser
from tapir.utils.pdfs import render_pdf
from tapir.utils.user_utils import UserUtils

CONTENT_TYPE_PDF = "application/pdf"


def get_member_card_barcode_pdf(tapir_user: TapirUser):
    templates = [
        "accounts/pdf/member_card_barcode_pdf.html",
    ]
    context = {
        "barcode_as_svg": UserUtils.get_member_card_barcode_as_svg(tapir_user),
    }
    return render_pdf(
        templates=templates,
        context=context,
        language=tapir_user.preferred_language,
    )
