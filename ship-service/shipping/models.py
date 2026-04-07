from django.db import models
import uuid


class Shipment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
    ]
    METHOD_CHOICES = [
        ("standard", "Standard Shipping"),
        ("express", "Express Shipping"),
        ("overnight", "Overnight Shipping"),
    ]
    order_id = models.PositiveIntegerField(help_text="FK to order-service")
    customer_id = models.PositiveIntegerField(help_text="FK to customer-service")
    address = models.TextField()
    method = models.CharField(max_length=50, choices=METHOD_CHOICES, default="standard")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    tracking_number = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = f"SHIP-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Shipment #{self.id} for Order #{self.order_id}"
