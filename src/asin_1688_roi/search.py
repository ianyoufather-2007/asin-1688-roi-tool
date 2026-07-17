"""1688 search client adapted from FengYing1314/crawler-1688 (MIT)."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from typing import Any
from urllib.parse import quote_from_bytes

from asin_1688_roi.models import CandidateProduct
from asin_1688_roi.mtop import MTopAuthenticationError, MTopClient, MTopProtocolError
from asin_1688_roi.utils import clean_text, to_float

SEARCH_API = "mtop.relationrecommend.WirelessRecommend.recommend"
SEARCH_APP_ID = 32517
SEARCH_JSONP_PREFIX = "fetchTpp_32517_getOfferList"
SEARCH_CALLBACK = f"mtopjsonp{SEARCH_JSONP_PREFIX}3"


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def strip_html(value: str) -> str:
    parser = _TextParser()
    parser.feed(value)
    return "".join(parser.parts).strip()


def encode_keyword_gbk(keyword: str) -> str:
    return quote_from_bytes(keyword.encode("gbk"), safe="")


def build_search_data(keyword: str, page: int, page_size: int, province: str, city: str) -> str:
    params = {
        "verticalProductFlag": "pccps",
        "searchScene": "pcOfferSearch",
        "charset": "GBK",
        "beginPage": page,
        "pageSize": page_size,
        "keywords": encode_keyword_gbk(keyword),
        "spm": "a26352.30366035.searchbox.0",
        "method": "getOfferList",
        "province": province,
        "city": city,
    }
    return json.dumps(
        {
            "appId": SEARCH_APP_ID,
            "params": json.dumps(params, ensure_ascii=False, separators=(",", ":")),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _first_key(data: dict[str, Any], names: tuple[str, ...]) -> Any:
    for node in _walk(data):
        for name in names:
            if name in node and node[name] not in (None, "", []):
                return node[name]
    return ""


def _price_text(data: dict[str, Any]) -> str:
    price_info = data.get("priceInfo") if isinstance(data.get("priceInfo"), dict) else {}
    value = price_info.get("price") or _first_key(data, ("price", "currentPrice", "priceText"))
    return clean_text(value)


def _candidate_from_item(asin: str, keyword: str, item: Any) -> CandidateProduct | None:
    if not isinstance(item, dict) or not isinstance(item.get("data"), dict):
        return None
    data: dict[str, Any] = item["data"]
    offer_id = clean_text(data.get("offerId"))
    title = strip_html(clean_text(data.get("title")))
    if not offer_id or not title:
        return None
    shop = data.get("shop") if isinstance(data.get("shop"), dict) else {}
    shop_addition = data.get("shopAddition") if isinstance(data.get("shopAddition"), dict) else {}
    price_text = _price_text(data)
    return CandidateProduct(
        asin=asin,
        search_keyword=keyword,
        offer_id=offer_id,
        title=title,
        product_url=clean_text(data.get("linkUrl")).replace("http://", "https://", 1),
        image_url=clean_text(_first_key(data, ("imageUrl", "imgUrl", "image", "picUrl"))),
        supplier=clean_text(shop.get("text") or data.get("companyName")),
        shop_url=clean_text(shop_addition.get("shopLinkUrl")).replace("http://", "https://", 1),
        province=clean_text(data.get("province")),
        city=clean_text(data.get("city")),
        page_price_text=price_text,
        # 搜索页价格可能是最低引流价，不自动作为完整销售单元采购价。
        comparison_price_cny=None,
        min_order_quantity=to_float(
            _first_key(data, ("minOrderQuantity", "minOrder", "beginAmount"))
        ),
        sales_text=clean_text(
            _first_key(data, ("saleQuantity", "saleCount", "sales", "tradeQuantity"))
        ),
        return_rate=clean_text(_first_key(data, ("returnRate", "repurchaseRate"))),
        raw_json=json.dumps(data, ensure_ascii=False, separators=(",", ":")),
    )


def search_candidates(
    mtop: MTopClient,
    *,
    asin: str,
    keyword: str,
    pages: int = 1,
    page_size: int = 30,
    province: str = "",
    city: str = "",
) -> list[CandidateProduct]:
    if pages <= 0 or page_size <= 0:
        raise ValueError("pages 和 page_size 必须是正整数")
    candidates: list[CandidateProduct] = []
    seen: set[str] = set()
    for page in range(1, pages + 1):
        result = mtop.request(
            api=SEARCH_API,
            version="2.0",
            data=build_search_data(keyword, page, page_size, province, city),
            callback=SEARCH_CALLBACK,
            referer="https://s.1688.com/",
            extra_query={
                "ignoreLogin": "true",
                "prefix": "h5api",
                "jsonpIncPrefix": SEARCH_JSONP_PREFIX,
                "timeout": "20000",
            },
        )
        if result.security_challenge or result.auth_required:
            raise MTopAuthenticationError("登录态或风控校验失败，请更新完整 Cookie")
        if not result.ok:
            raise MTopProtocolError("1688 搜索失败：" + ", ".join(result.ret))
        inner = result.data.get("data")
        group = inner.get("OFFER") if isinstance(inner, dict) else None
        items = group.get("items") if isinstance(group, dict) else None
        if not isinstance(items, list) or not items:
            break
        for item in items:
            candidate = _candidate_from_item(asin, keyword, item)
            if candidate and candidate.offer_id not in seen:
                seen.add(candidate.offer_id)
                candidates.append(candidate)
        has_more = group.get("hasMore")
        if has_more is False or clean_text(has_more).casefold() == "false":
            break
    return candidates
