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


class WishlistAddView(APIView):
    """Добавление товара в список желаний."""
    permission_classes = [AllowAny]
    serializer_class = WishlistItemSerializer

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для добавления товара в список желаний.

        Args:
            request (HttpRequest): Объект запроса с данными о товаре.

        Returns:
            Response: Ответ с сообщением об успешном добавлении или ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        product_id = int(request.data['product_id'])
        WishlistService.add_to_wishlist(request, product_id)
        CacheService.invalidate_cache(prefix=f"wishlist:{request.user.id}")
        logger.info(f"Product {product_id} added to wishlist via API for user={user_id}, path={request.path}")
        return Response({"message": "Товар добавлен в список желаний"}, status=status.HTTP_200_OK)


class WishlistItemDeleteView(APIView):
    """Удаление товара из списка желаний."""
    permission_classes = [AllowAny]

    @handle_api_errors
    def delete(self, request, pk):
        """Обрабатывает DELETE-запрос для удаления товара из списка желаний.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): ID товара для удаления.

        Returns:
            Response: Ответ с подтверждением удаления или ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        WishlistService.remove_from_wishlist(request, product_id=pk)
        CacheService.invalidate_cache(prefix=f"wishlist:{request.user.id}")
        logger.info(f"Product {pk} removed from wishlist via API for user={user_id}, path={request.path}")
        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistGetView(APIView):
    """Получение списка желаний."""
    permission_classes = [AllowAny]
    serializer_class = WishlistItemSerializer

    @handle_api_errors
    def get(self, request):
        """Обрабатывает GET-запрос для получения списка желаний.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            Response: Ответ со списком элементов желаний или ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if request.user.is_authenticated:
            cache_key = f"wishlist:{request.user.id}"
            cached_data = CacheService.get_cached_data(cache_key)
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
            CacheService.set_cached_data(cache_key, response_data, timeout=300)
        return Response(response_data)
