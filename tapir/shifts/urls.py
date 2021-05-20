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
        "shift/<int:pk>/done",
        views.mark_shift_attendance_done,
        name="mark_shiftattendance_done",
    ),
    path(
        "shift/<int:pk>/missed",
        views.mark_shift_attendance_missed,
        name="mark_shiftattendance_missed",
    ),
    path(
        "shifttemplate/overview",
        views.ShiftTemplateOverview.as_view(),
        name="shift_template_overview",
    ),
    path(
        "shift/create",
        views.CreateShiftView.as_view(),
        name="shift_create",
    ),
    path(
        "shift/<int:pk>/register",
        views.register_user_to_shift,
        name="shift_register_user",
    ),
]
