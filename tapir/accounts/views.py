import django.contrib.auth.views as auth_views
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET

from tapir import settings
from tapir.accounts import pdfs
from tapir.accounts.forms import (
    TapirUserForm,
    PasswordResetForm,
    EditUserLdapGroupsForm,
    TapirUserSelfUpdateForm,
    EditUsernameForm,
)
from tapir.accounts.models import (
    TapirUser,
    UpdateTapirUserLogEntry,
    LdapGroup,
    LdapPerson,
)
from tapir.coop.emails.tapir_account_created_email import TapirAccountCreatedEmail
from tapir.coop.pdfs import CONTENT_TYPE_PDF
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import (
    PERMISSION_ACCOUNTS_MANAGE,
    PERMISSION_ACCOUNTS_VIEW,
    PERMISSION_COOP_ADMIN,
)
from tapir.utils.shortcuts import set_header_for_file_download
from tapir.utils.user_utils import UserUtils


class TapirUserDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = TapirUser
    template_name = "accounts/user_detail.html"

    def get_permission_required(self):
        if self.request.user.pk == self.kwargs["pk"]:
            return []
        return [PERMISSION_ACCOUNTS_VIEW]


class TapirUserMeView(LoginRequiredMixin, generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("accounts:user_detail", args=[self.request.user.pk])


class TapirUserUpdateBaseView(
    LoginRequiredMixin,
    UpdateViewLogMixin,
    TapirFormMixin,
    generic.UpdateView,
):
    model = TapirUser

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            new_frozen = freeze_for_log(form.instance)
            if self.old_object_frozen != new_frozen:
                UpdateTapirUserLogEntry().populate(
                    old_frozen=self.old_object_frozen,
                    new_frozen=new_frozen,
                    tapir_user=form.instance,
                    actor=self.request.user,
                ).save()

            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        tapir_user: TapirUser = self.object
        context["page_title"] = _("Edit member: %(name)s") % {
            "name": UserUtils.build_display_name(
                tapir_user, UserUtils.DISPLAY_NAME_TYPE_FULL
            )
        }
        context["card_title"] = _("Edit member: %(name)s") % {
            "name": UserUtils.build_html_link(
                tapir_user, UserUtils.DISPLAY_NAME_TYPE_FULL
            )
        }
        return context


class TapirUserUpdateAdminView(TapirUserUpdateBaseView, PermissionRequiredMixin):
    permission_required = PERMISSION_ACCOUNTS_MANAGE
    form_class = TapirUserForm


class TapirUserUpdateSelfView(TapirUserUpdateBaseView, PermissionRequiredMixin):
    form_class = TapirUserSelfUpdateForm

    def get_permission_required(self):
        print(self.request.user.pk)
        print(self.kwargs["pk"])
        if self.request.user.pk == self.kwargs["pk"]:
            return []
        return [PERMISSION_ACCOUNTS_MANAGE]


class PasswordResetView(auth_views.PasswordResetView):
    # Form class to allow password reset despite unusable password in the db
    form_class = PasswordResetForm


@require_POST
@csrf_protect
@permission_required(PERMISSION_ACCOUNTS_MANAGE)
def send_user_welcome_email(request, pk):
    tapir_user = get_object_or_404(TapirUser, pk=pk)

    email = TapirAccountCreatedEmail(tapir_user)
    email.send_to_tapir_user(actor=request.user, recipient=tapir_user)

    messages.info(request, _("Account welcome email sent."))

    return redirect(tapir_user.get_absolute_url())


class UpdatePurchaseTrackingAllowedView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.RedirectView
):
    def has_permission(self):
        return self.request.user and self.request.user.pk == self.kwargs["pk"]

    def get_redirect_url(self, *args, **kwargs):
        return get_object_or_404(TapirUser, pk=self.kwargs["pk"]).get_absolute_url()

    def get(self, request, *args, **kwargs):
        tapir_user = get_object_or_404(TapirUser, pk=self.kwargs["pk"])

        old_frozen = freeze_for_log(tapir_user)
        tapir_user.allows_purchase_tracking = kwargs["allowed"] > 0
        new_frozen = freeze_for_log(tapir_user)

        with transaction.atomic():
            if old_frozen != new_frozen:
                UpdateTapirUserLogEntry().populate(
                    old_frozen=old_frozen,
                    new_frozen=new_frozen,
                    tapir_user=tapir_user,
                    actor=request.user,
                ).save()

            tapir_user.save()

        return super().get(request, args, kwargs)


@require_GET
@login_required
def member_card_barcode_pdf(request, pk):
    tapir_user = get_object_or_404(TapirUser, pk=pk)

    if request.user.pk != tapir_user.pk and not request.user.has_perm(
        PERMISSION_ACCOUNTS_MANAGE
    ):
        return HttpResponseForbidden(
            _(
                "You can only look at your own barcode unless you have member office rights"
            )
        )

    filename = "Member card barcode %s.pdf" % UserUtils.build_display_name_for_viewer(
        tapir_user, request.user
    )

    response = HttpResponse(content_type=CONTENT_TYPE_PDF)
    set_header_for_file_download(response, filename)

    pdf = pdfs.get_member_card_barcode_pdf(tapir_user)
    response.write(pdf.write_pdf())
    return response


class EditUserLdapGroupsView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TapirFormMixin,
    generic.FormView,
):
    form_class = EditUserLdapGroupsForm

    permission_required = PERMISSION_COOP_ADMIN

    def get_tapir_user(self) -> TapirUser:
        return get_object_or_404(TapirUser, pk=self.kwargs["pk"])

    def get_success_url(self):
        return self.get_tapir_user().get_absolute_url()

    def form_valid(self, form):
        user_dn = self.get_tapir_user().get_ldap().build_dn()
        for group_cn in settings.LDAP_GROUPS:
            group = LdapGroup.objects.get(cn=group_cn)

            if form.cleaned_data[group.cn] and user_dn not in group.members:
                group.members.append(user_dn)
                group.save()

            if not form.cleaned_data[group.cn] and user_dn in group.members:
                group.members.remove(user_dn)
                group.save()

        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "tapir_user": self.get_tapir_user(),
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["page_title"] = _("Edit member groups: %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                self.get_tapir_user(), self.request.user
            )
        }
        context["card_title"] = _("Edit member groups: %(name)s") % {
            "name": UserUtils.build_html_link_for_viewer(
                self.get_tapir_user(), self.request.user
            )
        }
        return context


class LdapGroupListView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView
):
    permission_required = PERMISSION_COOP_ADMIN

    def get_template_names(self):
        return [
            "accounts/ldap_group_list.html",
            "accounts/ldap_group_list.default.html",
        ]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        groups_data = {}
        for group_cn in settings.LDAP_GROUPS:
            group_members = []
            for ldap_person_dn in LdapGroup.objects.get(cn=group_cn).members:
                tapir_user_set = TapirUser.objects.filter(
                    username=LdapPerson.objects.get(dn=ldap_person_dn).uid
                )
                if tapir_user_set.exists():
                    group_members.append(tapir_user_set.first())
            group_members = sorted(
                group_members,
                key=lambda tapir_user: UserUtils.build_display_name_for_viewer(
                    tapir_user, self.request.user
                ),
            )
            groups_data[group_cn] = group_members

        context_data["groups"] = groups_data
        return context_data


class EditUsernameView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    form_class = EditUsernameForm
    model = TapirUser

    def get_target_user(self) -> TapirUser:
        return TapirUser.objects.get(pk=self.kwargs["pk"])

    def get_permission_required(self):
        if self.request.user.pk == self.get_target_user().pk:
            return []
        return [PERMISSION_ACCOUNTS_MANAGE]

    def get_template_names(self):
        return ["accounts/edit_username.html", "accounts/edit_username.default.html"]

    def form_valid(self, form):
        tapir_user_before = self.get_target_user()
        tapir_user_after: TapirUser = form.instance
        ldap_person = tapir_user_before.get_ldap()
        ldap_person.uid = tapir_user_after.username
        ldap_person.save()

        response = super().form_valid(form)

        old_frozen = freeze_for_log(tapir_user_before)
        new_frozen = freeze_for_log(tapir_user_after)
        if old_frozen != new_frozen:
            UpdateTapirUserLogEntry().populate(
                old_frozen=old_frozen,
                new_frozen=new_frozen,
                tapir_user=tapir_user_after,
                actor=self.request.user,
            ).save()

        return response
