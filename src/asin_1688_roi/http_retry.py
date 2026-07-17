from __future__ import annotations

import logging
import math
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: float = 0.5

    def __post_init__(self) -> None:
        if isinstance(self.max_attempts, bool) or not isinstance(self.max_attempts, int):
            raise ValueError("max_attempts 必须是正整数")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts 必须是正整数")
        if (
            isinstance(self.backoff_seconds, bool)
            or not isinstance(self.backoff_seconds, (int, float))
            or not math.isfinite(self.backoff_seconds)
            or self.backoff_seconds < 0
        ):
            raise ValueError("backoff_seconds 必须是大于等于 0 的有限数值")
        object.__setattr__(self, "backoff_seconds", float(self.backoff_seconds))

    def delay_after(self, attempt: int) -> float:
        return self.backoff_seconds * attempt


def _retryable_status(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code < 600


def request_with_retry(
    operation: Callable[[], httpx.Response],
    *,
    policy: RetryPolicy | None = None,
    sleep: Callable[[float], object] = time.sleep,
    operation_name: str = "HTTP 请求",
    logger: logging.Logger | None = None,
) -> httpx.Response:
    actual_policy = policy or RetryPolicy()
    actual_logger = logger or LOGGER

    for attempt in range(1, actual_policy.max_attempts + 1):
        try:
            response = operation()
        except httpx.TransportError as exc:
            if attempt == actual_policy.max_attempts:
                raise
            reason = type(exc).__name__
        else:
            if not _retryable_status(response.status_code):
                response.raise_for_status()
                return response
            if attempt == actual_policy.max_attempts:
                response.raise_for_status()
            reason = f"HTTP {response.status_code}"
            response.close()

        actual_logger.warning(
            "%s 暂时失败（%s），准备第 %d/%d 次请求",
            operation_name,
            reason,
            attempt + 1,
            actual_policy.max_attempts,
        )
        sleep(actual_policy.delay_after(attempt))

    raise RuntimeError("重试流程异常结束")
