# syntax=docker/dockerfile:1
# Image du backend MadaSource.
# Python identique à backend/.python-version et à requires-python (3.14) ;
# uv identique à la version utilisée en local (0.13.0).

FROM ghcr.io/astral-sh/uv:0.13.0 AS uv

FROM python:3.14.8-slim-trixie AS builder
COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dépendances d'abord, pour profiter du cache de couches. --frozen : uv.lock fait foi.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

FROM python:3.14.8-slim-trixie AS runtime
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --no-create-home app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
