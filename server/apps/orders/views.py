from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.services.cache_services import CacheService
from apps.orders.serializers import (
    OrderSerializer,
    OrderDetailSerializer
)
from apps.orders.services import order_services


class OrdersPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100
    page_size_query_param = 'page_size'


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
            CacheService.invalidate_cache(prefix=f"order_list:{request.user.id}")
            return Response(
                {"message": "Заказ успешно создан", "order_id": order.id},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"error": "Ошибка сервера"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = OrdersPagination

    def get(self, request):
        cache_key = CacheService.build_cache_key(request, prefix=f"order_list:{request.user.id}")
        cached_data = CacheService.get_cached_data(cache_key)
        if cached_data:
            return Response(cached_data)

        orders = order_services.OrderService.get_user_orders(user=request.user, request=request)

        # Пагинация
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)

        serializer = self.serializer_class(page, many=True)
        response_data = paginator.get_paginated_response(serializer.data).data
        CacheService.set_cached_data(cache_key, response_data, timeout=840)
        return Response(response_data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer

    def get(self, request, pk):
        cache_key = f"order_detail:{request.user.id}"
        cached_data = CacheService.get_cached_data(cache_key)
        if cached_data:
            return Response(cached_data)\

        order = order_services.OrderService.get_order_details(order_id=pk, user=request.user)
        serializer = self.serializer_class(order)
        CacheService.set_cached_data(cache_key, serializer.data, timeout=3600)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order_services.OrderService.cancel_order(order_id=pk, user=request.user)
        CacheService.invalidate_cache(prefix=f"order_detail:{pk}:{request.user.id}", pk=pk)
        CacheService.invalidate_cache(prefix=f"order_list:{request.user.id}")
        return Response('Заказ отменен', status=status.HTTP_200_OK)
