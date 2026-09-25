"""Resilience utilities: exponential backoff with jitter, rate-limit handling, and timeout retries."""

import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Set, Tuple, Type

from aletheia.evaluation.llm.client import LLMAPIError, LLMTimeoutError

logger = logging.getLogger("aletheia.reliability.resilience")

RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    LLMTimeoutError,
    LLMAPIError,
    ConnectionError,
    TimeoutError,
)


def is_retryable_error(exc: Exception) -> bool:
    """Determine whether an error is transient and safe to retry."""
    if isinstance(exc, LLMTimeoutError):
        return True

    if isinstance(exc, LLMAPIError):
        # 429 Too Many Requests, 500 Internal, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout
        err_msg = str(exc).lower()
        if any(code in err_msg for code in ["429", "rate limit", "500", "502", "503", "504", "overloaded", "quota"]):
            return True
        return False

    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True

    return False


def execute_with_retry(
    func: Callable[..., Any],
    *args,
    max_retries: int = 3,
    initial_backoff: float = 0.2,
    backoff_factor: float = 2.0,
    max_backoff: float = 5.0,
    jitter: bool = True,
    retry_hook: Optional[Callable[[int, Exception, float], None]] = None,
    **kwargs,
) -> Any:
    """Execute a callable with exponential backoff and jitter for transient errors.
    
    Returns:
        The result of func(*args, **kwargs).
    Raises:
        The final exception if max_retries is exceeded or error is non-retryable.
    """
    last_exception: Optional[Exception] = None
    current_backoff = initial_backoff

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            last_exception = exc
            if attempt == max_retries or not is_retryable_error(exc):
                logger.error(
                    f"Execution failed after {attempt} retries: {exc} (Retryable: {is_retryable_error(exc)})"
                )
                raise

            sleep_duration = min(max_backoff, current_backoff)
            if jitter:
                sleep_duration += random.uniform(0, 0.1 * sleep_duration)

            logger.warning(
                f"[Attempt {attempt + 1}/{max_retries}] Caught transient error '{exc}'. "
                f"Backing off for {sleep_duration:.3f}s before retry..."
            )

            if retry_hook:
                try:
                    retry_hook(attempt + 1, exc, sleep_duration)
                except Exception as hook_err:
                    logger.debug(f"Retry hook error: {hook_err}")

            time.sleep(sleep_duration)
            current_backoff *= backoff_factor

    if last_exception:
        raise last_exception


def retry_with_backoff(
    max_retries: int = 3,
    initial_backoff: float = 0.2,
    backoff_factor: float = 2.0,
    max_backoff: float = 5.0,
    jitter: bool = True,
):
    """Decorator applying exponential backoff retry to LLM completion calls."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return execute_with_retry(
                fn,
                *args,
                max_retries=max_retries,
                initial_backoff=initial_backoff,
                backoff_factor=backoff_factor,
                max_backoff=max_backoff,
                jitter=jitter,
                **kwargs,
            )
        return wrapper
    return decorator
