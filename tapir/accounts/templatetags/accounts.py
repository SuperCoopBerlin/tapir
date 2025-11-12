import phonenumbers
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from phonenumbers import PhoneNumberFormat

from tapir.accounts.models import TapirUser
from tapir.settings import PERMISSION_GROUP_MANAGE
from tapir.utils.user_utils import UserUtils

register = template.Library()


@register.filter
@stringfilter
def format_phone_number(phone_number):
    return (
        phonenumbers.format_number(
            phonenumbers.parse(
                number=phone_number, region=settings.PHONENUMBER_DEFAULT_REGION
            ),
            PhoneNumberFormat.INTERNATIONAL,
        )
        if phone_number
        else ""
    )


@register.inclusion_tag("accounts/purchase_tracking_card.html", takes_context=True)
def purchase_tracking_card(context, tapir_user: TapirUser):
    if not hasattr(tapir_user, "share_owner") or not tapir_user.share_owner:
        return context

    context["barcode_as_svg"] = UserUtils.get_member_card_barcode_as_svg(
        tapir_user=tapir_user
    )
    context["tapir_user"] = tapir_user
    request = context["request"]
    context["is_allowed_to_see_purchase_tracking"] = (
        tapir_user == request.user or request.user.has_perm(PERMISSION_GROUP_MANAGE)
    )
    return context
