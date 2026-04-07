# GitHub Copilot Instructions - Bookstore Microservices

## Project Overview

This is a microservices-based bookstore management system built with Django REST Framework for backend services and React/Next.js for frontend applications.

## Architecture

- **Microservices Pattern**: Each service is independent with its own database
- **API Gateway**: Central routing point at port 8000
- **Containerization**: All services run in Docker containers
- **Database**: PostgreSQL 15 for each service

## Services Structure

### Backend Services (Django REST Framework)

1. **catalog-service** (port 8004) - Book categories management
2. **book-service** (port 8005) - Book inventory and details
3. **customer-service** (port 8003) - Customer account management
4. **staff-service** (port 8001) - Staff/employee management
5. **manager-service** (port 8002) - Manager/admin management
6. **cart-service** (port 8006) - Shopping cart functionality
7. **order-service** (port 8007) - Order processing
8. **pay-service** (port 8009) - Payment processing
9. **ship-service** (port 8008) - Shipping/delivery management
10. **comment-rate-service** (port 8010) - Reviews and ratings
11. **recommender-ai-service** (port 8011) - AI-based recommendations

### Frontend Applications

- **frontend** (port 3000) - Main customer-facing web application (React + Vite)
- **admin-dashboard** (port 3001) - Admin data management dashboard (Next.js 14)

### API Gateway

- **api-gateway** (port 8000) - Routes requests to appropriate services

## Technology Stack

### Backend

- **Framework**: Django 4.x + Django REST Framework
- **Database**: PostgreSQL 15
- **Language**: Python 3.11
- **Container**: Docker with python:3.11-slim base image

### Frontend

- **Main App**: React 18 + Vite + TypeScript
- **Admin Dashboard**: Next.js 14 + TypeScript + Shadcn UI
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios

### DevOps

- **Containerization**: Docker & Docker Compose
- **Package Manager**: yarn (preferred)
- **Environment**: Development/Production via Docker

## Coding Standards

### Python/Django

- Use Django REST Framework's ViewSets and Serializers
- Follow PEP 8 style guide
- Use meaningful model and field names in Vietnamese context
- Always use migrations for database changes
- Implement proper error handling and validation
- Use environment variables for configuration

### TypeScript/React/Next.js

- TypeScript with strict mode enabled
- Functional components with hooks
- Use Shadcn UI components for consistency
- Tailwind CSS for styling
- Follow Next.js 14 app router conventions
- Use 'use client' directive when needed for client components

### File Structure

- Django apps: models.py, serializers.py, views.py, urls.py pattern
- Management commands in `management/commands/` for seed scripts
- Next.js: app router with service/[id] dynamic routing

## Database Conventions

- Primary keys: Auto-generated integer IDs
- Foreign keys: Use `{service}_id` pattern (e.g., `customer_id`, `book_id`)
- Timestamps: Include `created_at` and `updated_at` fields
- Soft deletes: Use `is_active` boolean field
- Use Vietnamese for display names and descriptions

## API Patterns

- RESTful endpoints following Django REST Framework conventions
- List endpoint: `/resource/`
- Detail endpoint: `/resource/{id}/`
- Use proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Return appropriate status codes
- Pagination enabled by default

## Docker Compose

- Each service has its own PostgreSQL container
- Services wait for database health checks
- Volume persistence for databases
- Network isolation via Docker network

## Data Seeding

- Management commands for seeding data: `python manage.py seed_{model_name}`
- Seed scripts located in each service's `management/commands/`
- Run seeds in order: catalogs → staff → customers → books → carts → orders → payments/shipments → comments
- Use provided PowerShell scripts for batch seeding

## Environment Variables

- Database: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- Service URLs: `{SERVICE_NAME}_SERVICE_URL`
- Frontend: `NEXT_PUBLIC_API_URL`

## Common Commands

### Docker

```bash
# Start all services
docker-compose up -d

# Rebuild specific service
docker-compose up --build {service-name}

# View logs
docker-compose logs -f {service-name}

# Stop all services
docker-compose down
```

### Django Management

```bash
# Run migrations
docker-compose exec {service} python manage.py migrate

# Create superuser
docker-compose exec {service} python manage.py createsuperuser

# Seed data
docker-compose exec {service} python manage.py seed_{model}
```

### Frontend Development

```bash
# Admin Dashboard
cd admin-dashboard
yarn install
yarn dev

# Main Frontend
cd frontend
yarn install
yarn dev
```

## Important Notes

1. **Port Allocation**: Ensure no port conflicts. Services use 8000-8011, frontends use 3000-3001
2. **CORS**: All Django services should allow requests from frontend origins
3. **Database Independence**: Each service manages its own data; no direct DB access between services
4. **Vietnamese Context**: Use Vietnamese for user-facing text, comments can be in English
5. **Error Handling**: Always return meaningful error messages and proper HTTP status codes
6. **Type Safety**: Use TypeScript strictly, avoid `any` types when possible
7. **Component Reusability**: Use Shadcn UI components, don't reinvent the wheel
8. **Performance**: Implement pagination, lazy loading, and efficient queries

## When Adding New Features

### New Django Service

1. Create service directory with Django structure
2. Add models with proper fields and relationships
3. Create serializers and viewsets
4. Define URL patterns
5. Add Dockerfile and requirements.txt
6. Add to docker-compose.yml
7. Create PostgreSQL container
8. Add seed command if needed
9. Update API Gateway routing

### New Frontend Feature

1. Create new components in appropriate directory
2. Use TypeScript for type safety
3. Follow existing patterns (hooks, API client)
4. Style with Tailwind CSS
5. Use Shadcn UI components
6. Handle loading and error states
7. Implement proper routing

## Security Considerations

- Never commit sensitive data or passwords
- Use environment variables for secrets
- Implement proper authentication/authorization (work in progress)
- Validate all user inputs
- Sanitize data before database operations
- Use HTTPS in production

## Testing Guidelines

- Write unit tests for Django models and serializers
- Test API endpoints with proper fixtures
- Test React components with React Testing Library
- Integration tests for critical workflows
- Load testing for performance bottlenecks

## Performance Best Practices

- Use database indexes on frequently queried fields
- Implement caching where appropriate
- Optimize queries (select_related, prefetch_related)
- Use pagination for large datasets
- Lazy load images and heavy components
- Minimize bundle size in frontend

## Code Review Checklist

- [ ] Code follows project conventions
- [ ] No hardcoded values; use environment variables
- [ ] Proper error handling implemented
- [ ] TypeScript types are correct and strict
- [ ] Components are properly organized
- [ ] Database migrations are included
- [ ] API endpoints are RESTful
- [ ] Code is well-documented
- [ ] No console.log in production code
- [ ] Responsive design implemented

## Getting Started for New Developers

1. Clone the repository
2. Install Docker and Docker Compose
3. Run `docker-compose up --build` to start all services
4. Wait for all services to be healthy
5. Run seed scripts: `.\seed_data.ps1` or `.\seed_data.bat`
6. Access services:
   - Main App: http://localhost:3000
   - Admin Dashboard: http://localhost:3001
   - API Gateway: http://localhost:8000
   - Individual services: http://localhost:800X

## Useful Resources

- Django REST Framework: https://www.django-rest-framework.org/
- Next.js 14: https://nextjs.org/docs
- Shadcn UI: https://ui.shadcn.com/
- Tailwind CSS: https://tailwindcss.com/
- Docker Compose: https://docs.docker.com/compose/

## Project Goals

- Build a scalable microservices architecture
- Practice modern web development patterns
- Implement clean code principles
- Create maintainable and documented code
- Deploy production-ready application

---

**Remember**: When suggesting code, always consider the microservices architecture, maintain consistency with existing patterns, and prioritize clean, maintainable code over clever solutions.
