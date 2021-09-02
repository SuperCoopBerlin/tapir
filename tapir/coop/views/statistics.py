from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count
from django.views import generic

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner, MemberStatus, DraftUser
from tapir.shifts.models import ShiftAttendanceMode


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

        members_in_abcd_system = active_users.filter(
            shift_user_data__attendance_mode=ShiftAttendanceMode.REGULAR
        ).order_by("id")
        context["members_in_abcd_system"] = members_in_abcd_system

        context["members_in_flying_system"] = active_users.filter(
            shift_user_data__attendance_mode=ShiftAttendanceMode.FLYING
        ).order_by("id")

        context["members_in_abcd_system_without_shift_attendance"] = (
            members_in_abcd_system.annotate(
                num_template_attendances=Count("shift_attendance_templates")
            )
            .filter(num_template_attendances=0)
            .order_by("id")
        )

        return context
