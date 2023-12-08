from typing import List

from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.settings import EMAIL_ADDRESS_MEMBER_OFFICE


class CoPurchaserUpdatedMail(TapirEmailBase):
    def __init__(self, tapir_user: TapirUser):
        super().__init__()
        self.tapir_user = tapir_user

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.co_purchaser_updated_mail"

    @classmethod
    def get_name(cls) -> str:
        return _("Co-purchaser updated")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member when their new co-purchaser gets registered on their profile."
        )

    def get_subject_templates(self) -> List:
        return [
            "coop/email/co_purchaser_updated.subject.html",
            "coop/email/co_purchaser_updated.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "coop/email/co_purchaser_updated.body.html",
            "coop/email/co_purchaser_updated.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {"EMAIL_ADDRESS_MEMBER_OFFICE": EMAIL_ADDRESS_MEMBER_OFFICE}

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        tapir_user = (
            TapirUser.objects.filter(share_owner__isnull=False)
            .exclude(co_purchaser="")
            .order_by("?")
            .first()
        )
        if tapir_user:
            share_owner = tapir_user.share_owner
        else:
            share_owner = (
                ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
            )
        if not share_owner:
            return None

        mail = cls(tapir_user=share_owner.user)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
