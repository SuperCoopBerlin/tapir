from django.conf import settings
from weasyprint import Document

from tapir.coop.config import COOP_SHARE_PRICE, COOP_ENTRY_AMOUNT
from tapir.coop.models import ShareOwner
from tapir.settings import (
    COOP_FULL_NAME,
    COOP_STREET,
    COOP_PLACE,
    COOP_NAME,
    EMAIL_ADDRESS_MEMBER_OFFICE,
)
from tapir.utils.pdfs import render_pdf


def get_shareowner_membership_confirmation_pdf(owner: ShareOwner):
    templates = [
        "coop/pdf/membership_confirmation_pdf.html",
        "coop/pdf/membership_confirmation_pdf.default.html",
    ]
    context = {
        "owner": owner,
        "COOP_NAME": COOP_NAME,
        "EMAIL_ADDRESS_MEMBER_OFFICE": EMAIL_ADDRESS_MEMBER_OFFICE,
        "COOP_FULL_NAME": COOP_FULL_NAME,
        "COOP_STREET": COOP_STREET,
        "COOP_PLACE": COOP_PLACE,
    }
    return render_pdf(
        templates=templates,
        context=context,
        language=owner.preferred_language,
    )


def get_membership_agreement_pdf(owner=None, num_shares=1):
    templates = [
        "coop/pdf/membership_agreement_pdf.html",
        "coop/pdf/membership_agreement_pdf.default.html",
    ]
    context = {
        "owner": owner,
        "coop_full_name": COOP_FULL_NAME,
        "coop_street": COOP_STREET,
        "coop_place": COOP_PLACE,
        "share_price": COOP_SHARE_PRICE,
        "entry_amount": COOP_ENTRY_AMOUNT,
        "num_shares": num_shares,
    }
    return render_pdf(
        templates=templates,
        context=context,
        language="de",  # render membership agreement with German locale
    )


def get_confirmation_extra_shares_pdf(
    share_owner: ShareOwner, num_shares: int
) -> Document:
    templates = [
        "coop/pdf/extra_shares_confirmation_pdf.html",
        "coop/pdf/extra_shares_confirmation_pdf.default.html",
    ]
    context = {
        "member_infos": share_owner.get_info(),
        "num_shares": num_shares,
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
