from django.db import models


class RefreshToken(models.Model):
    """Tracks issued refresh tokens for revocation support."""
    user_id = models.IntegerField()
    username = models.CharField(max_length=150)
    role = models.CharField(max_length=20)
    token_jti = models.CharField(max_length=36, unique=True)
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"RefreshToken({self.username}, revoked={self.is_revoked})"
