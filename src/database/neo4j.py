"""Шар взаємодії з графовою базою даних Neo4j на базі офіційного драйвера neo4j.

Забезпечує керування життєвим циклом Neo4j Driver, створення сесій для виконання Cypher-запитів,
діагностику підключення та коректне звільнення ресурсів.
"""

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional

from neo4j import Driver, GraphDatabase, Session

from src.config import settings

# Глобальний екземпляр драйвера Neo4j (ініціалізується ліниво)
_driver: Optional[Driver] = None


def get_neo4j_driver() -> Driver:
    """Повертає або ініціалізує синглтон драйвера Neo4j із пулом з'єднань.

    Використовує налаштування з settings (bolt_url, user, password).
    """
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_bolt_url,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=10,
        )
    return _driver


@contextmanager
def get_neo4j_session(database: Optional[str] = None) -> Generator[Session, None, None]:
    """Контекстний менеджер для створення та гарантованого закриття сесії Neo4j."""
    driver = get_neo4j_driver()
    session = driver.session(database=database) if database else driver.session()
    try:
        yield session
    finally:
        session.close()


def check_neo4j_connection() -> tuple[bool, str, float]:
    """Перевіряє доступність Neo4j шляхом виконання базового Cypher-запиту RETURN 1 AS result.

    Повертає:
        tuple[bool, str, float]: (успіх, повідомлення/деталі, час виконання в мс).
    """
    start_time = time.perf_counter()
    try:
        driver = get_neo4j_driver()
        # Перевірка базового з'єднання на рівні драйвера
        driver.verify_connectivity()

        # Виконання Cypher-запиту
        with get_neo4j_session() as session:
            record = session.run("RETURN 1 AS result").single()
            latency_ms = (time.perf_counter() - start_time) * 1000
            if record and record["result"] == 1:
                return True, "Підключення успішне (RETURN 1 AS result -> 1)", round(latency_ms, 2)
            return False, f"Неочікувана відповідь від Neo4j: {record}", round(latency_ms, 2)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return False, f"Помилка з'єднання з Neo4j: {exc}", round(latency_ms, 2)


def close_neo4j_driver() -> None:
    """Коректно закриває драйвер Neo4j та звільняє всі з'єднання пулу."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
