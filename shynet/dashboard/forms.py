from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "link", "origins", "respect_dnt", "collaborators"]
        widgets = {
            "name": forms.TextInput(),
            "origins": forms.TextInput(),
            "collaborators": forms.CheckboxSelectMultiple(),
            "respect_dnt": forms.RadioSelect(choices=[(True, "Yes"), (False, "No")])
        }
        labels = {
            "origins": "Allowed Hostnames",
            "respect_dnt": "Respect DNT",
        }
        help_texts = {
            "name": _("What should the service be called?"),
            "link": _("What's the service's primary URL?"),
            "origins": _(
                "At what hostnames does the service operate? This sets CORS headers, so use '*' if you're not sure (or don't care)."
            ),
            "respect_dnt": "Should visitors who have enabled <a href='https://en.wikipedia.org/wiki/Do_Not_Track'>Do Not Track</a> be excluded from all data?"
        }
