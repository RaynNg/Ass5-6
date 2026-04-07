from django.http import JsonResponse
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet

router = DefaultRouter()
router.register(r"carts", CartViewSet)


def health_check(request):
    try:
        from django.db import connection
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "error"
    return JsonResponse({"status": "ok", "service": "cart-service", "db": db_status})


urlpatterns = [
    path("", include(router.urls)),
    path("health/", health_check, name="health-check"),
]
