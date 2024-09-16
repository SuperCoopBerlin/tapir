from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.config import URL_MEMBER_MANUAL
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.shifts.config import (
    FREEZE_THRESHOLD,
    FREEZE_AFTER_DAYS,
    NB_WEEKS_IN_THE_FUTURE_FOR_MAKE_UP_SHIFTS,
)


class MemberFrozenEmail(TapirEmailBase):
    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.member_frozen"

    @classmethod
    def get_name(cls) -> str:
        return _("Shift status set to frozen")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member when their shift status gets set to frozen. Usually happens if they miss to many shifts."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/member_frozen.subject.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/member_frozen.body.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "url_member_manual": URL_MEMBER_MANUAL,
            "coop_name": settings.COOP_NAME,
            "freeze_threshold": FREEZE_THRESHOLD,
            "freeze_after_days": FREEZE_AFTER_DAYS,
            "nb_weeks_in_the_future_for_make_up_shifts": NB_WEEKS_IN_THE_FUTURE_FOR_MAKE_UP_SHIFTS,
        }

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
