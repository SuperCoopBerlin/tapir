from django.urls import path

from tapir.welcomedesk import views

app_name = "welcomedesk"
urlpatterns = [
    path(
        "search",
        views.WelcomeDeskSearchView.as_view(),
        name="welcome_desk_search",
    ),
    path(
        "member/<int:pk>",
        views.WelcomeDeskShareOwnerView.as_view(),
        name="welcome_desk_share_owner",
    ),
    path(
        "api/search",
        views.SearchMemberForWelcomeDeskView.as_view(),
        name="search",
    ),
]
