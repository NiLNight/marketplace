from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from apps.carts.services.cart_services import CartService
from apps.carts.serializers import CartItemSerializer
from apps.core.services.cache_services import CacheService
from apps.products.models import Product


class CartsAddView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer

    def post(self, request):
        """Добавление товара в корзину."""
        try:
            product_id = int(request.data.get('product_id'))
            quantity = int(request.data.get('quantity', 1))
            CartService.add_to_cart(request, product_id, quantity)
            CacheService.invalidate_cache(prefix=f"cart:{request.user.id}")
            return Response({"message": "Товар добавлен в корзину"})
        except ValidationError:
            return Response({'error': "Некорректное количество товара"})
        except (ValueError, TypeError) as e:
            return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({"error": "Товар не найден"}, status=404)


class CartsGetView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer

    def get(self, request):
        """Получение корзины."""
        if request.user.is_authenticated:
            cache_key = f"cart:{request.user.id}"
            cached_data = CacheService.get_cached_data(cache_key)
            if cached_data:
                return Response(cached_data)

        cart_items = CartService.get_cart(request)
        serializer = self.serializer_class(cart_items,
                                           many=True) if request.user.is_authenticated else self.serializer_class(
            [{'id': None, 'product': item['product'], 'quantity': item['quantity']} for item in cart_items], many=True
        )
        response_data = serializer.data
        if request.user.is_authenticated:
            CacheService.set_cached_data(cache_key, response_data, timeout=300)
        return Response(response_data)


class CartsItemUpdateView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer

    def patch(self, request, pk):
        quantity = int(request.data.get('quantity', 1))
        try:
            cart_item = CartService.update_cart_item(request, product_id=pk, quantity=quantity)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if cart_item:
            product = Product.objects.select_related('category').get(id=cart_item['product_id'])
            serializer_data = {
                'id': cart_item.get('id'),  # None для неавторизованных пользователей
                'product': product,
                'quantity': cart_item['quantity']
            }
            serializer = self.serializer_class(serializer_data)
            CacheService.invalidate_cache(prefix=f"cart:{request.user.id}")
            return Response(serializer.data)
        return Response({"error": "Товар не найден в корзине"}, status=status.HTTP_404_NOT_FOUND)


class CartsItemDeleteView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        success = CartService.remove_from_cart(request, product_id=pk)
        if success:
            CacheService.invalidate_cache(prefix=f"cart:{request.user.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Товар не найден в корзине"}, status=status.HTTP_404_NOT_FOUND)
