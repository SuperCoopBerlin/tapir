from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.coop.config import (
    on_welcome_session_attendance_update,
    get_ids_of_users_registered_to_a_shift_with_capability,
)
from tapir.core.config import sidebar_link_groups, feature_flag_solidarity_shifts
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
            url=reverse_lazy("shifts:calendar"),
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
            display_name="Solidarity Shifts",
            material_icon="favorite",
            url=reverse_lazy("shifts:solidarity_shifts"),
            required_feature_flag=feature_flag_solidarity_shifts,
            ordering=4,
        )

        shifts_group.add_link(
            display_name=_("Shift management"),
            material_icon="settings",
            url=reverse_lazy("shifts:shift_management"),
            required_permissions=[PERMISSION_SHIFTS_MANAGE],
            ordering=6,
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
        from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
        from tapir.shifts.emails.shift_missed_email import (
            ShiftMissedEmailBuilder,
        )
        from tapir.shifts.emails.shift_reminder_email import (
            ShiftReminderEmailBuilder,
        )
        from tapir.shifts.emails.second_shift_reminder_email import (
            SecondShiftReminderEmailBuilder,
        )
        from tapir.shifts.emails.stand_in_found_email import (
            StandInFoundEmailBuilder,
        )
        from tapir.shifts.emails.member_frozen_email import (
            MemberFrozenEmailBuilder,
        )
        from tapir.shifts.emails.freeze_warning_email import (
            FreezeWarningEmailBuilder,
        )
        from tapir.shifts.emails.unfreeze_notification_email import (
            UnfreezeNotificationEmailBuilder,
        )
        from tapir.shifts.emails.flying_member_registration_reminder_email import (
            FlyingMemberRegistrationReminderEmailBuilder,
        )

        TapirEmailBuilderBase.register_email(ShiftMissedEmailBuilder)
        TapirEmailBuilderBase.register_email(ShiftReminderEmailBuilder)
        TapirEmailBuilderBase.register_email(SecondShiftReminderEmailBuilder)
        TapirEmailBuilderBase.register_email(StandInFoundEmailBuilder)
        TapirEmailBuilderBase.register_email(MemberFrozenEmailBuilder)
        TapirEmailBuilderBase.register_email(FreezeWarningEmailBuilder)
        TapirEmailBuilderBase.register_email(UnfreezeNotificationEmailBuilder)
        TapirEmailBuilderBase.register_email(
            FlyingMemberRegistrationReminderEmailBuilder
        )
