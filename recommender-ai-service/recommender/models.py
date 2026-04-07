from django.db import models

# No persistent models — this service is stateless.
# It fetches data from comment-rate-service and book-service
# to compute recommendations dynamically.
