from chartjs.views import JSONView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    RedirectView,
)
from django.views.generic import TemplateView

from tapir.accounts.models import TapirUser
from tapir.core.config import (
    feature_flag_solidarity_shifts,
)
from tapir.core.models import FeatureFlag
from tapir.settings import (
    PERMISSION_SHIFTS_MANAGE,
)
from tapir.shifts.models import (
    ShiftAccountEntry,
)
from tapir.shifts.models import (
    ShiftAttendance,
    SolidarityShift,
)
from tapir.utils.shortcuts import get_first_of_next_month


class SolidarityShiftUsed(LoginRequiredMixin, RedirectView):
    def post(self, request, *args, **kwargs):
        date = timezone.now()
        tapir_user = get_object_or_404(TapirUser, pk=kwargs["pk"])

        if not (
            request.user.pk == tapir_user.pk
            or request.user.has_perm(PERMISSION_SHIFTS_MANAGE)
        ):
            return HttpResponseForbidden(
                "You don't have permission to use Solidarity Shifts on behalf of another user."
            )
        elif not FeatureFlag.get_flag_value(feature_flag_solidarity_shifts):
            return HttpResponseBadRequest(
                "The Solidarity Shift feature is not enabled."
            )

        solidarity_shift = SolidarityShift.objects.filter(is_used_up=False)[0]

        if not solidarity_shift:
            return HttpResponseBadRequest("There are no available Solidarity Shifts")
        if tapir_user.shift_user_data.get_used_solidarity_shifts_current_year() >= 2:
            return HttpResponseBadRequest(
                "You already used 2 Solidarity Shifts this year"
            )

        solidarity_shift.is_used_up = True
        solidarity_shift.date_used = date
        solidarity_shift.save()

        ShiftAccountEntry(
            user=tapir_user,
            value=1,
            is_solidarity_used=True,
            date=date,
            description="Solidarity shift received",
        ).save()

        messages.info(
            request, _("Solidarity Shift received. Account Balance increased by 1.")
        )

        return redirect(tapir_user.get_absolute_url())


class SolidarityShiftGiven(LoginRequiredMixin, RedirectView):
    def post(self, request, *args, **kwargs):
        if not FeatureFlag.get_flag_value(feature_flag_solidarity_shifts):
            return HttpResponseBadRequest(
                "The Solidarity Shift feature is not enabled."
            )
        tapir_user = get_object_or_404(TapirUser, pk=kwargs["pk"])
        shift_attendance = tapir_user.shift_attendances.filter(
            is_solidarity=False, state=ShiftAttendance.State.DONE
        ).first()
        if not shift_attendance:
            return ShiftAttendance.DoesNotExist(
                "Could not find a shift attendance to use as solidarity shift."
            )

        SolidarityShift.objects.create(shiftAttendance=shift_attendance)

        shift_attendance.is_solidarity = True
        shift_attendance.save()

        ShiftAccountEntry(
            user=tapir_user,
            value=-1,
            date=timezone.now(),
            description="Solidarity shift given",
            is_from_welcome_session=False,
        ).save()

        messages.info(
            request, _("Solidarity Shift given. Account Balance debited with -1.")
        )

        return redirect(tapir_user.get_absolute_url())


class SolidarityShiftsView(LoginRequiredMixin, TemplateView):
    template_name = "shifts/solidarity_shifts_overview.html"
    model = SolidarityShift

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_solidarity_shifts"] = SolidarityShift.objects.filter(
            is_used_up=False
        ).count()
        context["used_solidarity_shifts_total"] = SolidarityShift.objects.filter(
            is_used_up=True
        ).count()
        context["gifted_solidarity_shifts_total"] = SolidarityShift.objects.count()
        return context


class CacheDatesFirstSolidarityToTodayMixin:
    def __init__(self):
        super().__init__()

    def get_dates_from_first_solidarity_to_today(self):
        first_solidarity = SolidarityShift.objects.order_by("date_gifted").first()
        if not first_solidarity:
            return []

        current_date = first_solidarity.date_gifted.replace(day=1)
        end_date = timezone.now().date()
        dates = []
        while current_date < end_date:
            dates.append(current_date)
            current_date = get_first_of_next_month(current_date)

        return dates


class GiftedSolidarityShiftsJsonView(CacheDatesFirstSolidarityToTodayMixin, JSONView):
    def get_context_data(self, **kwargs):
        data = []
        dates = self.get_dates_from_first_solidarity_to_today()

        for date in dates:
            month_num = int(date.strftime("%m"))
            year = int(date.strftime("%Y"))
            data.append(
                SolidarityShift.objects.filter(
                    date_gifted__month=month_num, date_gifted__year=year
                ).count()
            )

        context_data = {
            "type": "bar",
            "data": {
                "labels": [date.strftime("%b %Y") for date in dates],
                "datasets": [
                    {
                        "label": _("Solidarity shifts gifted"),
                        "data": data,
                    }
                ],
            },
        }
        return context_data


class UsedSolidarityShiftsJsonView(CacheDatesFirstSolidarityToTodayMixin, JSONView):
    def get_context_data(self, **kwargs):
        data = []
        dates = self.get_dates_from_first_solidarity_to_today()

        for date in dates:
            month_num = int(date.strftime("%m"))
            year = int(date.strftime("%Y"))
            data.append(
                SolidarityShift.objects.filter(
                    date_used__month=month_num, date_used__year=year
                ).count()
            )

        context_data = {
            "type": "bar",
            "data": {
                "labels": [date.strftime("%b %Y") for date in dates],
                "datasets": [
                    {
                        "label": _("Solidarity shifts used"),
                        "data": data,
                    }
                ],
            },
        }
        return context_data
