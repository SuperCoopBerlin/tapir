import django.contrib.auth.views as auth_views
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET

from tapir import settings
from tapir.accounts import pdfs
from tapir.accounts.config import feature_flag_open_door, cache_key_open_door
from tapir.core.models import FeatureFlag
from tapir.accounts.forms import (
    TapirUserForm,
    PasswordResetForm,
    EditUserLdapGroupsForm,
    TapirUserSelfUpdateForm,
    EditUsernameForm,
    OptionalMailsForm,
)
from tapir.accounts.models import (
    TapirUser,
    UpdateTapirUserLogEntry,
    OptionalMails,
)
from tapir.coop.emails.co_purchaser_updated_mail import CoPurchaserUpdatedMail
from tapir.coop.emails.tapir_account_created_email import (
    TapirAccountCreatedEmailBuilder,
)
from tapir.coop.pdfs import CONTENT_TYPE_PDF
from tapir.core.services.send_mail_service import SendMailService
from tapir.core.views import TapirFormMixin
from tapir.log.util import freeze_for_log
from tapir.log.views import UpdateViewLogMixin
from tapir.settings import (
    PERMISSION_ACCOUNTS_MANAGE,
    PERMISSION_ACCOUNTS_VIEW,
    PERMISSION_COOP_ADMIN,
    PERMISSION_GROUP_MANAGE,
    GROUP_VORSTAND,
)
from tapir.utils.shortcuts import (
    set_header_for_file_download,
    set_group_membership,
    get_group_members,
    get_admin_ldap_connection,
)
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tapir_user: TapirUser = self.object

        context["is_allowed_to_see_purchase_tracking"] = (
            tapir_user == self.request.user
            or self.request.user.has_perm(PERMISSION_GROUP_MANAGE)
        )

        return context


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
            new_co_purchaser = new_frozen.get("co_purchaser", None)
            old_co_purchaser = self.old_object_frozen.get("co_purchaser", None)
            new_co_purchaser_2 = new_frozen.get("co_purchaser_2", None)
            old_co_purchaser_2 = self.old_object_frozen.get("co_purchaser_2", None)
            if (
                new_co_purchaser
                and new_co_purchaser != old_co_purchaser
                or new_co_purchaser_2
                and new_co_purchaser_2 != old_co_purchaser_2
            ):
                email_builder = CoPurchaserUpdatedMail(tapir_user=form.instance)
                SendMailService.send_to_tapir_user(
                    actor=self.request.user,
                    recipient=form.instance,
                    email_builder=email_builder,
                )

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

    email_builder = TapirAccountCreatedEmailBuilder(tapir_user)
    SendMailService.send_to_tapir_user(
        actor=request.user, recipient=tapir_user, email_builder=email_builder
    )

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
        PERMISSION_COOP_ADMIN
    ):
        return HttpResponseForbidden(
            _("You can only look at your own barcode unless you have admin rights")
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
    permission_required = PERMISSION_GROUP_MANAGE

    def get_tapir_user(self) -> TapirUser:
        return get_object_or_404(TapirUser, pk=self.kwargs["pk"])

    def get_success_url(self):
        return self.get_tapir_user().get_absolute_url()

    def form_valid(self, form):
        tapir_user = self.get_tapir_user()
        old_frozen = freeze_for_log(tapir_user)
        old_frozen["groups"] = tapir_user.get_ldap_user().group_names
        old_frozen["groups"] = (
            "No group"
            if not old_frozen["groups"]
            else ", ".join(tapir_user.get_ldap_user().group_names)
        )

        for group_cn in settings.LDAP_GROUPS:
            set_group_membership([tapir_user], group_cn, form.cleaned_data[group_cn])

        tapir_user_with_new_groups = self.get_tapir_user()
        new_frozen = freeze_for_log(tapir_user_with_new_groups)
        new_frozen["groups"] = tapir_user_with_new_groups.get_ldap_user().group_names
        new_frozen["groups"] = (
            "No group"
            if not new_frozen["groups"]
            else ", ".join(self.get_tapir_user().get_ldap_user().group_names)
        )
        if old_frozen != new_frozen:
            UpdateTapirUserLogEntry().populate(
                old_frozen=old_frozen,
                new_frozen=new_frozen,
                tapir_user=tapir_user,
                actor=self.request.user,
            ).save()

        return super().form_valid(form)

    def raise_permission_error_if_necessary(self, group_cn):
        if group_cn != GROUP_VORSTAND:
            return

        if not self.request.user.has_perm(PERMISSION_COOP_ADMIN):
            raise PermissionDenied(
                "Only members of the Vorstand can add or remove someone to the vorstand group."
            )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "tapir_user": self.get_tapir_user(),
                "request_user": self.request.user,
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
    permission_required = PERMISSION_GROUP_MANAGE

    def get_template_names(self):
        return [
            "accounts/ldap_group_list.html",
            "accounts/ldap_group_list.default.html",
        ]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        groups_data = {}
        for group_cn in settings.LDAP_GROUPS:
            group_member_dns = get_group_members(get_admin_ldap_connection(), group_cn)
            usernames = [
                dn.split(",")[0].replace("uid=", "") for dn in group_member_dns
            ]
            group_members = list(
                TapirUser.objects.filter(username__in=usernames).prefetch_related(
                    "share_owner"
                )
            )
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

        tapir_user_before.get_ldap_user().connection.rename_s(
            tapir_user_before.build_ldap_dn(),
            f"uid={tapir_user_after.username}",
        )

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


class MailSettingsView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TapirFormMixin,
    generic.FormView,
):
    form_class = OptionalMailsForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["page_title"] = _("Notification settings for %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                self.get_tapir_user().share_owner, self.request.user
            )
        }
        context_data["card_title"] = _("Notification settings for %(name)s") % {
            "name": UserUtils.build_display_name_for_viewer(
                self.get_tapir_user().share_owner, self.request.user
            )
        }
        return context_data

    def get_permission_required(self):
        if self.request.user.pk == self.get_tapir_user().pk:
            return []
        return [PERMISSION_ACCOUNTS_MANAGE]

    def get_tapir_user(self) -> TapirUser:
        return get_object_or_404(TapirUser, pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tapir_user"] = self.get_tapir_user()
        return kwargs

    def get_success_url(self):
        return self.get_tapir_user().get_absolute_url()

    @transaction.atomic
    def form_valid(self, form):
        o = OptionalMails.objects.filter(user=self.get_tapir_user())
        o.delete()
        # Save selected optional mails
        for optional_mail_choices in form.fields["optional_mails"].choices:
            is_selected = (
                optional_mail_choices[0] in form.cleaned_data["optional_mails"]
            )
            OptionalMails.objects.create(
                user=self.get_tapir_user(),
                mail_id=optional_mail_choices[0],
                choice=is_selected,
            )
        return super().form_valid(form)
        

class OpenDoorView(generic.View):
    """Combined view for door opening control.
    
    POST: Trigger door opening (requires authentication and CSRF)
    GET: Check door status (no authentication required)
    """
    
    @method_decorator(login_required)
    def post(self, request):
        """POST endpoint to trigger door opening.

        Sets cache key 'open_door' to True with 10-second TTL.
        Requires authentication and CSRF protection.
        """
        if not FeatureFlag.get_flag_value(feature_flag_open_door):
            raise PermissionDenied("The door opening feature is disabled.")

        user = request.user
        if not hasattr(user, 'share_owner') or not user.share_owner:
            raise PermissionDenied("You must be a member to open the door.")

        # Set cache key with 10-second TTL
        cache.set(cache_key_open_door, True, 10)
        return HttpResponse(status=200)
    
    def get(self, request):
        """GET endpoint to check door status.
        
        Returns 200 if cache key is True, otherwise returns 403.
        No content is provided as this simplifies the use in ressource
        resticted environments like microcontrollers.
        Deletes the cache key after checking (one-time use).
        No authentication required.
        """
        if not FeatureFlag.get_flag_value(feature_flag_open_door):
            return HttpResponse(status=403)
        
        door_status = cache.get(cache_key_open_door)
        
        if door_status is not None:
            cache.delete(cache_key_open_door)
        
        if door_status is True:
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=403)


class OpenDoorPageView(LoginRequiredMixin, generic.TemplateView):
    """Page view for the open door button."""

    template_name = "accounts/open_door_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["is_member"] = (
            hasattr(user, "share_owner") and user.share_owner is not None
        )
        return context
