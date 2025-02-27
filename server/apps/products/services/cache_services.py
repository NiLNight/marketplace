import hashlib


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
