import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        token in message
        for token in (
            "rate limit",
            "ratelimit",
            "429",
            "too many requests",
            "service tier capacity exceeded",
            "service_tier_capacity_exceeded",
        )
    )


def call_with_retry(
    fn: Callable[..., T],
    *args: Any,
    max_retries: int = 2,
    base_delay: float = 0.8,
    **kwargs: Any,
) -> T:
    delay = base_delay
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if not is_rate_limit_error(exc) or attempt >= max_retries:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("Retry loop exited unexpectedly.")
