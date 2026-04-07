import os
import requests
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer, AddToCartSerializer, UpdateCartItemSerializer

BOOK_SERVICE_URL = os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000")


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    @action(detail=False, methods=["get"])
    def by_customer(self, request):
        """Get cart by customer_id."""
        customer_id = request.query_params.get("customer_id")
        if not customer_id:
            return Response({"error": "customer_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart = Cart.objects.get(customer_id=customer_id)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
        # Enrich items with book details
        cart_data = CartSerializer(cart).data
        for item in cart_data["items"]:
            try:
                resp = requests.get(f"{BOOK_SERVICE_URL}/api/books/{item['book_id']}/", timeout=5)
                if resp.status_code == 200:
                    item["book"] = resp.json()
            except requests.RequestException:
                item["book"] = None
        return Response(cart_data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """Add a book to the customer's cart."""
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer_id = serializer.validated_data["customer_id"]
        book_id = serializer.validated_data["book_id"]
        quantity = serializer.validated_data["quantity"]

        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)
        item, created = CartItem.objects.get_or_create(
            cart=cart, book_id=book_id, defaults={"quantity": quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["put"])
    def update_item(self, request):
        """Update quantity of a cart item. Quantity 0 removes the item."""
        customer_id = request.data.get("customer_id")
        book_id = request.data.get("book_id")
        quantity = int(request.data.get("quantity", 1))
        try:
            cart = Cart.objects.get(customer_id=customer_id)
            item = CartItem.objects.get(cart=cart, book_id=book_id)
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save()
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["delete"])
    def remove_item(self, request):
        """Remove a book from the cart."""
        customer_id = request.query_params.get("customer_id")
        book_id = request.query_params.get("book_id")
        try:
            cart = Cart.objects.get(customer_id=customer_id)
            item = CartItem.objects.get(cart=cart, book_id=book_id)
            item.delete()
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["delete"])
    def clear(self, request):
        """Clear all items from a cart."""
        customer_id = request.query_params.get("customer_id")
        try:
            cart = Cart.objects.get(customer_id=customer_id)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(CartSerializer(cart).data)
