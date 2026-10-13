"""Test de l'endpoint /hello, ajouté par l'utilisateur au Jour 4."""

from fastapi.testclient import TestClient

from app.main import app


def test_hello_returns_greeting() -> None:
    with TestClient(app) as client:
        response = client.get("/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, MadaSource!"}
