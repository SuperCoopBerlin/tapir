from django.contrib import admin

from tapir.coop.models import ShareOwnership, DraftUser, ResignedMembership

admin.site.register(ShareOwnership)
admin.site.register(DraftUser)
admin.site.register(ResignedMembership)
