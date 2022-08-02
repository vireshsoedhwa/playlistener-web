from django.apps import AppConfig
from django.conf import settings

class FrontendConfig(AppConfig):
    name = 'frontend'
    def ready(self):
        print("DEBUG: " + str(settings.DEBUG))
        print("PRODUCTION: " + str(settings.PRODUCTION))
        print("GO_PIPELINE_LABEL: " + str(settings.GO_PIPELINE_LABEL))
        print("frontend started")
