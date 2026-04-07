from django.http import JsonResponse
from django.urls import path
from .views import RecommendView


def health_check(request):
    try:
        from django.db import connection
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "error"
    return JsonResponse({"status": "ok", "service": "recommender-ai-service", "db": db_status})


urlpatterns = [
    path("recommendations/", RecommendView.as_view(), name="recommendations"),
    path("health/", health_check, name="health-check"),
]
