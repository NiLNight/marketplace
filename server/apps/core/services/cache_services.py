import hashlib
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Сервис для управления кэшированием данных приложения.

    Предоставляет методы для создания ключей кэша, получения/сохранения данных и инвалидации кэша.
    """

    @staticmethod
    def build_cache_key(request, prefix: str) -> str:
        """
        Создает уникальный ключ кэша на основе параметров запроса.

        Args:
            request: HTTP-запрос, содержащий GET-параметры.
            prefix (str): Префикс для ключа кэша (например, 'product_list').

        Returns:
            str: Уникальный ключ кэша.
        """
        params = [
            f"{key}={value}"
            for key, value in sorted(request.GET.items())
            if key != 'page'
        ]
        # Создаем хеш из параметров
        params_str = "&".join(params)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:{params_hash}"

    @staticmethod
    def get_cached_data(key: str):
        """
        Получает данные из кэша по ключу.

        Args:
            key (str): Ключ кэша.

        Returns:
            Данные из кэша или None, если кэш пуст.
        """
        data = cache.get(key)
        logger.debug(f"Cache {'hit' if data else 'miss'} for key: {key}")
        return data

    @staticmethod
    def set_cached_data(key: str, data, timeout: int = 900):
        """
        Сохраняет данные в кэш.

        Args:
            key (str): Ключ кэша.
            data: Данные для сохранения.
            timeout (int, optional): Время жизни кэша в секундах (по умолчанию 15 минут).

        Returns:
            None: Метод не возвращает значения, только сохраняет данные в кэш.
        """
        cache.set(key, data, timeout)

    @staticmethod
    def invalidate_cache(prefix: str, pk: int = None):
        """
        Инвалидирует кэш по префиксу или конкретному ID.

        Args:
            prefix (str): Префикс ключа кэша (например, 'product_list').
            pk (int, optional): ID объекта для точечной инвалидации. По умолчанию None.

        Returns:
            None: Метод не возвращает значения, только инвалидирует кэш.
        """
        if pk:
            key = f"{prefix}:{pk}"
            cache.delete(key)
            logger.info(f"Invalidated cache for key: {key}")
        else:
            # Для Redis мы не можем использовать delete_pattern, поэтому просто удаляем конкретный ключ
            cache.delete(prefix)
            logger.info(f"Invalidated cache for key: {prefix}")

    # Специфичные методы для приложений

    @staticmethod
    def cache_product_list(request):
        """Кэширует список продуктов."""
        return CacheService.get_cached_data(CacheService.build_cache_key(request, prefix="product_list"))

    @staticmethod
    def cache_product_details(product_id: int):
        """Кэширует детали продукта."""
        return CacheService.get_cached_data(f"product_detail:{product_id}")

    @staticmethod
    def cache_order_list(request, user_id: int, status: str = None):
        """Кэширует список заказов пользователя."""
        key = f"order_list:{user_id}:{status or 'all'}"
        return CacheService.get_cached_data(CacheService.build_cache_key(request, prefix=key))

    @staticmethod
    def cache_order_detail(order_id: int, user_id: int):
        """Кэширует детали заказа."""
        return CacheService.get_cached_data(f"order_detail:{order_id}:{user_id}")

    @staticmethod
    def cache_review_list(product_id: int, request):
        """Кэширует список отзывов для продукта."""
        return CacheService.get_cached_data(CacheService.build_cache_key(request, prefix=f"reviews:{product_id}"))

    @staticmethod
    def cache_comment_list(review_id: int, request):
        """Кэширует список комментариев для отзыва."""
        return CacheService.get_cached_data(CacheService.build_cache_key(request, prefix=f"comments:{review_id}"))

    @staticmethod
    def cache_cart(user_id: int):
        """Кэширует содержимое корзины пользователя."""
        return CacheService.get_cached_data(f"cart:{user_id}")

    @staticmethod
    def cache_wishlist(user_id: int):
        """Кэширует список желаний пользователя."""
        return CacheService.get_cached_data(f"wishlist:{user_id}")

    @staticmethod
    def cache_user_profile(user_id: int):
        """Кэширует профиль пользователя."""
        return CacheService.get_cached_data(f"user_profile:{user_id}")

    @staticmethod
    def cache_delivery_list(user_id: int, request):
        """Кэширует список вариантов доставки для пользователя."""
        return CacheService.get_cached_data(CacheService.build_cache_key(request, prefix=f"delivery_list:{user_id}"))

    @staticmethod
    def cache_pickup_points_list(request, city: str = None):
        """Кэширует список пунктов выдачи."""
        return CacheService.get_cached_data(
            CacheService.build_cache_key(request, prefix=f"pickup_points:{city or 'all'}")
        )

    @staticmethod
    def cache_city_list(request):
        """Кэширует список городов."""
        return CacheService.get_cached_data(CacheService.build_cache_key(request, prefix="city_list"))
