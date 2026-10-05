"""Тести шару інфраструктури та підключень до баз даних (PostgreSQL, Neo4j, Redis)."""

import pytest
from sqlalchemy import text

from src.database import (
    check_infrastructure_health,
    check_neo4j_connection,
    check_postgres_connection,
    check_redis_connection,
    close_all_infrastructure_connections,
    get_db_session,
    get_neo4j_driver,
    get_neo4j_session,
    get_postgres_engine,
    get_redis_client,
)


@pytest.fixture(scope="module", autouse=True)
def cleanup_connections() -> None:
    """Гарантоване закриття відкритих з'єднань після виконання тестів модуля."""
    yield
    close_all_infrastructure_connections()


# ------------------------------------------------------------------------------
# Тести PostgreSQL
# ------------------------------------------------------------------------------
def test_postgres_engine_creation() -> None:
    """Перевірка ініціалізації SQLAlchemy Engine."""
    engine = get_postgres_engine()
    assert engine is not None
    assert engine.dialect.name == "postgresql"


def test_postgres_connection_select_1() -> None:
    """Перевірка виконання запиту SELECT 1 через підключення PostgreSQL."""
    is_ok, details, latency_ms = check_postgres_connection()
    assert is_ok is True, f"PostgreSQL недоступний: {details}"
    assert latency_ms > 0
    assert "Підключення успішне" in details


def test_postgres_session_context_manager() -> None:
    """Перевірка роботи контекстного менеджера сесій get_db_session()."""
    with get_db_session() as session:
        result = session.execute(text("SELECT 42 AS answer")).scalar()
        assert result == 42


# ------------------------------------------------------------------------------
# Тести Neo4j
# ------------------------------------------------------------------------------
def test_neo4j_driver_creation() -> None:
    """Перевірка створення офіційного драйвера Neo4j."""
    driver = get_neo4j_driver()
    assert driver is not None


def test_neo4j_connection_return_1() -> None:
    """Перевірка виконання Cypher-запиту RETURN 1 AS result."""
    is_ok, details, latency_ms = check_neo4j_connection()
    assert is_ok is True, f"Neo4j недоступний: {details}"
    assert latency_ms > 0
    assert "Підключення успішне" in details


def test_neo4j_session_cypher_execution() -> None:
    """Перевірка контекстного менеджера сесій get_neo4j_session()."""
    with get_neo4j_session() as session:
        record = session.run("RETURN 100 AS number, 'prozorro' AS text").single()
        assert record is not None
        assert record["number"] == 100
        assert record["text"] == "prozorro"


# ------------------------------------------------------------------------------
# Тести Redis
# ------------------------------------------------------------------------------
def test_redis_client_connection() -> None:
    """Перевірка створення клієнта Redis та виконання команди PING."""
    client = get_redis_client()
    assert client.ping() is True


def test_redis_set_get_delete_cycle() -> None:
    """Перевірка операцій запису, читання та видалення ключів у Redis."""
    is_ok, details, latency_ms = check_redis_connection()
    assert is_ok is True, f"Redis недоступний: {details}"
    assert latency_ms > 0
    assert "Підключення успішне" in details


def test_redis_custom_key_operations() -> None:
    """Перевірка встановлення та видалення кастомного ключа."""
    client = get_redis_client()
    key = "test:unit_test_key"
    client.set(key, "anomaly_detected_flag", ex=5)
    val = client.get(key)
    assert val == "anomaly_detected_flag"
    client.delete(key)
    assert client.get(key) is None


# ------------------------------------------------------------------------------
# Тест єдиного Health Check
# ------------------------------------------------------------------------------
def test_unified_infrastructure_health_check() -> None:
    """Перевірка комплексного діагностичного звіту всіх сервісів інфраструктури."""
    health = check_infrastructure_health()
    assert health.all_available is True, "Не всі сервіси інфраструктури доступні!"

    assert "PostgreSQL" in health.services
    assert health.services["PostgreSQL"].is_available is True
    assert health.services["PostgreSQL"].status_label == "OK"

    assert "Neo4j" in health.services
    assert health.services["Neo4j"].is_available is True
    assert health.services["Neo4j"].status_label == "OK"

    assert "Redis" in health.services
    assert health.services["Redis"].is_available is True
    assert health.services["Redis"].status_label == "OK"
