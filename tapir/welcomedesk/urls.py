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
        "api/search",
        views.SearchMemberForWelcomeDeskView.as_view(),
        name="search",
    ),
]
