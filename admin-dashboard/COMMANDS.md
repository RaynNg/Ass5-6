# Admin Dashboard - Yarn Commands

## Setup

```bash
# Install dependencies
yarn install

# Or install with frozen lockfile (recommended for CI)
yarn install --frozen-lockfile
```

## Development

```bash
# Start development server
yarn dev

# Build for production
yarn build

# Start production server
yarn start

# Run linter
yarn lint
```

## Docker

```bash
# Build and run with Docker Compose
docker-compose up --build admin-dashboard

# Or start all services
docker-compose up -d
```

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Port

- Development: http://localhost:3000
- Production (Docker): http://localhost:3001
