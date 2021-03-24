from django.contrib import admin

from tapir.shifts.models import ShiftTemplateGroup, ShiftTemplate, Shift


@admin.register(ShiftTemplateGroup)
class ShiftTemplateGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    pass


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    pass
