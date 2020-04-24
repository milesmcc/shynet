from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import Service, User
from allauth.account.admin import EmailAddress


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "link", "respect_dnt", "origins", "collaborators"]
        widgets = {
            "name": forms.TextInput(),
            "origins": forms.TextInput(),
            "respect_dnt": forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
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
            "respect_dnt": "Should visitors who have enabled <a href='https://en.wikipedia.org/wiki/Do_Not_Track'>Do Not Track</a> be excluded from all data?",
        }

    collaborators = forms.CharField(help_text="Which users should have read-only access to this service? (Comma separated list of emails.)", required=False)

    def clean_collaborators(self):
        collaborators = []
        for collaborator_email in self.cleaned_data["collaborators"].split(","):
            email = collaborator_email.strip()
            if email == "":
                continue
            collaborator_email_linked = EmailAddress.objects.filter(email__iexact=email).first()
            if collaborator_email_linked is None:
                raise forms.ValidationError(f"Email '{email}' is not registered")
            collaborators.append(collaborator_email_linked.user)
        return collaborators

    def get_initial_for_field(self, field, field_name):
        initial = super(ServiceForm, self).get_initial_for_field(field, field_name)
        if field_name == "collaborators":
            return ", ".join([user.email for user in (initial or [])])
        return initial
