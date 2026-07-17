from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

DEFAULT_ASSUMPTIONS_SOURCE = "内置默认参数"


def _finite_number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} 必须是有限数值")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} 必须是有限数值")
    return result


@dataclass(frozen=True)
class RoiAssumptions:
    commission_rate: float = 0.15
    storage_usd: float = 0.10
    conversion_rate: float = 0.10
    ad_traffic_share: float = 0.20
    weight_low_cny_per_kg: float = 8.50
    weight_high_cny_per_kg: float = 10.60
    volume_low_cny_per_cbm: float = 1360.0
    volume_high_cny_per_cbm: float = 1900.0

    def __post_init__(self) -> None:
        values = {
            item.name: _finite_number(item.name, getattr(self, item.name)) for item in fields(self)
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

        if not 0 <= self.commission_rate < 1:
            raise ValueError("commission_rate 必须大于等于 0 且小于 1")
        if self.storage_usd < 0:
            raise ValueError("storage_usd 必须大于等于 0")
        if not 0 < self.conversion_rate <= 1:
            raise ValueError("conversion_rate 必须大于 0 且小于等于 1")
        if not 0 <= self.ad_traffic_share <= 1:
            raise ValueError("ad_traffic_share 必须大于等于 0 且小于等于 1")
        for name in (
            "weight_low_cny_per_kg",
            "weight_high_cny_per_kg",
            "volume_low_cny_per_cbm",
            "volume_high_cny_per_cbm",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} 必须大于等于 0")

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> RoiAssumptions:
        allowed = {item.name for item in fields(cls)}
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise ValueError("未知参数：" + "、".join(unknown))
        return cls(**dict(values))

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


def load_roi_assumptions(path: str | Path | None) -> tuple[RoiAssumptions, str]:
    if path is None:
        return RoiAssumptions(), DEFAULT_ASSUMPTIONS_SOURCE

    source = Path(path).resolve()
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"ROI 参数文件不是有效 JSON：{exc.msg}") from exc
    if not isinstance(raw, dict):
        raise ValueError("ROI 参数文件根节点必须是 JSON 对象")
    return RoiAssumptions.from_mapping(raw), source.name
