from django.urls import path, include

from tapir.shifts import views

app_name = "shifts"
urlpatterns = [
    path(
        "upcoming/",
        views.UpcomingDaysView.as_view()
    ),
    # TODO(Leon Handreke): Can we somehow introduce a sub-namespace here?
    path("shift/<int:pk>/", views.ShiftDetailView.as_view(), name='shift_detail')
]
