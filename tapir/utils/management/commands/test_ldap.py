import ldap
from django.core.management.base import BaseCommand
from django_auth_ldap.config import LDAPSearch
from icecream import ic

from tapir.utils.shortcuts import get_admin_ldap_connection


class Command(BaseCommand):

    def handle(self, *args, **options):
        search = LDAPSearch(
            "ou=groups,dc=supercoop,dc=de",
            ldap.SCOPE_SUBTREE,
            filterstr="(objectClass=top)",
        )
        result = search.execute(get_admin_ldap_connection())
        if not result:
            ic("No results")
            return
        ic(result, result[0][1]._data)
