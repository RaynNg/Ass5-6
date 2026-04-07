from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Manager
from .serializers import ManagerSerializer


def health_check(request):
    try:
        from django.db import connection
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "error"
    return JsonResponse({"status": "ok", "service": "manager-service", "db": db_status})


class ManagerViewSet(viewsets.ModelViewSet):
    queryset = Manager.objects.all()
    serializer_class = ManagerSerializer

    @action(detail=False, methods=["post"])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        try:
            manager = Manager.objects.get(username=username)
            # Support hashed passwords with legacy plain-text migration
            if check_password(password, manager.password):
                return Response(ManagerSerializer(manager).data)
            if manager.password == password:
                manager.password = make_password(password)
                manager.save(update_fields=["password"])
                return Response(ManagerSerializer(manager).data)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Manager.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
