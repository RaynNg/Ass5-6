from rest_framework import serializers
from .models import CommentRate


class CommentRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentRate
        fields = "__all__"

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
