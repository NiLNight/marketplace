from django.test import TestCase
from apps.core.utils import unique_slugify


class UniqueSlugifyTest(TestCase):
    """
    Тесты для функции unique_slugify: генерация уникальных слагов, edge-cases.
    """

    def test_slugify_basic(self):
        slug = unique_slugify("Test Title")
        self.assertTrue(slug.startswith("test-title-"))
        self.assertEqual(len(slug.split("-")[-1]), 8)

    def test_slugify_cyrillic(self):
        slug = unique_slugify("Тестовый Заголовок")
        self.assertTrue(slug.startswith("testovyij-zagolovok-"))  # Исправлено на testovyij
        self.assertEqual(len(slug.split("-")[-1]), 8)

    def test_slugify_invalid_input(self):
        with self.assertRaises(TypeError):
            unique_slugify(123)
