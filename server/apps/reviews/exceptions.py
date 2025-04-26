from rest_framework.exceptions import APIException


class ReviewException(APIException):
    """Базовое исключение для операций с отзывами."""
    default_detail = 'Ошибка отзыва'
    status_code = 400

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class ReviewNotFound(ReviewException):
    """Исключение, если отзыв не найден."""
    default_detail = 'Отзыв не найден'
    status_code = 404


class InvalidReviewData(ReviewException):
    """Исключение, если данные отзыва некорректны."""
    default_detail = 'Некорректные данные отзыва'
