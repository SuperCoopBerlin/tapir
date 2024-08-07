import django_tables2
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, CreateView
from django_tables2.views import SingleTableView

from tapir.accounts.models import TapirUser
from tapir.coop.emails.tapir_account_created_email import TapirAccountCreatedEmail
from tapir.core.config import TAPIR_TABLE_TEMPLATE, TAPIR_TABLE_CLASSES
from tapir.core.views import TapirFormMixin
from tapir.settings import PERMISSION_SHIFTS_MANAGE, PERMISSION_ACCOUNTS_MANAGE
from tapir.utils.user_utils import UserUtils


class MemberManagementView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "coop/member_management.html"
    permission_required = PERMISSION_SHIFTS_MANAGE


class CreateGeneralTapirAccountView(
    TapirFormMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    permission_required = PERMISSION_ACCOUNTS_MANAGE
    model = TapirUser
    fields = ["first_name", "last_name", "username", "phone_number", "email"]

    def get_form(self, form_class=None):
        form = super(CreateGeneralTapirAccountView, self).get_form(form_class)
        form.fields["email"].required = True
        form.fields["email"].help_text = _(
            "Required. Please insert a valid email address."
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["page_title"] = _("Create Tapir account")
        context["card_title"] = _("Create Tapir account")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        tapir_user = form.instance
        email = TapirAccountCreatedEmail(tapir_user=tapir_user)
        email.send_to_tapir_user(actor=self.request.user, recipient=tapir_user)
        return response


class GeneralAccountsTable(django_tables2.Table):
    class Meta:
        model = TapirUser
        template_name = TAPIR_TABLE_TEMPLATE
        fields = ["id"]
        order_by = "id"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    display_name = django_tables2.Column(
        empty_values=(), verbose_name="Name", orderable=False
    )

    def before_render(self, request):
        self.request = request

    def render_display_name(self, value, record: TapirUser):
        return UserUtils.build_html_link_for_viewer(record, self.request.user)


class GeneralTapirAccountsListView(LoginRequiredMixin, SingleTableView):
    model = TapirUser
    paginate_by = 30
    template_name = "coop/general_accounts_list.html"
    table_class = GeneralAccountsTable
    queryset = TapirUser.objects.filter(share_owner__isnull=True)
