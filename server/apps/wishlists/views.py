from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.services.cache_services import CacheService
from apps.wishlists.exceptions import ProductNotAvailable, WishlistItemNotFound
from apps.wishlists.serializers import WishlistItemSerializer
from apps.wishlists.services.wishlist_services import WishlistService


class WishlistAddView(APIView):
    permission_classes = [AllowAny]
    serializer_class = WishlistItemSerializer

    def post(self, request):
        try:
            product_id = int(request.data['product_id'])
            WishlistService.add_to_wishlist(request, product_id)
            CacheService.invalidate_cache(prefix=f"wishlist:{request.user.id}")
            return Response({"message": "Товар добавлен в список желаний"}, status=status.HTTP_200_OK)
        except (ValueError, TypeError):
            return Response({"error": "Некорректный ID товара"}, status=status.HTTP_400_BAD_REQUEST)
        except ProductNotAvailable as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WishlistItemDeleteView(APIView):
    """Представление для удаления товара из списка желаний."""
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        try:
            success = WishlistService.remove_from_wishlist(request, product_id=pk)
            if success:
                CacheService.invalidate_cache(prefix=f"wishlist:{request.user.id}")
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"error": "Товар не найден в списке желаний"}, status=status.HTTP_404_NOT_FOUND)
        except WishlistItemNotFound:
            return Response({"error": "Товар не найден в списке желаний"}, status=status.HTTP_404_NOT_FOUND)


class WishlistGetView(APIView):
    """Представление для получения списка желаний."""
    permission_classes = [AllowAny]
    serializer_class = WishlistItemSerializer

    def get(self, request):
        if request.user.is_authenticated:
            cache_key = f"wishlist:{request.user.id}"
            cached_data = CacheService.get_cached_data(cache_key)
            if cached_data:
                return Response(cached_data)

        wishlist_items = WishlistService.get_wishlist(request)
        serializer = self.serializer_class(wishlist_items, many=True) if request.user.is_authenticated else \
            self.serializer_class([{'id': None, 'product': item} for item in wishlist_items], many=True)
        response_data = serializer.data
        if request.user.is_authenticated:
            CacheService.set_cached_data(cache_key, response_data, timeout=300)
        return Response(response_data)
