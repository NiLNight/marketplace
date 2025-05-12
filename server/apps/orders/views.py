import logging
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.services.cache_services import CacheService
from apps.orders.serializers import OrderSerializer, OrderDetailSerializer
from apps.orders.services.order_services import OrderService
from apps.orders.utils import handle_api_errors

logger = logging.getLogger(__name__)


class OrdersPagination(PageNumberPagination):
    """Класс пагинации для списка заказов."""
    page_size = 20
    max_page_size = 100
    page_size_query_param = 'page_size'


class OrderListView(APIView):
    """Представление для получения списка заказов пользователя."""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = OrdersPagination

    @handle_api_errors
    def get(self, request):
        """Обрабатывает GET-запрос для получения списка заказов.

        Args:
            request (HttpRequest): Объект запроса с параметрами фильтрации.

        Returns:
            Response: Ответ с данными заказов или ошибкой.
        """
        user_id = request.user.id
        cached_data = CacheService.cache_order_list(user_id, status=request.GET.get['status', None])
        if cached_data:
            return Response(cached_data)

        orders = OrderService.get_user_orders(user=request.user, request=request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)

        serializer = self.serializer_class(page, many=True)
        response_data = paginator.get_paginated_response(serializer.data).data
        cache_key = CacheService.build_cache_key(request, prefix=f"order_list:{user_id}")
        CacheService.set_cached_data(cache_key, response_data, timeout=840)  # 14 минут
        logger.info(f"Retrieved {len(orders)} orders for user={user_id}")
        return Response(response_data)


class OrderDetailView(APIView):
    """Представление для получения детальной информации о заказе."""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer

    @handle_api_errors
    def get(self, request, pk):
        """Обрабатывает GET-запрос для получения деталей заказа.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): Идентификатор заказа.

        Returns:
            Response: Ответ с данными заказа или ошибкой.
        """
        user_id = request.user.id
        cached_data = CacheService.cache_order_detail(pk, user_id)
        if cached_data:
            return Response(cached_data)

        order = OrderService.get_order_details(order_id=pk, user=request.user)
        serializer = self.serializer_class(order)
        response_data = serializer.data
        cache_key = f"order_detail:{pk}:{user_id}"
        CacheService.set_cached_data(cache_key, response_data, timeout=3600)  # 1 час
        logger.info(f"Order {pk} details retrieved for user={user_id}")
        return Response(response_data)


class OrderCreateView(APIView):
    """Представление для создания нового заказа."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для создания заказа из корзины.

        Args:
            request (HttpRequest): Объект запроса с данными о доставке.

        Returns:
            Response: Ответ с подтверждением создания заказа или ошибкой.
        """
        user_id = request.user.id
        delivery_id = request.data.get('delivery_id')
        if not delivery_id:
            logger.warning(f"Missing delivery_id for user={user_id}")
            return Response(
                {"error": "Не указаны данные доставки"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order = OrderService.create_order(user=request.user, delivery_id=delivery_id)
        CacheService.invalidate_cache(prefix=f"order_list:{user_id}")
        logger.info(f"Order {order.id} created successfully for user={user_id}")
        return Response(
            {"message": "Заказ успешно создан", "order_id": order.id},
            status=status.HTTP_201_CREATED
        )


class OrderCancelView(APIView):
    """Представление для отмены заказа."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request, pk):
        """Обрабатывает POST-запрос для отмены заказа.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): Идентификатор заказа.

        Returns:
            Response: Ответ с подтверждением отмены или ошибкой.
        """
        user_id = request.user.id
        OrderService.cancel_order(order_id=pk, user=request.user)
        CacheService.invalidate_cache(prefix=f"order_detail:{pk}", pk=user_id)
        CacheService.invalidate_cache(prefix=f"order_list:{user_id}")
        logger.info(f"Order {pk} cancelled successfully for user={user_id}")
        return Response({"message": "Заказ отменен"}, status=status.HTTP_200_OK)
