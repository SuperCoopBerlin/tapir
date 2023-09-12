from django.urls import path

from tapir.financingcampaign import views

app_name = "financingcampaign"
urlpatterns = [
    path(
        "general",
        views.FinancingCampaignGeneralView.as_view(),
        name="general",
    ),
    path(
        "create_campaign",
        views.FinancingCampaignCreateView.as_view(),
        name="create_campaign",
    ),
    path(
        "edit_campaign/<int:pk>",
        views.FinancingCampaignEditView.as_view(),
        name="edit_campaign",
    ),
    path(
        "delete_campaign/<int:pk>",
        views.FinancingCampaignDeleteView.as_view(),
        name="delete_campaign",
    ),
    path(
        "create_source",
        views.FinancingSourceCreateView.as_view(),
        name="create_source",
    ),
    path(
        "edit_source/<int:pk>",
        views.FinancingSourceEditView.as_view(),
        name="edit_source",
    ),
    path(
        "delete_source/<int:pk>",
        views.FinancingSourceDeleteView.as_view(),
        name="delete_source",
    ),
    path(
        "create_source_datapoint",
        views.FinancingSourceDatapointCreateView.as_view(),
        name="create_source_datapoint",
    ),
    path(
        "edit_source_datapoint/<int:pk>",
        views.FinancingSourceDatapointEditView.as_view(),
        name="edit_source_datapoint",
    ),
    path(
        "delete_source_datapoint/<int:pk>",
        views.FinancingSourceDatapointDeleteView.as_view(),
        name="delete_source_datapoint",
    ),
]
