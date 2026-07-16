"""MTop client adapted from FengYing1314/crawler-1688 (MIT)."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx

MTOP_APP_KEY = "12574478"
TOKEN_ERROR_MARKERS = (
    "FAIL_SYS_TOKEN_EMPTY",
    "FAIL_SYS_TOKEN_EXOIRED",
    "FAIL_SYS_TOKEN_EXPIRED",
    "FAIL_SYS_ILLEGAL_ACCESS",
)


class MTopConfigurationError(ValueError):
    pass


class MTopProtocolError(RuntimeError):
    pass


class MTopAuthenticationError(RuntimeError):
    pass


def parse_cookie_header(cookie_header: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for part in cookie_header.split(";"):
        name, separator, value = part.strip().partition("=")
        if separator and name:
            cookies[name] = value
    return cookies


def calculate_mtop_sign(token_cookie: str, timestamp_ms: str, app_key: str, data: str) -> str:
    token, separator, _ = token_cookie.partition("_")
    if not separator or not token:
        raise MTopConfigurationError("_m_h5_tk 不包含有效 token")
    return hashlib.md5(f"{token}&{timestamp_ms}&{app_key}&{data}".encode()).hexdigest()


def parse_jsonp(payload: str, callback: str) -> dict[str, Any]:
    text = payload.strip()
    prefix = f"{callback}("
    if not text.startswith(prefix):
        raise MTopProtocolError(f"响应不是预期 JSONP callback：{callback}")
    suffix = 2 if text.endswith(");") else 1 if text.endswith(")") else 0
    if not suffix:
        raise MTopProtocolError("JSONP 缺少结束括号")
    try:
        value = json.loads(text[len(prefix) : -suffix])
    except json.JSONDecodeError as exc:
        raise MTopProtocolError(f"JSONP 内部 JSON 无效：{exc}") from exc
    if not isinstance(value, dict):
        raise MTopProtocolError("JSONP 根节点不是对象")
    return value


@dataclass(frozen=True)
class MTopResult:
    status_code: int
    ret: tuple[str, ...]
    data: dict[str, Any]
    trace_id: str | None

    @property
    def ok(self) -> bool:
        return any(item.startswith("SUCCESS::") for item in self.ret)

    @property
    def security_challenge(self) -> bool:
        markers = ("RGV587_ERROR::SM", "FAIL_SYS_USER_VALIDATE")
        return any(any(marker in item for marker in markers) for item in self.ret)

    @property
    def auth_required(self) -> bool:
        markers = (
            "FAIL_SYS_SESSION_EXPIRED",
            "FAIL_SYS_TOKEN_EMPTY",
            "FAIL_SYS_TOKEN_EXOIRED",
            "FAIL_SYS_TOKEN_EXPIRED",
        )
        login_url = str(self.data.get("url", "")) + str(self.data.get("h5url", ""))
        return any(any(marker in item for marker in markers) for item in self.ret) or (
            "login." in login_url
        )


class MTopClient:
    def __init__(
        self,
        *,
        cookie_header: str,
        referer: str = "https://s.1688.com/",
        timeout: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ):
        cookies = parse_cookie_header(cookie_header)
        for required in ("_m_h5_tk", "_m_h5_tk_enc"):
            if not cookies.get(required):
                raise MTopConfigurationError(f"Cookie 缺少 {required}")
        jar = httpx.Cookies()
        for name, value in cookies.items():
            jar.set(name, value, domain=".1688.com", path="/")
        self._referer = referer
        self._client = httpx.Client(
            cookies=jar,
            timeout=timeout,
            transport=transport,
            headers={
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": referer,
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/150.0.0.0 Safari/537.36"
                ),
            },
        )

    def __enter__(self) -> MTopClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _cookie_value(self, name: str) -> str | None:
        values = [cookie.value for cookie in self._client.cookies.jar if cookie.name == name]
        return values[-1] if values else None

    def request(
        self,
        *,
        api: str,
        version: str,
        data: str,
        callback: str,
        referer: str | None = None,
        jsv: str = "2.7.4",
        extra_query: Mapping[str, str] | None = None,
    ) -> MTopResult:
        endpoint = f"https://h5api.m.1688.com/h5/{api.casefold()}/{version}/"
        previous_token: str | None = None
        for attempt in range(2):
            timestamp = str(int(time.time() * 1000))
            token_cookie = self._cookie_value("_m_h5_tk")
            if token_cookie is None:
                raise MTopConfigurationError("Cookie 中的 MTop token 已消失")
            query = {
                "jsv": jsv,
                "appKey": MTOP_APP_KEY,
                "t": timestamp,
                "sign": calculate_mtop_sign(token_cookie, timestamp, MTOP_APP_KEY, data),
                "api": api,
                "v": version,
                "type": "jsonp",
                "dataType": "jsonp",
                "timeout": "20000",
                "callback": callback,
                "data": data,
            }
            if extra_query:
                query.update(extra_query)
            response = self._client.get(
                endpoint, params=query, headers={"Referer": referer or self._referer}
            )
            response.raise_for_status()
            payload = parse_jsonp(response.text, callback)
            raw_ret = payload.get("ret", [])
            ret = (
                tuple(str(item) for item in raw_ret)
                if isinstance(raw_ret, list)
                else (str(raw_ret),)
            )
            refreshed = self._cookie_value("_m_h5_tk")
            token_error = any(marker in item for marker in TOKEN_ERROR_MARKERS for item in ret)
            if (
                attempt == 0
                and token_error
                and refreshed not in {None, token_cookie, previous_token}
            ):
                previous_token = token_cookie
                continue
            raw_data = payload.get("data", {})
            return MTopResult(
                status_code=response.status_code,
                ret=ret,
                data=raw_data if isinstance(raw_data, dict) else {"value": raw_data},
                trace_id=payload.get("traceId"),
            )
        raise MTopProtocolError("MTop token 刷新重试失败")
