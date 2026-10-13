"""Schéma OpenAPI : sous /api/v1, désactivé en production (api-conventions.md §13)."""

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute, iter_route_contexts
from fastapi.testclient import TestClient

from app.main import create_app
from tests.support import make_settings

pytestmark = pytest.mark.api

PRODUCTION_URL = "postgresql+asyncpg://madasource:StrongValue42@127.0.0.1:9/madasource"


def test_openapi_and_docs_are_served_under_api_prefix(client: TestClient) -> None:
    schema = client.get("/api/v1/openapi.json").json()

    assert set(schema["paths"]) == {"/api/v1/health/live", "/api/v1/health/ready"}
    assert client.get("/api/v1/docs").status_code == 200


@pytest.mark.parametrize("path", ["/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"])
def test_nothing_is_served_outside_api_prefix(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 404


def test_every_route_is_under_api_prefix(app: FastAPI) -> None:
    # iter_route_contexts : chemins effectifs, y compris ceux des routers inclus.
    paths = {context.path for context in iter_route_contexts(app.routes)}

    assert paths == {
        "/api/v1/openapi.json",
        "/api/v1/docs",
        "/api/v1/docs/oauth2-redirect",
        "/api/v1/health/live",
        "/api/v1/health/ready",
    }


def test_operation_ids_are_stable(app: FastAPI) -> None:
    operation_ids = {
        context.route.operation_id
        for context in iter_route_contexts(app.routes)
        if isinstance(context.route, APIRoute)
    }

    assert operation_ids == {"health_live", "health_ready"}


def test_ready_documents_its_problem_response(client: TestClient) -> None:
    schema = client.get("/api/v1/openapi.json").json()
    responses = schema["paths"]["/api/v1/health/ready"]["get"]["responses"]

    assert "application/problem+json" in responses["503"]["content"]


def test_production_does_not_serve_openapi_or_docs() -> None:
    settings = make_settings(
        app_env="production",
        database_url=PRODUCTION_URL,
        cors_allowed_origins=("https://app.example.com",),
    )
    with TestClient(create_app(settings)) as production_client:
        assert production_client.get("/api/v1/openapi.json").status_code == 404
        assert production_client.get("/api/v1/docs").status_code == 404
        assert production_client.get("/api/v1/health/live").status_code == 200
