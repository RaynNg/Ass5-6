from django.db.models import Avg
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CommentRate
from .serializers import CommentRateSerializer


class CommentRateViewSet(viewsets.ModelViewSet):
    queryset = CommentRate.objects.all()
    serializer_class = CommentRateSerializer

    @action(detail=False, methods=["get"])
    def by_book(self, request):
        book_id = request.query_params.get("book_id")
        if not book_id:
            return Response({"error": "book_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        reviews = CommentRate.objects.filter(book_id=book_id)
        avg = reviews.aggregate(avg_rating=Avg("rating"))
        return Response({
            "book_id": int(book_id),
            "average_rating": avg["avg_rating"],
            "total_reviews": reviews.count(),
            "reviews": CommentRateSerializer(reviews, many=True).data,
        })

    @action(detail=False, methods=["get"])
    def by_customer(self, request):
        customer_id = request.query_params.get("customer_id")
        if not customer_id:
            return Response({"error": "customer_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        reviews = CommentRate.objects.filter(customer_id=customer_id)
        return Response(CommentRateSerializer(reviews, many=True).data)

    @action(detail=False, methods=["get"])
    def all_ratings(self, request):
        """Return all ratings (used by recommender-ai-service)."""
        reviews = CommentRate.objects.all()
        return Response(CommentRateSerializer(reviews, many=True).data)
