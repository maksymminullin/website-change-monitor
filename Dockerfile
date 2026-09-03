FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && \
    DEBIAN_FRONTEND=noninteractive uv run playwright install --with-deps chromium && \
    chmod -R 777 /ms-playwright && \
    rm -rf /var/lib/apt/lists/*

COPY app ./app
COPY main.py ./main.py
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

RUN uv sync --frozen --no-dev --no-editable

RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser
