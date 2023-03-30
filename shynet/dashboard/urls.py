from django.urls import path

from . import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("service/new/", views.ServiceCreateView.as_view(), name="service_create"),
    path("service/<pk>/", views.ServiceView.as_view(), name="service"),
    path(
        "service/<pk>/manage/",
        views.ServiceUpdateView.as_view(),
        name="service_update",
    ),
    path(
        "service/<pk>/delete/",
        views.ServiceDeleteView.as_view(),
        name="service_delete",
    ),
    path(
        "service/<pk>/sessions/",
        views.ServiceSessionsListView.as_view(),
        name="service_session_list",
    ),
    path(
        "service/<pk>/sessions/<session_pk>/",
        views.ServiceSessionView.as_view(),
        name="service_session",
    ),
    path(
        "service/<pk>/locations/",
        views.ServiceLocationsListView.as_view(),
        name="service_location_list",
    ),
    path(
        "api-token-refresh/",
        views.RefreshApiTokenView.as_view(),
        name="api_token_refresh",
    ),
]
