# Deployment

Steps to deploy the Website Change Monitor to an Ubuntu server (e.g., DigitalOcean Droplet).

## Requirements

- Ubuntu 22.04 or 24.04
- Root or sudo SSH access
- DNS A record configured to point the domain (e.g., `web.monitor.com`) to the server IP.

## Setup Instructions

### 1. System Dependencies

SSH into the server and install Docker:

```bash
apt-get update && apt-get upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 2. Clone Repository

```bash
git clone https://github.com/maksymminullin/website-change-monitor.git
cd website-change-monitor
```

### 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env.production
```

Edit `.env.production` and configure the following variables:
- `SECRET_KEY`: Generate a secure key (e.g., using `openssl rand -hex 32`).
- `POSTGRES_PASSWORD`: Set a secure database password.
- `DATABASE_URL`: Ensure it matches the production DB connection string and the new password: `postgresql+asyncpg://postgres:YOUR_PASSWORD@db:5432/monitor_db`.

### 4. Deploy Services

Start the stack using the production compose file:

```bash
docker compose -f docker-compose-prod.yml up -d --build
```

### 5. Database Migrations

Apply Alembic migrations to initialize the database schema:

```bash
docker compose -f docker-compose-prod.yml exec api alembic upgrade head
```

The application is now accessible via HTTPS at the configured domain. Caddy automatically handles Let's Encrypt SSL certificate provisioning.

## Maintenance Commands

View logs:
```bash
docker compose -f docker-compose-prod.yml logs -f
```

Restart services:
```bash
docker compose -f docker-compose-prod.yml restart
```

Stop services:
```bash
docker compose -f docker-compose-prod.yml down
```
