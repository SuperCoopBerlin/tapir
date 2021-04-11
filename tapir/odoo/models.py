from __future__ import annotations

import xmlrpc.client

from django.conf import settings
from django.db import models

from tapir.accounts.models import TapirUser


class OdooAPI:
    """Class to handle Odoo API requests."""

    # Singleton instance
    _connection = None

    _common = None
    _uid = None
    _models = None

    @classmethod
    def get_connection(cls) -> OdooAPI:
        if cls._connection == None:
            cls._connection = __class__(
                settings.ODOO["BASE_URL"],
                settings.ODOO["DATABASE"],
                settings.ODOO["USERNAME"],
                settings.ODOO["PASSWORD"],
            )
        return cls._connection

    def __init__(self, base_url, db, user, password):
        """Initialize xmlrpc connection."""
        self._db = db
        self._username = user
        self._password = password

        self._common = xmlrpc.client.ServerProxy("{}xmlrpc/2/common".format(base_url))
        self._uid = self._common.authenticate(
            self._db, self._username, self._password, {}
        )
        self._models = xmlrpc.client.ServerProxy("{}xmlrpc/2/object".format(base_url))

    def fields_get(self, entity):
        fields = self._models.execute_kw(
            self._db,
            self._uid,
            self._password,
            entity,
            "fields_get",
            [],
            {"attributes": ["string", "help", "type"]},
        )
        return fields

    def search_count(self, entity, cond=[]):
        return self._models.execute_kw(
            self._db, self._uid, self._password, entity, "search_count", [cond]
        )

    def search_read(
        self, entity, cond=[], fields=[], limit=3500, offset=0, order="id ASC"
    ):
        fields_and_context = {
            "fields": fields,
            "limit": limit,
            "offset": offset,
            "order": order,
        }
        return self._models.execute_kw(
            self._db,
            self._uid,
            self._password,
            entity,
            "search_read",
            [cond],
            fields_and_context,
        )

    def write(self, entity, ids, fields):
        return self._models.execute_kw(
            self._db, self._uid, self._password, entity, "write", [ids, fields]
        )

    def create(self, entity, fields):
        return self._models.execute_kw(
            self._db, self._uid, self._password, entity, "create", [fields]
        )

    def execute(self, entity, method, ids, params={}):
        return self._models.execute_kw(
            self._db, self._uid, self._password, entity, method, [ids], params
        )


class OdooModel(models.Model):
    class Meta:
        abstract = True

    odoo_id = models.IntegerField(blank=False, null=False, unique=True)

    def get_absolute_url(self):
        # TODO(Leon Handreke): Is there a better way to build this?
        # TODO(Leon Handreke): This doesn't actually work yet, get site base URL using Sites framework
        return "{}web#model={}&id={}".format(
            settings.ODOO["BASE_URL"], self.odoo_model_name, self.odoo_id
        )

    def _odoo_get(self, fields):
        return OdooAPI.get_connection().search_read(
            self.odoo_model_name, cond=[["id", "=", str(self.odoo_id)]], fields=fields,
        )[0]

    def _odoo_get_field(self, field):
        return self._odoo_get([field])[field]

    @classmethod
    def _odoo_create(cls, fields):
        return OdooAPI.get_connection().create(cls.odoo_model_name, fields)

    def _odoo_write(self, fields):
        OdooAPI.get_connection().write(self.odoo_model_name, [self.odoo_id], fields)

    def _odoo_execute(self, method, params):
        OdooAPI.get_connection().execute(
            self.odoo_model_name, method, [self.odoo_id], params
        )


class OdooPartnerManager(models.Manager):
    def create_from_user(self, user):
        odoo_id = self.model._odoo_create(self.model._field_dict_from_user(user))
        return self.create(odoo_id=odoo_id, user=user)

    def create_from_draft_user(self, draft_user):
        odoo_id = self.model._odoo_create(self.model._field_dict_from_user(draft_user))
        return self.create(odoo_id=odoo_id)


class OdooPartner(OdooModel):
    objects = OdooPartnerManager()

    odoo_model_name = "res.partner"

    user = models.OneToOneField(
        TapirUser,
        blank=True,
        null=True,
        related_name="odoo_partner",
        on_delete=models.PROTECT,
    )

    @staticmethod
    def _field_dict_from_user(user):
        return {
            "firstname": user.first_name,
            "lastname": user.last_name,
            "street": user.street,
            "street2": user.street_2,
            "city": user.city,
            "zip": user.postcode,
            # TODO(Leon Handreke): Figure out the proper country code here or find a way to
            # let the server do the translation
            "country_id": 57,
            "website": user.get_absolute_url(),
        }

    def update_from_user(self):
        self._odoo_write(self._field_dict_from_user(self.user))

    def update_from_draft_user(self, draft_user):
        self._odoo_write(self._field_dict_from_user(draft_user))
