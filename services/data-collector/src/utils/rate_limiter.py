"""
Rate limiter for API requests
"""

import asyncio
import time
from typing import Dict, List


class RateLimiter:
    """Async rate limiter using token bucket algorithm"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a rate limit token"""
        async with self.lock:
            now = time.time()

            # Remove old requests outside the window
            self.requests = [req_time for req_time in self.requests
                           if now - req_time < self.window_seconds]

            # Check if we can make a request
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = self.window_seconds - (now - oldest_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    return await self.acquire()

            # Record this request
            self.requests.append(now)

    def get_remaining_requests(self) -> int:
        """Get number of remaining requests in current window"""
        now = time.time()
        recent_requests = [req_time for req_time in self.requests
                          if now - req_time < self.window_seconds]
        return max(0, self.max_requests - len(recent_requests))

    def get_reset_time(self) -> float:
        """Get time when rate limit window resets"""
        if not self.requests:
            return time.time()

        now = time.time()
        oldest_request = min(req_time for req_time in self.requests
                           if now - req_time < self.window_seconds)
        return oldest_request + self.window_seconds