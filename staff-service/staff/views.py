from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Staff
from .serializers import StaffSerializer


def health_check(request):
    try:
        from django.db import connection
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "error"
    return JsonResponse({"status": "ok", "service": "staff-service", "db": db_status})


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

    @action(detail=False, methods=["post"])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        try:
            staff = Staff.objects.get(username=username)
            # Support hashed passwords with legacy plain-text migration
            if check_password(password, staff.password):
                return Response(StaffSerializer(staff).data)
            if staff.password == password:
                staff.password = make_password(password)
                staff.save(update_fields=["password"])
                return Response(StaffSerializer(staff).data)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Staff.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
