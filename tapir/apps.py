from django.contrib.admin.apps import AdminConfig


class TapirAdminConfig(AdminConfig):
    default_site = "tapir.admin.TapirAdminSite"
