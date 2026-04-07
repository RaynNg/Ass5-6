import os
import time
import requests
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Service registry
SERVICES = {
    "staff": os.environ.get("STAFF_SERVICE_URL", "http://staff-service:8000"),
    "managers": os.environ.get("MANAGER_SERVICE_URL", "http://manager-service:8000"),
    "customers": os.environ.get("CUSTOMER_SERVICE_URL", "http://customer-service:8000"),
    "catalogs": os.environ.get("CATALOG_SERVICE_URL", "http://catalog-service:8000"),
    "books": os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000"),
    "carts": os.environ.get("CART_SERVICE_URL", "http://cart-service:8000"),
    "orders": os.environ.get("ORDER_SERVICE_URL", "http://order-service:8000"),
    "shipments": os.environ.get("SHIP_SERVICE_URL", "http://ship-service:8000"),
    "payments": os.environ.get("PAY_SERVICE_URL", "http://pay-service:8000"),
    "comments": os.environ.get("COMMENT_SERVICE_URL", "http://comment-rate-service:8000"),
    "recommendations": os.environ.get("RECOMMENDER_SERVICE_URL", "http://recommender-ai-service:8000"),
    "auth": os.environ.get("AUTH_SERVICE_URL", "http://auth-service:8000"),
}

# Gateway metrics counters
_request_count = 0
_start_time = time.time()


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "ok", "service": "api-gateway"})


class GatewayProxyView(APIView):
    """
    Generic proxy view that forwards requests to the appropriate microservice.
    URL pattern: /api/<service_name>/<path>
    Forwards authenticated user headers injected by JWTAuthMiddleware.
    """

    def _proxy(self, request, service_name, path=""):
        global _request_count
        _request_count += 1

        base_url = SERVICES.get(service_name)
        if not base_url:
            return Response(
                {"error": f"Unknown service: {service_name}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        url = f"{base_url}/api/{path}"
        if not url.endswith("/"):
            url += "/"

        params = request.query_params.dict()

        headers = {"Content-Type": "application/json"}
        # Forward authenticated user context to downstream services
        for meta_key, header_name in (
            ("HTTP_X_USER_ID", "X-User-Id"),
            ("HTTP_X_USER_ROLE", "X-User-Role"),
            ("HTTP_X_USER_NAME", "X-User-Name"),
        ):
            value = request.META.get(meta_key)
            if value:
                headers[header_name] = value

        try:
            method = request.method.lower()
            kwargs = {"params": params, "headers": headers, "timeout": 30}

            if method in ["post", "put", "patch"]:
                kwargs["json"] = request.data

            resp = getattr(requests, method)(url, **kwargs)

            try:
                data = resp.json()
            except ValueError:
                data = {"detail": resp.text}

            return Response(data, status=resp.status_code)

        except requests.ConnectionError:
            return Response(
                {"error": f"Service '{service_name}' is unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except requests.Timeout:
            return Response(
                {"error": f"Service '{service_name}' timed out"},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )

    def get(self, request, service_name, path=""):
        return self._proxy(request, service_name, path)

    def post(self, request, service_name, path=""):
        return self._proxy(request, service_name, path)

    def put(self, request, service_name, path=""):
        return self._proxy(request, service_name, path)

    def patch(self, request, service_name, path=""):
        return self._proxy(request, service_name, path)

    def delete(self, request, service_name, path=""):
        return self._proxy(request, service_name, path)


class ServiceListView(APIView):
    """List all registered services."""

    def get(self, request):
        return Response({name: url for name, url in SERVICES.items()})


class MetricsView(APIView):
    """
    GET /api/metrics/
    Aggregates health status from all registered services and returns gateway stats.
    """

    def get(self, request):
        service_health = {}
        for name, base_url in SERVICES.items():
            start = time.time()
            try:
                resp = requests.get(f"{base_url}/api/health/", timeout=3)
                latency_ms = round((time.time() - start) * 1000, 2)
                svc_status = "ok" if resp.status_code == 200 else "degraded"
            except requests.RequestException:
                latency_ms = None
                svc_status = "unreachable"

            service_health[name] = {
                "status": svc_status,
                "url": base_url,
                "latency_ms": latency_ms,
            }

        uptime_s = round(time.time() - _start_time)
        return Response(
            {
                "gateway": {
                    "status": "ok",
                    "uptime_s": uptime_s,
                    "requests_total": _request_count,
                },
                "services": service_health,
            }
        )
