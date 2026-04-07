from rest_framework import serializers


class RecommendationRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    top_n = serializers.IntegerField(default=5, required=False)
