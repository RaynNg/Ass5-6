from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"


class CreateOrderSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    payment_method = serializers.CharField(max_length=50)
    shipping_method = serializers.CharField(max_length=50)
    shipping_address = serializers.CharField()
