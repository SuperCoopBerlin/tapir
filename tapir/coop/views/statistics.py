from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db.models import Count
from django.views import generic
from django.views.generic import TemplateView

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner, MemberStatus, DraftUser
from tapir.shifts.models import (
    ShiftAttendanceMode,
    ShiftSlotTemplate,
    ShiftTemplate,
)


class StatisticsView(PermissionRequiredMixin, generic.TemplateView):
    template_name = "coop/statistics.html"
    permission_required = "coop.manage"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_members = ShareOwner.objects.with_status(MemberStatus.ACTIVE)
        active_users = TapirUser.objects.filter(share_owner__in=active_members)

        context["active_members"] = active_members.order_by("id")
        context["active_users"] = active_users.order_by("id")
        context["members_missing_accounts"] = active_members.filter(user=None).order_by(
            "id"
        )
        context["applicants"] = DraftUser.objects.order_by("id")

        members_in_abcd_system = active_users.with_shift_attendance_mode(
            ShiftAttendanceMode.REGULAR
        ).order_by("id")
        context["members_in_abcd_system"] = members_in_abcd_system

        context["members_in_flying_system"] = active_users.with_shift_attendance_mode(
            ShiftAttendanceMode.FLYING
        ).order_by("id")

        context["members_in_abcd_system_without_shift_attendance"] = (
            members_in_abcd_system.annotate(
                num_template_attendances=Count("shift_attendance_templates")
            )
            .filter(num_template_attendances=0)
            .order_by("id")
        )

        slot_types = ShiftSlotTemplate.objects.values("name").distinct()
        users_by_slot_type = dict()
        for slot_type in slot_types:
            displayed_name = slot_type["name"]
            if displayed_name == "":
                displayed_name = "General"
            users_by_slot_type[
                displayed_name
            ] = TapirUser.objects.registered_to_shift_slot_name(slot_type["name"])
        context["users_by_slot_name"] = users_by_slot_type

        abcd_shifts = ShiftTemplate.objects.all()
        abcd_shifts_not_full = abcd_shifts.filter(
            slot_templates__attendance_template__isnull=True
        ).distinct()
        context["abcd_shifts"] = abcd_shifts
        context["abcd_shifts_not_full"] = abcd_shifts_not_full

        slot_templates = ShiftSlotTemplate.objects.all()
        slot_templates_free = slot_templates.filter(attendance_template__isnull=True)
        context["slot_templates"] = slot_templates
        context["slot_templates_free"] = slot_templates_free

        return context


class AboutView(LoginRequiredMixin, TemplateView):
    template_name = "coop/about.html"
