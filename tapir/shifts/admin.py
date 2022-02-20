from django.contrib import admin

from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftTemplate,
    Shift,
    ShiftAttendanceTemplate,
    ShiftAttendance,
    ShiftUserData,
    ShiftSlot,
    ShiftSlotTemplate,
)

admin.site.register(ShiftUserData)


class ShiftAdminPermissionMixin:
    def has_module_permission(self, request):
        return request.user.has_perm("shifts.manage")

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("shifts.manage")

    def has_add_permission(self, request, obj=None):
        return request.user.has_perm("shifts.manage")

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("shifts.manage")

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm("shifts.manage")


class ShiftTemplateInline(ShiftAdminPermissionMixin, admin.TabularInline):
    model = ShiftTemplate
    show_change_link = True
    extra = 3


@admin.register(ShiftTemplateGroup)
class ShiftTemplateGroupAdmin(ShiftAdminPermissionMixin, admin.ModelAdmin):
    inlines = [ShiftTemplateInline]


class ShiftSlotTemplateInline(ShiftAdminPermissionMixin, admin.TabularInline):
    model = ShiftSlotTemplate
    extra = 1


class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 0


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(ShiftAdminPermissionMixin, admin.ModelAdmin):
    inlines = [ShiftSlotTemplateInline, ShiftInline]


class ShiftAttendanceTemplateInline(admin.TabularInline):
    model = ShiftAttendanceTemplate
    extra = 1


@admin.register(ShiftSlotTemplate)
class ShiftSlotTemplateAdmin(ShiftAdminPermissionMixin, admin.ModelAdmin):
    inlines = [ShiftAttendanceTemplateInline]


class ShiftSlotInline(admin.TabularInline):
    model = ShiftSlot
    extra = 1


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    inlines = [ShiftSlotInline]
    list_display = ["name", "start_time", "end_time"]
    search_fields = ["name", "start_time", "end_time"]


class ShiftAttendanceInline(admin.TabularInline):
    model = ShiftAttendance
    extra = 1


@admin.register(ShiftSlot)
class ShiftSlotAdmin(admin.ModelAdmin):
    inlines = [ShiftAttendanceInline]
    list_display = ["name", "optional"]
    search_fields = ["name"]
