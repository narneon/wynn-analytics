import asyncio
import time


class RateLimiter:
    """
    Simple async rate limiter.

    Allows up to `max_calls` every `period_seconds`.
    Example:
        max_calls=120, period_seconds=60
        means 120 requests per minute.
    """

    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period_seconds = period_seconds

        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        while True:
            async with self._lock:
                now = time.monotonic()

                # Remove timestamps outside the current window
                self._timestamps = [
                    ts for ts in self._timestamps
                    if now - ts < self.period_seconds
                ]

                if len(self._timestamps) < self.max_calls:
                    self._timestamps.append(now)
                    return

                oldest = self._timestamps[0]
                wait_time = self.period_seconds - (now - oldest)

            await asyncio.sleep(max(wait_time, 0.05))