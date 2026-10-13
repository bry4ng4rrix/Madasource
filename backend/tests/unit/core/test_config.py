"""Configuration validée au démarrage (D-11)."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from tests.support import make_settings

pytestmark = pytest.mark.unit

PRODUCTION_URL = "postgresql+asyncpg://madasource:StrongValue42@db.example.com:5432/madasource"


def test_valid_local_settings() -> None:
    settings = make_settings()

    assert settings.app_env == "local"
    assert settings.docs_enabled is True


def test_database_url_is_secret_in_repr() -> None:
    settings = make_settings(database_url="postgresql+asyncpg://user:SuperSecret1@host/db")

    assert "SuperSecret1" not in repr(settings)
    assert "SuperSecret1" not in str(settings.model_dump())


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user:pw@host/db",
        "postgresql+psycopg://user:pw@host/db",
        "sqlite+aiosqlite:///db.sqlite",
    ],
)
def test_database_url_requires_asyncpg_driver(url: str) -> None:
    with pytest.raises(ValidationError, match="postgresql\\+asyncpg"):
        make_settings(database_url=url)


def test_database_url_requires_a_database_name() -> None:
    with pytest.raises(ValidationError, match="nommer une base"):
        make_settings(database_url="postgresql+asyncpg://user:pw@host")


def test_invalid_database_url_error_does_not_reveal_it() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_settings(database_url="not a url with Secret-Value-123")

    assert "Secret-Value-123" not in str(excinfo.value)


def test_test_environment_requires_a_test_database() -> None:
    with pytest.raises(ValidationError, match="_test"):
        make_settings(app_env="test", database_url="postgresql+asyncpg://u:p@h/madasource")

    settings = make_settings(app_env="test", database_url="postgresql+asyncpg://u:p@h/x_test")
    assert settings.database_name == "x_test"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"cors_allowed_origins": ("*",)}, "ne peut pas contenir"),
        ({"cors_allowed_origins": ("http://app.example.com",)}, "HTTPS"),
        ({"database_url": "postgresql+asyncpg://u:changeme0local0only@h/db"}, "mot de passe"),
    ],
)
def test_production_refuses_dangerous_settings(overrides: dict[str, object], message: str) -> None:
    values: dict[str, object] = {
        "app_env": "production",
        "database_url": PRODUCTION_URL,
        "cors_allowed_origins": ("https://app.example.com",),
    }
    values.update(overrides)
    with pytest.raises(ValidationError, match=message):
        make_settings(**values)


def test_production_accepts_safe_settings_and_disables_docs() -> None:
    settings = make_settings(
        app_env="production",
        database_url=PRODUCTION_URL,
        cors_allowed_origins=("https://app.example.com",),
    )

    assert settings.docs_enabled is False


@pytest.mark.parametrize(
    ("app_env", "demo_mode"), [("local", True), ("production", True), ("demo", False)]
)
def test_demo_mode_and_demo_environment_go_together(app_env: str, demo_mode: bool) -> None:
    with pytest.raises(ValidationError, match="DEMO_MODE"):
        make_settings(
            app_env=app_env,
            demo_mode=demo_mode,
            database_url=PRODUCTION_URL,
            cors_allowed_origins=("https://app.example.com",),
        )


def test_demo_environment_disables_docs() -> None:
    assert make_settings(app_env="demo", demo_mode=True).docs_enabled is False


@pytest.mark.parametrize(
    "origin", ["https://app.example.com/", "https://app.example.com/path", "ftp://x", "app"]
)
def test_malformed_cors_origin_is_refused(origin: str) -> None:
    with pytest.raises(ValidationError, match="CORS_ALLOWED_ORIGINS"):
        make_settings(cors_allowed_origins=(origin,))


def test_settings_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://a.example.com, http://localhost:3000")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    settings = Settings()

    assert settings.app_env == "staging"
    assert settings.cors_allowed_origins == ("https://a.example.com", "http://localhost:3000")
    assert settings.log_level == "WARNING"


def test_missing_database_url_prevents_start(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="database_url"):
        Settings()
