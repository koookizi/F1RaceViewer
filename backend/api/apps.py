from django.apps import AppConfig
import os
import fastf1

class ApiConfig(AppConfig):
    name = 'api'

    # for caching fastf1
    def ready(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(base_dir, "fastf1_cache")

        os.makedirs(cache_dir, exist_ok=True)

        fastf1.Cache.enable_cache(cache_dir)
