from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, reverse, redirect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)
from rules.contrib.views import PermissionRequiredMixin

from analytics.models import Session, Hit
from core.models import Service, _default_api_token, RESULTS_LIMIT

from .forms import ServiceForm
from .mixins import DateRangeMixin


class DashboardView(LoginRequiredMixin, DateRangeMixin, ListView):
    model = Service
    template_name = "dashboard/pages/dashboard.html"
    paginate_by = settings.DASHBOARD_PAGE_SIZE

    def get_queryset(self):
        return Service.objects.filter(
            Q(owner=self.request.user) | Q(collaborators__in=[self.request.user])
        ).distinct()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        for service in data["object_list"]:
            service.stats = service.get_core_stats(
                self.get_start_date(), self.get_end_date()
            )

        return data


class ServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "dashboard/pages/service_create.html"
    permission_required = "core.create_service"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:service", kwargs={"pk": self.object.uuid})


class ServiceView(
    LoginRequiredMixin, PermissionRequiredMixin, DateRangeMixin, DetailView
):
    model = Service
    template_name = "dashboard/pages/service.html"
    permission_required = "core.view_service"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["script_protocol"] = "https://" if settings.SCRIPT_USE_HTTPS else "http://"
        data["stats"] = self.object.get_core_stats(data["start_date"], data["end_date"])
        data["RESULTS_LIMIT"] = RESULTS_LIMIT
        data["object_list"] = Session.objects.filter(
            service=self.get_object(),
            start_time__lt=self.get_end_date(),
            start_time__gt=self.get_start_date(),
        ).order_by("-start_time")[:10]
        return data


class ServiceUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = Service
    form_class = ServiceForm
    template_name = "dashboard/pages/service_update.html"
    permission_required = "core.change_service"
    success_message = "Your changes were saved successfully."

    def get_success_url(self):
        return reverse("dashboard:service", kwargs={"pk": self.object.uuid})

    def form_valid(self, *args, **kwargs):
        resp = super().form_valid(*args, **kwargs)
        cache.set(
            f"service_origins_{self.object.uuid}", self.object.origins, timeout=3600
        )
        cache.set(
            f"script_inject_{self.object.uuid}", self.object.script_inject, timeout=3600
        )
        return resp

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data["script_protocol"] = "https://" if settings.SCRIPT_USE_HTTPS else "http://"
        return data


class ServiceDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView
):
    model = Service
    form_class = ServiceForm
    template_name = "dashboard/pages/service_delete.html"
    permission_required = "core.delete_service"
    success_message = "The service was deleted successfully."

    def get_success_url(self):
        return reverse("dashboard:dashboard")


class ServiceSessionsListView(
    LoginRequiredMixin, PermissionRequiredMixin, DateRangeMixin, ListView
):
    model = Session
    template_name = "dashboard/pages/service_session_list.html"
    paginate_by = 20
    permission_required = "core.view_service"

    def get_object(self):
        return get_object_or_404(Service, pk=self.kwargs.get("pk"))

    def get_queryset(self):
        return Session.objects.filter(
            service=self.get_object(),
            start_time__lt=self.get_end_date(),
            start_time__gt=self.get_start_date(),
        ).order_by("-start_time")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["object"] = self.get_object()
        return data


class ServiceLocationsListView(
    LoginRequiredMixin, PermissionRequiredMixin, DateRangeMixin, ListView
):
    model = Hit
    template_name = "dashboard/pages/service_location_list.html"
    paginate_by = RESULTS_LIMIT
    permission_required = "core.view_service"

    def get_object(self):
        return get_object_or_404(Service, pk=self.kwargs.get("pk"))

    def get_queryset(self):
        hits = Hit.objects.filter(
            service=self.get_object(),
            start_time__lt=self.get_end_date(),
            start_time__gt=self.get_start_date(),
        )
        self.hit_count = hits.count()

        return (
            hits.values("location").annotate(count=Count("location")).order_by("-count")
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["object"] = self.get_object()
        data["hit_count"] = self.hit_count
        return data


class ServiceSessionView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Session
    template_name = "dashboard/pages/service_session.html"
    pk_url_kwarg = "session_pk"
    context_object_name = "session"
    permission_required = "core.view_service"

    def get_permission_object(self, **kwargs):
        return self.get_object().service

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["object"] = get_object_or_404(Service, pk=self.kwargs.get("pk"))
        return data


class RefreshApiTokenView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.api_token = _default_api_token()
        request.user.save()
        return redirect("account_change_password")
