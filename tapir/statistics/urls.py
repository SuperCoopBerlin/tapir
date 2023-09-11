from django.urls import path

from tapir.statistics import views

app_name = "statistics"
urlpatterns = [
    path(
        "main_statistics",
        views.MainStatisticsView.as_view(),
        name="main_statistics",
    ),
    path(
        "member_count_evolution_json",
        views.MemberCountEvolutionJsonView.as_view(),
        name="member_count_evolution_json",
    ),
    path(
        "new_members_per_month_json",
        views.NewMembersPerMonthJsonView.as_view(),
        name="new_members_per_month_json",
    ),
    path(
        "purchasing_members_json",
        views.PurchasingMembersJsonView.as_view(),
        name="purchasing_members_json",
    ),
    path(
        "working_members_json",
        views.WorkingMembersJsonView.as_view(),
        name="working_members_json",
    ),
]
