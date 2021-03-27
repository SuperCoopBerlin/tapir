from django.urls import path

from tapir.coop import views

app_name = "coop"
urlpatterns = [
    path(
        "share/create/user/<int:user_pk>/",
        views.CoopShareOwnershipCreateView.as_view(),
        name="share_create",
    ),
    path(
        "share/update/<int:pk>/",
        views.CoopShareOwnershipUpdateView.as_view(),
        name="share_update",
    ),
]
