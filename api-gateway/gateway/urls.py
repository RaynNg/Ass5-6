from django.urls import path, re_path
from .views import GatewayProxyView, ServiceListView, MetricsView, health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("services/", ServiceListView.as_view(), name="service-list"),
    path("metrics/", MetricsView.as_view(), name="metrics"),
    re_path(r"^(?P<service_name>[\w-]+)/(?P<path>.*)$", GatewayProxyView.as_view(), name="gateway-proxy"),
]
