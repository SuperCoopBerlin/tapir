import datetime

from django.conf import settings
from weasyprint import Document

from tapir.coop import config
from tapir.coop.models import ShareOwner
from tapir.utils.pdfs import render_pdf

CONTENT_TYPE_PDF = "application/pdf"


def get_shareowner_membership_confirmation_pdf(
    share_owner: ShareOwner, num_shares: int, date: datetime.date
):
    templates = [
        "coop/pdf/membership_confirmation_pdf.html",
        "coop/pdf/membership_confirmation_pdf.default.html",
    ]
    context = {
        "share_owner": share_owner,
        "num_shares": num_shares,
        "date": date,
    }
    return render_pdf(
        templates=templates,
        context=context,
        language=share_owner.preferred_language,
    )


def get_membership_agreement_pdf(share_owner=None, num_shares=1):
    templates = [
        "coop/pdf/membership_agreement_pdf.html",
        "coop/pdf/membership_agreement_pdf.default.html",
    ]
    context = {
        "share_owner": share_owner,
        "coop_full_name": settings.COOP_FULL_NAME,
        "coop_street": settings.COOP_STREET,
        "coop_place": settings.COOP_PLACE,
        "share_price": config.COOP_SHARE_PRICE,
        "entry_amount": config.COOP_ENTRY_AMOUNT,
        "num_shares": num_shares,
    }
    return render_pdf(
        templates=templates,
        context=context,
        language="de",  # render membership agreement with German locale
    )


def get_confirmation_extra_shares_pdf(
    share_owner: ShareOwner, num_shares: int, date: datetime.date
) -> Document:
    templates = [
        "coop/pdf/extra_shares_confirmation_pdf.html",
        "coop/pdf/extra_shares_confirmation_pdf.default.html",
    ]
    context = {
        "member_infos": share_owner.get_info(),
        "num_shares": num_shares,
        "date": date,
        "member_number": share_owner.id,
        "coop_full_name": settings.COOP_FULL_NAME,
        "coop_street": settings.COOP_STREET,
        "coop_place": settings.COOP_PLACE,
        "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
    }
    return render_pdf(
        templates=templates,
        context=context,
        language=share_owner.get_info().preferred_language,
    )
