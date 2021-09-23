from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class ClientPermsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_anonymous:
            return
        if request.META.get("HTTP_X_SSL_CLIENT_VERIFY") != "SUCCESS":
            return

        if request.META["HTTP_X_SSL_CLIENT_S_DN"] in settings.CLIENT_PERMISSIONS.keys():
            request.user.client_perms = settings.CLIENT_PERMISSIONS[
                request.META["HTTP_X_SSL_CLIENT_S_DN"]
            ]
