from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.coop.config import (
    on_welcome_session_attendance_update,
    get_ids_of_users_registered_to_a_shift_with_capability,
)
from tapir.core.config import sidebar_link_groups
from tapir.settings import PERMISSION_SHIFTS_MANAGE


class ShiftConfig(AppConfig):
    name = "tapir.shifts"

    def ready(self):
        self.register_sidebar_links()
        self.register_emails()

        from tapir.shifts.utils import (
            update_shift_account_depending_on_welcome_session_status,
        )

        on_welcome_session_attendance_update.append(
            update_shift_account_depending_on_welcome_session_status
        )

        from tapir.shifts import utils

        get_ids_of_users_registered_to_a_shift_with_capability.append(
            utils.get_ids_of_users_registered_to_a_shift_with_capability
        )

    @classmethod
    def register_sidebar_links(cls):
        shifts_group = sidebar_link_groups.get_group(_("Shifts"), 4)

        shifts_group.add_link(
            display_name=_("Shift calendar"),
            material_icon="calendar_today",
            url=reverse_lazy("shifts:calendar_future"),
            ordering=1,
        )

        shifts_group.add_link(
            display_name=_("ABCD-shifts week-plan"),
            material_icon="today",
            url=reverse_lazy("shifts:shift_template_overview"),
            ordering=2,
        )

        shifts_group.add_link(
            display_name="SET ON RENDER",
            material_icon="table_view",
            url=reverse_lazy("shifts:shift_template_group_calendar"),
            ordering=3,
            on_render=cls.get_link_display_name_abcd_calendar,
        )

        shifts_group.add_link(
            display_name=_("Past shifts"),
            material_icon="history",
            url=reverse_lazy("shifts:calendar_past"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
            ordering=4,
        )

        shifts_group.add_link(
            display_name=_("Shift exemptions"),
            material_icon="beach_access",
            url=reverse_lazy("shifts:shift_exemption_list"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
            ordering=5,
        )

        shifts_group.add_link(
            display_name=_("Members on alert"),
            material_icon="priority_high",
            url=reverse_lazy("shifts:members_on_alert"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
            ordering=6,
        )

        shifts_group.add_link(
            display_name=_("Add a shift"),
            material_icon="add_circle_outline",
            url=reverse_lazy("shifts:create_shift"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
            ordering=7,
        )

        shifts_group.add_link(
            display_name=_("Add an ABCD shift"),
            material_icon="add_circle_outline",
            url=reverse_lazy("shifts:shift_template_create"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
            ordering=8,
        )

        shifts_group.add_link(
            display_name=_("Shift statistics"),
            material_icon="calculate",
            url=reverse_lazy("shifts:statistics"),
            ordering=9,
        )

    @classmethod
    def get_link_display_name_abcd_calendar(cls, link):
        from tapir.shifts.templatetags.shifts import get_current_week_group

        current_week_group_name = "???"
        current_week_group = get_current_week_group()
        if current_week_group is not None:
            current_week_group_name = current_week_group.name

        link.display_name = _(
            "ABCD annual calendar, current week: {current_week_group_name}"
        ).format(current_week_group_name=current_week_group_name)

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
