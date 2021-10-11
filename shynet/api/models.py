from django.db import models
from core.models import User
from secrets import token_urlsafe


def _default_token_value():
    return token_urlsafe(32)


class ApiToken(models.Model):
    name = models.CharField(max_length=64)
    value = models.TextField(default=_default_token_value, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_tokens")

    class Meta:
        ordering = ["name", "value"]

    def __str__(self):
        return self.name
