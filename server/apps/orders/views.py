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
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class OrdersPagination(PageNumberPagination):
    """
    Класс пагинации для списка заказов.

    Attributes:
        page_size: Количество элементов на странице (по умолчанию 20).
        max_page_size: Максимальное количество элементов на странице.
        page_size_query_param: Параметр запроса для установки размера страницы.
    """
    page_size = 20
    max_page_size = 100
    page_size_query_param = 'page_size'


class OrderListView(APIView):
    """
    Представление для получения списка заказов пользователя.

    Поддерживает пагинацию, кэширование и фильтрацию по статусу.

    Attributes:
        permission_classes: Требует аутентификации пользователя.
        serializer_class: Сериализатор для преобразования данных заказов.
        pagination_class: Пагинация с настраиваемым размером страницы.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = OrdersPagination

    @handle_api_errors
    def get(self, request):
        """
        Обрабатывает GET-запрос для получения списка заказов.

        Args:
            request (HttpRequest): Объект запроса с параметрами фильтрации.

        Returns:
            Response: Ответ с данными заказов или ошибкой.

        Raises:
            Exception: Если получение данных заказов не удалось (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id
        cached_data = CacheService.cache_order_list(request, user_id, request.GET.get('status', 'all'))
        if cached_data:
            logger.info(f"Retrieved cached orders for user={user_id}, "
                        f"path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(cached_data)

        orders = OrderService.get_user_orders(user=request.user, request=request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)

        serializer = self.serializer_class(page, many=True)
        response_data = paginator.get_paginated_response(serializer.data).data
        CacheService.set_cached_data(
            CacheService.build_cache_key(request, prefix=f"order_list:{user_id}:{request.GET.get('status', 'all')}"),
            response_data,
            timeout=60 * 15
        )  # 15 мин
        logger.info(f"Retrieved {len(orders)} orders for user={user_id}, "
                    f"path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
        return Response(response_data)


class OrderDetailView(APIView):
    """
    Представление для получения детальной информации о заказе.

    Поддерживает кэширование данных заказа.

    Attributes:
        permission_classes: Требует аутентификации пользователя.
        serializer_class: Сериализатор для преобразования данных заказа.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer

    @handle_api_errors
    def get(self, request, pk):
        """
        Обрабатывает GET-запрос для получения деталей заказа.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): Идентификатор заказа.

        Returns:
            Response: Ответ с данными заказа или ошибкой.

        Raises:
            ValueError: Если pk не является числом.
            Exception: Если получение данных заказа не удалось (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id
        try:
            pk = int(pk)
        except ValueError:
            logger.warning(f"Invalid pk={pk} for user={user_id}, path={request.path}, "
                           f"IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": _("Идентификатор заказа должен быть числом"), "code": "invalid_pk"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cached_data = CacheService.cache_order_detail(pk, user_id)
        if cached_data:
            logger.info(f"Retrieved cached order details for order={pk}, user={user_id}, "
                        f"path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(cached_data)

        order = OrderService.get_order_details(order_id=pk, user=request.user, request=request)
        serializer = self.serializer_class(order)
        response_data = serializer.data
        cache_key = f"order_detail:{pk}:{user_id}"
        CacheService.set_cached_data(cache_key, response_data, timeout=60 * 15)  # 15 мин
        logger.info(f"Order {pk} details retrieved for user={user_id}, path={request.path}, "
                    f"IP={request.META.get('REMOTE_ADDR')}")
        return Response(response_data)


class OrderCreateView(APIView):
    """
    Представление для создания нового заказа.

    Создает заказ из корзины пользователя с указанием пункта выдачи.

    Attributes:
        permission_classes: Требует аутентификации пользователя.
    """
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request):
        """
        Обрабатывает POST-запрос для создания заказа из корзины.

        Args:
            request (HttpRequest): Объект запроса с данными о пункте выдачи.

        Returns:
            Response: Ответ с подтверждением создания заказа или ошибкой.

        Raises:
            Exception: Если создание заказа не удалось из-за некорректных данных или других ошибок (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id
        pickup_point_id = request.data.get('pickup_point_id')

        if not pickup_point_id:
            logger.warning(f"Missing pickup_point_id for user={user_id},"
                           f" path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": _("Не указан пункт выдачи"), "code": "missing_input"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = OrderService.create_order(
            user=request.user,
            pickup_point_id=pickup_point_id,
            request=request
        )
        CacheService.invalidate_cache(prefix=f"order_list:{user_id}")
        logger.info(f"Order {order.id} created successfully for user={user_id},"
                    f" path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
        return Response(
            {"message": _("Заказ успешно создан"), "order_id": order.id},
            status=status.HTTP_201_CREATED
        )


class OrderCancelView(APIView):
    """
    Представление для отмены заказа.

    Позволяет отменить заказ в статусе processing.

    Attributes:
        permission_classes: Требует аутентификации пользователя.
    """
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request, pk):
        """
        Обрабатывает POST-запрос для отмены заказа.

        Args:
            request (HttpRequest): Объект запроса.
            pk (int): Идентификатор заказа.

        Returns:
            Response: Ответ с подтверждением отмены или ошибкой.

        Raises:
            ValueError: Если pk не является числом.
            Exception: Если отмена заказа не удалась из-за некорректных данных или других ошибок (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id
        try:
            pk = int(pk)
        except ValueError:
            logger.warning(f"Invalid pk={pk} for user={user_id},"
                           f" path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": _("Идентификатор заказа должен быть числом"), "code": "invalid_pk"},
                status=status.HTTP_400_BAD_REQUEST
            )

        OrderService.cancel_order(order_id=pk, user=request.user, request=request)
        CacheService.invalidate_cache(prefix=f"order_detail:{pk}:{user_id}")
        CacheService.invalidate_cache(prefix=f"order_list:{user_id}")
        logger.info(f"Order {pk} cancelled successfully for user={user_id},"
                    f" path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
        return Response({"message": _("Заказ отменен")}, status=status.HTTP_200_OK)
