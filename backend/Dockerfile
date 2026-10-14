# Image du backend MadaSource.
# Python identique à backend/.python-version et à requires-python (3.14) ;
# uv identique à la version utilisée en local (0.13.0).
# Images épinglées par étiquette et condensat (Jour 7) : une étiquette republiée ne change
# pas l'image construite. Mise à jour : nouvelle étiquette, nouveau condensat, relecture.

FROM ghcr.io/astral-sh/uv:0.13.0@sha256:cdc6093146eb3ff6a40107b38f008b789e050e77ad87865e381d9917da55a168 AS uv

FROM python:3.14.8-slim-trixie@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS builder
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

FROM python:3.14.8-slim-trixie@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS runtime
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
# Fabrique d'application ; un seul journal d'accès, celui de l'application (D-12) ;
# aucune bannière de version (en-tête Server, security-design.md §16).
CMD ["uvicorn", "--factory", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000", \
     "--no-access-log", "--no-server-header"]
