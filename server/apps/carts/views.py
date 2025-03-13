from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from apps.carts.services.cart_services import CartService
from apps.carts.serializers import CartItemSerializer
from apps.products.models import Product


class CartsAddView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer

    def post(self, request):
        """Добавление товара в корзину."""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        try:
            CartService.add_to_cart(request, product_id, quantity)
            return Response({"message": "Товар добавлен в корзину"})
        except Product.DoesNotExist:
            return Response({"error": "Товар не найден"}, status=404)


class CartsGetView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer

    def get(self, request):
        """Получение корзины."""
        cart_items = CartService.get_cart(request)
        if request.user.is_authenticated:
            serializer = CartItemSerializer(cart_items, many=True)
        else:
            serializer = CartItemSerializer([{
                'id': None,
                'product': item['product'],
                'quantity': item['quantity']
            } for item in cart_items], many=True)
        return Response(serializer.data)


class CartsItemUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer

    def patch(self, request, pk):
        quantity = int(request.data.get('quantity', 1))
        cart_item = CartService.update_cart_item(request.user, product_id=pk, quantity=quantity)
        if cart_item:
            serializer = self.serializer_class(cart_item)
            return Response(serializer.data)
        return Response({"error": "Товар не найден в корзине"}, status=status.HTTP_404_NOT_FOUND)


class CartsItemDeleteView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        success = CartService.remove_from_cart(request, product_id=pk)
        if success:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Товар не найден в корзине"}, status=status.HTTP_404_NOT_FOUND)
