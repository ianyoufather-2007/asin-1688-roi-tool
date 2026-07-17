import httpx
import pytest

from asin_1688_roi.http_retry import RetryPolicy, request_with_retry


def _response(status_code: int) -> httpx.Response:
    return httpx.Response(
        status_code,
        request=httpx.Request("GET", "https://example.test/resource"),
    )


def test_retryable_status_succeeds_on_next_attempt_without_real_sleep():
    responses = iter([_response(503), _response(200)])
    delays: list[float] = []

    response = request_with_retry(
        lambda: next(responses),
        policy=RetryPolicy(max_attempts=3, backoff_seconds=0.25),
        sleep=delays.append,
        operation_name="测试请求",
    )

    assert response.status_code == 200
    assert delays == [0.25]


def test_transport_error_is_raised_after_retry_limit():
    attempts = 0

    def fail():
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("offline")

    with pytest.raises(httpx.ConnectError, match="offline"):
        request_with_retry(
            fail,
            policy=RetryPolicy(max_attempts=2, backoff_seconds=0),
            sleep=lambda _seconds: None,
        )

    assert attempts == 2


def test_non_retryable_client_error_fails_immediately():
    attempts = 0

    def fail():
        nonlocal attempts
        attempts += 1
        return _response(400)

    with pytest.raises(httpx.HTTPStatusError):
        request_with_retry(fail, policy=RetryPolicy(max_attempts=3, backoff_seconds=0))

    assert attempts == 1


@pytest.mark.parametrize(
    ("max_attempts", "backoff_seconds"),
    [(0, 0.5), (True, 0.5), (3, -0.1), (3, float("inf"))],
)
def test_retry_policy_rejects_invalid_values(max_attempts, backoff_seconds):
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=max_attempts, backoff_seconds=backoff_seconds)
