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
# Dépendances d'abord, pour profiter du cache de couches.
# --locked : échoue si uv.lock ne correspond plus à pyproject.toml.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

FROM python:3.14.8-slim-trixie AS runtime
# Utilisateur d'exécution à UID fixe. Le code et l'environnement restent la propriété de
# root : l'application peut les lire, pas les modifier.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app --no-create-home app
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8000
# Fabrique d'application ; un seul journal d'accès, celui de l'application (D-12).
CMD ["uvicorn", "--factory", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
