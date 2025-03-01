import hashlib
from django.core.cache import cache


class CacheServices:
    @staticmethod
    def build_cache_key(request):
        params = [
            f"{key}={value}"
            for key, value in sorted(request.GET.items())
            if key != 'page'
        ]

        # Создаем хеш из параметров
        params_str = "&".join(params)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()

        return f"product_list:{params_hash}"

    @staticmethod
    def invalidate_product_list_cache():
        cache.delete_pattern("product_list:*")

    @staticmethod
    def invalidate_product_cache(product_id):
        cache.delete(f"product_detail:{product_id}")

    @staticmethod
    def clear_all_product_cache():
        cache.delete_pattern("*product*")
