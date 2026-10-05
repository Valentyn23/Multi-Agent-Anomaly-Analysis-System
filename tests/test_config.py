"""Модульні тести для централізованої системи конфігурації."""

import pytest
from src.config.settings import Settings, get_settings


def test_settings_loaded_successfully() -> None:
    """Перевірка коректного створення екземпляра налаштувань та завантаження з середовища."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert len(settings.APP_NAME) > 0


def test_postgres_settings_values() -> None:
    """Перевірка зчитування хосту, порту, користувача та бази даних PostgreSQL."""
    settings = get_settings()
    assert settings.POSTGRES_DB == "prozorro_anomaly_db"
    assert settings.POSTGRES_USER == "postgres"
    assert settings.POSTGRES_HOST == "localhost"
    assert settings.POSTGRES_PORT == 5432
    assert len(settings.POSTGRES_PASSWORD) > 0


def test_neo4j_settings_values() -> None:
    """Перевірка зчитування хосту, портів та користувача Neo4j."""
    settings = get_settings()
    assert settings.NEO4J_USER == "neo4j"
    assert settings.NEO4J_HOST == "localhost"
    assert settings.NEO4J_HTTP_PORT == 7474
    assert settings.NEO4J_BOLT_PORT == 7687
    assert len(settings.NEO4J_PASSWORD) > 0


def test_redis_settings_values() -> None:
    """Перевірка зчитування хосту та порту Redis."""
    settings = get_settings()
    assert settings.REDIS_HOST == "localhost"
    assert settings.REDIS_PORT == 6379


def test_connection_uris_generation() -> None:
    """Перевірка коректності формування URI з'єднань без відкриття реальних сокетів."""
    settings = get_settings()

    # PostgreSQL DSN
    assert settings.postgres_dsn.startswith("postgresql://")
    assert f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}" in settings.postgres_dsn

    assert settings.postgres_async_dsn.startswith("postgresql+asyncpg://")
    assert f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}" in settings.postgres_async_dsn

    # Neo4j URLs
    assert settings.neo4j_bolt_url == f"bolt://{settings.NEO4J_HOST}:{settings.NEO4J_BOLT_PORT}"
    assert settings.neo4j_http_url == f"http://{settings.NEO4J_HOST}:{settings.NEO4J_HTTP_PORT}"

    # Redis URL
    assert settings.redis_url.startswith("redis://")
    assert f"{settings.REDIS_HOST}:{settings.REDIS_PORT}/0" in settings.redis_url


def test_sanitized_summary_does_not_leak_secrets() -> None:
    """Перевірка відсутності відкритих паролів у діагностичному зведенні."""
    settings = get_settings()
    summary = settings.get_sanitized_summary()

    for key, value in summary.items():
        assert settings.POSTGRES_PASSWORD not in value, f"Пароль PostgreSQL знайдено у ключі {key}"
        assert settings.NEO4J_PASSWORD not in value, f"Пароль Neo4j знайдено у ключі {key}"
        if settings.REDIS_PASSWORD:
            assert settings.REDIS_PASSWORD not in value, f"Пароль Redis знайдено у ключі {key}"


def test_settings_singleton() -> None:
    """Перевірка, що get_settings повертає той самий кешований екземпляр (патерн Singleton)."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
