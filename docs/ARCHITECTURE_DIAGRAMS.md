# Architecture Diagrams - Bookstore Microservices

## 1) Overall System Architecture

```mermaid
graph LR
    U[Users] --> F1[Frontend - React/Vite :3000]
    U --> F2[Admin Dashboard - Next.js :3001]

    F1 --> G[API Gateway :8000]
    F2 --> G

    G --> AUTH[auth-service :8012]
    G --> STAFF[staff-service :8001]
    G --> MANAGER[manager-service :8002]
    G --> CUSTOMER[customer-service :8003]
    G --> CATALOG[catalog-service :8004]
    G --> BOOK[book-service :8005]
    G --> CART[cart-service :8006]
    G --> ORDER[order-service :8007]
    G --> SHIP[ship-service :8008]
    G --> PAY[pay-service :8009]
    G --> COMMENT[comment-rate-service :8010]
    G --> AI[recommender-ai-service :8011]

    AUTH --> AUTHDB[(PostgreSQL - auth_db)]
    STAFF --> STAFFDB[(PostgreSQL - staff_db)]
    MANAGER --> MANAGERDB[(PostgreSQL - manager_db)]
    CUSTOMER --> CUSTOMERDB[(PostgreSQL - customer_db)]
    CATALOG --> CATALOGDB[(PostgreSQL - catalog_db)]
    BOOK --> BOOKDB[(PostgreSQL - book_db)]
    CART --> CARTDB[(PostgreSQL - cart_db)]
    ORDER --> ORDERDB[(PostgreSQL - order_db)]
    SHIP --> SHIPDB[(PostgreSQL - ship_db)]
    PAY --> PAYDB[(PostgreSQL - pay_db)]
    COMMENT --> COMMENTDB[(PostgreSQL - comment_db)]
    AI --> AIDB[(PostgreSQL - recommender_db)]

    ORDER --> PAY
    ORDER --> SHIP
    ORDER --> CART
    ORDER --> CUSTOMER
    ORDER --> BOOK
    CART --> BOOK
    CART --> CUSTOMER
    COMMENT --> CUSTOMER
    COMMENT --> BOOK
    AI --> BOOK
    AI --> COMMENT
```

## 2) API Gateway Service

```mermaid
graph TB
    F1[Frontend :3000] --> G[api-gateway :8000]
    F2[Admin Dashboard :3001] --> G

    G --> AUTH[auth-service]
    G --> STAFF[staff-service]
    G --> MANAGER[manager-service]
    G --> CUSTOMER[customer-service]
    G --> CATALOG[catalog-service]
    G --> BOOK[book-service]
    G --> CART[cart-service]
    G --> ORDER[order-service]
    G --> SHIP[ship-service]
    G --> PAY[pay-service]
    G --> COMMENT[comment-rate-service]
    G --> AI[recommender-ai-service]

    G -. middleware .-> MW[Auth + Routing + Validation]
```

## 3) auth-service

```mermaid
graph LR
    Client[Frontend/Admin via Gateway] --> AUTH[auth-service]
    AUTH --> AUTHDB[(PostgreSQL auth_db)]
    AUTH --> JWT[JWT Token / Session]
    AUTH --> CUSTOMER[customer-service]
    AUTH --> STAFF[staff-service]
    AUTH --> MANAGER[manager-service]
```

## 4) staff-service

```mermaid
graph LR
    G[API Gateway] --> STAFF[staff-service]
    STAFF --> STAFFDB[(PostgreSQL staff_db)]
    STAFF --> AUTH[auth-service]
    MANAGER[manager-service] --> STAFF
```

## 5) manager-service

```mermaid
graph LR
    G[API Gateway] --> MANAGER[manager-service]
    MANAGER --> MANAGERDB[(PostgreSQL manager_db)]
    MANAGER --> STAFF[staff-service]
    MANAGER --> CATALOG[catalog-service]
    MANAGER --> BOOK[book-service]
```

## 6) customer-service

```mermaid
graph LR
    G[API Gateway] --> CUSTOMER[customer-service]
    CUSTOMER --> CUSTOMERDB[(PostgreSQL customer_db)]
    CUSTOMER --> AUTH[auth-service]
    CART[cart-service] --> CUSTOMER
    ORDER[order-service] --> CUSTOMER
    COMMENT[comment-rate-service] --> CUSTOMER
```

## 7) catalog-service

```mermaid
graph LR
    G[API Gateway] --> CATALOG[catalog-service]
    CATALOG --> CATALOGDB[(PostgreSQL catalog_db)]
    BOOK[book-service] --> CATALOG
    MANAGER[manager-service] --> CATALOG
```

## 8) book-service

```mermaid
graph LR
    G[API Gateway] --> BOOK[book-service]
    BOOK --> BOOKDB[(PostgreSQL book_db)]
    BOOK --> CATALOG[catalog-service]
    CART[cart-service] --> BOOK
    ORDER[order-service] --> BOOK
    COMMENT[comment-rate-service] --> BOOK
    AI[recommender-ai-service] --> BOOK
```

## 9) cart-service

```mermaid
graph LR
    G[API Gateway] --> CART[cart-service]
    CART --> CARTDB[(PostgreSQL cart_db)]
    CART --> CUSTOMER[customer-service]
    CART --> BOOK[book-service]
    ORDER[order-service] --> CART
```

## 10) order-service

```mermaid
graph LR
    G[API Gateway] --> ORDER[order-service]
    ORDER --> ORDERDB[(PostgreSQL order_db)]

    ORDER --> CUSTOMER[customer-service]
    ORDER --> CART[cart-service]
    ORDER --> BOOK[book-service]
    ORDER --> PAY[pay-service]
    ORDER --> SHIP[ship-service]
```

## 11) ship-service

```mermaid
graph LR
    G[API Gateway] --> SHIP[ship-service]
    SHIP --> SHIPDB[(PostgreSQL ship_db)]
    ORDER[order-service] --> SHIP
    SHIP --> CUSTOMER[customer-service]
```

## 12) pay-service

```mermaid
graph LR
    G[API Gateway] --> PAY[pay-service]
    PAY --> PAYDB[(PostgreSQL pay_db)]
    ORDER[order-service] --> PAY
    PAY --> CUSTOMER[customer-service]
```

## 13) comment-rate-service

```mermaid
graph LR
    G[API Gateway] --> COMMENT[comment-rate-service]
    COMMENT --> COMMENTDB[(PostgreSQL comment_db)]
    COMMENT --> CUSTOMER[customer-service]
    COMMENT --> BOOK[book-service]
    AI[recommender-ai-service] --> COMMENT
```

## 14) recommender-ai-service

```mermaid
graph LR
    G[API Gateway] --> AI[recommender-ai-service]
    AI --> AIDB[(PostgreSQL recommender_db)]
    AI --> BOOK[book-service]
    AI --> COMMENT[comment-rate-service]
    AI --> CUSTOMER[customer-service]
```

---

## Notes

- Port for auth-service is set to 8012 as a suggested value because current range 8000-8011 is already occupied.
- If actual runtime dependencies differ from this model, update service-to-service edges accordingly.
- These diagrams focus on logical architecture (request flow + service boundaries + per-service database).
