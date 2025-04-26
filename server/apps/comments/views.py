import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.core.services.cache_services import CacheService
from apps.comments.models import Comment
from apps.comments.services.comment_services import CommentService
from apps.comments.services.like_services import LikeService
from apps.comments.serializers import CommentSerializer, CommentCreateSerializer
from apps.comments.utils import handle_api_errors
from apps.comments.exceptions import CommentNotFound, CommentException
from mptt.utils import get_cached_trees

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Пагинация для списков."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommentListView(APIView):
    """Получение списка комментариев к отзыву."""
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    @handle_api_errors
    def get(self, request, review_id: int):
        """Обрабатывает GET-запрос для списка комментариев.

        Args:
            request: Объект запроса.
            review_id (int): ID отзыва.

        Returns:
            Response: Пагинированный список комментариев или ошибка.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Retrieving comments for review={review_id}, user={user_id}")
        cache_key = CacheService.build_cache_key(request, prefix=f"comments:{review_id}")
        cached_data = CacheService.get_cached_data(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for comments of review={review_id}, user={user_id}")
            return Response(cached_data)

        try:
            comments = Comment.objects.prefetch_related('children').filter(review_id=review_id).prefetch_related('user',
                                                                                                                 'likes')
            root_nodes = get_cached_trees(comments)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(root_nodes, request)
            serializer = CommentSerializer(page, many=True)
            response_data = paginator.get_paginated_response(serializer.data).data

            CacheService.set_cached_data(cache_key, response_data, timeout=300)
            logger.info(f"Retrieved {len(root_nodes)} comments for review={review_id}, user={user_id}")
            return Response(response_data)
        except Exception as e:
            logger.error(f"Error retrieving comments for review={review_id}: {str(e)}, user={user_id}")
            return Response(
                {"error": "Внутренняя ошибка сервера", "code": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CommentCreateView(APIView):
    """Создание нового комментария."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для создания комментария.

        Args:
            request: Объект запроса.

        Returns:
            Response: Данные созданного комментария или ошибка.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Creating comment by user={user_id}")
        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                comment = CommentService.create_comment(serializer.validated_data, request.user)
                CacheService.invalidate_cache(prefix=f"comments:{comment.review_id}")
                logger.info(f"Created Comment {comment.id}, user={user_id}")
                return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating comment: {str(e)}, user={user_id}")
                return Response({"error": str(e), "code": "create_error"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"Invalid data for comment creation: {serializer.errors}, user={user_id}")
        return Response({"error": serializer.errors, "code": "validation_error"}, status=status.HTTP_400_BAD_REQUEST)


class CommentUpdateView(APIView):
    """Обновление существующего комментария."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def patch(self, request, pk: int):
        """Обрабатывает PATCH-запрос для обновления комментария.

        Args:
            request: Объект запроса.
            pk (int): ID комментария.

        Returns:
            Response: Обновленные данные или ошибка.

        Raises:
            CommentNotFound: Если комментарий не найден.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Updating Comment {pk}, user={user_id}")
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            logger.warning(f"Comment {pk} not found, user={user_id}")
            raise CommentNotFound()
        serializer = CommentCreateSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_comment = CommentService.update_comment(comment, serializer.validated_data, request.user)
                CacheService.invalidate_cache(prefix=f"comments:{updated_comment.review_id}")
                logger.info(f"Updated Comment {pk}, user={user_id}")
                return Response(CommentSerializer(updated_comment).data, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error updating Comment {pk}: {str(e)}, user={user_id}")
                return Response({"error": str(e), "code": "update_error"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"Invalid data for Comment {pk}: {serializer.errors}, user={user_id}")
        return Response({"error": serializer.errors, "code": "validation_error"}, status=status.HTTP_400_BAD_REQUEST)


class CommentLikeView(APIView):
    """Управление лайками для комментариев."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request, pk: int):
        """Обрабатывает POST-запрос для переключения лайка комментария.

        Args:
            request: Объект запроса.
            pk (int): ID комментария.

        Returns:
            Response: Результат операции или ошибка.

        Raises:
            CommentNotFound: Если комментарий не найден.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Toggling like for comment={pk}, user={user_id}")
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            logger.warning(f"Comment {pk} not found, user={user_id}")
            raise CommentNotFound()
        try:
            result = LikeService.toggle_like(comment, request.user)
            logger.info(f"Like toggled for comment={pk}: {result['action']}, user={user_id}")
            return Response(result)
        except CommentException as e:
            logger.error(f"Error toggling like for comment={pk}: {str(e)}, user={user_id}")
            return Response({"error": str(e), "code": e.__class__.__name__.lower()}, status=e.status_code)
