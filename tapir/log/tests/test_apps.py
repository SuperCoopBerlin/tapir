from types import SimpleNamespace
from unittest.mock import call, patch

from django.db import OperationalError
from django.db.backends.base.base import NO_DB_ALIAS
from django.test import SimpleTestCase

from tapir.log.apps import (
    HSTORE_CONNECTION_MARKER,
    ensure_hstore_for_open_connections,
    ensure_hstore_type_handlers,
)


def postgres_connection():
    return SimpleNamespace(
        alias="default",
        connection=object(),
        vendor="postgresql",
    )


class TestEnsureHstoreTypeHandlers(SimpleTestCase):
    @patch("tapir.log.apps.register_type_handlers")
    @patch("tapir.log.apps.get_hstore_oids")
    def test_ignores_non_postgresql_connections(
        self, get_hstore_oids, register_type_handlers
    ):
        connection = SimpleNamespace(connection=object(), vendor="sqlite")

        self.assertFalse(ensure_hstore_type_handlers(connection))

        get_hstore_oids.cache_clear.assert_not_called()
        get_hstore_oids.assert_not_called()
        register_type_handlers.assert_not_called()

    @patch("tapir.log.apps.register_type_handlers")
    @patch("tapir.log.apps.get_hstore_oids")
    def test_ignores_django_no_database_connection(
        self, get_hstore_oids, register_type_handlers
    ):
        connection = postgres_connection()
        connection.alias = NO_DB_ALIAS

        self.assertFalse(ensure_hstore_type_handlers(connection))

        get_hstore_oids.cache_clear.assert_not_called()
        get_hstore_oids.assert_not_called()
        register_type_handlers.assert_not_called()

    @patch("tapir.log.apps.register_type_handlers")
    @patch("tapir.log.apps.get_hstore_oids")
    def test_retries_after_hstore_extension_becomes_available(
        self, get_hstore_oids, register_type_handlers
    ):
        connection = postgres_connection()
        get_hstore_oids.side_effect = [((), ()), ((1234,), (1235,))]

        self.assertFalse(ensure_hstore_type_handlers(connection))
        self.assertTrue(ensure_hstore_type_handlers(connection))
        self.assertTrue(ensure_hstore_type_handlers(connection))

        self.assertIs(
            connection.connection,
            getattr(connection, HSTORE_CONNECTION_MARKER),
        )
        self.assertEqual(2, get_hstore_oids.cache_clear.call_count)
        self.assertEqual(2, get_hstore_oids.call_count)
        register_type_handlers.assert_called_once_with(connection)

    @patch("tapir.log.apps.register_type_handlers")
    @patch("tapir.log.apps.get_hstore_oids", return_value=((1234,), (1235,)))
    def test_registers_again_for_a_reopened_raw_connection(
        self, get_hstore_oids, register_type_handlers
    ):
        connection = postgres_connection()

        self.assertTrue(ensure_hstore_type_handlers(connection))
        connection.connection = object()
        self.assertTrue(ensure_hstore_type_handlers(connection))

        self.assertEqual(2, get_hstore_oids.cache_clear.call_count)
        self.assertEqual(2, get_hstore_oids.call_count)
        self.assertEqual(
            [call(connection), call(connection)],
            register_type_handlers.call_args_list,
        )

    @patch("tapir.log.apps.register_type_handlers")
    @patch("tapir.log.apps.get_hstore_oids")
    def test_does_not_hide_database_errors(
        self, get_hstore_oids, register_type_handlers
    ):
        connection = postgres_connection()
        get_hstore_oids.side_effect = OperationalError("database unavailable")

        with self.assertRaises(OperationalError):
            ensure_hstore_type_handlers(connection)

        register_type_handlers.assert_not_called()

    @patch("tapir.log.apps.ensure_hstore_type_handlers")
    @patch("tapir.log.apps.connections.all")
    def test_rechecks_all_initialized_connections(self, all_connections, ensure_hstore):
        connections = [postgres_connection(), postgres_connection()]
        all_connections.return_value = connections

        ensure_hstore_for_open_connections()

        all_connections.assert_called_once_with(initialized_only=True)
        self.assertEqual(
            [call(connections[0]), call(connections[1])],
            ensure_hstore.call_args_list,
        )
