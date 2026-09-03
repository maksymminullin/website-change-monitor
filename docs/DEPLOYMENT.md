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

### 2. GitHub SSH Key Configuration

To clone the repository securely, generate an SSH key on the server:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```
Press `Enter` to accept the default file location and leave the passphrase empty.

Display the generated public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the output and add it to your GitHub account:
1. Go to GitHub -> Settings -> SSH and GPG keys.
2. Click "New SSH key".
3. Paste the key and save.

### 3. Clone Repository

Once the SSH key is added to GitHub, clone the repository and navigate into the project directory:

```bash
git clone git@github.com:maksymminullin/website-change-monitor.git
cd website-change-monitor
```

### 4. Environment Configuration

Ensure you are inside the `website-change-monitor` directory. Copy the example environment file:

```bash
cp .env.example .env.production
```

Edit `.env.production` using a text editor (e.g., `nano`):

```bash
nano .env.production
```

Configure the following variables:
- `SECRET_KEY`: Generate a secure key. You can generate one by running `openssl rand -hex 32` in a separate terminal.
- `POSTGRES_PASSWORD`: Set a secure database password.
- `DATABASE_URL`: Ensure it matches the production DB connection string and incorporates the new password: `postgresql+asyncpg://postgres:YOUR_PASSWORD@db:5432/monitor_db`.

Save the file and exit the editor (in `nano`: press `Ctrl+O`, `Enter`, then `Ctrl+X`).

### 5. Deploy Services

Start the stack using the production compose file. This command downloads the required images and starts the containers in the background:

```bash
docker compose -f docker-compose-prod.yml up -d --build
```

### 6. Database Migrations

Apply Alembic migrations to initialize the database schema:

```bash
docker compose -f docker-compose-prod.yml exec api alembic upgrade head
```

The application is now accessible via HTTPS at the configured domain. Caddy automatically handles Let's Encrypt SSL certificate provisioning.

## Maintenance Commands

View real-time logs:
```bash
docker compose -f docker-compose-prod.yml logs -f
```

Restart all services:
```bash
docker compose -f docker-compose-prod.yml restart
```

Stop all services:
```bash
docker compose -f docker-compose-prod.yml down
```

## Continuous Deployment (GitHub Actions)

The repository includes a CI/CD pipeline (`.github/workflows/ci-cd.yml`) that automatically runs linting, testing, and deploys the application to the production server upon pushing to the `main` branch.

To enable automated deployments, the GitHub Actions runner requires SSH access to your server.

### 1. Generate a Dedicated SSH Key for GitHub Actions

On your server, run the following command to generate a new key pair without a passphrase:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_actions -N ""
```

### 2. Authorize the Key on the Server

Append the public key to the server's authorized keys list to allow access:

```bash
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
```

### 3. Add Secrets to GitHub

Output the private key content:

```bash
cat ~/.ssh/github_actions
```

Copy the entire output (including the `BEGIN` and `END` header/footer lines).

Navigate to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions**. Create the following two repository secrets:

- `SSH_PRIVATE_KEY`: Paste the private key content copied in the previous step.
- `HOST_IP`: Enter the public IPv4 address of your server.

Once configured, any push to the `main` branch will trigger the automated deployment pipeline.
