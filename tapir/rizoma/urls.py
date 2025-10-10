from django.urls import path

from tapir.rizoma import views

app_name = "rizoma"
urlpatterns = [
  path(
        "shifts/all",
        views.RizomaAllShiftsView.as_view(),
        name="all_shifts",
    ),
]
