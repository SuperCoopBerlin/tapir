import django_auth_ldap
from django_auth_ldap.backend import LDAPBackend, _LDAPUser
from icecream import ic


class LoggingLdapBackend(LDAPBackend):
    def authenticate_ldap_user(self, ldap_user: _LDAPUser, password):
        result = super().authenticate_ldap_user(ldap_user, password)
        return ic(result)


def ldap_error(**kwargs):
    exception = kwargs["exception"]
    ic(
        kwargs,
        kwargs["exception"],
        dir(exception),
        exception.args,
    )


django_auth_ldap.backend.ldap_error.connect(ldap_error)
