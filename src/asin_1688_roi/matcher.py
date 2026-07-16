from __future__ import annotations

from difflib import SequenceMatcher

from asin_1688_roi.models import CandidateProduct, TargetProduct
from asin_1688_roi.utils import clean_text, normalize_no, normalize_yes


def _text_score(target: str, candidate: str) -> tuple[float, bool]:
    left, right = clean_text(target).casefold(), clean_text(candidate).casefold()
    if not left:
        return 0.0, False
    if not right:
        return 0.0, True
    if left in right or right in left:
        return 1.0, False
    return SequenceMatcher(None, left, right).ratio(), False


def _number_score(
    target: float | None, candidate: float | None, tolerance: float
) -> tuple[float, bool]:
    if target is None:
        return 0.0, False
    if candidate is None:
        return 0.0, True
    if target == 0:
        return (1.0 if candidate == 0 else 0.0), False
    difference = abs(candidate - target) / abs(target)
    return max(0.0, 1.0 - difference / tolerance), False


def _size_score(target: TargetProduct, candidate: CandidateProduct) -> tuple[float, bool]:
    dimensions = [
        _number_score(target.length_cm, candidate.length_cm, 0.20),
        _number_score(target.width_cm, candidate.width_cm, 0.20),
        _number_score(target.height_cm, candidate.height_cm, 0.20),
    ]
    available = [score for score, missing in dimensions if not missing]
    missing_any = any(missing for _, missing in dimensions)
    if not any(
        value is not None for value in (target.length_cm, target.width_cm, target.height_cm)
    ):
        return 0.0, False
    if not available:
        return 0.0, True
    return sum(available) / len(available), missing_any


def evaluate_candidate(target: TargetProduct, candidate: CandidateProduct) -> CandidateProduct:
    if normalize_yes(candidate.manual_valid):
        candidate.match_score = 100.0
        candidate.match_status = "有效-人工确认"
        candidate.rejection_reason = ""
        return candidate
    if normalize_no(candidate.manual_valid):
        candidate.match_score = 0.0
        candidate.match_status = "无效-人工驳回"
        candidate.rejection_reason = candidate.manual_reason or "人工驳回"
        return candidate

    checks = {
        "材质": (*_text_score(target.material, candidate.material), 20),
        "尺寸": (*_size_score(target, candidate), 20),
        "功能": (*_text_score(target.function, candidate.function), 15),
        "结构": (*_text_score(target.structure, candidate.structure), 20),
        "销售单元": (*_text_score(target.sales_unit, candidate.sales_unit), 10),
        "套装数量": (*_number_score(target.pack_quantity, candidate.pack_quantity, 0.01), 10),
        "配件数量": (
            *_number_score(target.accessory_quantity, candidate.accessory_quantity, 0.01),
            5,
        ),
    }
    weighted = 0.0
    available_weight = 0.0
    missing: list[str] = []
    failed: list[str] = []
    for name, (score, is_missing, weight) in checks.items():
        target_defined = getattr(
            target,
            {
                "材质": "material",
                "尺寸": "length_cm",
                "功能": "function",
                "结构": "structure",
                "销售单元": "sales_unit",
                "套装数量": "pack_quantity",
                "配件数量": "accessory_quantity",
            }[name],
            None,
        ) not in (None, "")
        if name == "尺寸":
            target_defined = any(
                v is not None for v in (target.length_cm, target.width_cm, target.height_cm)
            )
        if not target_defined:
            continue
        available_weight += weight
        weighted += score * weight
        if is_missing:
            missing.append(name)
        elif score < 0.70:
            failed.append(name)
    candidate.match_score = round(weighted / available_weight * 100, 2) if available_weight else 0.0

    hard_fields = {"材质", "结构", "销售单元", "套装数量", "配件数量"}
    hard_failed = [name for name in failed if name in hard_fields]
    hard_missing = [name for name in missing if name in hard_fields]
    if candidate.comparison_price_cny is None:
        failed.append("完整销售单元采购价")
    if hard_failed:
        candidate.match_status = "无效-规格不符"
    elif hard_missing or missing:
        candidate.match_status = "需人工补规格"
    elif failed:
        candidate.match_status = "无效-匹配度不足"
    elif candidate.comparison_price_cny is None:
        candidate.match_status = "需人工补价格"
    elif candidate.match_score >= 85:
        candidate.match_status = "有效-自动"
    else:
        candidate.match_status = "需人工确认"
    candidate.rejection_reason = "；".join(
        (["缺少：" + "、".join(missing)] if missing else [])
        + (["不匹配：" + "、".join(failed)] if failed else [])
    )
    return candidate


def evaluate_all(
    targets: list[TargetProduct], candidates: list[CandidateProduct]
) -> list[CandidateProduct]:
    target_map = {target.asin: target for target in targets}
    return [
        evaluate_candidate(target_map[c.asin], c) if c.asin in target_map else c for c in candidates
    ]


def valid_candidates(candidates: list[CandidateProduct]) -> list[CandidateProduct]:
    return [c for c in candidates if c.match_status in {"有效-自动", "有效-人工确认"}]
