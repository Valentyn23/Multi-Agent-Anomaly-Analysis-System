"""Шар взаємодії з in-memory сховищем Redis на базі клієнта redis-py.

Забезпечує створення підключення до Redis, виконання перевірки працездатності (ping, set/get/delete)
та коректне закриття з'єднань.
"""

import time
from typing import Optional

import redis

from src.config import settings

# Глобальний екземпляр Redis клієнта (ініціалізується ліниво)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Повертає або ініціалізує синглтон клієнта Redis із пулом з'єднань.

    Використовує URL підключення з settings.redis_url.
    Параметр decode_responses=True забезпечує автоматичне декодування байтів у рядки str.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )
    return _redis_client


def check_redis_connection() -> tuple[bool, str, float]:
    """Перевіряє доступність Redis через PING та тестову операцію запису/читання/видалення ключа.

    Повертає:
        tuple[bool, str, float]: (успіх, повідомлення/деталі, час виконання в мс).
    """
    start_time = time.perf_counter()
    test_key = "health_check:test_key"
    test_val = "ok_val"
    try:
        client = get_redis_client()

        # Крок 1: PING
        if not client.ping():
            latency_ms = (time.perf_counter() - start_time) * 1000
            return False, "Redis не відповів на команду PING", round(latency_ms, 2)

        # Крок 2: Тестовий запис з коротким TTL (10 секунд на випадок збою)
        client.set(test_key, test_val, ex=10)

        # Крок 3: Тестове читання
        read_val = client.get(test_key)
        if read_val != test_val:
            client.delete(test_key)
            latency_ms = (time.perf_counter() - start_time) * 1000
            return False, f"Неспівпадіння значення: очікувалось '{test_val}', отримано '{read_val}'", round(latency_ms, 2)

        # Крок 4: Очищення тестового ключа
        client.delete(test_key)

        latency_ms = (time.perf_counter() - start_time) * 1000
        return True, "Підключення успішне (PING -> PONG, SET/GET/DELETE перевірено)", round(latency_ms, 2)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return False, f"Помилка з'єднання з Redis: {exc}", round(latency_ms, 2)


def close_redis_client() -> None:
    """Коректно закриває з'єднання клієнта Redis."""
    global _redis_client
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
