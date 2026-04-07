from django.urls import path
from .views import TokenObtainView, TokenRefreshView, ValidateTokenView, LogoutView, health_check

urlpatterns = [
    path("auth/token/", TokenObtainView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/validate/", ValidateTokenView.as_view(), name="token-validate"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/health/", health_check, name="auth-health"),
]
