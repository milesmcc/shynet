import factory
from django.contrib.auth import get_user_model
from factory import post_generation
from factory.django import DjangoModelFactory

from .models import Service


class UserFactory(DjangoModelFactory):
    username = factory.Faker("user_name")
    email = factory.Faker("email")
    first_name = factory.Faker("name")

    @post_generation
    def password(self, create, extracted, **kwargs):
        password = (
            extracted
            or factory.Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )

        self.set_password(password)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]


class ServiceFactory(DjangoModelFactory):
    class Meta:
        model = Service

    name = factory.Faker("company")
