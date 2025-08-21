import logging

import ldap
from django.contrib.auth.models import AbstractUser, UserManager, User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django_auth_ldap.backend import _LDAPUser, LDAPBackend
from django_auth_ldap.config import LDAPSearch
from ldap import modlist
from ldap.ldapobject import LDAPObject
from phonenumber_field.modelfields import PhoneNumberField

from tapir import utils, settings
from tapir.coop.config import get_ids_of_users_registered_to_a_shift_with_capability
from tapir.core.config import help_text_displayed_name
from tapir.log.models import UpdateModelLogEntry
from tapir.settings import (
    PERMISSIONS,
    REG_PERSON_BASE_DN,
    REG_PERSON_OBJECT_CLASSES,
    AUTH_LDAP_SERVER_URI,
)
from tapir.utils.models import CountryField
from tapir.utils.shortcuts import get_html_link, get_admin_ldap_connection
from tapir.utils.user_utils import UserUtils

log = logging.getLogger(__name__)


class TapirUserQuerySet(models.QuerySet):
    def registered_to_shift_slot_name(self, slot_name: str):
        return self.filter(
            shift_attendance_templates__slot_template__name=slot_name
        ).distinct()

    def registered_to_abcd_shift_slot_with_capability(self, capability: str):
        return self.filter(
            shift_attendance_templates__slot_template__required_capabilities__contains=[
                capability
            ]
        ).distinct()

    def registered_to_shift_slot_with_capability(self, capability: str):
        user_ids = get_ids_of_users_registered_to_a_shift_with_capability[0](capability)
        return self.filter(id__in=user_ids).distinct()

    def has_capability(self, capability: str):
        return self.filter(
            shift_user_data__capabilities__contains=[capability]
        ).distinct()


class TapirUserManager(UserManager.from_queryset(TapirUserQuerySet)):
    use_in_migrations = True


class TapirUser(AbstractUser):
    usage_name = models.CharField(
        _("Displayed name"),
        max_length=150,
        blank=True,
        help_text=_(help_text_displayed_name),
    )
    pronouns = models.CharField(_("Pronouns"), max_length=150, blank=True)
    phone_number = PhoneNumberField(_("Phone number"), blank=True)
    birthdate = models.DateField(_("Birthdate"), blank=True, null=True)
    street = models.CharField(_("Street and house number"), max_length=150, blank=True)
    street_2 = models.CharField(_("Extra address line"), max_length=150, blank=True)
    postcode = models.CharField(_("Postcode"), max_length=32, blank=True)
    city = models.CharField(_("City"), max_length=50, blank=True)
    country = CountryField(_("Country"), blank=True, default="DE")
    co_purchaser = models.CharField(_("Co-Purchaser"), max_length=150, blank=True)
    co_purchaser_mail = models.EmailField(_("Co-Purchaser mail"), blank=True)
    co_purchaser_2 = models.CharField(
        _("Second co-Purchaser"), max_length=150, blank=True
    )
    co_purchaser_2_mail = models.EmailField(_("Co-Purchaser mail 2"), blank=True)
    allows_purchase_tracking = models.BooleanField(
        _("Allow purchase tracking"), blank=False, null=False, default=False
    )
    excluded_fields_for_logs = ["password"]

    preferred_language = models.CharField(
        _("Preferred Language"),
        choices=utils.models.PREFERRED_LANGUAGES,
        default="de",
        max_length=16,
    )

    objects = TapirUserManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ldap_user = None
        self.__cached_perms = None
        self.client_perms = []

    def get_display_name(self, display_type):
        return UserUtils.build_display_name(self, display_type)

    def get_html_link(self, display_type):
        return get_html_link(
            url=self.get_absolute_url(), text=self.get_display_name(display_type)
        )

    def get_display_address(self):
        return UserUtils.build_display_address(
            self.street, self.street_2, self.postcode, self.city
        )

    def get_absolute_url(self):
        return reverse("accounts:user_detail", args=[self.pk])

    def get_permissions_display(self):
        user_perms = [perm for perm in PERMISSIONS if self.has_perm(perm)]
        if len(user_perms) == 0:
            return _("None")
        return ", ".join(user_perms)

    def get_groups_display(self):
        group_names = self.get_ldap_user().group_names
        if len(group_names) == 0:
            return _("None")
        return ", ".join(group_names)

    def has_perm(self, perm, obj=None):
        if perm in self.client_perms:
            return True

        if self.__cached_perms is None:
            self.__build_cached_perms()

        return self.__cached_perms.get(perm, False)

    def __build_cached_perms(self):
        self.__cached_perms = {}
        for (
            permission_name,
            groups_that_have_this_permission,
        ) in settings.PERMISSIONS.items():
            self.__cached_perms[permission_name] = (
                not groups_that_have_this_permission.isdisjoint(
                    self.get_ldap_user().group_names
                )
            )

    def get_member_number(self):
        if not hasattr(self, "share_owner") or not self.share_owner:
            return None

        return self.share_owner.get_member_number()

    def get_info(self):
        return self

    def get_is_company(self):
        if not hasattr(self, "share_owner") or not self.share_owner:
            return False

        return self.share_owner.get_is_company()

    def get_ldap_user(self) -> _LDAPUser | None:
        if self.ldap_user:
            return self.ldap_user

        search = LDAPSearch(
            "ou=people,dc=supercoop,dc=de", ldap.SCOPE_SUBTREE, f"(uid={self.username})"
        )
        result = search.execute(get_admin_ldap_connection())
        if not result:
            return None

        self.ldap_user = _LDAPUser(backend=LDAPBackend(), user=self)
        return self.ldap_user

    def build_ldap_dn(self):
        return f"uid={self.username},{REG_PERSON_BASE_DN}"

    def build_ldap_modlist(self):
        user_modlist = {
            "uid": [self.username],
            "sn": [self.last_name],
            "cn": [
                UserUtils.build_display_name(self, UserUtils.DISPLAY_NAME_TYPE_FULL)
            ],
            "mail": [self.email],
            "objectclass": REG_PERSON_OBJECT_CLASSES,
        }
        user_modlist = {
            key: [value_in_list.encode("utf-8") for value_in_list in value_list]
            for key, value_list in user_modlist.items()
        }  # Ldap expects byte-strings

        return user_modlist

    def create_ldap(self):
        connection = get_admin_ldap_connection()
        connection.add_s(
            self.build_ldap_dn(), modlist.addModlist(self.build_ldap_modlist())
        )

    def save(self, **kwargs):
        super().save(**kwargs)
        ldap_user = self.get_ldap_user()
        if ldap_user:
            self.get_ldap_user().connection.modify_s(
                self.build_ldap_dn(),
                modlist.modifyModlist(
                    self.build_ldap_modlist(), self.build_ldap_modlist()
                ),
            )
        else:
            self.create_ldap()

    def set_password(self, raw_password):
        # force null Django password (will use LDAP password)
        self.set_unusable_password()

        ldap_user = self.get_ldap_user()
        connection: LDAPObject = ldap_user.connection
        connection.passwd_s(self.build_ldap_dn(), None, raw_password)

    def check_password(self, raw_password):
        connection = ldap.initialize(AUTH_LDAP_SERVER_URI)
        try:
            connection.simple_bind_s(self.build_ldap_dn(), raw_password)
        except ldap.INVALID_CREDENTIALS:
            return False
        return True

    def clean(self):
        user_with_same_username = TapirUser.objects.filter(
            username__iexact=self.username
        ).first()
        if user_with_same_username is None:
            return
        if user_with_same_username.id == self.id:
            return
        # It is important to check case-insensitive because the ldap auth uses case-insensitive search to look for users.
        raise ValidationError({"username": _("This username is already taken.")})


class UpdateTapirUserLogEntry(UpdateModelLogEntry):
    template_name = "accounts/log/update_tapir_user_log_entry.html"
    excluded_fields = ["password"]

    def populate(
        self,
        old_frozen: dict,
        new_frozen: dict,
        tapir_user: TapirUser,
        actor: TapirUser | User,
    ):
        return super().populate_base(
            actor=actor,
            tapir_user=tapir_user,
            old_frozen=old_frozen,
            new_frozen=new_frozen,
        )


def language_middleware(get_response):
    def middleware(request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            translation.activate(user.preferred_language)
        response = get_response(request)
        translation.deactivate()
        return response

    return middleware


def get_optional_mail_choices_wrapper():
    from tapir.core.services.optional_mail_choices_service import (
        OptionalMailChoicesService,
    )

    return OptionalMailChoicesService.get_optional_mail_choices


class OptionalMails(models.Model):
    user = models.ForeignKey(
        "accounts.TapirUser",
        null=False,
        related_name="mail_setting",
        on_delete=models.CASCADE,
    )
    mail_id = models.CharField(
        max_length=256,
        blank=False,
        choices=get_optional_mail_choices_wrapper,
    )
    choice = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "mail_id"], name="user-mail-constraint"
            )
        ]
