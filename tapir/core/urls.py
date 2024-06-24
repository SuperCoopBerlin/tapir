from django.urls import path

from tapir.core import views

app_name = "core"
urlpatterns = [
    path(
        "email_list",
        views.EmailListView.as_view(),
        name="email_list",
    ),
    path(
        "featureflag_list",
        views.FeatureFlagListView.as_view(),
        name="featureflag_list",
    ),
    path(
        "featureflag/<int:pk>/update",
        views.FeatureFlagUpdateView.as_view(),
        name="featureflag_update",
    ),
    path(
        "error",
        views.ErrorView.as_view(),
        name="error",
    ),
]
