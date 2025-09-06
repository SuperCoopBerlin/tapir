from typing import List

from django.utils.translation import gettext_lazy as _


from tapir.coop.models import ShareOwner
from tapir.core.mail_option import MailOption
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.shifts.models import Shift, ShiftWatch, StaffingEventsChoices


class ShiftWatchEmailBuilder(TapirEmailBuilderBase):
    option = MailOption.OPTIONAL_ENABLED

    def __init__(self, shift_watch: ShiftWatch, staffing_event: StaffingEventsChoices):
        super().__init__()
        self.shift = shift_watch.shift
        self.reason = f"{staffing_event.label}: {shift_watch.shift.get_display_name()}"

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.shift_watch_mail"

    @classmethod
    def get_name(cls) -> str:
        return _("Watched Shift has changed")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member when a shift staffing is changed relevantely and the user is watching this shift."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/shift_watch.subject.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/shift_watch.body.html",
        ]

    def get_extra_context(self) -> dict:
        return {"shift": self.shift, "reason": self.reason}

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        shift_watch = ShiftWatch.objects.order_by("?").first()
        if not share_owner or not shift_watch:
            return None
        mail = cls(
            shift_watch=shift_watch, staffing_event=StaffingEventsChoices.UNDERSTAFFED
        )
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
