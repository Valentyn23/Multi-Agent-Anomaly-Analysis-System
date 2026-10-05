"""Централізована конфігурація та налаштування середовища застосунку.

Використовує Pydantic Settings для завантаження, валідації та безпечного управління
змінними середовища з файлу .env без витоку конфіденційних даних у коді чи системі контролю версій.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Кореневий каталог проєкту (де розташований файл .env)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Схема налаштувань застосунку з типізацією, валідацією та обчислюваними URL підключень."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH) if ENV_FILE_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --------------------------------------------------------------------------
    # Параметри середовища застосунку
    # --------------------------------------------------------------------------
    APP_NAME: str = Field(
        default="Мультиагентна система аналізу аномалій у публічних закупівлях",
        description="Назва програмної системи",
    )
    APP_ENV: str = Field(
        default="development",
        description="Тип середовища виконання (development, testing, production)",
    )
    DEBUG: bool = Field(
        default=True,
        description="Прапорець режиму налагодження",
    )

    # --------------------------------------------------------------------------
    # Конфігурація PostgreSQL
    # --------------------------------------------------------------------------
    POSTGRES_DB: str = Field(
        default="prozorro_anomaly_db",
        description="Назва бази даних PostgreSQL",
    )
    POSTGRES_USER: str = Field(
        default="postgres",
        description="Ім'я користувача PostgreSQL",
    )
    POSTGRES_PASSWORD: str = Field(
        ...,
        description="Пароль до бази даних PostgreSQL (обов'язковий параметр з .env)",
    )
    POSTGRES_HOST: str = Field(
        default="localhost",
        description="Хост сервера PostgreSQL",
    )
    POSTGRES_PORT: int = Field(
        default=5432,
        description="Порт сервера PostgreSQL",
    )

    # --------------------------------------------------------------------------
    # Конфігурація графової бази даних Neo4j
    # --------------------------------------------------------------------------
    NEO4J_USER: str = Field(
        default="neo4j",
        description="Ім'я користувача Neo4j",
    )
    NEO4J_PASSWORD: str = Field(
        ...,
        description="Пароль до бази даних Neo4j (обов'язковий параметр з .env)",
    )
    NEO4J_HOST: str = Field(
        default="localhost",
        description="Хост сервера Neo4j",
    )
    NEO4J_HTTP_PORT: int = Field(
        default=7474,
        description="HTTP-порт вебінтерфейсу Neo4j",
    )
    NEO4J_BOLT_PORT: int = Field(
        default=7687,
        description="Порт бінарного протоколу Bolt для Neo4j",
    )
    NEO4J_HEAP_INITIAL_SIZE: str = Field(
        default="512m",
        description="Початковий розмір пам'яті купи JVM для Neo4j",
    )
    NEO4J_HEAP_MAX_SIZE: str = Field(
        default="2G",
        description="Максимальний розмір пам'яті купи JVM для Neo4j",
    )
    NEO4J_PAGECACHE_SIZE: str = Field(
        default="1G",
        description="Розмір дискового кешу сторінок (pagecache) для Neo4j",
    )

    # --------------------------------------------------------------------------
    # Конфігурація Redis
    # --------------------------------------------------------------------------
    REDIS_HOST: str = Field(
        default="localhost",
        description="Хост сервера Redis",
    )
    REDIS_PORT: int = Field(
        default=6379,
        description="Порт сервера Redis",
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Пароль аутентифікації Redis (за наявності)",
    )

    # --------------------------------------------------------------------------
    # Обчислювані рядки підключення (без відкриття мережевих сокетів)
    # --------------------------------------------------------------------------
    @computed_field
    @property
    def postgres_dsn(self) -> str:
        """Формує стандартний синхронний DSN для підключення до PostgreSQL (SQLAlchemy / psycopg2)."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def postgres_async_dsn(self) -> str:
        """Формує асинхронний DSN для підключення до PostgreSQL через asyncpg."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def neo4j_bolt_url(self) -> str:
        """Формує URL підключення за бінарним протоколом Bolt для Neo4j."""
        return f"bolt://{self.NEO4J_HOST}:{self.NEO4J_BOLT_PORT}"

    @computed_field
    @property
    def neo4j_http_url(self) -> str:
        """Формує HTTP URL для доступу до вебінтерфейсу або API Neo4j."""
        return f"http://{self.NEO4J_HOST}:{self.NEO4J_HTTP_PORT}"

    @computed_field
    @property
    def redis_url(self) -> str:
        """Формує URL підключення до Redis (використовується для Celery та кешу)."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    def get_sanitized_summary(self) -> dict[str, str]:
        """Повертає безпечний словник параметрів з'єднання без розкриття паролів.

        Використовується для безпечного логування під час старту та діагностики системи.
        """
        return {
            "environment": self.APP_ENV,
            "postgres": f"{self.POSTGRES_USER}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}",
            "neo4j_bolt": f"{self.NEO4J_USER}@{self.NEO4J_HOST}:{self.NEO4J_BOLT_PORT}",
            "neo4j_http": f"{self.NEO4J_HOST}:{self.NEO4J_HTTP_PORT}",
            "redis": f"{self.REDIS_HOST}:{self.REDIS_PORT}/0 (аутентифікація: {'увімкнена' if self.REDIS_PASSWORD else 'вимкнена'})",
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Повертає кешований екземпляр-синглтон налаштувань застосунку."""
    return Settings()


# Глобальний екземпляр для зручного імпорту в модулях:
# from src.config import settings
settings = get_settings()
