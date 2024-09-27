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
        "frozen_members_json",
        views.FrozenMembersJsonView.as_view(),
        name="frozen_members_json",
    ),
    path(
        "co_purchasers_json",
        views.CoPurchasersJsonView.as_view(),
        name="co_purchasers_json",
    ),
    path(
        "financing_campaign_json/<int:pk>",
        views.FinancingCampaignJsonView.as_view(),
        name="financing_campaign_json",
    ),
    path(
        "update_purchase_data_manually",
        views.UpdatePurchaseDataManuallyView.as_view(),
        name="update_purchase_data_manually",
    ),
    path(
        "user/<int:pk>/basket_sum_evolution_json",
        views.BasketSumEvolutionJsonView.as_view(),
        name="basket_sum_evolution_json",
    ),
    path(
        "shift_cancelling_rate",
        views.ShiftCancellingRateView.as_view(),
        name="shift_cancelling_rate",
    ),
    path(
        "shift_cancelling_rate_json",
        views.ShiftCancellingRateJsonView.as_view(),
        name="shift_cancelling_rate_json",
    ),
    path(
        "shift_count_by_category_json",
        views.ShiftCountByCategoryJsonView.as_view(),
        name="shift_count_by_category_json",
    ),
]
