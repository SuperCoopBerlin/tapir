from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.core.tapir_email_base import TapirEmailBase, all_emails


class StandInFoundEmail(TapirEmailBase):
    shift = None

    def __init__(self, shift):
        self.shift = shift

    @staticmethod
    def get_unique_id() -> str:
        return "tapir.shifts.stand_in_found"

    @staticmethod
    def get_name() -> str:
        return _("Stand-in found")

    @staticmethod
    def get_description() -> str:
        return _(
            "Sent to a member that was looking for a stand-in"
            "when the corresponding slot is taken over by another member."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/stand_in_found.subject.html",
            "shifts/email/stand_in_found.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/stand_in_found.body.html",
            "shifts/email/stand_in_found.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "shift": self.shift,
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
            "coop_name": settings.COOP_NAME,
        }


all_emails[StandInFoundEmail.get_unique_id()] = StandInFoundEmail
