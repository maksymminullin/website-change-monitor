# Website Сhange Monitor


Website Monitor is a full-stack application for tracking changes on public web pages.

Users can add URLs to monitor, browse saved content snapshots, archive pages to pause scheduled checks, and reactivate them when monitoring should resume. A separate background worker periodically fetches active pages and stores a new snapshot only when the extracted page content has changed.

## Features

- User registration and authentication
- Add public URLs for monitoring
- Duplicate URL validation for each user
- Automatic page-title extraction
- Scheduled checks performed by a dedicated worker container
- SHA-256 content hashing to avoid duplicate snapshots
- Snapshot history displayed in a modal with Previous and Next navigation
- Archive pages to stop scheduled checks
- Reactivate archived pages to resume monitoring
- Automatic `last_checked_at` and `last_changed_at` updates
- Alembic database migrations
- Docker Compose setup with separate API, worker, and PostgreSQL services

## How it works

1. A user adds a URL to monitor.
2. The worker selects tracked pages whose status is `active`.
3. The worker fetches the page with HTTPX.
4. BeautifulSoup extracts readable text and the page title from the HTML response.
5. The worker calculates a SHA-256 hash for the extracted text.
6. The hash is compared with the most recent stored snapshot.
7. If the content hash differs, the worker creates a new snapshot in PostgreSQL.
8. The worker updates `last_checked_at`; it also updates `last_changed_at` when content changes.
9. Archived pages are excluded from future scheduled checks.

## Architecture

The project uses a layered architecture with clear separation between API, service, and data-access layers.

In the service layer, the Unit of Work pattern is implemented using SQLAlchemy's async session directly, without a separate UoW class. This follows SQLAlchemy's design, where the session itself acts as the unit of work.

```mermaid
flowchart LR
    Browser[Browser] --> API[FastAPI API and Web UI]
    API --> DB[(PostgreSQL)]

    Worker[Background Worker\nAPScheduler] --> DB
    Worker --> Websites[Tracked websites]
```

### Docker services

| Service | Responsibility |
|---|---|
| `db` | PostgreSQL database for users, tracked pages, and snapshots |
| `api` | FastAPI application serving Jinja2 pages and REST API endpoints |
| `worker` | APScheduler process that fetches active pages and creates snapshots |

## Tech stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy Async ORM, PostgreSQL, Alembic, APScheduler, HTTPX, BeautifulSoup4, Pydantic

**Frontend:** Jinja2 templates, HTMX, Tailwind CSS, daisyUI, Lucide icons

**Infrastructure:** Docker, Docker Compose, uv

## Run locally

### Prerequisites

- Docker and Docker Compose
- Git

### Development setup

Clone the repository:

```bash
git clone https://github.com/maksymminullin/website-change-monitor.git
cd website-change-monitor
```

Create the local development environment file from the template:

```bash
cp .env.example .env
```

Update values in `.env` if needed, then start all services:

```bash
docker compose up --build
```

Apply database migrations in a separate terminal:

```bash
docker compose exec api alembic upgrade head
```

Open the application:

```text
http://localhost:8000
```

## Test setup

Create a test environment file from the test template:

```bash
cp .env.test.example .env.test
```

The test configuration uses a separate database named `monitor_test_db`. Create it once in the local PostgreSQL container:

```bash
docker compose exec db psql -U postgres -d postgres -c "CREATE DATABASE monitor_test_db;"
```

The `.env.test` file must point to the local test database:

```env
DATABASE_URL=postgresql+asyncpg://postgres:test_password@localhost:5433/monitor_test_db
JWT_SECRET_KEY=replace_with_test_jwt_secret
```

> `.env` and `.env.test` contain local values and should not be committed. `.env.example` and `.env.test.example` are safe templates committed to the repository.

## Useful commands

Stop the stack:

```bash
docker compose down
```

View logs for all containers:

```bash
docker compose logs --tail=100 -f
```

View logs for a specific container:

```bash
docker compose logs --tail=100 -f api
docker compose logs --tail=100 -f worker
docker compose logs --tail=100 -f db
```

Apply migrations:

```bash
docker compose exec api alembic upgrade head
```

Create a new migration:

```bash
docker compose exec api alembic revision --autogenerate -m "describe change"
```

Open a PostgreSQL shell:

```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

## Limitations

The worker currently uses HTTPX and BeautifulSoup, so it can monitor websites that return meaningful content in their initial HTML response.

Websites that render content entirely in the browser with JavaScript can return empty or incomplete HTML to the worker. Browser-based rendering is not implemented yet.

## TODO

- Write automated tests
- Add browser-based parsing with Playwright for JavaScript-rendered websites and complex single-page applications
- Add a snapshot-diff view that highlights added and removed content between two snapshots, similar to GitHub's file-diff interface
