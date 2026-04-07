from django.http import JsonResponse
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentRateViewSet

router = DefaultRouter()
router.register(r"comments", CommentRateViewSet)


def health_check(request):
    try:
        from django.db import connection
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "error"
    return JsonResponse({"status": "ok", "service": "comment-rate-service", "db": db_status})


urlpatterns = [
    path("", include(router.urls)),
    path("health/", health_check, name="health-check"),
]
