from asin_1688_roi.matcher import evaluate_candidate
from asin_1688_roi.models import CandidateProduct, TargetProduct


def test_manual_valid_overrides():
    target = TargetProduct(asin="B000000000", selling_price_usd=20, cpc_usd=1, material="PP")
    candidate = CandidateProduct(
        asin=target.asin,
        search_keyword="x",
        material="steel",
        manual_valid="是",
        comparison_price_cny=10,
    )
    evaluated = evaluate_candidate(target, candidate)
    assert evaluated.match_status == "有效-人工确认"
    assert evaluated.match_score == 100


def test_missing_specs_not_auto_valid():
    target = TargetProduct(
        asin="B000000000",
        selling_price_usd=20,
        cpc_usd=1,
        material="PP",
        structure="抽拉",
        sales_unit="1套",
        pack_quantity=1,
    )
    candidate = CandidateProduct(
        asin=target.asin,
        search_keyword="x",
        title="商品",
        comparison_price_cny=10,
    )
    evaluated = evaluate_candidate(target, candidate)
    assert evaluated.match_status == "需人工补规格"


def test_dimension_mismatch_is_not_ignored_when_other_dimensions_match():
    target = TargetProduct(
        asin="B000000000",
        selling_price_usd=20,
        cpc_usd=1,
        length_cm=10,
        width_cm=10,
        height_cm=10,
    )
    candidate = CandidateProduct(
        asin=target.asin,
        search_keyword="x",
        comparison_price_cny=10,
        length_cm=10,
        width_cm=100,
        height_cm=10,
    )

    evaluated = evaluate_candidate(target, candidate)

    assert evaluated.match_status == "无效-匹配度不足"
    assert evaluated.match_score < 85
