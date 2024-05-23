import django_tables2
import django_filters
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.utils.html import format_html
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.shortcuts import redirect
from tapir.core.config import TAPIR_TABLE_CLASSES, TAPIR_TABLE_TEMPLATE
from tapir.utils.user_utils import UserUtils
from tapir.core.templatetags.core import tapir_button_link_to_action
from tapir.settings import PERMISSION_COOP_MANAGE

from django_filters.views import FilterView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir.coop.forms import MembershipCancelForm
from tapir.core.views import TapirFormMixin
from tapir.coop.models import ResignedMembership, ResignMembershipCreateLogEntry, ResignMembershipUpdateLogEntry
from tapir.coop.services.ResignMemberService import ResignMemberService
from tapir.log.views import UpdateViewLogMixin
from tapir.log.util import freeze_for_log

from django.db import transaction


class ResignedShareOwnerTable(django_tables2.Table):
    class Meta: 
        model = ResignedMembership
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "share_owner",
            "cancellation_date",
            "cancellation_reason",
            "paid_out",
            "pay_out_day",
            ]
        sequence = [
            "share_owner",
            "cancellation_reason",
            "cancellation_date",
            "pay_out_day",
            "paid_out",            
            "add_buttons",
            ]
        order_by = "-cancellation_date"
        attrs = {"class": TAPIR_TABLE_CLASSES}
        empty_text = "No entries"
        default = "No entries"

    cancellation_reason = django_tables2.Column(
        attrs = {"td": {"class": "col-4 text-break"}} 
    )
    pay_out_day = django_tables2.DateColumn(
        attrs = {"td": {"class": "" }}
    )
    add_buttons = django_tables2.Column(
        empty_values=(),
        verbose_name="Actions",
        orderable=False,
        exclude_from_export=True,
        default = "No entries",
    )

    def before_render(self, request):
        self.request = request
    
    def render_share_owner(self, record: ResignedMembership):
        return UserUtils.build_html_link_for_viewer(
            record.share_owner, self.request.user
        )

    def value_share_owner(self, record: ResignedMembership):
        return record.share_owner.get_member_number()

    def render_cancellation_reason(self, record: ResignedMembership):
        return f"{record.cancellation_reason}"
    
    def render_pay_out_day(self, record: ResignedMembership):
        if record.willing_to_gift_shares_to_coop:
            return "Gifted " + chr(8594) + " coop"
        elif record.transfering_shares_to != None:
            return "Gifted " + chr(8594) + " member"
        return record.pay_out_day.strftime("%d/%m/%Y")

    def render_add_buttons(self, value, record: ResignedMembership):
        return format_html(
            "<a href='{}' class='{}'>{}</a>",
            # <form action='{}' method='{}'>{}</form>",
            reverse_lazy("coop:resignedmember_detail", args=[record.pk]),
            tapir_button_link_to_action(),
            format_html("<span class='material-icons'>edit</span>"),
            # reverse_lazy('coop:resign_member_remove', kwargs={'pk': record.pk}),
            # "POST",
            # format_html("<input type='hidden' name='csrfmiddlewaretoken' value='{}' />",
            #             csrf(html_request)['csrf_token']),
            # format_html("<button class='{}'><span class='material-icons'>cancel</span></button>",
            #             tapir_button_link_to_action(),
            #             ),
        )

class ResignedMemberFilter(django_filters.FilterSet):
    display_name = django_filters.CharFilter(
        method="display_name_filter", label=_("Search member"))
    paid_out = django_filters.BooleanFilter(widget=django_filters.widgets.BooleanWidget())

    class Meta:
        model = ResignedMembership
        fields = ["display_name", "paid_out"]

    @staticmethod
    def display_name_filter(queryset: ResignedMembership.ResignedMemberQuerySet, name, value: str):
        # if value.isdigit():
        #     return queryset.filter(id=int(value))
        return queryset.with_term(value).distinct()




class ResignedShareOwnersList(
    LoginRequiredMixin,
    FilterView,
    ExportMixin,
    SingleTableView,
):
    table_class = ResignedShareOwnerTable
    model = ResignedMembership
    template_name = "coop/resigned_members_list.html"
    export_formats = ["csv", "json"]
    filterset_class = ResignedMemberFilter

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["total_of_resigned_members"] = ResignedMembership.objects.count()
        # context_data["resigned_member"] = ResignedMembership.objects.filter(id=self.kwargs["pk"])
        return context_data

class ResignShareOwnerEditView(LoginRequiredMixin, 
    PermissionRequiredMixin,
    TapirFormMixin,
    UpdateViewLogMixin,
    UpdateView,
):
    model = ResignedMembership
    form_class = MembershipCancelForm
    permission_required = PERMISSION_COOP_MANAGE
    success_url = reverse_lazy("coop:resigned_members_list")

    # def get_form_kwargs(self):
    #     share_owner = super().get_share_owner() 
    #     kwargs = super(MembershipCancelForm, self).get_form_kwargs()
    #     kwargs.update({'share_owner': share_owner})
    #     return kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)    
        # share_owner = super().get_share_owner()    
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
            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                ResignMembershipUpdateLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    model=form.instance,
                    actor=self.request.user,
                ).save()

        return result
        
class ResignShareOwnerCreateView(LoginRequiredMixin, 
    PermissionRequiredMixin,
    TapirFormMixin,
    CreateView
):
    model = ResignedMembership
    form_class = MembershipCancelForm
    permission_required = PERMISSION_COOP_MANAGE
    success_url = reverse_lazy("coop:resigned_members_list")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Resign a new membership")
        context_data["card_title"] = context_data["page_title"]
        return context_data

    def form_valid(self, form):
        with transaction.atomic():
            result = super().form_valid(form)
            ResignMemberService.update_shifts_and_shares(form.instance)
            ResignMembershipCreateLogEntry().populate(
                actor=self.request.user,
                model=form.instance,
            ).save()
        return result

class ResignedShareOwnerDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    permission_required = PERMISSION_COOP_MANAGE
    model = ResignedMembership
        

class ResignedShareOwnerRemoveFromListView(
    LoginRequiredMixin, 
    PermissionRequiredMixin, 
    DeleteView
):
    model = ResignedMembership
    permission_required = PERMISSION_COOP_MANAGE
    success_url = reverse_lazy("coop:resigned_members_list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        ResignMemberService.delete_end_dates(self.object)
        self.object.delete()
        response = redirect(self.success_url)
        return response
        
