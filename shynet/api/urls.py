from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.DashboardApiView.as_view(), name="services"),
]
