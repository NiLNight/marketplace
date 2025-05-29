from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
import logging

logger = logging.getLogger(__name__)


class CustomJWTAuthentication(JWTAuthentication):
    """Кастомная аутентификация JWT с поддержкой cookies.

    Переопределяет стандартную аутентификацию для работы с токенами из cookies.

    Attributes:
        AUTH_HEADER_TYPES (tuple): Поддерживаемые типы заголовков аутентификации.
        AUTH_HEADER_NAME (str): Имя заголовка для токена аутентификации.
    """

    def authenticate(self, request):
        """Аутентификация пользователя.

        Проверяет наличие токена в заголовке Authorization или cookies.

        Args:
            request (HttpRequest): HTTP-запрос.

        Returns:
            tuple: Кортеж из объекта пользователя (User) и валидированного токена (Token), если аутентификация успешна.
            None: Если токен не предоставлен.

        Raises:
            AuthenticationFailed: Если токен недействителен или пользователь неактивен.
            InvalidToken: Если токен не может быть декодирован или истек срок его действия.
        """
        header = self.get_header(request)
        raw_token = None

        if header:
            raw_token = self.get_raw_token(header)
        else:
            # Если токен не найден в заголовке, проверяем cookies как альтернативный источник
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
        except InvalidToken:
            logger.error(f"Invalid token provided from IP={request.META.get('REMOTE_ADDR')}, "
                         f"User-Agent={request.META.get('HTTP_USER_AGENT')}")
            raise AuthenticationFailed({
                "detail": "Неверный токен",
                "code": "token_invalid"
            })
