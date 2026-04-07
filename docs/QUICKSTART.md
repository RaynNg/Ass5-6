# Bookstore Microservices - Quick Start Guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)
- Yarn package manager

### Start All Services

```powershell
# Build and start all services
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f [service-name]
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Customer web app |
| **Admin Dashboard** | http://localhost:3001 | Data management studio |
| **API Gateway** | http://localhost:8000 | Central API endpoint |
| Catalog Service | http://localhost:8004 | Categories API |
| Book Service | http://localhost:8005 | Books API |
| Customer Service | http://localhost:8003 | Customers API |
| Staff Service | http://localhost:8001 | Staff API |
| Manager Service | http://localhost:8002 | Managers API |
| Cart Service | http://localhost:8006 | Shopping cart API |
| Order Service | http://localhost:8007 | Orders API |
| Payment Service | http://localhost:8009 | Payments API |
| Shipping Service | http://localhost:8008 | Shipments API |
| Comment Service | http://localhost:8010 | Reviews API |
| Recommender Service | http://localhost:8011 | AI recommendations API |

## 📊 Seed Data

### Seed All Services

```powershell
# PowerShell
.\seed_data.ps1

# Or batch file
seed_data.bat
```

### Seed Individual Service

```bash
docker-compose exec [service-name] python manage.py seed_[model]
```

**Examples:**
```bash
docker-compose exec catalog-service python manage.py seed_catalogs
docker-compose exec book-service python manage.py seed_books
docker-compose exec customer-service python manage.py seed_customers
```

## 🛠️ Development

### Backend (Django)

```bash
# Run migrations
docker-compose exec [service] python manage.py migrate

# Create migrations
docker-compose exec [service] python manage.py makemigrations

# Create superuser
docker-compose exec [service] python manage.py createsuperuser

# Django shell
docker-compose exec [service] python manage.py shell
```

### Frontend (React + Vite)

```bash
cd frontend
yarn install
yarn dev       # Start dev server
yarn build     # Build for production
yarn preview   # Preview production build
```

### Admin Dashboard (Next.js)

```bash
cd admin-dashboard
yarn install
yarn dev       # Start dev server (port 3000)
yarn build     # Build for production
yarn start     # Start production server
yarn lint      # Run linter
```

## 📦 Docker Commands

### Build & Start

```bash
# Build and start all
docker-compose up --build

# Start in background
docker-compose up -d

# Build specific service
docker-compose build [service-name]

# Start specific service
docker-compose up [service-name]
```

### Stop & Clean

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v

# Remove all containers and images
docker-compose down --rmi all

# Clean up system
docker system prune -a
```

### Logs & Debugging

```bash
# View logs
docker-compose logs [service-name]

# Follow logs
docker-compose logs -f [service-name]

# Last 100 lines
docker-compose logs --tail=100 [service-name]

# Execute command in container
docker-compose exec [service-name] bash

# Inspect container
docker inspect [container-id]
```

## 🗃️ Database

### Access PostgreSQL

```bash
# Connect to database
docker-compose exec postgres-[service] psql -U postgres -d [db_name]

# Example: Catalog database
docker-compose exec postgres-catalog psql -U postgres -d catalog_db
```

### Database Names

- `staff_db` - Staff service
- `manager_db` - Manager service
- `customer_db` - Customer service
- `catalog_db` - Catalog service
- `book_db` - Book service
- `cart_db` - Cart service
- `order_db` - Order service
- `pay_db` - Payment service
- `ship_db` - Shipping service
- `comment_db` - Comment service
- `recommender_db` - Recommender service

## 🔧 Common Tasks

### Reset Database

```bash
# Stop services
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v

# Restart and seed
docker-compose up -d
.\seed_data.ps1
```

### Update Dependencies

**Python (Backend):**
```bash
# Add package to requirements.txt, then:
docker-compose build [service-name]
```

**JavaScript (Frontend):**
```bash
cd frontend
yarn add [package-name]
yarn install
```

**JavaScript (Admin Dashboard):**
```bash
cd admin-dashboard
yarn add [package-name]
yarn install
```

### View Service Health

```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose ps [service-name]

# Health check
curl http://localhost:8000/health  # If health endpoint exists
```

## 📝 Project Structure

```
bookstore_microservice/
├── .github/
│   └── copilot-instructions.md    # GitHub Copilot config
├── api-gateway/                    # API Gateway service
├── book-service/                   # Book management
├── catalog-service/                # Catalog management
├── customer-service/               # Customer management
├── staff-service/                  # Staff management
├── manager-service/                # Manager management
├── cart-service/                   # Shopping cart
├── order-service/                  # Order processing
├── pay-service/                    # Payment processing
├── ship-service/                   # Shipping management
├── comment-rate-service/           # Reviews & ratings
├── recommender-ai-service/         # AI recommendations
├── frontend/                       # Customer web app (React + Vite)
├── admin-dashboard/                # Admin dashboard (Next.js 14)
├── docker-compose.yml              # Docker orchestration
├── seed_data.ps1                   # PowerShell seed script
├── seed_data.bat                   # Batch seed script
└── seed_data.sh                    # Bash seed script
```

## 🎯 Common Issues

### Port Already in Use

```bash
# Find process using port
netstat -ano | findstr :[PORT]

# Kill process (Windows)
taskkill /PID [process-id] /F

# Or change port in docker-compose.yml
```

### Container Won't Start

```bash
# Check logs
docker-compose logs [service-name]

# Rebuild
docker-compose build --no-cache [service-name]

# Remove and recreate
docker-compose rm [service-name]
docker-compose up [service-name]
```

### Database Connection Error

```bash
# Wait for database to be healthy
docker-compose ps

# Check database logs
docker-compose logs postgres-[service]

# Restart database
docker-compose restart postgres-[service]
```

## 📚 Documentation

- Main README: `/README.md`
- Admin Dashboard: `/admin-dashboard/README.md`
- Copilot Instructions: `/.github/copilot-instructions.md`
- Yarn Commands: `/admin-dashboard/COMMANDS.md`

## 🔗 Useful Links

- Django REST Framework: https://www.django-rest-framework.org/
- Next.js 14: https://nextjs.org/docs
- Shadcn UI: https://ui.shadcn.com/
- Tailwind CSS: https://tailwindcss.com/
- Docker Compose: https://docs.docker.com/compose/
- Yarn: https://yarnpkg.com/

---

**Need Help?** Check the full documentation or GitHub Copilot instructions for detailed guidance.
