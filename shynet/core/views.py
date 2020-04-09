from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = "core/pages/index.html"