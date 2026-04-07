import sys
from django.apps import AppConfig


class ShippingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shipping"

    def ready(self):
        # Don't start consumer during management commands (e.g., migrate)
        if "runserver" not in sys.argv and "gunicorn" not in " ".join(sys.argv):
            return
        from .saga_consumer import start_consumer
        start_consumer()
