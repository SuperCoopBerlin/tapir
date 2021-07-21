from django.urls import path
from django.views import generic

from tapir.shifts import views

app_name = "shifts"
urlpatterns = [
    path(
        "",
        generic.RedirectView.as_view(pattern_name="shifts:shift_upcoming"),
        name="index",
    ),
    path("upcoming/", views.UpcomingDaysView.as_view(), name="shift_upcoming"),
    # TODO(Leon Handreke): Can we somehow introduce a sub-namespace here?
    path("shift/<int:pk>/", views.ShiftDetailView.as_view(), name="shift_detail"),
    path(
        "shift/create",
        views.CreateShiftView.as_view(),
        name="shift_create",
    ),
    path(
        "shiftslot/<int:pk>/register/<int:user_pk>",
        views.shiftslot_register_user,
        name="shiftslot_register_user",
    ),
    path(
        "shift/<int:pk>/edit",
        views.EditShiftView.as_view(),
        name="shift_edit",
    ),
    path(
        "shiftattendance/<int:pk>/done",
        views.mark_shift_attendance_done,
        name="mark_shiftattendance_done",
    ),
    path(
        "shiftattendance/<int:pk>/missed",
        views.mark_shift_attendance_missed,
        name="mark_shiftattendance_missed",
    ),
    path(
        "shifttemplate/overview",
        views.ShiftTemplateOverview.as_view(),
        name="shift_template_overview",
    ),
    path(
        "shifttemplate/overview/register/<int:user_pk>",
        views.ShiftTemplateOverviewRegister.as_view(),
        name="shift_template_overview_register",
    ),
    path(
        "shifttemplate/<int:pk>/register/<int:user_pk>",
        views.shifttemplate_register_user,
        name="shifttemplate_register_user",
    ),
    path(
        "shiftslottemplate/<int:pk>/unregister/<int:user_pk>",
        views.slottemplate_unregister_user,
        name="slottemplate_unregister_user",
    ),
    path(
        "timetable",
        views.UpcomingShiftsAsTimetable.as_view(),
        name="upcoming_timetable",
    ),
]
