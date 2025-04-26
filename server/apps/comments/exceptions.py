from rest_framework.exceptions import APIException


class CommentException(APIException):
    """Базовое исключение для операций с комментариями."""
    default_detail = 'Ошибка комментария'
    status_code = 400

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class CommentNotFound(CommentException):
    """Исключение, если комментарий не найден."""
    default_detail = 'Комментарий не найден'
    status_code = 404


class InvalidCommentData(CommentException):
    """Исключение, если данные комментария некорректны."""
    default_detail = 'Некорректные данные комментария'
