from django.apps import AppConfig
from django.contrib.postgres.signals import get_hstore_oids, register_type_handlers
from django.core.signals import request_started
from django.db import connections
from django.db.backends.base.base import NO_DB_ALIAS
from django.db.backends.signals import connection_created
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_link_groups
from tapir.settings import PERMISSION_COOP_MANAGE

HSTORE_CONNECTION_MARKER = "_tapir_hstore_registered_connection"


def ensure_hstore_type_handlers(connection) -> bool:
    """Register HStore adapters for the current raw PostgreSQL connection.

    A web process can open its connection before the migration that creates the
    HStore extension runs in another process. Django then caches the empty OID
    lookup. Retry the lookup until the extension exists and remember successful
    registration for the lifetime of the raw connection.
    """
    if connection.vendor != "postgresql" or connection.alias == NO_DB_ALIAS:
        return False

    raw_connection = connection.connection
    if raw_connection is None:
        return False
    if getattr(connection, HSTORE_CONNECTION_MARKER, None) is raw_connection:
        return True

    get_hstore_oids.cache_clear()
    oids, _ = get_hstore_oids(connection.alias)
    if not oids:
        return False

    register_type_handlers(connection)
    setattr(connection, HSTORE_CONNECTION_MARKER, raw_connection)
    return True


def ensure_hstore_on_connection_created(sender, connection, **kwargs):
    ensure_hstore_type_handlers(connection)


def ensure_hstore_for_open_connections(**kwargs):
    for connection in connections.all(initialized_only=True):
        ensure_hstore_type_handlers(connection)


class LogConfig(AppConfig):
    name = "tapir.log"

    def ready(self):
        self.register_sidebar_link_groups()
        self._register_db_signal_handlers()

    @staticmethod
    def register_sidebar_link_groups():
        sidebar_link_groups.get_group(_("Management")).add_link(
            display_name=_("Logs"),
            material_icon="manage_search",
            url=reverse_lazy("log:log_overview"),
            ordering=1,
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

    @staticmethod
    def _register_db_signal_handlers():
        connection_created.connect(
            ensure_hstore_on_connection_created,
            dispatch_uid="tapir.log.ensure_hstore_on_connection_created",
            weak=False,
        )
        request_started.connect(
            ensure_hstore_for_open_connections,
            dispatch_uid="tapir.log.ensure_hstore_for_open_connections",
            weak=False,
        )
        ensure_hstore_for_open_connections()
