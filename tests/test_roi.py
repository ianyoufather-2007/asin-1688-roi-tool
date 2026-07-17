import math

import httpx
import pytest

import asin_1688_roi.roi as roi_module
from asin_1688_roi.http_retry import RetryPolicy
from asin_1688_roi.models import CandidateProduct, TargetProduct
from asin_1688_roi.roi import calculate_results, fetch_fx_usd_cny, logistics_cost
from asin_1688_roi.roi_config import RoiAssumptions


def test_logistics_takes_maximum():
    target = TargetProduct(
        asin="B000000000",
        selling_price_usd=39.99,
        cpc_usd=1,
        package_weight_kg=2.0,
        package_length_cm=40,
        package_width_cm=30,
        package_height_cm=10,
    )
    assert logistics_cost(target) == 22.8


def test_roi_complete():
    target = TargetProduct(
        asin="B000000000",
        selling_price_usd=39.99,
        cpc_usd=1,
        package_weight_kg=2.0,
        fba_fee_usd=7.0,
    )
    candidate = CandidateProduct(
        asin=target.asin,
        search_keyword="测试",
        comparison_price_cny=50,
        product_url="https://detail.1688.com/offer/1.html",
        match_status="有效-人工确认",
    )
    result = calculate_results([target], [candidate], 7.0)[0]
    assert result.procurement_cost_cny == 50
    assert result.roi is not None


@pytest.mark.parametrize("fx", [0, -1, math.inf, math.nan, True])
def test_calculation_rejects_non_positive_exchange_rate(fx):
    with pytest.raises(ValueError, match="汇率"):
        calculate_results([], [], fx)


def test_non_positive_procurement_price_is_not_used():
    target = TargetProduct(
        asin="B000000001",
        selling_price_usd=20,
        cpc_usd=1,
        package_weight_kg=1,
        fba_fee_usd=5,
    )
    candidate = CandidateProduct(
        asin=target.asin,
        search_keyword="测试",
        comparison_price_cny=-10,
        match_status="有效-人工确认",
    )

    result = calculate_results([target], [candidate], 7)[0]

    assert result.procurement_cost_cny is None
    assert result.valid_candidate_count == 0
    assert "采购价" in result.status


def test_fetch_fx_uses_current_official_frankfurter_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == roi_module.FX_API_URL
        return httpx.Response(200, json={"date": "2026-07-15", "rate": 7.1234})

    rate = fetch_fx_usd_cny(transport=httpx.MockTransport(handler))

    assert rate == 7.1234


def test_fetch_fx_retries_retryable_server_error():
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"rate": 7.2})

    rate = fetch_fx_usd_cny(
        transport=httpx.MockTransport(handler),
        retry_policy=RetryPolicy(max_attempts=2, backoff_seconds=0),
    )

    assert rate == 7.2
    assert attempts == 2


@pytest.mark.parametrize("rate", [None, 0, -1, math.inf, True])
def test_fetch_fx_rejects_invalid_rate(rate):
    def handler(_request: httpx.Request) -> httpx.Response:
        if rate == math.inf:
            return httpx.Response(200, content=b'{"rate": Infinity}')
        return httpx.Response(200, json={"rate": rate})

    transport = httpx.MockTransport(handler)

    with pytest.raises(ValueError, match="CNY"):
        fetch_fx_usd_cny(transport=transport)


def test_exchange_rate_source_is_retained_for_traceability():
    target = TargetProduct(asin="B000000001", selling_price_usd=20, cpc_usd=1)

    result = calculate_results(
        [target],
        [],
        7,
        fx_source="运行参数 --fx",
    )[0]

    assert result.fx_source == "运行参数 --fx"


def test_custom_assumptions_change_costs_and_are_snapshotted():
    target = TargetProduct(
        asin="B000000001",
        selling_price_usd=20,
        cpc_usd=1,
        package_weight_kg=2,
        fba_fee_usd=5,
    )
    candidate = CandidateProduct(
        asin=target.asin,
        search_keyword="测试",
        comparison_price_cny=50,
        product_url="https://detail.1688.com/offer/1.html",
        match_status="有效-人工确认",
    )
    assumptions = RoiAssumptions(
        commission_rate=0.10,
        storage_usd=0.20,
        conversion_rate=0.20,
        ad_traffic_share=0.10,
        weight_low_cny_per_kg=5,
        weight_high_cny_per_kg=6,
        volume_low_cny_per_cbm=1000,
        volume_high_cny_per_cbm=1200,
    )

    result = calculate_results(
        [target],
        [candidate],
        7,
        assumptions=assumptions,
        assumptions_source="test-profile.json",
    )[0]

    assert result.commission_cny == 14
    assert result.storage_cost_cny == pytest.approx(1.4)
    assert result.ad_cost_cny == pytest.approx(3.5)
    assert result.logistics_cost_cny == 12
    assert result.assumptions_source == "test-profile.json"
    assert '"commission_rate":0.1' in result.assumptions_snapshot
