from rest_framework.exceptions import APIException


class CommentException(APIException):
    """Базовое исключение для операций с комментариями.

    Attributes:
        status_code (int): Код HTTP-статуса (400).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 400
    default_detail = 'Ошибка комментария'
    default_code = 'comment_error'


class CommentNotFound(CommentException):
    """Исключение, если комментарий не найден.

    Attributes:
        status_code (int): Код HTTP-статуса (404).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 404
    default_detail = 'Комментарий не найден'
    default_code = 'not_found'


class InvalidCommentData(CommentException):
    """Исключение, если данные комментария некорректны.

    Attributes:
        status_code (int): Код HTTP-статуса (400, унаследован).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    default_detail = 'Некорректные данные комментария'
    default_code = 'invalid_data'


class LikeOperationFailed(CommentException):
    """Исключение, если операция с лайком не удалась.

    Attributes:
        status_code (int): Код HTTP-статуса (400, унаследован).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    default_detail = 'Ошибка при обработке лайка'
    default_code = 'like_operation_failed'
