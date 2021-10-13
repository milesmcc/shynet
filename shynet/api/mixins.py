from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from .models import ApiToken


class ApiTokenRequiredMixin:
    def _get_user_by_token(self, request):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Token '):
            return AnonymousUser()

        token = token.split(' ')[1]
        api_token = ApiToken.objects.filter(value=token).first()
        if not api_token:
            return AnonymousUser()

        return api_token.user

    def dispatch(self, request, *args, **kwargs):
        request.user = self._get_user_by_token(request)
        if not request.user.is_authenticated:
            return JsonResponse(data={}, status=403)

        return super().dispatch(request, *args, **kwargs)
