from django.db import models


class CommentRate(models.Model):
    customer_id = models.PositiveIntegerField(help_text="FK to customer-service")
    book_id = models.PositiveIntegerField(help_text="FK to book-service")
    rating = models.PositiveIntegerField(
        help_text="Rating from 1 to 5",
    )
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["customer_id", "book_id"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Rating {self.rating}/5 by customer {self.customer_id} for book {self.book_id}"
