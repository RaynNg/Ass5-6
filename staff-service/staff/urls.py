from django.http import JsonResponse
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StaffViewSet, health_check

router = DefaultRouter()
router.register(r"staff", StaffViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("health/", health_check, name="health-check"),
]
