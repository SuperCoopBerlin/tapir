import django_tables2
import django_filters
from django.db import OperationalError, ProgrammingError
from django_filters import DateRangeFilter
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from django.utils.translation import gettext_lazy as _

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.log.forms import CreateTextLogEntryForm
from tapir.log.models import EmailLogEntry, TextLogEntry, LogEntry
from tapir.log.util import freeze_for_log
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
    user = TapirUser.objects.filter(pk=kwargs.get("user_pk")).first()
    share_owner = ShareOwner.objects.filter(pk=kwargs.get("shareowner_pk")).first()

    log_entry = TextLogEntry().populate(
        actor=request.user, user=user, share_owner=share_owner
    )

    form = CreateTextLogEntryForm(request.POST, instance=log_entry)

    if not form.is_valid():
        return HttpResponseBadRequest(str(form.errors))

    form.save()
    return safe_redirect(request.GET.get("next"), "/", request)


class LogTable(django_tables2.Table):
    entry = django_tables2.Column(
        empty_values=(), accessor="as_leaf_class__render", verbose_name="Message"
    )

    class Meta:
        model = LogEntry
        template_name = "django_tables2/bootstrap.html"
        fields = ["created_date", "actor", "user", "entry"]

    def render_actor(self, value):
        return value.get_display_name()


class LogFilter(django_filters.FilterSet):
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm("coop.view"):
            userfield_choices = [
                (
                    TapirUser.objects.get(username=self.request.user).id,
                    TapirUser.objects.get(
                        username=self.request.user
                    ).get_display_name(),
                )
            ]
        else:
            userfield_choices = [
                (
                    x,
                    TapirUser.objects.get(pk=x).get_display_name(),
                )
                for x in TapirUser.objects.all()
                .values_list("id", flat=True)
                .distinct()
                .order_by("username")
                if x is not None
            ]
        # First Method
        self.filters["user"].extra["choices"] = userfield_choices

    user = django_filters.ChoiceFilter(choices=[])  # choices depend on request
    time = DateRangeFilter(field_name="created_date")

    try:
        actorchoices = [
            (
                TapirUser.objects.get(pk=x).id,
                TapirUser.objects.get(pk=x).get_display_name(),
            )
            for x in LogEntry.objects.all().values_list("actor", flat=True).distinct()
            if x is not None
        ]
    except (OperationalError, ProgrammingError) as e:
        actorchoices = []

    actor = django_filters.ChoiceFilter(choices=actorchoices, label=_("Actor"))

    class Meta:
        model = LogEntry
        fields = ["time", "actor", "user"]


class LogTableView(SingleTableMixin, FilterView):
    model = LogEntry
    table_class = LogTable
    template_name = "log/log_overview.html"

    filterset_class = LogFilter

    def get_queryset(self):
        queryset = LogEntry.objects.all()
        if not self.request.user.has_perm("coop.view"):
            return queryset.filter(user=self.request.user)
        return queryset
