import uuid
import datetime
import requests
import jwt
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import generate_access_token, generate_refresh_token, decode_token
from .models import RefreshToken

# Role → (service URL, login path)
ROLE_SERVICE_MAP = {
    "customer": (settings.CUSTOMER_SERVICE_URL, "/api/customers/login/"),
    "staff": (settings.STAFF_SERVICE_URL, "/api/staff/login/"),
    "manager": (settings.MANAGER_SERVICE_URL, "/api/managers/login/"),
}


class TokenObtainView(APIView):
    """
    POST /api/auth/token/
    Body: {username, password, role}
    Returns: {access, refresh, user_id, username, role}
    """

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        role = request.data.get("role", "customer")

        if not username or not password:
            return Response(
                {"error": "username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role not in ROLE_SERVICE_MAP:
            return Response(
                {"error": f"Invalid role. Choose from: {list(ROLE_SERVICE_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_url, login_path = ROLE_SERVICE_MAP[role]
        try:
            resp = requests.post(
                f"{service_url}{login_path}",
                json={"username": username, "password": password},
                timeout=10,
            )
        except requests.RequestException:
            return Response(
                {"error": "Authentication service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if resp.status_code != 200:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user_data = resp.json()
        user_id = user_data.get("id")

        access = generate_access_token(user_id, username, role)
        refresh = generate_refresh_token(user_id, username, role)

        # Persist refresh token for revocation support
        jti = str(uuid.uuid4())
        RefreshToken.objects.create(
            user_id=user_id,
            username=username,
            role=role,
            token_jti=jti,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS),
        )

        return Response(
            {
                "access": access,
                "refresh": refresh,
                "user_id": user_id,
                "username": username,
                "role": role,
            },
            status=status.HTTP_200_OK,
        )


class TokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    Body: {refresh}
    Returns: {access}
    """

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            return Response({"error": "Refresh token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

        if payload.get("type") != "refresh":
            return Response({"error": "Invalid token type"}, status=status.HTTP_401_UNAUTHORIZED)

        access = generate_access_token(payload["user_id"], payload["username"], payload["role"])
        return Response({"access": access}, status=status.HTTP_200_OK)


class ValidateTokenView(APIView):
    """
    GET /api/auth/validate/
    Header: Authorization: Bearer <access_token>
    Returns: {user_id, username, role} or 401
    """

    def get(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response({"error": "Missing or invalid Authorization header"}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return Response({"error": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

        if payload.get("type") != "access":
            return Response({"error": "Invalid token type"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            {
                "user_id": payload["user_id"],
                "username": payload["username"],
                "role": payload["role"],
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Header: Authorization: Bearer <refresh_token>
    Revokes the refresh token.
    """

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = decode_token(refresh_token)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        RefreshToken.objects.filter(
            user_id=payload.get("user_id"),
            username=payload.get("username"),
            is_revoked=False,
        ).update(is_revoked=True)

        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


def health_check(request):
    """Health check endpoint."""
    try:
        from django.db import connection
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "error"
    return JsonResponse({"status": "ok", "service": "auth-service", "db": db_status})
