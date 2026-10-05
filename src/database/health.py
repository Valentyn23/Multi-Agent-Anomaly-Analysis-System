"""Єдиний модуль перевірки працездатності інфраструктури (Health Check).

Координує діагностику з'єднань із трьома базовими сховищами:
- PostgreSQL (транзакційне первинне сховище);
- Neo4j (графова база даних);
- Redis (in-memory брокер повідомлень та кеш).
"""

from dataclasses import dataclass
from typing import Dict

from src.database.neo4j import check_neo4j_connection, close_neo4j_driver
from src.database.postgres import check_postgres_connection, close_postgres_engine
from src.database.redis import check_redis_connection, close_redis_client


@dataclass
class ServiceHealth:
    """Результат перевірки окремого сервісу інфраструктури."""

    name: str
    is_available: bool
    details: str
    latency_ms: float

    @property
    def status_label(self) -> str:
        """Повертає текстовий статус сервісу."""
        return "OK" if self.is_available else "FAIL"


@dataclass
class InfrastructureHealth:
    """Зведений результат діагностики всієї інфраструктури системи."""

    all_available: bool
    services: Dict[str, ServiceHealth]


def check_infrastructure_health() -> InfrastructureHealth:
    """Виконує комплексну перевірку доступності PostgreSQL, Neo4j та Redis.

    Повертає структурований об'єкт InfrastructureHealth з детальним статусом
    та часом відгуку для кожного сервісу.
    """
    pg_ok, pg_details, pg_latency = check_postgres_connection()
    neo_ok, neo_details, neo_latency = check_neo4j_connection()
    redis_ok, redis_details, redis_latency = check_redis_connection()

    services = {
        "PostgreSQL": ServiceHealth(
            name="PostgreSQL",
            is_available=pg_ok,
            details=pg_details,
            latency_ms=pg_latency,
        ),
        "Neo4j": ServiceHealth(
            name="Neo4j",
            is_available=neo_ok,
            details=neo_details,
            latency_ms=neo_latency,
        ),
        "Redis": ServiceHealth(
            name="Redis",
            is_available=redis_ok,
            details=redis_details,
            latency_ms=redis_latency,
        ),
    }

    all_ok = pg_ok and neo_ok and redis_ok
    return InfrastructureHealth(all_available=all_ok, services=services)


def close_all_infrastructure_connections() -> None:
    """Звільняє всі з'єднання та закриває пули PostgreSQL, Neo4j та Redis."""
    close_postgres_engine()
    close_neo4j_driver()
    close_redis_client()
