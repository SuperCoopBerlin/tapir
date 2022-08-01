import datetime

import django_filters
import django_tables2
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST
from django_filters import DateRangeFilter
from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.log.forms import CreateTextLogEntryForm
from tapir.log.models import EmailLogEntry, TextLogEntry, LogEntry
from tapir.log.util import freeze_for_log
from tapir.utils.filters import TapirUserModelChoiceFilter, ShareOwnerModelChoiceFilter
from tapir.utils.shortcuts import safe_redirect


@require_GET
@permission_required("coop.manage")
def email_log_entry_content(request, pk):
    log_entry = get_object_or_404(EmailLogEntry, pk=pk)
    filename = "tapir_email_{}_{}.eml".format(
        log_entry.user.username if log_entry.user else str(log_entry.share_owner.id),
        log_entry.created_date.strftime("%Y-%m-%d_%H-%M-%S"),
    )

    response = HttpResponse(content_type="application/octet-stream")
    response["Content-Disposition"] = 'filename="{}"'.format(filename)
    response.write(log_entry.email_content)
    return response


class UpdateViewLogMixin:
    def get_object(self, *args, **kwargs):
        result = super().get_object(*args, **kwargs)
        self.old_object_frozen = freeze_for_log(result)
        return result


@require_POST
@permission_required("coop.manage")
def create_text_log_entry(request, **kwargs):
    member_type = kwargs.get("member_type")
    member_id = kwargs.get("member_pk")

    if member_type == "tapir_user":
        member = TapirUser.objects.get(id=member_id)
        log_entry = TextLogEntry().populate(actor=request.user, user=member)
    else:
        member = ShareOwner.objects.get(id=member_id)
        log_entry = TextLogEntry().populate(actor=request.user, share_owner=member)

    form = CreateTextLogEntryForm(request.POST, instance=log_entry)

    if not form.is_valid():
        return HttpResponseBadRequest(str(form.errors))

    form.save()

    return safe_redirect(member.get_absolute_url(), "/", request)


class LogTable(django_tables2.Table):
    entry = django_tables2.Column(
        empty_values=(),
        accessor="as_leaf_class__render",
        verbose_name=_("Message"),
        orderable=False,
    )
    member = django_tables2.Column(
        empty_values=(), accessor="user", verbose_name=_("Member")
    )
    actor = django_tables2.Column(verbose_name=_("Actor"))

    class Meta:
        model = LogEntry
        template_name = "django_tables2/bootstrap.html"
        fields = ["created_date", "actor", "member", "entry"]

    def render_created_date(self, value: datetime.datetime):
        return value.strftime("%d.%m.%Y %H:%M")

    def render_member(self, record):
        # show user or share_owner, depending on what is available
        value = (
            record.user.share_owner if record.user is not None else record.share_owner
        )
        return format_html(
            "<a href={}>{}</a>",
            value.get_absolute_url(),
            value.get_info().get_display_name(),
        )

    def render_actor(self, value: TapirUser):
        return format_html(
            "<a href={}>{}</a>",
            value.get_absolute_url(),
            value.get_display_name(),
        )


class LogFilter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.request.user.has_perm("coop.view"):
            # In case the user who requests the Logs actually has permission, make a list of all ShareOwners
            share_owner_list = ShareOwner.objects.order_by("id")
        else:
            share_owner_list = ShareOwner.objects.filter(
                id=self.request.user.share_owner.id
            )
        self.filters["members"].field.queryset = share_owner_list
        self.filters["actor"].field.queryset = TapirUser.objects.filter(
            id__in=LogEntry.objects.all().values_list("actor", flat=True).distinct()
        )

    time = DateRangeFilter(field_name="created_date")
    actor = TapirUserModelChoiceFilter(label=_("Actor"))
    members = ShareOwnerModelChoiceFilter(method="member_filter", label=_("Member"))

    def member_filter(self, queryset: QuerySet, name, value: ShareOwner):
        # check if value is either in user or share_owner (can only be in one)
        return queryset.filter(
            Q(share_owner__id=value.id) | Q(user__share_owner=value.id)
        )

    class Meta:
        model = LogEntry
        fields = ["time", "actor", "members"]


class LogTableView(LoginRequiredMixin, FilterView, SingleTableView):
    model = LogEntry
    table_class = LogTable
    template_name = "log/log_overview.html"

    filterset_class = LogFilter

    def get_queryset(self):
        queryset = LogEntry.objects.all()
        if not self.request.user.has_perm("coop.view"):
            return queryset.filter(user=self.request.user)
        return queryset
