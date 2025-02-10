"""
Кастомная аутентификация JWT с поддержкой cookies
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken


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
        public_paths = [
            '/api/register/',
            '/api/confirm-code/',
            '/api/resend-code/'
        ]
        if request.path in public_paths:
            return None

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
            user = self.get_user(validated_token)

            # Проверка активности пользователя
            if not user.is_active:
                raise AuthenticationFailed({
                    "detail": "Аккаунт не активирован",
                    "code": "user_inactive"
                })

            return user, validated_token
        except InvalidToken as e:
            raise AuthenticationFailed({
                "detail": f"Неверный токен: {str(e)}",
                "code": "token_invalid"
            })
