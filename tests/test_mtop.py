import httpx
import pytest

from asin_1688_roi.http_retry import RetryPolicy
from asin_1688_roi.mtop import (
    MTopClient,
    MTopConfigurationError,
    MTopProtocolError,
    MTopResult,
    parse_jsonp,
)


def test_parse_jsonp_wraps_invalid_json_as_protocol_error():
    with pytest.raises(MTopProtocolError, match="JSONP"):
        parse_jsonp("callback({not-json})", "callback")


def test_login_redirect_is_treated_as_authentication_required():
    result = MTopResult(
        status_code=200,
        ret=("FAIL_SYS_REDIRECT",),
        data={"url": "https://login.1688.com/member/signin.htm"},
        trace_id=None,
    )

    assert result.auth_required


def test_client_supports_mock_transport_for_offline_verification():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "h5api.m.1688.com"
        return httpx.Response(
            200,
            text='callback({"ret":["SUCCESS::调用成功"],"data":{"ok":true}})',
        )

    with MTopClient(
        cookie_header="_m_h5_tk=token_1999999999999; _m_h5_tk_enc=encoded",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = client.request(
            api="mtop.example.test",
            version="1.0",
            data="{}",
            callback="callback",
        )

    assert result.ok
    assert result.data == {"ok": True}


def test_client_rejects_empty_required_cookie_values():
    with pytest.raises(MTopConfigurationError, match="Cookie"):
        MTopClient(cookie_header="_m_h5_tk=; _m_h5_tk_enc=")


def test_client_retries_transient_transport_error():
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectError("temporary offline")
        return httpx.Response(
            200,
            text='callback({"ret":["SUCCESS::调用成功"],"data":{"ok":true}})',
        )

    with MTopClient(
        cookie_header="_m_h5_tk=token_1999999999999; _m_h5_tk_enc=encoded",
        transport=httpx.MockTransport(handler),
        retry_policy=RetryPolicy(max_attempts=2, backoff_seconds=0),
    ) as client:
        result = client.request(
            api="mtop.example.test",
            version="1.0",
            data="{}",
            callback="callback",
        )

    assert result.ok
    assert attempts == 2
