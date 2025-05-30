from rest_framework.exceptions import APIException


class ReviewException(APIException):
    """Базовое исключение для операций с отзывами.

    Attributes:
        status_code (int): Код HTTP-статуса (400).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 400
    default_detail = 'Ошибка при обработке отзыва'
    default_code = 'review_error'


class ReviewNotFound(ReviewException):
    """Исключение, вызываемое при отсутствии отзыва.

    Attributes:
        status_code (int): Код HTTP-статуса (404).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 404
    default_detail = 'Отзыв не найден'
    default_code = 'not_found'


class InvalidReviewData(ReviewException):
    """Исключение, вызываемое при некорректных данных отзыва.

    Attributes:
        status_code (int): Код HTTP-статуса (400, унаследован).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    default_detail = 'Некорректные данные отзыва'
    default_code = 'invalid_data'


class LikeOperationFailed(ReviewException):
    """Исключение, вызываемое при ошибке операции с лайком.

    Attributes:
        status_code (int): Код HTTP-статуса (400, унаследован).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    default_detail = 'Ошибка при обработке лайка'
    default_code = 'like_operation_failed'
