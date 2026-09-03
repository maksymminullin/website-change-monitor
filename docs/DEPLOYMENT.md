# Deployment Guide (DigitalOcean)

This guide walks you through deploying the Website Change Monitor on a fresh DigitalOcean Ubuntu Droplet.

## 1. Prerequisites
- A DigitalOcean Droplet running **Ubuntu 22.04 or 24.04**.
- An **A Record** in your DNS settings pointing `web.monitor.com` to your Droplet's IP address. (Caddy needs this to generate the SSL certificate).

## 2. Connect to your Droplet
Open your terminal and connect to your server via SSH:
```bash
ssh root@YOUR_DROPLET_IP
```

## 3. Install Docker and Docker Compose
Run the following commands on your server to install Docker:
```bash
# Update packages
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

Verify the installation:
```bash
docker compose version
```

## 4. Download the Project
Clone the repository to your server:
```bash
git clone https://github.com/maksymminullin/website-change-monitor.git
cd website-change-monitor
```

## 5. Configure Production Environment Variables
Create the production environment file:
```bash
cp .env.example .env.production
```

Now, edit this file using `nano`:
```bash
nano .env.production
```

Inside the file, change the following values:
1. `SECRET_KEY`: Generate a random string. You can use this command in another terminal: `openssl rand -hex 32`
2. `POSTGRES_PASSWORD`: Change it to a secure password.
3. `DATABASE_URL`: Update it to match your new password (e.g., `postgresql+asyncpg://postgres:YOUR_NEW_PASSWORD@db:5432/monitor_db`). Notice it uses `db:5432` instead of `127.0.0.1:5433` because in production, containers communicate via the internal Docker network.

Save and exit `nano` by pressing `Ctrl+O`, `Enter`, and then `Ctrl+X`.

## 6. Start the Application
Start the containers in detached mode using the production compose file:
```bash
docker compose -f docker-compose-prod.yml up -d --build
```
*This will download the PostgreSQL and Caddy images, and build the Python API and Worker images. It might take a few minutes.*

## 7. Apply Database Migrations
Initialize the database tables:
```bash
docker compose -f docker-compose-prod.yml exec api alembic upgrade head
```

## 8. Verify
Your application should now be live!
Visit **https://web.monitor.com** in your browser. Caddy will automatically provision a Let's Encrypt SSL certificate for you.

## Useful Commands
- View Logs: `docker compose -f docker-compose-prod.yml logs -f`
- Restart App: `docker compose -f docker-compose-prod.yml restart`
- Stop App: `docker compose -f docker-compose-prod.yml down`
