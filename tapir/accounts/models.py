import logging

import ldap
import ldapdb.models
import pyasn1.codec.ber.encoder
import pyasn1.type.namedtype
import pyasn1.type.univ
from django.conf import settings
from django.db import connections, router
from ldapdb.models.fields import CharField, ListField
from django.contrib.auth.models import AbstractUser

log = logging.getLogger(__name__)


class LdapUser(AbstractUser):
    
    class Meta:
        abstract = True

    def get_ldap(self):
        return LdapPerson.objects.get(uid=self.get_username())

    def has_ldap(self):
        result = LdapPerson.objects.filter(uid=self.get_username())
        return len(result) == 1

    def create_ldap(self):
        username = self.username
        LdapPerson.objects.create(uid=username, sn=username, cn=username)

    def set_ldap_password(self, raw_password):
        ldap_person = self.get_ldap()
        ldap_person.change_password(raw_password)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # create LDAP user (if required)
        if not self.has_ldap():
            self.create_ldap()

        super(LdapUser, self).save(force_insert, force_update, using, update_fields)

        # force null Django password (will use LDAP password instead)
        self.set_unusable_password()

    def delete(self):
        self.get_ldap().delete()
        super(LdapUser, self).delete()

    def set_password(self, raw_password):

        # force null Django password (will use LDAP password)
        self.set_unusable_password()

        # create LDAP user (if required)
        if self.get_username():
            if not self.has_ldap():
                self.create_ldap()

            # set LDAP password
            self.set_ldap_password(raw_password)

    def check_password(self, raw_password):
        ldap_person = self.get_ldap()
        return True


class TapirUser(LdapUser):
    pass


# The following LDAP-related models were taken from https://source.puri.sm/liberty/host/middleware/-/blob/master/ldapregister/models.py
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
    uid = CharField(db_column="uid", max_length=200, primary_key=True)
    cn = CharField(db_column="cn", max_length=200)
    description = CharField(db_column="description", max_length=200)
    sn = CharField(db_column="sn", max_length=200)
    mail = CharField(db_column="mail", max_length=200)

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
