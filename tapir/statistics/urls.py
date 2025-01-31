from django.urls import path

from tapir.statistics import views
from tapir.statistics.views.available_colourblindness_types_view import (
    AvailableColourblindnessTypes,
)
from tapir.statistics.views.available_columns_view import AvailableColumnsView
from tapir.statistics.views.available_datasets_view import AvailableDatasetsView
from tapir.statistics.views.dataset_export_view import DatasetExportView
from tapir.statistics.views.dataset_graph_point_view import DatasetGraphPointView
from tapir.statistics.views.fancy_export_view import FancyExportView
from tapir.statistics.views.fancy_graph_view import FancyGraphView

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
        "fancy_graph",
        FancyGraphView.as_view(),
        name="fancy_graph",
    ),
    path(
        "fancy_export",
        FancyExportView.as_view(),
        name="fancy_export",
    ),
    path(
        "available_export_columns",
        AvailableColumnsView.as_view(),
        name="available_export_columns",
    ),
    path(
        "available_datasets",
        AvailableDatasetsView.as_view(),
        name="available_datasets",
    ),
    path(
        "export_dataset",
        DatasetExportView.as_view(),
        name="export_dataset",
    ),
    path(
        "graph_point",
        DatasetGraphPointView.as_view(),
        name="graph_point",
    ),
    path(
        "available_colourblindness_types",
        AvailableColourblindnessTypes.as_view(),
        name="available_colourblindness_types",
    ),
]
