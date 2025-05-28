from rest_framework.throttling import SimpleRateThrottle
import logging

logger = logging.getLogger(__name__)


class CeleryThrottle(SimpleRateThrottle):
    """
    Ограничение частоты запросов для отправки кода подтверждения.

    Ограничивает до 5 запросов в час на основе email или IP (для анонимных пользователей).
    """
    scope = 'verification_code'

    def __init__(self):
        super().__init__()
        self._request = None  # Атрибут для хранения request

    def get_cache_key(self, request, view):
        """
        Формирует ключ кэша на основе email или IP.

        Args:
            request: HTTP-запрос.
            view: Представление.

        Returns:
            str: Ключ кэша.
        """
        email = request.data.get('email', '').lower() or request.query_params.get('email', '').lower()
        user_id = request.user.id if request.user.is_authenticated else None
        if email:
            cache_key = f"throttle_verification_code_email_{email}"
        else:
            ident = request.META.get('REMOTE_ADDR', 'anonymous')
            cache_key = f"throttle_verification_code_ip_{ident}"

        logger.debug(f"Throttle cache key: {cache_key}, user_id={user_id or 'anonymous'}")
        return cache_key

    def get_rate(self):
        """
        Возвращает лимит частоты запросов.

        Returns:
            str: Лимит '5/hour'.
        """
        return '5/hour'

    def parse_rate(self, rate):
        """
        Парсит лимит частоты.

        Args:
            rate: Строка формата 'количество/период'.

        Returns:
            tuple: (количество, период в секундах).
        """
        num, period = super().parse_rate(rate)
        if period == 'hour':
            return num, 3600  # 1 час = 3600 секунд
        return num, period

    def allow_request(self, request, view):
        """
        Проверяет, разрешен ли запрос.

        Args:
            request: HTTP-запрос.
            view: Представление.

        Returns:
            bool: True, если запрос разрешен, иначе False.
        """
        self._request = request  # Сохраняем request для использования в throttle_failure
        if not super().allow_request(request, view):
            self.throttle_failure()  # Вызываем без аргумента для совместимости
            return False
        return True

    def throttle_failure(self):
        """
        Логирует превышение лимита.
        """
        request = self._request  # Используем сохранённый request
        email = request.data.get('email', '').lower() or request.query_params.get('email', '').lower()
        user_id = request.user.id if request.user.is_authenticated else None
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        logger.warning(
            f"Throttle limit exceeded for verification code, email={email or 'none'}, "
            f"user_id={user_id or 'anonymous'}, IP={ip}"
        )
