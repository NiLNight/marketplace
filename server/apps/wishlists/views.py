import logging
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from apps.core.services.cache_services import CacheService
from apps.wishlists.serializers import WishlistItemSerializer
from apps.wishlists.services.wishlist_services import WishlistService
from apps.wishlists.utils import handle_api_errors

logger = logging.getLogger(__name__)


class WishlistGetView(APIView):
    """Получение списка желаний.

    Attributes:
        permission_classes: Классы разрешений для доступа (доступно всем).
        serializer_class: Класс сериализатора для преобразования данных списка желаний.
    """
    permission_classes = [AllowAny]
    serializer_class = WishlistItemSerializer

    @handle_api_errors
    def get(self, request):
        """Обрабатывает GET-запрос для получения списка желаний.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            Response: Ответ со списком элементов желаний или ошибкой.

        Raises:
            Exception: Если получение данных списка желаний не удалось (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if request.user.is_authenticated:
            cached_data = CacheService.cache_wishlist(user_id)
            if cached_data:
                return Response(cached_data)

        wishlist_items = WishlistService.get_wishlist(request)
        serializer = self.serializer_class(
            wishlist_items, many=True
        ) if request.user.is_authenticated else self.serializer_class(
            [{'id': None, 'product': item} for item in wishlist_items], many=True
        )
        response_data = serializer.data
        if request.user.is_authenticated:
            cache_key = f"wishlist:{request.user.id}"
            CacheService.set_cached_data(cache_key, response_data, timeout=300)
        logger.info(f"Retrieved wishlist, user={user_id}, items={len(response_data)}")
        return Response(response_data)


class WishlistAddView(APIView):
    """Добавление товара в список желаний.

    Attributes:
        permission_classes: Классы разрешений для доступа (доступно всем).
    """
    permission_classes = [AllowAny]

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для добавления товара в список желаний.

        Args:
            request (HttpRequest): Объект запроса с данными о товаре.

        Returns:
            Response: Ответ с сообщением об успешном добавлении или ошибкой.

        Raises:
            Exception: Если добавление товара не удалось из-за некорректных данных или других ошибок (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        product_id = int(request.data['product_id'])
        WishlistService.add_to_wishlist(request, product_id)
        CacheService.invalidate_cache(prefix=f"wishlist", pk=user_id)
        logger.info(f"Product {product_id} added to wishlist via API for user={user_id}, path={request.path}")
        return Response({"message": "Товар добавлен в список желаний"}, status=status.HTTP_200_OK)


class WishlistItemDeleteView(APIView):
    """Удаление товара из списка желаний.

    Attributes:
        permission_classes: Классы разрешений для доступа (доступно всем).
    """
    permission_classes = [AllowAny]

    @handle_api_errors
    def delete(self, request, pk):
        """Обрабатывает DELETE-запрос для удаления товара из списка желаний.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): ID товара для удаления.

        Returns:
            Response: Ответ с подтверждением удаления или ошибкой.

        Raises:
            Exception: Если удаление товара не удалось из-за других ошибок (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        WishlistService.remove_from_wishlist(request, product_id=pk)
        CacheService.invalidate_cache(prefix=f"wishlist", pk=user_id)
        logger.info(f"Product {pk} removed from wishlist via API for user={user_id}, path={request.path}")
        return Response(status=status.HTTP_204_NO_CONTENT)
