import logging

from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.comments.models import Comment
from apps.core.services.cache_services import CacheService
from apps.comments.services.comment_services import CommentService
from apps.comments.serializers import CommentSerializer, CommentCreateSerializer
from apps.comments.utils import handle_api_errors
from apps.core.services.like_services import LikeService

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Настройки пагинации для списков комментариев.

    Определяет размер страницы и параметры запроса для пагинированных ответов.

    Attributes:
        page_size (int): Количество элементов на странице по умолчанию.
        page_size_query_param (str): Параметр запроса для изменения размера страницы.
        max_page_size (int): Максимально допустимый размер страницы.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommentListView(APIView):
    """Представление для получения списка комментариев к отзыву.

    Attributes:
        permission_classes: Классы разрешений для доступа (доступно всем).
        pagination_class: Класс пагинации для списков комментариев.
        serializer_class: Класс сериализатора для преобразования данных комментариев.
    """
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    serializer_class = CommentSerializer

    @handle_api_errors
    def get(self, request, review_id: int):
        """Обрабатывает GET-запросы для получения пагинированного списка комментариев.

        Args:
            request (HttpRequest): Входящий объект запроса.
            review_id (int): ID отзыва для получения комментариев.

        Returns:
            Response: Пагинированный список комментариев или ответ с ошибкой.

        Raises:
            Exception: Если получение списка комментариев не удалось (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Retrieving comments for review={review_id}, user={user_id}")

        cached_data = CacheService.cache_comment_list(review_id, request)
        if cached_data:
            return Response(cached_data)

        root_nodes = CommentService.get_comments(review_id, request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(root_nodes, request)
        serializer = self.serializer_class(page, many=True, context={'request': request})

        response_data = paginator.get_paginated_response(serializer.data).data
        cache_key = CacheService.build_cache_key(request, prefix=f"comments:{review_id}")
        CacheService.set_cached_data(cache_key, response_data, timeout=300)
        logger.info(f"Retrieved {len(root_nodes)} comments for review={review_id}, user={user_id}")
        return Response(response_data)


class CommentCreateView(APIView):
    """Представление для создания нового комментария.

    Attributes:
        permission_classes: Классы разрешений для доступа (только для аутентифицированных).
        serializer_class: Класс сериализатора для создания комментариев.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CommentCreateSerializer

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запросы для создания нового комментария.

        Args:
            request (HttpRequest): Входящий объект запроса с данными комментария.

        Returns:
            Response: Данные созданного комментария или ответ с ошибкой.

        Raises:
            Exception: Если создание комментария не удалось из-за некорректных данных или других ошибок (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Creating comment by user={user_id}")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = CommentService.create_comment(serializer.validated_data, request.user)

        CacheService.invalidate_cache(prefix=f"comments:{comment.review_id}")
        logger.info(f"Created Comment {comment.id}, user={user_id}")
        return Response(CommentSerializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)


class CommentUpdateView(APIView):
    """Представление для обновления существующего комментария.

    Attributes:
        permission_classes: Классы разрешений для доступа (только для аутентифицированных).
        serializer_class: Класс сериализатора для обновления комментариев.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CommentCreateSerializer

    @handle_api_errors
    def patch(self, request, pk: int):
        """Обрабатывает PATCH-запросы для обновления комментария.

        Args:
            request (HttpRequest): Входящий объект запроса с обновленными данными.
            pk (int): ID комментария для обновления.

        Returns:
            Response: Данные обновленного комментария или ответ с ошибкой.

        Raises:
            Exception: Если обновление комментария не удалось из-за некорректных данных или других ошибок (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Updating Comment {pk}, user={user_id}, path={request.path}")

        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_comment = CommentService.update_comment(pk, serializer.validated_data, request.user)
        CacheService.invalidate_cache(prefix=f"comments:{updated_comment.review_id}")
        logger.info(f"Updated Comment {pk}, user={user_id}")
        return Response(CommentSerializer(updated_comment, context={'request': request}).data, status=status.HTTP_200_OK)


class CommentDeleteView(APIView):
    """Представление для удаления комментария.

    Attributes:
        permission_classes: Классы разрешений для доступа (только для аутентифицированных).
    """
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def delete(self, request, pk: int):
        """Обрабатывает DELETE-запросы для удаления комментария.

        Args:
            request (HttpRequest): Входящий объект запроса.
            pk (int): ID комментария для удаления.

        Returns:
            Response: Сообщение об удалении или ответ с ошибкой.

        Raises:
            Exception: Если удаление комментария не удалось из-за отсутствия прав или других ошибок (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Deleting Comment {pk}, user={user_id}, path={request.path}")

        CommentService.delete_comment(pk, request.user)
        CacheService.invalidate_cache(prefix=f"comments")
        logger.info(f"Deleted Comment {pk}, user={user_id}")
        return Response({"message": "Комментарий удален"}, status=status.HTTP_204_NO_CONTENT)


class CommentLikeView(APIView):
    """Представление для управления лайками комментариев.

    Attributes:
        permission_classes: Классы разрешений для доступа (только для аутентифицированных).
    """
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request, pk: int):
        """Обрабатывает POST-запросы для переключения лайка комментария.

        Args:
            request (HttpRequest): Входящий объект запроса.
            pk (int): ID комментария для лайка или снятия лайка.

        Returns:
            Response: Результат операции с лайком или ответ с ошибкой.

        Raises:
            Exception: Если операция с лайком не удалась из-за ошибки базы данных или других проблем (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Toggling like for comment={pk}, user={user_id}, path={request.path}")

        content_type = ContentType.objects.get_for_model(Comment)
        result = LikeService.toggle_like(content_type, pk, request.user)
        CacheService.invalidate_cache(prefix=f"comments")
        logger.info(f"Like toggled for comment={pk}: {result['action']}, user={user_id}")
        return Response(result, status=status.HTTP_200_OK)
