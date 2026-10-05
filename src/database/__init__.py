"""Пакет роботи з базами даних та сховищами інфраструктурного шару."""

from src.database.health import (
    InfrastructureHealth,
    ServiceHealth,
    check_infrastructure_health,
    close_all_infrastructure_connections,
)
from src.database.neo4j import (
    check_neo4j_connection,
    close_neo4j_driver,
    get_neo4j_driver,
    get_neo4j_session,
)
from src.database.postgres import (
    check_postgres_connection,
    close_postgres_engine,
    get_db_session,
    get_postgres_engine,
    get_session_factory,
)
from src.database.redis import (
    check_redis_connection,
    close_redis_client,
    get_redis_client,
)

__all__ = [
    # PostgreSQL
    "get_postgres_engine",
    "get_session_factory",
    "get_db_session",
    "check_postgres_connection",
    "close_postgres_engine",
    # Neo4j
    "get_neo4j_driver",
    "get_neo4j_session",
    "check_neo4j_connection",
    "close_neo4j_driver",
    # Redis
    "get_redis_client",
    "check_redis_connection",
    "close_redis_client",
    # Health check
    "ServiceHealth",
    "InfrastructureHealth",
    "check_infrastructure_health",
    "close_all_infrastructure_connections",
]
