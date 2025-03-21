from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.orders.service import order_services


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        delivery_id = request.data.get('delivery_id')
        if not delivery_id:
            Response(
                {"error": "Не указаны данные доставки или оплаты"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            order = order_services.OrderService.create_order(
                user=request.user,
                delivery_id=delivery_id
            )
            return Response(
                {"message": "Заказ успешно создан", "order_id": order.id},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"error": "Ошибка сервера"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
