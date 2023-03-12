from typing import List

from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase


class UnfreezeNotificationEmail(TapirEmailBase):
    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.unfreeze_notification"

    @classmethod
    def get_name(cls) -> str:
        return _("Unfreeze Notification")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member when their shift status gets set from frozen to flying."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/unfreeze_notification.subject.html",
            "shifts/email/unfreeze_notification.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/unfreeze_notification.body.html",
            "shifts/email/unfreeze_notification.body.default.html",
        ]

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        if not share_owner:
            return None
        mail = cls()
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
