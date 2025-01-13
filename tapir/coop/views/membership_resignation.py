import django_filters
import django_tables2
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django_filters.views import FilterView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir.coop.config import feature_flag_membership_resignation
from tapir.coop.emails.membershipresignation_confirmation_email import (
    MembershipResignationConfirmation,
)
from tapir.coop.emails.membershipresignation_transferred_shares_confirmation import (
    MembershipResignationTransferredSharesConfirmation,
)
from tapir.coop.forms import MembershipResignationForm
from tapir.coop.models import (
    MembershipResignation,
    MembershipResignationCreateLogEntry,
    MembershipResignationUpdateLogEntry,
    MembershipResignationDeleteLogEntry,
    ShareOwner,
    UpdateShareOwnerLogEntry,
)
from tapir.coop.services.membership_resignation_service import (
    MembershipResignationService,
)
from tapir.core.config import TAPIR_TABLE_CLASSES, TAPIR_TABLE_TEMPLATE
from tapir.core.models import FeatureFlag
from tapir.core.services.send_mail_service import SendMailService
from tapir.core.templatetags.core import tapir_button_link_to_action
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import (
    PERMISSION_RESIGNATION_VIEW,
    PERMISSION_RESIGNATION_MANAGE,
)
from tapir.utils.forms import DateInputTapir
from tapir.utils.user_utils import UserUtils


class MembershipResignationTable(django_tables2.Table):
    class Meta:
        model = MembershipResignation
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "share_owner",
            "cancellation_date",
            "cancellation_reason_category",
            "cancellation_reason",
            "paid_out",
            "pay_out_day",
            "resignation_type",
        ]
        sequence = [
            "share_owner",
            "cancellation_date",
            "pay_out_day",
            "paid_out",
            "cancellation_reason_category",
            "cancellation_reason",
            "add_buttons",
        ]
        exclude = ["resignation_type"]
        order_by = "-cancellation_date"
        attrs = {"class": TAPIR_TABLE_CLASSES}
        empty_text = "No entries"
        default = "No entries"

    pay_out_day = django_tables2.DateColumn(
        format="d/m/Y",
        verbose_name="Membership ends",
        default="",
        attrs={"td": {"class": "col-2"}},
    )
    paid_out = django_tables2.Column(
        attrs={"td": {"class": "col-2"}},
    )
    add_buttons = django_tables2.Column(
        empty_values=(),
        verbose_name="Actions",
        orderable=False,
        exclude_from_export=True,
    )

    def before_render(self, request):
        self.request = request

    def render_share_owner(self, record: MembershipResignation):
        return UserUtils.build_html_link_for_viewer(
            record.share_owner, self.request.user
        )

    def value_share_owner(self, record: MembershipResignation):
        return record.share_owner.get_member_number()

    def render_cancellation_reason(self, record: MembershipResignation):
        return record.cancellation_reason

    def render_cancellation_date(self, record: MembershipResignation):
        return record.cancellation_date.strftime("%d/%m/%Y")

    def render_paid_out(self, record: MembershipResignation):
        match record.resignation_type:
            case MembershipResignation.ResignationType.GIFT_TO_COOP:
                return _(f"Share(s) gifted {chr(8594)} SuperCoop")
            case MembershipResignation.ResignationType.BUY_BACK:
                return "Yes" if record.paid_out else "No"
            case MembershipResignation.ResignationType.TRANSFER:
                return format_html(
                    "{} {} {}",
                    _("Share(s) gifted"),
                    chr(8594),
                    UserUtils.build_html_link_for_viewer(
                        record.transferring_shares_to, self.request.user
                    ),
                )
            case _:
                raise ValueError(f"Unknown resignation type: {record.resignation_type}")

    def render_add_buttons(self, value, record: MembershipResignation):
        return format_html(
            "<a href='{}' class='{}'>{}</a>",
            reverse_lazy("coop:membership_resignation_detail", args=[record.pk]),
            tapir_button_link_to_action(),
            format_html("<span class='material-icons'>more_horiz</span>"),
        )


class MembershipResignationFilter(django_filters.FilterSet):
    display_name = django_filters.CharFilter(
        method="display_name_filter", label=_("Search member or ID")
    )
    pay_out_start_date = django_filters.DateFilter(
        field_name="pay_out_day",
        widget=DateInputTapir(format="%d/%m/%Y"),
        lookup_expr="gte",
        label=_("Pay out start date"),
    )
    pay_out_end_date = django_filters.DateFilter(
        field_name="pay_out_day",
        widget=DateInputTapir(format="%d/%m/%Y"),
        lookup_expr="lte",
        label=_("Pay out end date"),
    )
    paid_out = django_filters.BooleanFilter(
        widget=django_filters.widgets.BooleanWidget()
    )
    cancellation_reason_category = django_filters.ChoiceFilter(
        choices=MembershipResignation.CancellationReasons.choices
    )

    class Meta:
        model = MembershipResignation
        fields = ["display_name", "paid_out", "pay_out_start_date", "pay_out_end_date"]

    @staticmethod
    def display_name_filter(
        queryset: MembershipResignation.MembershipResignationQuerySet, name, value: str
    ):
        return queryset.with_name_or_id(value).distinct()


class MembershipResignationList(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FilterView,
    ExportMixin,
    SingleTableView,
):
    table_class = MembershipResignationTable
    model = MembershipResignation
    template_name = "coop/membership_resignation_list.html"
    export_formats = ["csv", "json"]
    filterset_class = MembershipResignationFilter
    permission_required = PERMISSION_RESIGNATION_VIEW

    def get_context_data(self, **kwargs):
        if not FeatureFlag.get_flag_value(feature_flag_membership_resignation):
            raise PermissionDenied("The membership resignation feature is disabled.")

        context_data = super().get_context_data(**kwargs)
        context_data["total_of_resigned_members"] = (
            MembershipResignation.objects.count()
        )
        return context_data


class MembershipResignationEditView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TapirFormMixin,
    UpdateViewLogMixin,
    UpdateView,
):
    model = MembershipResignation
    form_class = MembershipResignationForm
    permission_required = PERMISSION_RESIGNATION_MANAGE
    success_url = reverse_lazy("coop:membership_resignation_list")

    def get_context_data(self, **kwargs):
        if not FeatureFlag.get_flag_value(feature_flag_membership_resignation):
            raise PermissionDenied("The membership resignation feature is disabled.")

        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Cancel membership of %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                person=self.object.share_owner, viewer=self.request.user
            )
        }
        context_data["card_title"] = _("Cancel membership of %(name)s") % {
            "name": UserUtils.build_html_link_for_viewer(
                person=self.object.share_owner, viewer=self.request.user
            )
        }
        return context_data

    def form_valid(self, form):
        with transaction.atomic():
            result = super().form_valid(form)
            membership_resignation: MembershipResignation = form.instance
            MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
                resignation=membership_resignation, actor=self.request.user
            )
            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                MembershipResignationUpdateLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    model=form.instance,
                    actor=self.request.user,
                ).save()
        return result


class MembershipResignationCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    model = MembershipResignation
    form_class = MembershipResignationForm
    permission_required = PERMISSION_RESIGNATION_MANAGE
    success_url = reverse_lazy("coop:membership_resignation_list")
    template_name = "coop/membership_resignation_form.html"

    def get_context_data(self, **kwargs):
        if not FeatureFlag.get_flag_value(feature_flag_membership_resignation):
            raise PermissionDenied("The membership resignation feature is disabled.")

        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Resign a new membership")
        context_data["card_title"] = context_data["page_title"]
        return context_data

    @transaction.atomic
    def form_valid(self, form):
        result = super().form_valid(form)
        membership_resignation: MembershipResignation = form.instance
        MembershipResignationService.update_shifts_and_shares_and_pay_out_day(
            resignation=membership_resignation, actor=self.request.user
        )
        MembershipResignationService.update_membership_pauses(membership_resignation)
        MembershipResignationCreateLogEntry().populate(
            actor=self.request.user,
            model=membership_resignation,
        ).save()
        email_builder_resignation_confirmation = MembershipResignationConfirmation(
            membership_resignation=membership_resignation
        )
        SendMailService.send_to_share_owner(
            actor=self.request.user,
            recipient=membership_resignation.share_owner,
            email_builder=email_builder_resignation_confirmation,
        )
        if (
            membership_resignation.resignation_type
            == MembershipResignation.ResignationType.TRANSFER
        ):
            email_builder_transfer_confirmation = (
                MembershipResignationTransferredSharesConfirmation(
                    member_resignation=membership_resignation
                )
            )
            SendMailService.send_to_share_owner(
                actor=self.request.user,
                recipient=membership_resignation.transferring_shares_to,
                email_builder=email_builder_transfer_confirmation,
            )

        if (
            form.cleaned_data["set_member_status_investing"]
            == MembershipResignationForm.SetMemberStatusInvestingChoices.MEMBER_BECOMES_INVESTING
        ):
            self.switch_member_to_investing(membership_resignation.share_owner)
        return result

    def switch_member_to_investing(self, share_owner: ShareOwner):
        if share_owner.is_investing:
            return

        with transaction.atomic():
            old_frozen = freeze_for_log(share_owner)
            share_owner.is_investing = True
            share_owner.save()
            new_frozen = freeze_for_log(share_owner)

            UpdateShareOwnerLogEntry().populate(
                old_frozen=old_frozen,
                new_frozen=new_frozen,
                share_owner=share_owner,
                actor=self.request.user,
            ).save()


class MembershipResignationDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    permission_required = PERMISSION_RESIGNATION_VIEW
    model = MembershipResignation

    def get(self, request, *args, **kwargs):
        if not FeatureFlag.get_flag_value(feature_flag_membership_resignation):
            raise PermissionDenied("The membership resignation feature is disabled.")

        return super().get(request, *args, **kwargs)


class MembershipResignationDeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DeleteView,
    UpdateViewLogMixin,
):
    model = MembershipResignation
    permission_required = PERMISSION_RESIGNATION_MANAGE
    success_url = reverse_lazy("coop:membership_resignation_list")

    def form_valid(self, form):
        with transaction.atomic():
            if not FeatureFlag.get_flag_value(feature_flag_membership_resignation):
                raise PermissionDenied(
                    "The membership resignation feature is disabled."
                )

            with transaction.atomic():
                MembershipResignationService.on_resignation_deleted(self.get_object())
                MembershipResignationDeleteLogEntry().populate(
                    model=self.get_object(),
                    actor=self.request.user,
                ).save()
        return super().form_valid(form)
