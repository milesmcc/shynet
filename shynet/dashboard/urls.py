from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

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
]
