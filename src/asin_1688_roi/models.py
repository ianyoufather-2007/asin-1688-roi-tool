from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TargetProduct:
    asin: str
    selling_price_usd: float
    cpc_usd: float
    amazon_title: str = ""
    search_keywords: list[str] = field(default_factory=list)
    material: str = ""
    function: str = ""
    structure: str = ""
    sales_unit: str = ""
    pack_quantity: float | None = None
    accessory_quantity: float | None = None
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    product_weight_kg: float | None = None
    package_length_cm: float | None = None
    package_width_cm: float | None = None
    package_height_cm: float | None = None
    package_weight_kg: float | None = None
    fba_fee_usd: float | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["search_keywords"] = " | ".join(self.search_keywords)
        return value


@dataclass
class CandidateProduct:
    asin: str
    search_keyword: str
    offer_id: str = ""
    title: str = ""
    product_url: str = ""
    image_url: str = ""
    supplier: str = ""
    shop_url: str = ""
    province: str = ""
    city: str = ""
    page_price_text: str = ""
    comparison_price_cny: float | None = None
    min_order_quantity: float | None = None
    sales_text: str = ""
    return_rate: str = ""
    material: str = ""
    function: str = ""
    structure: str = ""
    sales_unit: str = ""
    pack_quantity: float | None = None
    accessory_quantity: float | None = None
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    detail_text: str = ""
    screenshot_path: str = ""
    source_timestamp: str = ""
    manual_valid: str = ""
    manual_reason: str = ""
    match_score: float | None = None
    match_status: str = ""
    rejection_reason: str = ""
    raw_json: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RoiResult:
    asin: str
    selling_price_usd: float
    cpc_usd: float
    fx_usd_cny: float
    procurement_cost_cny: float | None
    logistics_cost_cny: float | None
    fba_fee_usd: float | None
    commission_cny: float
    storage_cost_cny: float
    ad_cost_cny: float
    inferred_real_profit_cny: float | None
    inferred_real_margin: float | None
    roi: float | None
    valid_candidate_count: int
    procurement_source: str
    status: str
    fx_source: str = "调用方传入"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
