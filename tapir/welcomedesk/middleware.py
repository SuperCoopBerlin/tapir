import datetime

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from tapir.settings import PERMISSION_WELCOMEDESK_VIEW
from tapir.shifts.models import Shift, ShiftAttendance


class WelcomeDeskPermsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_anonymous:
            return

        current_shifts = Shift.objects.filter(
            start_time__lt=timezone.now() + datetime.timedelta(minutes=20),
            end_time__gt=timezone.now() - datetime.timedelta(minutes=20),
        )
        user_is_currently_doing_a_shift = (
            ShiftAttendance.objects.filter(
                user=request.user, slot__shift__in=current_shifts
            )
            .with_valid_state()
            .exists()
        )
        if user_is_currently_doing_a_shift:
            request.user.client_perms = [PERMISSION_WELCOMEDESK_VIEW]
