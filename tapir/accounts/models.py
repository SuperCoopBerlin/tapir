import logging

import ldap
import ldapdb.models
import ldapdb.models.fields as ldapdb_fields
import pyasn1.codec.ber.encoder
import pyasn1.type.namedtype
import pyasn1.type.univ
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager, User
from django.db import connections, router, models
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from tapir import utils
from tapir.accounts import validators
from tapir.coop.config import get_ids_of_users_registered_to_a_shift_with_capability
from tapir.core.config import help_text_displayed_name
from tapir.log.models import UpdateModelLogEntry
from tapir.settings import PERMISSIONS
from tapir.utils.models import CountryField
from tapir.utils.shortcuts import get_html_link
from tapir.utils.user_utils import UserUtils

log = logging.getLogger(__name__)


class LdapUser(AbstractUser):
    class Meta:
        abstract = True


class TapirUserQuerySet(models.QuerySet):
    def with_shift_attendance_mode(self, attendance_mode: str):
        return self.filter(shift_user_data__attendance_mode=attendance_mode)

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


class TapirUser(LdapUser):
    username_validator = validators.UsernameValidator()

    # Copy-pasted from django/contrib/auth/models.py to override validators
    username = models.CharField(
        _("Username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and ./-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

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

    def has_perm(self, perm, obj=None):
        # This is a hack to allow permissions based on client certificates. ClientPermsMiddleware checks the
        # certificate in the request and adds the extra permissions the user object, which is accessible here.
        if hasattr(self, "client_perms") and perm in self.client_perms:
            return True

        return super().has_perm(perm=perm, obj=obj)

    def get_permissions_display(self):
        user_perms = [perm for perm in PERMISSIONS if self.has_perm(perm)]
        if len(user_perms) == 0:
            return _("None")
        return ", ".join(user_perms)

    def get_groups_display(self):
        user_dn = self.get_ldap().build_dn()
        user_groups = [
            group.cn for group in LdapGroup.objects.all() if user_dn in group.members
        ]
        if len(user_groups) == 0:
            return _("None")
        return ", ".join(user_groups)

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


class UpdateTapirUserLogEntry(UpdateModelLogEntry):
    template_name = "accounts/log/update_tapir_user_log_entry.html"
    excluded_fields = ["password"]

    def populate(
        self,
        old_frozen: dict,
        new_frozen: dict,
        tapir_user: TapirUser,
        actor: User,
    ):
        return super().populate_base(
            actor=actor,
            tapir_user=tapir_user,
            old_frozen=old_frozen,
            new_frozen=new_frozen,
        )


# The following LDAP-related models were taken from
# https://source.puri.sm/liberty/host/middleware/-/blob/master/ldapregister/models.py
class LdapPerson(ldapdb.models.Model):
    """
    Class for representing an LDAP person entry.
    """

    class Meta:
        verbose_name = "LDAP person"
        verbose_name_plural = "LDAP people"

    # LDAP meta-data
    base_dn = settings.REG_PERSON_BASE_DN
    object_classes = settings.REG_PERSON_OBJECT_CLASSES

    # Minimal attributes
    uid = ldapdb_fields.CharField(db_column="uid", max_length=200, primary_key=True)
    cn = ldapdb_fields.CharField(db_column="cn", max_length=200)
    sn = ldapdb_fields.CharField(db_column="sn", max_length=200)
    mail = ldapdb_fields.CharField(db_column="mail", max_length=200)

    def __str__(self):
        return self.uid

    def __unicode__(self):
        return self.uid

    def change_password(self, raw_password, using=None):
        # dig into the ldapdb primitives
        using = using or router.db_for_write(self.__class__, instance=self)
        connection = connections[using]
        cursor = connection._cursor()

        # call pyldap_orm password modification
        cursor.connection.extop_s(PasswordModify(self.dn, raw_password))

    def check_password(self, raw_password, using=None):
        using = using or router.db_for_write(self.__class__, instance=self)
        conn_params = connections[using].get_connection_params()

        # This is copy-pasta from django-ldapdb/ldapdb/backends/ldap/base.py
        connection = ldap.ldapobject.ReconnectLDAPObject(
            uri=conn_params["uri"],
            retry_max=conn_params["retry_max"],
            retry_delay=conn_params["retry_delay"],
            bytes_mode=False,
        )
        options = conn_params["options"]
        for opt, value in options.items():
            if opt == "query_timeout":
                connection.timeout = int(value)
            elif opt == "page_size":
                self.page_size = int(value)
            else:
                connection.set_option(opt, value)
        if conn_params["tls"]:
            connection.start_tls_s()

        # After setting up the connection, we try to authenticate
        try:
            connection.simple_bind_s(self.dn, raw_password)
        except ldap.INVALID_CREDENTIALS:
            return False

        return True


# The following code taken from https://github.com/asyd/pyldap_orm/blob/master/pyldap_orm/controls.py
# Copyright 2016 Bruno Bonfils
# SPDX-License-Identifier: Apache-2.0 (no NOTICE file)


class PasswordModify(ldap.extop.ExtendedRequest):
    """
    Implements RFC 3062, LDAP Password Modify Extended Operation
    Reference: https://www.ietf.org/rfc/rfc3062.txt
    """

    def __init__(self, identity, new, current=None):
        self.requestName = "1.3.6.1.4.1.4203.1.11.1"
        self.identity = identity
        self.new = new
        self.current = current

    def encodedRequestValue(self):
        request = self.PasswdModifyRequestValue()
        request.setComponentByName("userIdentity", self.identity)
        if self.current is not None:
            request.setComponentByName("oldPasswd", self.current)
        request.setComponentByName("newPasswd", self.new)
        return pyasn1.codec.ber.encoder.encode(request)

    class PasswdModifyRequestValue(pyasn1.type.univ.Sequence):
        """
        PyASN1 representation of:
            PasswdModifyRequestValue ::= SEQUENCE {
            userIdentity    [0]  OCTET STRING OPTIONAL
            oldPasswd       [1]  OCTET STRING OPTIONAL
            newPasswd       [2]  OCTET STRING OPTIONAL }
        """

        componentType = pyasn1.type.namedtype.NamedTypes(
            pyasn1.type.namedtype.OptionalNamedType(
                "userIdentity",
                pyasn1.type.univ.OctetString().subtype(
                    implicitTag=pyasn1.type.tag.Tag(
                        pyasn1.type.tag.tagClassContext,
                        pyasn1.type.tag.tagFormatSimple,
                        0,
                    )
                ),
            ),
            pyasn1.type.namedtype.OptionalNamedType(
                "oldPasswd",
                pyasn1.type.univ.OctetString().subtype(
                    implicitTag=pyasn1.type.tag.Tag(
                        pyasn1.type.tag.tagClassContext,
                        pyasn1.type.tag.tagFormatSimple,
                        1,
                    )
                ),
            ),
            pyasn1.type.namedtype.OptionalNamedType(
                "newPasswd",
                pyasn1.type.univ.OctetString().subtype(
                    implicitTag=pyasn1.type.tag.Tag(
                        pyasn1.type.tag.tagClassContext,
                        pyasn1.type.tag.tagFormatSimple,
                        2,
                    )
                ),
            ),
        )


class LdapGroup(ldapdb.models.Model):
    """
    Class for representing an LDAP group entry.
    """

    class Meta:
        verbose_name = "LDAP group"
        verbose_name_plural = "LDAP groups"

    # LDAP meta-data
    base_dn = settings.REG_GROUP_BASE_DN
    object_classes = settings.REG_GROUP_OBJECT_CLASSES

    # LDAP group attributes
    cn = ldapdb_fields.CharField(db_column="cn", max_length=200, primary_key=True)
    description = ldapdb_fields.CharField(db_column="description", max_length=200)
    members = ldapdb_fields.ListField(db_column="member")

    def __str__(self):
        return self.cn

    def __unicode__(self):
        return self.cn


def language_middleware(get_response):
    def middleware(request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            translation.activate(user.preferred_language)
        response = get_response(request)
        translation.deactivate()
        return response

    return middleware
