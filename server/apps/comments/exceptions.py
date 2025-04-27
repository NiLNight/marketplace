from rest_framework.exceptions import APIException


class CommentException(APIException):
    """Базовое исключение для операций с комментариями."""
    status_code = 400
    default_detail = 'Ошибка комментария'
    default_code = 'comment_error'


class CommentNotFound(CommentException):
    """Исключение, если комментарий не найден."""
    status_code = 404
    default_detail = 'Комментарий не найден'
    default_code = 'not_found'


class InvalidCommentData(CommentException):
    """Исключение, если данные комментария некорректны."""
    default_detail = 'Некорректные данные комментария'
    default_code = 'invalid_data'


class LikeOperationFailed(CommentException):
    """Исключение, если операция с лайком не удалась."""
    default_detail = 'Ошибка при обработке лайка'
    default_code = 'like_operation_failed'
