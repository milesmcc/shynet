from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import reverse, get_object_or_404
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    TemplateView,
    UpdateView,
    DeleteView,
    ListView,
)

from .forms import ServiceForm
from .mixins import BaseUrlMixin, DateRangeMixin
from .models import Service

from analytics.models import Session


class IndexView(TemplateView):
    template_name = "core/pages/index.html"


class DashboardView(LoginRequiredMixin, DateRangeMixin, TemplateView):
    template_name = "core/pages/dashboard.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["services"] = Service.objects.filter(owner=self.request.user)
        for service in data["services"]:
            service.stats = service.get_core_stats(data["start_date"], data["end_date"])
        return data


class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "core/pages/service_create.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ServiceView(LoginRequiredMixin, DateRangeMixin, DetailView):
    model = Service
    template_name = "core/pages/service.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["stats"] = self.object.get_core_stats(data["start_date"], data["end_date"])
        return data


class ServiceUpdateView(LoginRequiredMixin, BaseUrlMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = "core/pages/service_update.html"

    def get_success_url(self):
        return reverse("core:service", kwargs={"uuid": self.object.uuid})


class ServiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Service
    form_class = ServiceForm
    template_name = "core/pages/service_delete.html"

    def get_success_url(self):
        return reverse("core:dashboard")


class ServiceSessionsListView(LoginRequiredMixin, DateRangeMixin, ListView):
    model = Session
    template_name = "core/pages/service_session_list.html"
    paginate_by = 20

    def get_object(self):
        return get_object_or_404(Service, pk=self.kwargs.get("pk"))

    def get_queryset(self):
        return Session.objects.filter(
            service=self.get_object(),
            start_time__lt=self.get_end_date(),
            start_time__gt=self.get_start_date(),
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["object"] = self.get_object()
        return data


class ServiceSessionView(LoginRequiredMixin, DetailView):
    model = Session
    template_name = "core/pages/service_session.html"
    pk_url_kwarg = "session_pk"
    context_object_name = "session"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["object"] = get_object_or_404(Service, pk=self.kwargs.get("pk"))
        return data
