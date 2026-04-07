import os
import time
import json
import logging
import threading
from django.http import JsonResponse

logger = logging.getLogger("gateway")

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:8000")

# Routes that don't require authentication
# Note: Gateway URL pattern is /api/<service_name>/<path>
# e.g., /api/auth/auth/token/ → http://auth-service:8000/api/auth/token/
PUBLIC_PATHS = {
    ("POST", "/api/customers/customers/register/"),
    ("POST", "/api/customers/customers/login/"),
    ("POST", "/api/staff/staff/login/"),
    ("POST", "/api/managers/managers/login/"),
    ("GET", "/api/health/"),
    ("GET", "/api/metrics/"),
    ("GET", "/api/services/"),
}

# Path prefixes that are always public (any HTTP method)
PUBLIC_ANY_PREFIXES = (
    "/api/auth/",         # all JWT auth endpoints
)

# Path prefixes that are public for GET requests only
PUBLIC_GET_PREFIXES = (
    "/api/books/",
    "/api/catalogs/",
    "/api/recommendations/",
)


def _is_public(method, path):
    if (method, path) in PUBLIC_PATHS:
        return True
    if any(path.startswith(p) for p in PUBLIC_ANY_PREFIXES):
        return True
    if method == "GET" and any(path.startswith(p) for p in PUBLIC_GET_PREFIXES):
        return True
    return False


class JWTAuthMiddleware:
    """
    Validates JWT Bearer tokens on protected routes by calling the auth-service.
    Injects X-User-Id, X-User-Role, X-User-Name headers for downstream services.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        method = request.method

        if _is_public(method, path):
            return self.get_response(request)

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Authentication required. Provide Authorization: Bearer <token>"},
                status=401,
            )

        token = auth_header.split(" ", 1)[1]
        try:
            import requests as req
            resp = req.get(
                f"{AUTH_SERVICE_URL}/api/auth/validate/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            if resp.status_code != 200:
                return JsonResponse({"error": "Invalid or expired token"}, status=401)

            user_info = resp.json()
            request.META["HTTP_X_USER_ID"] = str(user_info.get("user_id", ""))
            request.META["HTTP_X_USER_ROLE"] = str(user_info.get("role", ""))
            request.META["HTTP_X_USER_NAME"] = str(user_info.get("username", ""))

        except Exception:
            return JsonResponse({"error": "Auth service unavailable"}, status=503)

        return self.get_response(request)


class RateLimitMiddleware:
    """
    Simple in-memory rate limiter: 100 requests per minute per IP.
    Uses a sliding window counter per IP address.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._counts = {}
        self._lock = threading.Lock()
        self.limit = 100
        self.window = 60  # seconds

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def __call__(self, request):
        ip = self._get_client_ip(request)
        now = time.time()

        with self._lock:
            if ip not in self._counts:
                self._counts[ip] = []
            # Remove timestamps older than the window
            self._counts[ip] = [t for t in self._counts[ip] if now - t < self.window]
            count = len(self._counts[ip])

            if count >= self.limit:
                return JsonResponse(
                    {"error": "Rate limit exceeded. Max 100 requests per minute."},
                    status=429,
                    headers={"Retry-After": str(self.window)},
                )
            self._counts[ip].append(now)

        return self.get_response(request)


class RequestLoggingMiddleware:
    """Logs structured JSON for every request/response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_id": request.META.get("HTTP_X_USER_ID", "-"),
            "role": request.META.get("HTTP_X_USER_ROLE", "-"),
            "ip": request.META.get("REMOTE_ADDR", "-"),
        }
        logger.info(json.dumps(log_entry))
        return response
