class WishlistException(Exception):
    """Базовое исключение для операций со списком желаний."""
    default_detail = 'Ошибка списка желаний'
    status_code = 400

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class ProductNotAvailable(WishlistException):
    """Исключение, если товар недоступен для добавления в список желаний."""
    default_detail = 'Товар недоступен для списка желаний'


class WishlistItemNotFound(WishlistException):
    """Исключение, если элемент не найден в списке желаний."""
    default_detail = 'Элемент списка желаний не найден'
    status_code = 404
