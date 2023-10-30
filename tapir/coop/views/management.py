from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView

from tapir.settings import PERMISSION_SHIFTS_MANAGE


class MemberManagementView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "coop/member_management.html"
    permission_required = PERMISSION_SHIFTS_MANAGE
