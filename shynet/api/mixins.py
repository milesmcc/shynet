from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse

User = get_user_model()


class ApiTokenRequiredMixin:
    def _get_user_by_token(self, request):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Token "):
            return AnonymousUser()

        token = token.split(" ")[1]
        user: User = User.objects.filter(api_token=token).first()
        return user or AnonymousUser()

    def dispatch(self, request, *args, **kwargs):
        request.user = self._get_user_by_token(request)
        return (
            super().dispatch(request, *args, **kwargs)
            if request.user.is_authenticated
            else JsonResponse(data={}, status=HTTPStatus.FORBIDDEN)
        )
