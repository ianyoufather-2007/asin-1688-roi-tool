from __future__ import annotations

import math
from collections import defaultdict

import httpx

from asin_1688_roi.matcher import valid_candidates
from asin_1688_roi.models import CandidateProduct, RoiResult, TargetProduct

COMMISSION_RATE = 0.15
STORAGE_USD = 0.10
CONVERSION_RATE = 0.10
AD_TRAFFIC_SHARE = 0.20
FX_API_URL = "https://api.frankfurter.dev/v2/rate/USD/CNY"


def fetch_fx_usd_cny(timeout: float = 10.0, transport: httpx.BaseTransport | None = None) -> float:
    with httpx.Client(timeout=timeout, transport=transport) as client:
        response = client.get(FX_API_URL)
        response.raise_for_status()
    rate = response.json().get("rate")
    if (
        isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(rate)
        or rate <= 0
    ):
        raise ValueError("汇率接口未返回有效的 USD/CNY")
    return float(rate)


def logistics_cost(target: TargetProduct) -> float | None:
    weight = target.package_weight_kg or target.product_weight_kg
    dimensions = (target.package_length_cm, target.package_width_cm, target.package_height_cm)
    values: list[float] = []
    if weight is not None:
        values.extend([weight * 8.50, weight * 10.60])
    if all(value is not None for value in dimensions):
        volume = dimensions[0] * dimensions[1] * dimensions[2] / 1_000_000
        values.extend([volume * 1360, volume * 1900])
    return max(values) if values else None


def calculate_results(
    targets: list[TargetProduct],
    candidates: list[CandidateProduct],
    fx: float,
    *,
    fx_source: str = "调用方传入",
) -> list[RoiResult]:
    if isinstance(fx, bool) or not math.isfinite(fx) or fx <= 0:
        raise ValueError("USD/CNY 汇率必须是大于 0 的有限数值")
    candidate_map: dict[str, list[CandidateProduct]] = defaultdict(list)
    for candidate in valid_candidates(candidates):
        candidate_map[candidate.asin].append(candidate)
    results: list[RoiResult] = []
    for target in targets:
        valid = [
            c
            for c in candidate_map[target.asin]
            if c.comparison_price_cny is not None and c.comparison_price_cny > 0
        ]
        selected = max(valid, key=lambda c: c.comparison_price_cny or 0) if valid else None
        procurement = selected.comparison_price_cny if selected else None
        logistics = logistics_cost(target)
        revenue = target.selling_price_usd * fx
        commission = revenue * COMMISSION_RATE
        storage = STORAGE_USD * fx
        ad = target.cpc_usd * AD_TRAFFIC_SHARE / CONVERSION_RATE * fx
        profit = None
        margin = None
        roi = None
        missing: list[str] = []
        if procurement is None:
            missing.append("采购价")
        if logistics is None:
            missing.append("重量/包装尺寸")
        if target.fba_fee_usd is None:
            missing.append("FBA")
        if not missing:
            profit = (
                revenue
                - commission
                - procurement
                - logistics
                - target.fba_fee_usd * fx
                - storage
                - ad
            )
            margin = profit / revenue if revenue else None
            denominator = procurement + logistics
            roi = profit / denominator if denominator else None
        results.append(
            RoiResult(
                asin=target.asin,
                selling_price_usd=target.selling_price_usd,
                cpc_usd=target.cpc_usd,
                fx_usd_cny=fx,
                procurement_cost_cny=procurement,
                logistics_cost_cny=logistics,
                fba_fee_usd=target.fba_fee_usd,
                commission_cny=commission,
                storage_cost_cny=storage,
                ad_cost_cny=ad,
                inferred_real_profit_cny=profit,
                inferred_real_margin=margin,
                roi=roi,
                valid_candidate_count=len(valid),
                procurement_source=selected.product_url if selected else "",
                status="完整" if not missing else "缺少：" + "、".join(missing),
                fx_source=fx_source.strip() or "调用方传入",
            )
        )
    return results
