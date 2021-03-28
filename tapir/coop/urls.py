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
    path("user/draft/", views.DraftUserListView.as_view(), name="draftuser_list"),
    path(
        "user/draft/create",
        views.DraftUserCreateView.as_view(),
        name="draftuser_create",
    ),
    path(
        "user/draft/<int:pk>/edit",
        views.DraftUserUpdateView.as_view(),
        name="draftuser_update",
    ),
    path(
        "user/draft/<int:pk>",
        views.DraftUserDetailView.as_view(),
        name="draftuser_detail",
    ),
    path(
        "user/draft/<int:pk>/delete",
        views.DraftUserDeleteView.as_view(),
        name="draftuser_delete",
    ),
]
