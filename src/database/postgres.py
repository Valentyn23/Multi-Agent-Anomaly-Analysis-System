"""Шар взаємодії з реляційною базою даних PostgreSQL на базі SQLAlchemy 2.x.

Забезпечує створення пулу з'єднань (Engine), фабрики сесій (sessionmaker),
контекстних менеджерів для безпечної роботи з транзакціями та діагностику підключення.
"""

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings

# Глобальний екземпляр Engine (ініціалізується ліниво)
_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker[Session]] = None


def get_postgres_engine() -> Engine:
    """Повертає або ініціалізує синглтон SQLAlchemy Engine із пулом з'єднань.

    Використовує параметри з централізованої конфігурації settings.
    pool_pre_ping=True запобігає використанню обірваних з'єднань у довготривалих процесах.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.postgres_dsn,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Повертає налаштовану фабрику сесій SQLAlchemy 2.x."""
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_postgres_engine()
        _SessionFactory = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _SessionFactory


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Контекстний менеджер для роботи із сесією бази даних.

    Автоматично фіксує (commit) транзакцію у разі успішного завершення блоку,
    виконує відкат (rollback) у разі виникнення помилки та гарантовано закриває сесію.
    """
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_postgres_connection() -> tuple[bool, str, float]:
    """Перевіряє доступність PostgreSQL за допомогою базового запиту SELECT 1.

    Повертає:
        tuple[bool, str, float]: (успіх, повідомлення/деталі, час виконання в мс).
    """
    start_time = time.perf_counter()
    try:
        engine = get_postgres_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            latency_ms = (time.perf_counter() - start_time) * 1000
            if result == 1:
                return True, "Підключення успішне (SELECT 1 -> 1)", round(latency_ms, 2)
            return False, f"Неочікувана відповідь: {result}", round(latency_ms, 2)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return False, f"Помилка з'єднання з PostgreSQL: {exc}", round(latency_ms, 2)


def close_postgres_engine() -> None:
    """Коректно закриває пул з'єднань SQLAlchemy та звільняє ресурси."""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionFactory = None
