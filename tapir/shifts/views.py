import datetime
from collections import defaultdict

from django.views.generic import TemplateView, DetailView

from tapir.shifts.models import Shift


class UpcomingDaysView(TemplateView):

    template_name = "shifts/upcoming_days.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        shifts_by_days = defaultdict(list)
        for shift in Shift.objects.filter(start_time__gte=datetime.date.today()):
            shifts_by_days[shift.start_time.date()].append(shift)

        # Django template language can't loop defaultdict
        context_data['shifts_by_days'] = dict(shifts_by_days)
        return context_data


class ShiftDetailView(DetailView):
    model = Shift
    template_name = "shifts/shift_detail.html"
