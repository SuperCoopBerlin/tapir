from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_link_groups
from tapir.settings import PERMISSION_SHIFTS_MANAGE


class ShiftConfig(AppConfig):
    name = "tapir.shifts"

    def ready(self):
        self.register_sidebar_links()
        self.register_emails()

    @staticmethod
    def register_sidebar_links():
        shifts_group_name = _("Shifts")

        sidebar_link_groups.add_link(
            group_name=shifts_group_name,
            display_name=_("Shift calendar"),
            material_icon="calendar_today",
            url=reverse_lazy("shifts:calendar_future"),
        )

        sidebar_link_groups.add_link(
            group_name=shifts_group_name,
            display_name=_("ABCD-shifts week-plan"),
            material_icon="today",
            url=reverse_lazy("shifts:shift_template_overview"),
        )

        from tapir.shifts.templatetags.shifts import get_current_week_group

        current_week_group_name = "???"
        current_week_group = get_current_week_group()
        if current_week_group is not None:
            current_week_group_name = current_week_group.name
        sidebar_link_groups.add_link(
            group_name=shifts_group_name,
            display_name=_(
                "ABCD annual calendar, current week: {current_week_group_name}"
            ).format(current_week_group_name=current_week_group_name),
            material_icon="table_view",
            url=reverse_lazy("shifts:shift_template_group_calendar"),
        )

        sidebar_link_groups.add_link(
            group_name=shifts_group_name,
            display_name=_("Past shifts"),
            material_icon="history",
            url=reverse_lazy("shifts:calendar_past"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
        )

        sidebar_link_groups.add_link(
            group_name=shifts_group_name,
            display_name=_("Shift exemptions"),
            material_icon="beach_access",
            url=reverse_lazy("shifts:shift_exemption_list"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
        )

        sidebar_link_groups.add_link(
            group_name=shifts_group_name,
            display_name=_("Members on alert"),
            material_icon="priority_high",
            url=reverse_lazy("shifts:members_on_alert"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
        )

        sidebar_link_groups.add_link(
            group_name=shifts_group_name,
            display_name=_("Add a shift"),
            material_icon="add_circle_outline",
            url=reverse_lazy("shifts:create_shift"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
        )

        sidebar_link_groups.add_link(
            group_name=_("Miscellaneous"),
            display_name=_("Shift statistics"),
            material_icon="calculate",
            url=reverse_lazy("shifts:statistics"),
        )

    @staticmethod
    def register_emails():
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
