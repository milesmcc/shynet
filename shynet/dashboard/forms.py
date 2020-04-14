from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "link", "origins", "collaborators"]
        widgets = {
            "name": forms.TextInput(),
            "origins": forms.TextInput(),
            "collaborators": forms.CheckboxSelectMultiple(),
        }
        labels = {
            "origins": "Allowed Hostnames",
        }
        help_texts = {
            "name": _("What should the service be called?"),
            "link": _("What's the service's primary URL?"),
            "origins": _(
                "At what hostnames does the service operate? This sets CORS headers, so use '*' if you're not sure (or don't care)."
            ),
        }
