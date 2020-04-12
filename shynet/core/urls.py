from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("dash/", views.DashboardView.as_view(), name="dashboard"),
    path("dash/service/new/", views.ServiceCreateView.as_view(), name="service_create"),
    path("dash/service/<pk>/", views.ServiceView.as_view(), name="service"),
    path(
        "dash/service/<pk>/manage/",
        views.ServiceUpdateView.as_view(),
        name="service_update",
    ),
]
