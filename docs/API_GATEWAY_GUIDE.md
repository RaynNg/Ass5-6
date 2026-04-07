# API Gateway - Routing Guide

## 📚 Overview

The API Gateway routes requests from frontend applications to appropriate microservices. All external requests should go through the API Gateway at `http://localhost:8000`.

## 🔀 Routing Pattern

### URL Format

```
/api/{service_name}/{resource_path}
```

### How It Works

```
Client Request
     ↓
http://localhost:8000/api/{service_name}/{path}
     ↓
API Gateway (port 8000)
     ↓
http://{service_name}:8000/api/{path}
     ↓
Microservice Response
```

## 📋 Service Registry

### Service Name Mappings

| Service Name      | Internal URL                         | Description            |
| ----------------- | ------------------------------------ | ---------------------- |
| `catalogs`        | `http://catalog-service:8000`        | Book categories        |
| `books`           | `http://book-service:8000`           | Book inventory         |
| `customers`       | `http://customer-service:8000`       | Customer accounts      |
| `staff`           | `http://staff-service:8000`          | Staff management       |
| `managers`        | `http://manager-service:8000`        | Manager/admin accounts |
| `carts`           | `http://cart-service:8000`           | Shopping carts         |
| `orders`          | `http://order-service:8000`          | Order processing       |
| `shipments`       | `http://ship-service:8000`           | Shipping/delivery      |
| `payments`        | `http://pay-service:8000`            | Payment processing     |
| `comments`        | `http://comment-rate-service:8000`   | Reviews & ratings      |
| `recommendations` | `http://recommender-ai-service:8000` | AI recommendations     |

## 🎯 Endpoint Examples

### List Resources

#### Catalogs

```bash
# Through API Gateway
GET http://localhost:8000/api/catalogs/catalogs/

# Direct (for testing only)
GET http://localhost:8004/api/catalogs/
```

#### Books

```bash
# Through API Gateway
GET http://localhost:8000/api/books/books/

# Direct (for testing only)
GET http://localhost:8005/api/books/
```

#### Customers

```bash
# Through API Gateway
GET http://localhost:8000/api/customers/customers/

# Direct (for testing only)
GET http://localhost:8003/api/customers/
```

### Single Resource

#### Get Catalog by ID

```bash
# Through API Gateway
GET http://localhost:8000/api/catalogs/catalogs/1/

# Direct (for testing only)
GET http://localhost:8004/api/catalogs/1/
```

#### Get Book by ID

```bash
# Through API Gateway
GET http://localhost:8000/api/books/books/42/

# Direct (for testing only)
GET http://localhost:8005/api/books/42/
```

### Create Resource

#### Create Order

```bash
# Through API Gateway
POST http://localhost:8000/api/orders/orders/
Content-Type: application/json

{
  "customer_id": 1,
  "total_price": 150000,
  "status": "pending"
}
```

### Update Resource

#### Update Payment Status

```bash
# Through API Gateway
PATCH http://localhost:8000/api/payments/payments/5/
Content-Type: application/json

{
  "status": "completed"
}
```

## 🔧 Configuration

### API Gateway Settings

File: `api-gateway/gateway/views.py`

```python
SERVICES = {
    "staff": os.environ.get("STAFF_SERVICE_URL", "http://staff-service:8000"),
    "managers": os.environ.get("MANAGER_SERVICE_URL", "http://manager-service:8000"),
    "customers": os.environ.get("CUSTOMER_SERVICE_URL", "http://customer-service:8000"),
    "catalogs": os.environ.get("CATALOG_SERVICE_URL", "http://catalog-service:8000"),
    "books": os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000"),
    "carts": os.environ.get("CART_SERVICE_URL", "http://cart-service:8000"),
    "orders": os.environ.get("ORDER_SERVICE_URL", "http://order-service:8000"),
    "shipments": os.environ.get("SHIP_SERVICE_URL", "http://ship-service:8000"),
    "payments": os.environ.get("PAY_SERVICE_URL", "http://pay-service:8000"),
    "comments": os.environ.get("COMMENT_SERVICE_URL", "http://comment-rate-service:8000"),
    "recommendations": os.environ.get("RECOMMENDER_SERVICE_URL", "http://recommender-ai-service:8000"),
}
```

### Environment Variables

You can override service URLs using environment variables in `docker-compose.yml`:

```yaml
api-gateway:
  environment:
    - CATALOG_SERVICE_URL=http://catalog-service:8000
    - BOOK_SERVICE_URL=http://book-service:8000
    # etc...
```

## 📱 Frontend Configuration

### Admin Dashboard

File: `admin-dashboard/lib/api.ts`

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const services: Service[] = [
  {
    id: "catalog",
    endpoint: "/api/catalogs/catalogs/",
    // ...
  },
  {
    id: "book",
    endpoint: "/api/books/books/",
    // ...
  },
  // etc...
];
```

### Environment Variables

File: `admin-dashboard/.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Docker Environment:**

```yaml
admin-dashboard:
  environment:
    - NEXT_PUBLIC_API_URL=http://api-gateway:8000
```

## 🧪 Testing

### Test All Endpoints

**PowerShell:**

```powershell
.\test_api_endpoints.ps1
```

**Bash:**

```bash
./test_api_endpoints.sh
```

### Test Individual Endpoint

**Using curl:**

```bash
curl http://localhost:8000/api/catalogs/catalogs/
```

**Using PowerShell:**

```powershell
Invoke-WebRequest http://localhost:8000/api/catalogs/catalogs/ | Select-Object -ExpandProperty Content
```

### Test with Query Parameters

```bash
# Pagination
curl "http://localhost:8000/api/books/books/?page=2&page_size=20"

# Search
curl "http://localhost:8000/api/books/books/?search=python"

# Filter
curl "http://localhost:8000/api/books/books/?catalog_id=5"
```

## ❌ Common Errors

### 404 Not Found

**Problem:**

```
GET /catalogs/ → 404 Not Found
```

**Solution:**

```
GET /api/catalogs/catalogs/ → 200 OK
```

Always include:

1. `/api/` prefix
2. Service name
3. Resource path

### 503 Service Unavailable

**Problem:**

```json
{ "error": "Service 'books' is unavailable" }
```

**Solution:**

```bash
# Check if service is running
docker-compose ps book-service

# Restart service
docker-compose restart book-service

# Check logs
docker-compose logs book-service -f
```

### 504 Gateway Timeout

**Problem:**

```json
{ "error": "Service 'books' timed out" }
```

**Timeout is set to 30 seconds.** Check service logs:

```bash
docker-compose logs book-service -f
```

## 🔍 Debugging

### Check API Gateway

```bash
# View API Gateway logs
docker-compose logs api-gateway -f

# Check if API Gateway is running
docker-compose ps api-gateway

# Test API Gateway health
curl http://localhost:8000/api/health/
```

### Check Service Registry

```bash
# List available services
curl http://localhost:8000/api/services/
```

Response:

```json
{
  "catalogs": "http://catalog-service:8000/api/catalogs/",
  "books": "http://book-service:8000/api/books/",
  "customers": "http://customer-service:8000/api/customers/",
  ...
}
```

### Check Individual Service

```bash
# Direct service access (bypassing API Gateway)
curl http://localhost:8004/api/catalogs/
curl http://localhost:8005/api/books/
```

## 📊 Performance

### Timeout Configuration

Default timeout: **30 seconds**

To modify, edit `api-gateway/gateway/views.py`:

```python
resp = getattr(requests, method)(url, **kwargs, timeout=30)
```

### Connection Pooling

API Gateway uses `requests` library which automatically handles connection pooling.

## 🔐 Security Notes

1. **CORS**: API Gateway should have CORS configured for frontend origins
2. **Rate Limiting**: Consider adding rate limiting in production
3. **Authentication**: Add JWT token validation in production
4. **HTTPS**: Use HTTPS in production environment

## 📚 Additional Resources

- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Microservices Architecture](https://microservices.io/)

---

**Last Updated:** March 10, 2026
