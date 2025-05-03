from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
import logging

logger = logging.getLogger(__name__)


class CustomJWTAuthentication(JWTAuthentication):
    """Кастомная аутентификация JWT с поддержкой cookies.

    Переопределяет стандартную аутентификацию для работы с токенами из cookies.
    """

    def authenticate(self, request):
        """Аутентификация пользователя.

        Проверяет наличие токена в заголовке Authorization или cookies.

        Args:
            request: HTTP-запрос.

        Returns:
            tuple: Пользователь и валидированный токен, если аутентификация успешна.

        Raises:
            AuthenticationFailed: Если токен недействителен или пользователь неактивен.
        """
        header = self.get_header(request)
        raw_token = None

        if header:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])

        if not raw_token:
            logger.debug("No token provided in request")
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)

            if not user.is_active:
                logger.warning(f"User {user.id} is inactive")
                raise AuthenticationFailed(
                    "Аккаунт деактивирован",
                    code="user_inactive"
                )

            logger.info(f"User {user.id} authenticated successfully")
            return user, validated_token
        except InvalidToken as e:
            logger.error(f"Invalid token: {str(e)}")
            raise AuthenticationFailed({
                "detail": f"Неверный токен: {str(e)}",
                "code": "token_invalid"
            })
