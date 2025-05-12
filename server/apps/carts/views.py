import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.carts.exceptions import CartItemNotFound
from apps.carts.services.cart_services import CartService
from apps.carts.serializers import CartItemSerializer
from apps.core.services.cache_services import CacheService
from apps.products.models import Product
from apps.carts.utils import handle_api_errors

logger = logging.getLogger(__name__)


class CartsGetView(APIView):
    """Получение содержимого корзины."""
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer

    @handle_api_errors
    def get(self, request):
        """Обрабатывает GET-запрос для получения содержимого корзины.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            Response: Ответ с данными корзины или ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if request.user.is_authenticated:
            cached_data = CacheService.cache_cart(user_id)
            if cached_data:
                return Response(cached_data)

        cart_items = CartService.get_cart(request)
        serializer = self.serializer_class(cart_items,
                                           many=True) if request.user.is_authenticated else self.serializer_class(
            [{'id': None, 'product': item['product'], 'quantity': item['quantity']} for item in cart_items], many=True
        )
        response_data = serializer.data
        if request.user.is_authenticated:
            cache_key = f"cart:{request.user.id}"
            CacheService.set_cached_data(cache_key, response_data, timeout=300)
        logger.info(f"Retrieved cart, user={user_id}, items={len(response_data)}")
        return Response(response_data)


class CartsAddView(APIView):
    """Добавление товара в корзину."""
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для добавления товара в корзину.

        Args:
            request (HttpRequest): Объект запроса с данными о товаре и количестве.

        Returns:
            Response: Ответ с сообщением об успешном добавлении или ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        product_id = int(request.data['product_id'])
        quantity = int(request.data.get('quantity', 1))
        CartService.add_to_cart(request, product_id, quantity)
        CacheService.invalidate_cache(prefix=f"cart", pk=user_id)
        logger.info(f"Added product {product_id} to cart, user={user_id}")
        return Response({"message": "Товар добавлен в корзину"}, status=status.HTTP_200_OK)


class CartsItemUpdateView(APIView):
    """Обновление количества товара в корзине."""
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer

    @handle_api_errors
    def patch(self, request, pk):
        """Обрабатывает PATCH-запрос для обновления количества товара в корзине.

        Args:
            request (HttpRequest): Объект запроса с новым количеством.
            pk (int): ID товара.

        Returns:
            Response: Ответ с обновленными данными или ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        quantity = int(request.data.get('quantity', 1))
        cart_item = CartService.update_cart_item(request, product_id=pk, quantity=quantity)
        if cart_item:
            product = Product.objects.select_related('category').get(id=cart_item['product_id'])
            serializer_data = {
                'id': cart_item.get('id'),
                'product': product,
                'quantity': cart_item['quantity']
            }
            serializer = self.serializer_class(serializer_data)
            CacheService.invalidate_cache(prefix=f"cart", pk=user_id)
            logger.info(f"Updated cart item {pk}, quantity={quantity}, user={user_id}")
            return Response(serializer.data)
        logger.warning(f"Cart item {pk} not found, user={user_id}")
        raise CartItemNotFound()


class CartsItemDeleteView(APIView):
    """Удаление товара из корзины."""
    permission_classes = [AllowAny]

    @handle_api_errors
    def delete(self, request, pk):
        """Обрабатывает DELETE-запрос для удаления товара из корзины.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): ID товара.

        Returns:
            Response: Подтверждение удаления или ошибка.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        success = CartService.remove_from_cart(request, product_id=pk)
        if success:
            CacheService.invalidate_cache(prefix=f"cart", pk=user_id)
            logger.info(f"Removed product {pk} from cart, user={user_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.warning(f"Product {pk} not found in cart, user={user_id}")
        raise CartItemNotFound()
