import logging
from pytils.translit import slugify
import uuid

logger = logging.getLogger(__name__)


def unique_slugify(name: str) -> str:
    """Генерирует уникальный слаг на основе имени с добавлением UUID.

    Преобразует входную строку в слаг с помощью slugify и добавляет уникальный
    идентификатор для обеспечения уникальности.

    Args:
        name (str): Входная строка для преобразования в слаг.

    Returns:
        str: Уникальный слаг в формате '<slugified_name>-<uuid_hex>'.

    Raises:
        TypeError: Если входной аргумент name не является строкой.
    """
    logger.debug(f"Generating unique slug for name='{name}'")
    try:
        if not isinstance(name, str):
            logger.error(f"Invalid input type for name: {type(name)}, expected str")
            raise TypeError("Аргумент 'name' должен быть строкой")
        unique_slug = f"{slugify(name)}-{uuid.uuid1().hex[:8]}"
        logger.debug(f"Generated unique slug: {unique_slug}")
        return unique_slug
    except Exception as e:
        logger.error(f"Failed to generate unique slug for name='{name}': {str(e)}")
        raise
