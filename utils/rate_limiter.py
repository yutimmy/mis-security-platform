"""Simple rate limiter utilities for controlling external API usage."""

import time
from collections import deque
from time import monotonic
from typing import Deque


class RateLimiter:
    """Token-bucket style rate limiter tracking calls within a rolling window."""

    def __init__(self, max_calls: int, period: float = 60.0) -> None:
        if max_calls < 0:
            raise ValueError("max_calls must be non-negative")
        if period <= 0:
            raise ValueError("period must be positive")

        self.max_calls = max_calls
        self.period = period
        self._timestamps: Deque[float] = deque()

    def acquire(self) -> None:
        """Block until a slot is available, then reserve it. Always succeeds."""
        if self.max_calls == 0:
            # 如果速率限制為 0，永遠等待（實際上不應該發生）
            time.sleep(float("inf"))
            return

        while True:
            now = monotonic()
            self._purge_expired(now)

            if len(self._timestamps) < self.max_calls:
                # 有空位，佔用它
                self._timestamps.append(now)
                return

            # 沒有空位，等待最舊的時間戳過期
            wait_time = self.time_until_available()
            if wait_time > 0:
                # 加一點緩衝時間（100ms）確保清理完成
                time.sleep(wait_time + 0.1)

    def try_acquire(self) -> bool:
        """Return True and reserve a slot if under the limit, otherwise False."""
        if self.max_calls == 0:
            return False

        now = monotonic()
        self._purge_expired(now)

        if len(self._timestamps) >= self.max_calls:
            return False

        self._timestamps.append(now)
        return True

    def time_until_available(self) -> float:
        """Seconds until the next slot frees up (0 when a call is allowed now)."""
        if self.max_calls == 0:
            return float("inf")

        now = monotonic()
        self._purge_expired(now)

        if len(self._timestamps) < self.max_calls:
            return 0.0

        oldest = self._timestamps[0]
        return max(0.0, self.period - (now - oldest))

    def _purge_expired(self, now: float) -> None:
        while self._timestamps and now - self._timestamps[0] >= self.period:
            self._timestamps.popleft()

