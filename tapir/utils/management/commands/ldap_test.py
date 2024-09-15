import ldap
from django.core.management.base import BaseCommand
from django_auth_ldap.config import LDAPSearch
from icecream import ic


class Command(BaseCommand):

    def handle(self, *args, **options):
        connection = ldap.initialize("ldap://openldap")
        bind_message = connection.bind("cn=admin,dc=supercoop,dc=de", "admin")
        bind_result = connection.result(bind_message)
        ic(bind_result)
        for scope in [
            ldap.SCOPE_SUBTREE,
            ldap.SCOPE_BASE,
            ldap.SCOPE_ONELEVEL,
            ldap.SCOPE_SUBORDINATE,
        ]:
            try:
                search = LDAPSearch(
                    "dc=supercoop,dc=de",
                    scope,
                )
                result = search.execute(connection)
                result = sorted([r[0] for r in result])
                ic(scope, result)
            except:
                ic("Failed", scope)
