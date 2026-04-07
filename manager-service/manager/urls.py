from django.http import JsonResponse
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ManagerViewSet, health_check

router = DefaultRouter()
router.register(r"managers", ManagerViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("health/", health_check, name="health-check"),
]
