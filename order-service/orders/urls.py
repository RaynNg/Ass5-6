from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, health_check

router = DefaultRouter()
router.register(r"orders", OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("health/", health_check, name="health-check"),
]
