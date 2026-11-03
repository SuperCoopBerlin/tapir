from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.settings import PERMISSION_TEAMLEADERPAGE_VIEW
from tapir.shifts.models import CapabilityTranslation


class TeamleaderPermsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_anonymous:
            return

        user: TapirUser = request.user
        try:
            capability = CapabilityTranslation.objects.get(name="Teamleader").capability
        except ObjectDoesNotExist:
            raise Http404(_("The qualification 'Teamleader' does not exist."))
        if capability in user.shift_user_data.capabilities.all():
            user.client_perms.append(PERMISSION_TEAMLEADERPAGE_VIEW)
