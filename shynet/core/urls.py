from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("dash/", views.DashboardView.as_view(), name="dashboard"),
]
