from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    username = models.TextField(default=lambda: str(uuid.uuid4()), unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email

class Service(models.Model):
    ACTIVE = "AC"
    ARCHIVED = "AR"
    SERVICE_STATUSES = [(ACTIVE, "Active"), (ARCHIVED, "Archived")]

    uuid = models.UUIDField(primary_key=True)
    name = models.TextField(max_length=64)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owning_services")
    collaborators = models.ManyToManyField(User, related_name="collaborating_services")
    created = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True)
    status = models.CharField(max_length=2, choices=SERVICE_STATUSES, default=ACTIVE)
