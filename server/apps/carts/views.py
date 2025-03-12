from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.carts.services.cart_services import CartService
from apps.carts.serializers import CartItemSerializer
from apps.products.models import Product


class CartsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer

    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        try:
            cart_item = CartService.add_to_cart(request.user, product_id, quantity)
            serializer = self.serializer_class(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Product.DoesNotExist:
            return Response({"error": "Товар не найден"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Некорректное количество"}, status=status.HTTP_400_BAD_REQUEST)
