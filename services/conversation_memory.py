import time
from collections import defaultdict, deque
from typing import Deque, Dict, List

# Max messages to keep per user (user + assistant pairs)
MAX_HISTORY = 10
# How long to keep history without activity (seconds) — 30 minutes
HISTORY_TTL = 1800


class ConversationMemory:
    """
    In-memory per-user conversation history for multi-turn AI chat.
    Stores the last MAX_HISTORY message pairs per user with TTL expiry.
    """

    def __init__(self) -> None:
        # user_id -> deque of {"role": ..., "content": ...}
        self._history: Dict[int, Deque[dict]] = defaultdict(lambda: deque(maxlen=MAX_HISTORY * 2))
        # user_id -> last activity timestamp
        self._last_active: Dict[int, float] = {}

    def add(self, user_id: int, role: str, content: str) -> None:
        self._expire_if_idle(user_id)
        self._history[user_id].append({"role": role, "content": content})
        self._last_active[user_id] = time.time()

    def get(self, user_id: int) -> List[dict]:
        self._expire_if_idle(user_id)
        return list(self._history[user_id])

    def clear(self, user_id: int) -> None:
        self._history[user_id].clear()
        self._last_active.pop(user_id, None)

    def _expire_if_idle(self, user_id: int) -> None:
        last = self._last_active.get(user_id)
        if last and time.time() - last > HISTORY_TTL:
            self._history[user_id].clear()
            del self._last_active[user_id]


# Singleton — shared across all requests
conversation_memory = ConversationMemory()
