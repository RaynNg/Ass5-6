from django.db import models


class Cart(models.Model):
    customer_id = models.PositiveIntegerField(unique=True, help_text="FK to customer-service")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for customer {self.customer_id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    book_id = models.PositiveIntegerField(help_text="FK to book-service")
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["cart", "book_id"]

    def __str__(self):
        return f"CartItem(cart={self.cart_id}, book={self.book_id}, qty={self.quantity})"
