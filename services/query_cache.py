import threading
import time
from typing import Any, Callable, Dict, Tuple

from core.config import settings


class TTLCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._values: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get_or_set(self, key: str, factory: Callable[[], Any]) -> Any:
        if self.ttl_seconds == 0:
            return factory()

        now = time.time()
        with self._lock:
            entry = self._values.get(key)
            if entry and entry[0] > now:
                return entry[1]

        value = factory()
        with self._lock:
            self._values[key] = (time.time() + self.ttl_seconds, value)
        return value

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            keys_to_remove = [key for key in self._values if key.startswith(prefix)]
            for key in keys_to_remove:
                self._values.pop(key, None)


read_cache = TTLCache(settings.read_cache_ttl_seconds)


def make_cache_key(user_id: int, action: str, parsed: dict) -> str:
    items = sorted((key, value) for key, value in parsed.items() if value is not None)
    return f"user:{user_id}:{action}:{repr(items)}"


def invalidate_user_cache(user_id: int) -> None:
    read_cache.invalidate_prefix(f"user:{user_id}:")
