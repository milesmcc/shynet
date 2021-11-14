from django.contrib.auth import get_user_model
import factory
from factory.django import DjangoModelFactory
from .models import Service


class UserFactory(DjangoModelFactory):
    username = factory.Faker("user_name")
    email = factory.Faker("email")
    name = factory.Faker("name")

    @post_generation
    def password(self, create, extracted, **kwargs):
        password = (
            extracted
            if extracted
            else factory.Faker(
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
