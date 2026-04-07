import os
import requests
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer
from .saga import OrderSagaOrchestrator

CART_SERVICE_URL = os.environ.get("CART_SERVICE_URL", "http://cart-service:8000")
BOOK_SERVICE_URL = os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000")


def health_check(request):
    """Health check endpoint."""
    try:
        from django.db import connection
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "error"
    return JsonResponse({"status": "ok", "service": "order-service", "db": db_status})


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=False, methods=["post"])
    def create_from_cart(self, request):
        """
        Create an order from the customer's cart using the Saga pattern.

        Saga steps:
          1. Fetch cart & calculate total
          2. Create order (status=pending)
          3. [Saga] Reserve payment via RabbitMQ → pay-service
          4. [Saga] Reserve shipping via RabbitMQ → ship-service
          5. Confirm order (status=confirmed) or compensate on failure
          6. Clear cart & update book stock
        """
        ser = CreateOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        customer_id = ser.validated_data["customer_id"]
        payment_method = ser.validated_data["payment_method"]
        shipping_method = ser.validated_data["shipping_method"]
        shipping_address = ser.validated_data["shipping_address"]

        # Step 1: Fetch cart
        try:
            cart_resp = requests.get(
                f"{CART_SERVICE_URL}/api/carts/by_customer/",
                params={"customer_id": customer_id},
                timeout=5,
            )
            cart_data = cart_resp.json()
        except requests.RequestException:
            return Response({"error": "Failed to fetch cart"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not cart_data.get("items"):
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch book prices and calculate total
        total = 0
        order_items = []
        for item in cart_data["items"]:
            try:
                book_resp = requests.get(f"{BOOK_SERVICE_URL}/api/books/{item['book_id']}/", timeout=5)
                book = book_resp.json()
                price = float(book["price"])
            except requests.RequestException:
                return Response(
                    {"error": f"Failed to fetch book {item['book_id']}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            order_items.append({"book_id": item["book_id"], "quantity": item["quantity"], "price": price})
            total += price * item["quantity"]

        # Step 2: Create order with status=pending (saga starts)
        order = Order.objects.create(
            customer_id=customer_id,
            total_amount=total,
            payment_method=payment_method,
            shipping_method=shipping_method,
            shipping_address=shipping_address,
            status="pending",
        )
        for oi in order_items:
            OrderItem.objects.create(order=order, **oi)

        # Steps 3–5: Run saga orchestration (payment → shipping → confirm / compensate)
        order, error = OrderSagaOrchestrator().execute(
            order, order_items, customer_id, payment_method, shipping_method, shipping_address
        )

        if error:
            return Response({"error": error, "order": OrderSerializer(order).data}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Step 6: Clear cart (best-effort)
        try:
            requests.delete(
                f"{CART_SERVICE_URL}/api/carts/clear/",
                params={"customer_id": customer_id},
                timeout=5,
            )
        except requests.RequestException:
            pass

        # Step 7: Update book stock (best-effort)
        for oi in order_items:
            try:
                requests.post(
                    f"{BOOK_SERVICE_URL}/api/books/{oi['book_id']}/update_stock/",
                    json={"quantity": -oi["quantity"]},
                    timeout=5,
                )
            except requests.RequestException:
                pass

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def by_customer(self, request):
        customer_id = request.query_params.get("customer_id")
        if not customer_id:
            return Response({"error": "customer_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        orders = Order.objects.filter(customer_id=customer_id)
        return Response(OrderSerializer(orders, many=True).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in ["shipped", "delivered"]:
            return Response({"error": "Cannot cancel"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = "cancelled"
        order.save()
        return Response(OrderSerializer(order).data)
