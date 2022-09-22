from django.apps import AppConfig


class ShiftConfig(AppConfig):
    name = "tapir.shifts"

    def ready(self):
        from tapir.core.tapir_email_base import TapirEmailBase
        from tapir.shifts.emails.shift_missed_email import (
            ShiftMissedEmail,
        )
        from tapir.shifts.emails.shift_reminder_email import (
            ShiftReminderEmail,
        )
        from tapir.shifts.emails.stand_in_found_email import (
            StandInFoundEmail,
        )

        TapirEmailBase.register_email(ShiftMissedEmail)
        TapirEmailBase.register_email(ShiftReminderEmail)
        TapirEmailBase.register_email(StandInFoundEmail)
