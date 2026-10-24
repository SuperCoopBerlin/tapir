from django.utils.deprecation import MiddlewareMixin

from tapir.accounts.models import TapirUser
from tapir.settings import PERMISSION_TEAMLEADERPAGE_VIEW
from tapir.shifts.models import ShiftUserCapability


class TeamleaderPermsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_anonymous:
            return

        user: TapirUser = request.user
        if ShiftUserCapability.SHIFT_COORDINATOR in user.shift_user_data.capabilities:
            user.client_perms.append(PERMISSION_TEAMLEADERPAGE_VIEW)
