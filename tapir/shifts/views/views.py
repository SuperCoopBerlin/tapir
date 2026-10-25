import datetime
from typing import Any

import django_tables2
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.management import call_command
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.defaulttags import register
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    RedirectView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import FormView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from tapir.accounts.models import TapirUser
from tapir.core.config import (
    TAPIR_TABLE_CLASSES,
    TAPIR_TABLE_TEMPLATE,
)
from tapir.core.services.send_mail_service import SendMailService
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import (
    PERMISSION_ACCOUNTS_MANAGE,
    PERMISSION_COOP_MANAGE,
    PERMISSION_SHIFTS_MANAGE,
    PERMISSION_TEAMLEADERPAGE_MANAGE,
    PERMISSION_TEAMLEADERPAGE_VIEW,
    PERMISSION_WELCOMEDESK_VIEW,
)
from tapir.shifts.emails.teamleader_page_updated_email import TeamleaderPageUpdatedEmail
from tapir.shifts.forms import (
    CreateShiftAccountEntryForm,
    RecurringShiftWatchForm,
    ShiftUserDataForm,
    ShiftWatchForm,
    TeamleaderPageForm,
    UserCapabilityValidityForm,
)
from tapir.shifts.models import (
    SHIFT_ATTENDANCE_STATES,
    CapabilityTranslation,
    RecurringShiftWatch,
    Shift,
    ShiftAccountEntry,
    ShiftAttendance,
    ShiftSlot,
    ShiftTemplate,
    ShiftUserData,
    ShiftWatch,
    TeamleaderPageContent,
    TeamleaderPageContentStatus,
    UpdateShiftUserDataLogEntry,
    UserCapabilityValidity,
)
from tapir.shifts.services.shift_watch_creation_service import ShiftWatchCreator
from tapir.shifts.templatetags.shifts import shift_name_as_class
from tapir.utils.expection_utils import TapirException
from tapir.utils.user_utils import UserUtils


class SelectedUserViewMixin:
    """Mixin to allow passing a selected_user GET param to a view.

    This is useful to use a view in a for-somebody-else context, e.g. when going there
    from a user page. Often, this user will be passed on to a following view or modify
    the behavior of the view."""

    def get_selected_user(self):
        if "selected_user" in self.request.GET:
            return get_object_or_404(TapirUser, pk=self.request.GET["selected_user"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_user"] = self.get_selected_user()
        return context


class EditShiftUserDataView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateViewLogMixin,
    TapirFormMixin,
    UpdateView,
):
    permission_required = PERMISSION_SHIFTS_MANAGE
    model = ShiftUserData
    form_class = ShiftUserDataForm

    def get_initial(self):
        shift_user_data: ShiftUserData = self.get_object()
        return {
            "shift_partner": (
                shift_user_data.shift_partner.user.id
                if shift_user_data.shift_partner
                else None
            )
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"request_user": self.request.user})
        return kwargs

    def get_success_url(self):
        return self.object.user.get_absolute_url()

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)

        tapir_user = form.cleaned_data["shift_partner"]
        form.instance.shift_partner = tapir_user.shift_user_data if tapir_user else None
        form.instance.save()

        new_frozen = freeze_for_log(form.instance)
        if self.old_object_frozen != new_frozen:
            UpdateShiftUserDataLogEntry().populate(
                old_frozen=self.old_object_frozen,
                new_frozen=new_frozen,
                tapir_user=self.object.user,
                actor=self.request.user,
            ).save()

        return response

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        tapir_user: TapirUser = self.object.user
        context_data["page_title"] = _("Edit user shift data: %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                tapir_user, self.request.user
            )
        }
        context_data["card_title"] = _("Edit user shift data: %(name)s") % {
            "name": UserUtils.build_html_link_for_viewer(tapir_user, self.request.user)
        }
        return context_data


def get_shift_slot_names():
    shift_slot_names = (
        ShiftSlot.objects.filter(shift__start_time__gt=timezone.now())
        .values_list("name", flat=True)
        .distinct()
    )
    shift_slot_names = [
        (shift_name_as_class(name), _(name)) for name in shift_slot_names if name != ""
    ]
    shift_slot_names.append(("", _("General")))
    return shift_slot_names


@register.filter
def dictionary_get(dic, key):
    return dic[key] if key in dic else None


class UserShiftAccountLog(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "shifts/user_shift_account_log.html"

    def get_target_user(self) -> TapirUser:
        return TapirUser.objects.get(pk=self.kwargs["user_pk"])

    def get_permission_required(self):
        if self.request.user == self.get_target_user():
            return []
        return [PERMISSION_SHIFTS_MANAGE]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_target_user()
        context["user"] = user
        context["entries_data"] = [
            {
                "entry": entry,
                "balance_at_date": user.shift_user_data.get_account_balance(
                    at_date=entry.date
                ),
            }
            for entry in ShiftAccountEntry.objects.filter(user=user).order_by("-date")
        ]
        return context


class CreateShiftAccountEntryView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, CreateView
):
    model = ShiftAccountEntry
    form_class = CreateShiftAccountEntryForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_target_user(self) -> TapirUser:
        return TapirUser.objects.get(pk=self.kwargs["user_pk"])

    def form_valid(self, form):
        form.instance.user = self.get_target_user()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        tapir_user = self.get_target_user()
        context_data["page_title"] = _("Shift account: %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                tapir_user, self.request.user
            )
        }
        context_data["card_title"] = _(
            "Create manual shift account entry for: %(link)s"
        ) % {
            "link": UserUtils.build_html_link_for_viewer(tapir_user, self.request.user)
        }
        return context_data

    def get_success_url(self):
        return self.get_target_user().get_absolute_url()


class ShiftDetailView(LoginRequiredMixin, DetailView):
    model = Shift
    template_name = "shifts/shift_detail.html"
    context_object_name = "shift"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift: Shift = context["shift"]
        slots = (
            shift.slots.all()
            .annotate(
                is_occupied=Count(
                    "attendances",
                    filter=Q(
                        attendances__state__in=[
                            ShiftAttendance.State.PENDING,
                            ShiftAttendance.State.DONE,
                        ]
                    ),
                )
            )
            .prefetch_related("slot_template__attendance_template__user")
        )

        if shift.shift_template:
            self.get_past_shifts_data(shift.shift_template, context)

        for slot in slots:
            slot.can_self_register = slot.user_can_attend(self.request.user)
            slot.can_self_unregister = slot.user_can_self_unregister(self.request.user)
            slot.can_look_for_stand_in = slot.user_can_look_for_standin(
                self.request.user
            )

            slot.previous_attendances = ShiftAttendance.objects.filter(slot=slot)
            if slot.get_valid_attendance() is not None:
                slot.previous_attendances = slot.previous_attendances.exclude(
                    id=slot.get_valid_attendance().id
                )

        context["slots"] = slots
        context["attendance_states"] = ShiftAttendance.State
        context["NB_DAYS_FOR_SELF_UNREGISTER"] = Shift.NB_DAYS_FOR_SELF_UNREGISTER
        context["NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN"] = (
            Shift.NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN
        )
        context["SHIFT_ATTENDANCE_STATES"] = SHIFT_ATTENDANCE_STATES

        return context

    @staticmethod
    def get_past_shifts_data(shift_template: ShiftTemplate, context: dict = None):
        if context is None:
            context = {}
        past_shifts = (
            Shift.objects.filter(
                shift_template=shift_template, end_time__lt=timezone.now()
            )
            .annotate(
                valid_attendance_count=Count(
                    "slots__attendances",
                    filter=Q(
                        slots__attendances__state__in=[
                            ShiftAttendance.State.DONE,
                        ]
                    ),
                )
            )
            .order_by("start_time")
        )
        context["no_of_past_shifts"] = past_shifts.count()

        # Sum valid attendances for related shifts
        total_valid_attendances = sum(s.valid_attendance_count for s in past_shifts)

        context["total_valid_attendances"] = total_valid_attendances

        # Calculate total working hours
        total_hours = sum(
            (s.end_time - s.start_time).total_seconds()
            * s.valid_attendance_count
            / 3600
            for s in past_shifts
        )
        context["total_hours"] = round(total_hours)
        context["first_shift_date"] = past_shifts.first().start_time.date()
        return context


class ShiftDayPrintableView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "shifts/shift_day_printable.html"
    permission_required = PERMISSION_WELCOMEDESK_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        day = datetime.datetime.strptime(kwargs["day"], "%d-%m-%y").date()
        context["shifts"] = Shift.objects.filter(start_time__date=day).order_by(
            "start_time"
        )
        return context


class ShiftTemplateDetail(LoginRequiredMixin, SelectedUserViewMixin, DetailView):
    template_name = "shifts/shift_template_detail.html"
    model = ShiftTemplate

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.prefetch_related(
            "slot_templates__attendance_template__user__share_owner"
        )


class ShiftUserDataTable(django_tables2.Table):
    class Meta:
        model = ShiftUserData
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "account_balance",
            "attendance_mode",
        ]
        sequence = (
            "display_name",
            "account_balance",
            "attendance_mode",
        )
        order_by = "account_balance"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    display_name = django_tables2.Column(
        empty_values=(), verbose_name="Name", orderable=False
    )
    email = django_tables2.Column(empty_values=(), orderable=False, visible=False)

    def before_render(self, request):
        self.request = request

    def render_display_name(self, value, record: ShiftUserData):
        return UserUtils.build_html_link_for_viewer(record.user, self.request.user)

    def value_display_name(self, value, record: ShiftUserData):
        return UserUtils.build_display_name_for_viewer(record.user, self.request.user)

    def value_email(self, value, record: ShiftUserData):
        return record.user.email


class MembersOnAlertView(
    LoginRequiredMixin, PermissionRequiredMixin, ExportMixin, SingleTableView
):
    table_class = ShiftUserDataTable
    model = ShiftUserData
    template_name = "shifts/members_on_alert_list.html"
    permission_required = PERMISSION_COOP_MANAGE

    export_formats = ["csv", "json"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("user")
            .annotate(account_balance=Sum("user__shift_account_entries__value"))
            .filter(account_balance__lt=-1)
            .order_by("user__date_joined")
        )


class ShiftManagementView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "shifts/shift_management.html"
    permission_required = PERMISSION_SHIFTS_MANAGE


class RunFreezeChecksManuallyView(
    LoginRequiredMixin, PermissionRequiredMixin, RedirectView
):
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_redirect_url(self, *args, **kwargs):
        return reverse("shifts:shift_management")

    def get(self, request, *args, **kwargs):
        call_command("run_freeze_checks")
        messages.info(request, _("Frozen statuses updated."))
        return super().get(request, args, kwargs)


class UnwatchShiftView(LoginRequiredMixin, RedirectView):
    def post(self, request, *args, **kwargs):
        shift = get_object_or_404(Shift, id=kwargs["shift"])
        ShiftWatch.objects.filter(user=request.user, shift=shift).delete()
        return redirect("shifts:shift_detail", pk=kwargs["shift"])


class WatchShiftView(LoginRequiredMixin, TapirFormMixin, CreateView):
    model = ShiftWatch
    form_class = ShiftWatchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Shift changes you would like to be informed about")
        context["card_title"] = _("Shift changes you would like to be informed about")
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "request_user": self.request.user,
            }
        )
        return kwargs

    def get_success_url(self):
        return reverse_lazy("shifts:shift_detail", args=[self.kwargs["shift"]])

    def form_valid(self, form):
        form.instance.shift = Shift.objects.get(id=self.kwargs["shift"])
        form.instance.user = self.request.user

        # set initial status to avoid initial notifications
        status = ShiftWatchCreator.get_initial_staffing_status_for_shift(
            shift=form.instance.shift
        )
        form.instance.last_staffing_status = status
        return super().form_valid(form)


class CreateRecurringShiftWatchView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, CreateView
):
    form_class = RecurringShiftWatchForm
    model = RecurringShiftWatch

    def get_permission_required(self):
        if self.request.user.pk == self.kwargs["pk"]:
            return []
        return [PERMISSION_ACCOUNTS_MANAGE]

    def get_success_url(self):
        user_pk = self.kwargs.get("pk")
        return reverse("shifts:shiftwatch_overview", args=[user_pk])

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        user = TapirUser.objects.get(pk=self.kwargs["pk"])
        context_data["page_title"] = _(
            "Create a rule for recurring shift watch for %(name)s"
        ) % {
            "name": UserUtils.build_display_name(user, UserUtils.DISPLAY_NAME_TYPE_FULL)
        }
        context_data["card_title"] = context_data["page_title"]
        context_data["help_text"] = _(
            "Please select either %(shift_template_group)s and/or weekdays, or alternatively %(shift_templates)s."
        ) % {
            "shift_template_group": context_data["form"]
            .fields["shift_template_group"]
            .label,
            "shift_templates": context_data["form"].fields["shift_templates"].label,
        }
        return context_data

    def form_valid(self, form):
        user_pk = self.kwargs.get("pk")
        form.instance.user = TapirUser.objects.get(pk=user_pk)

        response = super().form_valid(form)
        ShiftWatchCreator.create_shift_watches_for_recurring(form.instance)
        return response


class RecurringShiftwatchListView(LoginRequiredMixin, generic.ListView):

    template_name = "shifts/shiftwatch_overview.html"
    context_object_name = "recurringshiftwatches"

    def get_permission_required(self):
        if self.request.user.pk == self.kwargs["pk"]:
            return []
        return [PERMISSION_ACCOUNTS_MANAGE]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_pk = self.kwargs.get("pk")
        user = TapirUser.objects.get(pk=self.kwargs["pk"])
        context["tapir_user"] = user
        context["page_title"] = _("Recurring Shiftwatch List of %(name)s") % {
            "name": UserUtils.build_display_name(user, UserUtils.DISPLAY_NAME_TYPE_FULL)
        }
        context["card_title"] = _("Recurring Shiftwatch List of %(name)s") % {
            "name": UserUtils.build_display_name(user, UserUtils.DISPLAY_NAME_TYPE_FULL)
        }
        context["shift_watches"] = (
            ShiftWatch.objects.filter(
                user__id=user_pk, shift__end_time__gte=timezone.now()
            )
            .order_by("shift__start_time")
            .prefetch_related(
                "shift", "shift__shift_template", "shift__shift_template__group"
            )
        )
        return context

    def get_queryset(self):
        user_pk = self.kwargs.get("pk")
        return RecurringShiftWatch.objects.filter(user__id=user_pk)

    def post(self, request, *args, **kwargs):
        user_pk = kwargs.get("pk")
        selected_recurring_ids = request.POST.getlist("recurringshiftwatch_ids")
        selected_watch_ids = request.POST.getlist("shiftwatch_ids")

        RecurringShiftWatch.objects.filter(
            id__in=selected_recurring_ids, user__id=user_pk
        ).delete()

        ShiftWatch.objects.filter(id__in=selected_watch_ids, user__id=user_pk).delete()

        return redirect("shifts:shiftwatch_overview", pk=user_pk)


class TeamleaderPageTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    template_name = "shifts/teamleader_page.html"
    permission_required = [PERMISSION_TEAMLEADERPAGE_VIEW]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context_data = super().get_context_data(**kwargs)
        content_object = TeamleaderPageContent.objects.filter(
            status=TeamleaderPageContentStatus.LIVE
        ).first()
        if content_object is None:
            context_data["updated_on"] = timezone.now()
            context_data["page_content"] = _("No content published yet")
        else:
            context_data["updated_on"] = content_object.updated_on
            context_data["page_content"] = content_object.content
        return context_data


class TeamleaderPageEditView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "shifts/teamleader_page_edit.html"
    permission_required = [PERMISSION_TEAMLEADERPAGE_MANAGE]
    form_class = TeamleaderPageForm

    def get_success_url(self) -> str:
        return reverse("shifts:teamleader_page_edit")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        draft_content = TeamleaderPageContent.objects.filter(
            status=TeamleaderPageContentStatus.DRAFT
        ).first()
        kwargs.update({"draft_content": draft_content})
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context_data = super().get_context_data(**kwargs)

        self.add_content_context(
            status=TeamleaderPageContentStatus.LIVE, context_data=context_data
        )
        self.add_content_context(
            status=TeamleaderPageContentStatus.DRAFT, context_data=context_data
        )
        return context_data

    @classmethod
    def add_content_context(
        cls, status: TeamleaderPageContentStatus, context_data: dict
    ):
        page_object = TeamleaderPageContent.objects.filter(status=status).first()
        if page_object is None:
            return

        context = {
            "updated_by": page_object.updated_by,
            "updated_on": page_object.updated_on,
            "page_content": page_object.content,
        }

        context_data[status.value] = context

    def form_valid(self, form: TeamleaderPageForm) -> HttpResponse:
        if "save_draft" in form.data:
            self.save_content(
                form.data["draft_content"], status=TeamleaderPageContentStatus.DRAFT
            )
        elif "publish" in form.data:
            self.publish(form)
        else:
            raise TapirException("Unknown action in TeamleaderPageEditView")

        return super().form_valid(form)

    def save_content(self, content: str, status: TeamleaderPageContentStatus):
        content_object = TeamleaderPageContent.objects.filter(status=status).first()
        if content_object is None:
            content_object = TeamleaderPageContent(status=status)
        content_object.content = content
        content_object.updated_by = self.request.user
        content_object.save()

    def publish(self, form: TeamleaderPageForm):
        self.save_content(
            form.data["draft_content"], status=TeamleaderPageContentStatus.DRAFT
        )
        self.save_content(
            form.data["draft_content"], status=TeamleaderPageContentStatus.LIVE
        )

        for teamleader in TapirUser.objects.has_capability(
            CapabilityTranslation.objects.get(name="Teamleader").capability
        ):
            email_builder = TeamleaderPageUpdatedEmail()
            SendMailService.send_to_tapir_user(
                actor=self.request.user,
                recipient=teamleader,
                email_builder=email_builder,
            )


class UserCapabilityValidityTable(django_tables2.Table):
    """Tabelle für Gültigkeitszeiträume einer Capability."""

    class Meta:
        model = UserCapabilityValidity
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "id",
            "user_capability__shift_user_data__user",
            "user_capability__capability__get_current_translation__name",
            "start_date",
            "end_date",
        ]
        sequence = (
            "id",
            "user_capability__shift_user_data__user",
            "user_capability__capability__get_current_translation__name",
            "start_date",
            "end_date",
            "status",
            "actions",
        )
        order_by = "-start_date"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    user_capability__shift_user_data__user = django_tables2.Column(
        verbose_name=_("Member")
    )

    user_capability__capability__get_current_translation__name = django_tables2.Column(
        verbose_name=_("Qualification")
    )
    status = django_tables2.TemplateColumn(
        template_code='<span class="badge {{ record.user_capability.get_badge_class }}">{{ record.user_capability.get_status_label }}</span>',
        verbose_name="Status",
        orderable=False,
    )

    actions = django_tables2.TemplateColumn(
        template_code="""
            {% load core %}
            <a href="{% url "shifts:usercapabilityvalidity_delete" pk=record.pk %}"
                class="{% tapir_button_custom "outline-danger" %}">
                <span class="material-icons">delete</span>
            </a>
        """,
        verbose_name="Aktionen",
        orderable=False,
    )

    def before_render(self, request):
        self.request = request

    def render_user_capability__shift_user_data__user(
        self, value, record: UserCapabilityValidity
    ):
        return UserUtils.build_html_link_for_viewer(
            record.user_capability.shift_user_data.user, self.request.user
        )

    def render_start_date(self, value, record: UserCapabilityValidity):
        return record.start_date.strftime("%d.%m.%Y")

    def render_end_date(self, value, record: UserCapabilityValidity):
        return record.end_date.strftime("%d.%m.%Y")


class UserCapabilityValidityListView(
    LoginRequiredMixin,
    ExportMixin,
    SingleTableView,
):
    model = UserCapabilityValidity
    table_class = UserCapabilityValidityTable
    template_name = "shifts/usercapability_overview.html"
    context_object_name = "capabilities"

    def get_queryset(self):
        queryset = super().get_queryset()

        # Nur Gültigkeitszeiträume von Capabilities mit can_expire=True
        queryset = queryset.filter(
            user_capability__capability__capabilitytranslation__can_expire=True
        ).distinct()

        if not self.request.user.has_perm(PERMISSION_SHIFTS_MANAGE):
            queryset = queryset.filter(
                user_capability__shift_user_data__id=self.request.user.shift_user_data.id
            )

        shift_user_data_id = self.request.GET.get("shift_user_data_id", None)
        if shift_user_data_id is not None:
            queryset = queryset.filter(
                user_capability__shift_user_data__id=shift_user_data_id
            )

        return (
            queryset.select_related("user_capability__capability")
            .prefetch_related("user_capability__capability")
            .order_by("-start_date")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        shift_user_data_id = self.request.GET.get("shift_user_data_id", None)
        if shift_user_data_id is not None:
            shift_user_data = ShiftUserData.objects.get(pk=shift_user_data_id)
            context["shift_user_data"] = shift_user_data
            context["target_user"] = shift_user_data.user

            context["page_title"] = _("Expirable capabilities of %(name)s") % {
                "name": UserUtils.build_display_name(
                    shift_user_data.user, UserUtils.DISPLAY_NAME_TYPE_FULL
                )
            }
            context["card_title"] = _("Expirable capabilities of %(name)s") % {
                "name": UserUtils.build_display_name(
                    shift_user_data.user, UserUtils.DISPLAY_NAME_TYPE_FULL
                )
            }
        else:
            context["page_title"] = _("Expirable capabilities")
            context["card_title"] = _("Expirable capabilities")

        return context


class UserCapabilityValidityCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TapirFormMixin, CreateView
):
    model = UserCapabilityValidity
    form_class = UserCapabilityValidityForm
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift_user_data = get_object_or_404(ShiftUserData, pk=self.kwargs["pk"])

        context["title"] = _("Add Validity Period")
        context["page_title"] = _("Add validity period for: %(name)s") % {
            "name": UserUtils.build_display_name(
                shift_user_data.user, UserUtils.DISPLAY_NAME_TYPE_FULL
            )
        }
        context["card_title"] = _("Add validity period for: %(name)s") % {
            "name": UserUtils.build_display_name(
                shift_user_data.user, UserUtils.DISPLAY_NAME_TYPE_FULL
            )
        }
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        shift_user_data = get_object_or_404(ShiftUserData, pk=self.kwargs["pk"])
        kwargs["target_user"] = shift_user_data.user
        return kwargs

    def get_success_url(self):
        return reverse("shifts:usercapability_overview")


class UserCapabilityValidityDeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DeleteView,
    UpdateViewLogMixin,
):
    model = UserCapabilityValidity
    permission_required = PERMISSION_SHIFTS_MANAGE

    def get_success_url(self):
        return reverse("shifts:usercapability_overview")
