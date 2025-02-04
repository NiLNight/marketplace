"""
Кастомная аутентификация JWT с поддержкой cookies
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class CustomJWTAuthentication(JWTAuthentication):
    """
    Переопределенная аутентификация JWT:
    - Поддержка токенов из cookies
    - Кастомизация сообщений об ошибках
    """
    def authenticate(self, request):
        """
        Основной метод аутентификации:
        1. Проверка заголовка Authorization
        2. Проверка cookies
        """
        header = self.get_header(request)
        raw_token = None

        if header:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])

        if not raw_token:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except AuthenticationFailed as e:
            raise AuthenticationFailed({
                "detail": f"Authentication failed: {str(e)}"
            })