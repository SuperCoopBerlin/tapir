from django.contrib import admin

from tapir.accounts.models import TapirUser


@admin.register(TapirUser)
class TapirUserAdmin(admin.ModelAdmin):
    list_display = ["username", "is_staff", "is_active", "email"]
    list_filter = ("is_staff", "is_active")
    search_fields = ["username", "first_name", "last_name", "email"]
