from django.contrib import admin

from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftTemplate,
    Shift,
    ShiftAttendanceTemplate,
)


class ShiftTemplateInline(admin.TabularInline):
    model = ShiftTemplate


@admin.register(ShiftTemplateGroup)
class ShiftTemplateGroupAdmin(admin.ModelAdmin):
    inlines = [ShiftTemplateInline]


class ShiftAttendanceTemplateInline(admin.TabularInline):
    model = ShiftAttendanceTemplate


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    inlines = [ShiftAttendanceTemplateInline]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    pass
