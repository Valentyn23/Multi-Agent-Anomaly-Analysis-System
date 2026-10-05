"""Головна точка входу мультиагентної системи аналізу аномалій.

Виконує завантаження конфігурації та комплексну діагностику доступності
всіх інфраструктурних сервісів (PostgreSQL, Neo4j, Redis).
"""

import sys

from src.config import settings
from src.database import check_infrastructure_health, close_all_infrastructure_connections


def main() -> int:
    """Виконує запуск діагностики та відображає стан готовності інфраструктури."""
    print("=" * 70)
    print(f" {settings.APP_NAME}")
    print("=" * 70)
    print("Конфігурація: OK\n")

    print("Стан інфраструктури:")
    health = check_infrastructure_health()

    for name, srv in health.services.items():
        if srv.is_available:
            print(f"  {name:<12}: OK ({srv.latency_ms:.2f} мс)")
        else:
            print(f"  {name:<12}: ПОМИЛКА -> {srv.details}")

    print()
    if health.all_available:
        print("Усі інфраструктурні сервіси доступні.")
        exit_code = 0
    else:
        print("УВАГА: Деякі сервіси інфраструктури недоступні!")
        exit_code = 1

    print("=" * 70)
    close_all_infrastructure_connections()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
