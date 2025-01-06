from typing import List

from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.shifts import config


class FlyingMemberRegistrationReminderEmailBuilder(TapirEmailBuilderBase):
    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.flying_member_registration_reminder_email"

    @classmethod
    def get_name(cls) -> str:
        return _("Flying member registration reminder")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to flying members %(nb_days)s days after a cycle has begun, if they haven't registered to a shift for this cycle."
            % {
                "nb_days": config.FLYING_MEMBERS_REGISTRATION_REMINDER_DAYS_AFTER_CYCLE_START
            }
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/flying_member_registration_reminder_email.subject.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/flying_member_registration_reminder_email.body.html",
        ]

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
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
