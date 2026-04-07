from rest_framework import viewsets
from .models import Catalog
from .serializers import CatalogSerializer


class CatalogViewSet(viewsets.ModelViewSet):
    queryset = Catalog.objects.all()
    serializer_class = CatalogSerializer
