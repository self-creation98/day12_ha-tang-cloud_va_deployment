"""
In-Memory Rate Limiter — Sliding Window Counter

Giới hạn số request mỗi user trong 1 khoảng thời gian.
Trong production: thay bằng Redis-based rate limiter để scale.
"""
import time
from collections import defaultdict, deque
from fastapi import HTTPException

from app.config import settings


_rate_windows: dict[str, deque] = defaultdict(deque)


def check_rate_limit(key: str):
    """
    Kiểm tra rate limit theo sliding window.
    Raise 429 nếu vượt quá settings.rate_limit_per_minute.
    """
    now = time.time()
    window = _rate_windows[key]

    # Loại bỏ timestamps cũ (ngoài window 60s)
    while window and window[0] < now - 60:
        window.popleft()

    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )

    window.append(now)
