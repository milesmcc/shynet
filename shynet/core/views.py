from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(TemplateView):
    template_name = "core/pages/index.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/pages/dashboard.html"
