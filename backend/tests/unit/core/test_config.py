"""Configuration validée au démarrage (D-11)."""

import secrets

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from tests.support import DEPLOYED_DATABASE_URL, TEST_SIGNING_KEY, make_settings

pytestmark = pytest.mark.unit

PRODUCTION_URL = DEPLOYED_DATABASE_URL


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
        make_settings(app_env="test", database_url="postgresql+asyncpg://u:p@h:5434/madasource")

    settings = make_settings(app_env="test", database_url="postgresql+asyncpg://u:p@h:5434/x_test")
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
    settings = make_settings(app_env="demo", demo_mode=True, database_url=PRODUCTION_URL)

    assert settings.docs_enabled is False


@pytest.mark.parametrize(
    "origin", ["https://app.example.com/", "https://app.example.com/path", "ftp://x", "app"]
)
def test_malformed_cors_origin_is_refused(origin: str) -> None:
    with pytest.raises(ValidationError, match="CORS_ALLOWED_ORIGINS"):
        make_settings(cors_allowed_origins=(origin,))


def test_settings_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("DATABASE_URL", PRODUCTION_URL)
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://a.example.com, http://localhost:3000")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("AUTH_SIGNING_KEY", TEST_SIGNING_KEY)

    settings = Settings()

    assert settings.app_env == "staging"
    assert settings.cors_allowed_origins == ("https://a.example.com", "http://localhost:3000")
    assert settings.log_level == "WARNING"


def test_missing_database_url_prevents_start(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="database_url"):
        Settings()


def test_app_env_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    # Sans APP_ENV, une instance déployée ne doit pas tomber dans le régime de local.
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("DATABASE_URL", PRODUCTION_URL)

    with pytest.raises(ValidationError, match="app_env"):
        Settings()


@pytest.mark.parametrize("password", ["Xy7@Secret:Part99", "p@ss:wo:rd@Leak77"])
def test_database_url_parse_error_does_not_reveal_password(password: str) -> None:
    url = f"postgresql+asyncpg://madasource:{password}@db.example.com:5432/madasource"

    with pytest.raises(ValidationError) as excinfo:
        make_settings(database_url=url)

    message = str(excinfo.value)
    assert "n'est pas une URL" in message
    for fragment in ("Secret", "Part99", "Leak77", "db.example.com"):
        assert fragment not in message


@pytest.mark.parametrize("app_env", ["staging", "production", "demo"])
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"cors_allowed_origins": ("*",)}, "ne peut pas contenir"),
        (
            {"database_url": "postgresql+asyncpg://u:changeme0local0only@h/db"},
            "mot de passe d'exemple",
        ),
        ({"database_url": "postgresql+asyncpg://u:short@h/db"}, "au moins 12"),
        ({"database_url": "postgresql+asyncpg://u@h/db"}, "au moins 12"),
    ],
)
def test_deployed_environments_refuse_dangerous_settings(
    app_env: str, overrides: dict[str, object], message: str
) -> None:
    values: dict[str, object] = {
        "app_env": app_env,
        "demo_mode": app_env == "demo",
        "database_url": PRODUCTION_URL,
        "cors_allowed_origins": ("https://app.example.com",),
    }
    values.update(overrides)
    with pytest.raises(ValidationError, match=message):
        make_settings(**values)


def test_production_refuses_debug_logs() -> None:
    with pytest.raises(ValidationError, match="DEBUG"):
        make_settings(
            app_env="production",
            database_url=PRODUCTION_URL,
            cors_allowed_origins=("https://app.example.com",),
            log_level="DEBUG",
        )


@pytest.mark.parametrize(
    "query",
    [
        # asyncpg reçoit la requête telle quelle : chacune de ces clés remplacerait la cible
        # vérifiée sur l'URL (garde-fou _test).
        *(
            f"{key}=Tail"
            for key in [
                "database",
                "dbname",
                "host",
                "port",
                "user",
                "password",
                "dsn",
                "service",
                "servicefile",
                "passfile",
                "target_session_attrs",
            ]
        ),
        "%64atabase=Tail",
        "SSL=Tail",
        "ssl=require&ssl=Tail",
    ],
)
def test_query_parameter_outside_allowlist_is_refused(query: str) -> None:
    url = f"postgresql+asyncpg://madasource:pw@localhost:5434/madasource_test?{query}"
    with pytest.raises(ValidationError) as excinfo:
        make_settings(app_env="test", database_url=url)

    assert "n'est pas une URL" in str(excinfo.value)
    assert "Tail" not in str(excinfo.value)


@pytest.mark.parametrize("query", ["ssl=require", "prepared_statement_cache_size=0"])
def test_allowlisted_query_parameters_are_accepted(query: str) -> None:
    url = f"postgresql+asyncpg://madasource:pw@localhost:5434/madasource?{query}"
    assert make_settings(database_url=url).database_name == "madasource"


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+asyncpg://madasource:pw@/madasource_test",
        "postgresql+asyncpg://madasource:pw@localhost/madasource_test",
    ],
    ids=["sans-hote", "sans-port"],
)
def test_test_environment_requires_explicit_host_and_port(url: str) -> None:
    # Sinon asyncpg compléterait par PGHOST, PGPORT ou 5432 : un autre serveur que celui vérifié.
    with pytest.raises(ValidationError, match="précise l'hôte et le port"):
        make_settings(app_env="test", database_url=url)


def test_local_environment_accepts_default_port() -> None:
    url = "postgresql+asyncpg://madasource:pw@localhost/madasource"
    assert make_settings(database_url=url).database_name == "madasource"


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+asyncpg://madasource:Pass@Tail@db.example.com/madasource",
        "postgresql+asyncpg://madasource:S3cr@ss:word@db.example.com:5432/madasource",
    ],
)
def test_unencoded_at_sign_in_password_is_refused(url: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_settings(database_url=url)

    assert "n'est pas une URL" in str(excinfo.value)
    assert "Tail" not in str(excinfo.value)
    assert "word" not in str(excinfo.value)


def test_signing_key_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("DATABASE_URL", PRODUCTION_URL)
    monkeypatch.delenv("AUTH_SIGNING_KEY", raising=False)

    with pytest.raises(ValidationError, match="auth_signing_key"):
        Settings()


def test_short_signing_key_is_refused_without_echo() -> None:
    with pytest.raises(ValidationError, match="au moins 43") as excinfo:
        make_settings(auth_signing_key="test-short-Tail")

    assert "Tail" not in str(excinfo.value)


def test_signing_key_is_secret_in_repr() -> None:
    settings = make_settings()

    assert TEST_SIGNING_KEY not in repr(settings)
    assert settings.auth_signing_key.get_secret_value() == TEST_SIGNING_KEY


@pytest.mark.parametrize("app_env", ["staging", "production", "demo"])
def test_example_signing_key_is_refused_when_deployed(app_env: str) -> None:
    with pytest.raises(ValidationError, match="clé de signature d'exemple"):
        make_settings(
            app_env=app_env,
            demo_mode=app_env == "demo",
            database_url=PRODUCTION_URL,
            cors_allowed_origins=("https://app.example.com",),
            auth_signing_key="changeme0signing0key0for0local0development0only",
        )


def test_example_signing_key_is_accepted_locally() -> None:
    key = "changeme0signing0key0for0local0development0only"
    assert make_settings(auth_signing_key=key).auth_signing_key.get_secret_value() == key


@pytest.mark.parametrize(
    ("memory_kib", "time_cost"),
    [(46 * 1024, 1), (19 * 1024, 2), (12 * 1024, 3), (9 * 1024, 4), (7 * 1024, 5), (7 * 1024, 10)],
)
def test_owasp_argon2_profiles_are_accepted(memory_kib: int, time_cost: int) -> None:
    settings = make_settings(password_hash_memory_kib=memory_kib, password_hash_time_cost=time_cost)

    assert settings.password_hash_memory_kib == memory_kib


@pytest.mark.parametrize(
    ("memory_kib", "time_cost"),
    [
        # Juste sous chaque profil de l'OWASP (un produit mémoire x itérations ne suffit pas).
        (46 * 1024 - 1, 1),
        (36 * 1024, 1),
        (19 * 1024 - 1, 2),
        (12 * 1024 - 1, 3),
        (9 * 1024 - 1, 4),
        (7 * 1024 - 1, 5),
        (7 * 1024 - 1, 10),
    ],
)
def test_argon2_below_owasp_minimums_is_refused(memory_kib: int, time_cost: int) -> None:
    with pytest.raises(ValidationError, match="minimums de l'OWASP"):
        make_settings(password_hash_memory_kib=memory_kib, password_hash_time_cost=time_cost)


def test_security_defaults() -> None:
    settings = make_settings()

    assert (
        settings.password_hash_memory_kib,
        settings.password_hash_time_cost,
        settings.password_hash_parallelism,
    ) == (19 * 1024, 2, 1)
    assert (settings.password_min_length, settings.password_max_length) == (12, 128)
    assert settings.max_request_body_bytes == 1024 * 1024


DEPLOYED = {
    "app_env": "production",
    "database_url": PRODUCTION_URL,
    "cors_allowed_origins": ("https://app.example.com",),
}


@pytest.mark.parametrize(
    "key",
    ["a" * 43, " " * 43, "\u00e9" * 43, "abcdefghij" * 5, "test-key with spaces " + "x" * 30],
)
def test_deployed_environment_refuses_handmade_signing_key(key: str) -> None:
    with pytest.raises(ValidationError, match="générée aléatoirement") as excinfo:
        make_settings(**DEPLOYED, auth_signing_key=key)

    assert key not in str(excinfo.value)


def test_deployed_environment_accepts_generated_signing_key() -> None:
    key = secrets.token_urlsafe(48)

    assert (
        make_settings(**DEPLOYED, auth_signing_key=key).auth_signing_key.get_secret_value() == key
    )


def test_handmade_signing_key_is_accepted_locally() -> None:
    assert make_settings(auth_signing_key="a" * 43).app_env == "local"


@pytest.mark.parametrize("value", ["*", "10.0.0.1,*", "0.0.0.0/0", "::/0", "10.0.0.1, 0.0.0.0/0"])
def test_deployed_environment_refuses_trusting_every_proxy(value: str) -> None:
    with pytest.raises(ValidationError, match="FORWARDED_ALLOW_IPS"):
        make_settings(**DEPLOYED, forwarded_allow_ips=value)


@pytest.mark.parametrize("value", ["10.0.0.1", "10.0.0.0/8, 192.168.1.10", "unix:/run/proxy.sock"])
def test_deployed_environment_accepts_a_known_proxy_list(value: str) -> None:
    assert make_settings(**DEPLOYED, forwarded_allow_ips=value).forwarded_allow_ips == value


def test_deployed_environment_accepts_a_known_proxy() -> None:
    assert (
        make_settings(**DEPLOYED, forwarded_allow_ips="10.0.0.1").forwarded_allow_ips == "10.0.0.1"
    )
