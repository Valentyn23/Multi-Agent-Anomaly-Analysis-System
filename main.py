"""Головна точка входу мультиагентної системи аналізу аномалій.

На поточному етапі виконує перевірку завантаження конфігурації та готовності середовища.
"""

from src.config import settings


def main() -> None:
    """Виводить безпечну діагностичну інформацію про завантажені налаштування."""
    print("=" * 70)
    print(f" {settings.APP_NAME}")
    print("=" * 70)
    print("Конфігурацію успішно завантажено.\n")

    summary = settings.get_sanitized_summary()
    print(f"Середовище:    {summary['environment']}")
    print(f"PostgreSQL:     {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print(f"Neo4j Bolt:     {settings.NEO4J_HOST}:{settings.NEO4J_BOLT_PORT}")
    print(f"Neo4j HTTP:     {settings.NEO4J_HOST}:{settings.NEO4J_HTTP_PORT}")
    print(f"Redis:          {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print("\nПеревірка згенерованих URI з'єднань (паролі приховано):")
    print(
        f" - PostgreSQL DSN: postgresql://{settings.POSTGRES_USER}:****@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    print(f" - Neo4j Bolt URL: {settings.neo4j_bolt_url}")
    print(f" - Redis URL:      redis://:****@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")
    print("=" * 70)
    print("Конфігурація валідна та готова до наступних етапів системи.")
    print("=" * 70)


if __name__ == "__main__":
    main()
