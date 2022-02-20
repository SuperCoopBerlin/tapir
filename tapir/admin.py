from django.contrib import admin


class TapirAdminSite(admin.AdminSite):
    def has_permission(self, request):
        """This function only controls whether the admin app can be accessed
        at all. Individual model access is controlled in the ModelAdmin instances.
        """
        return super().has_permission(request) or request.user.has_perm("shifts.manage")
