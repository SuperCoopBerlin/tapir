from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django_auth_ldap.backend import LDAPBackend


class CustomLdapBackend(LDAPBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)

        if user is None:
            messages.info(request, _("Invalid username or password"))

        return user
