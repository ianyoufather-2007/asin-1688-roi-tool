from __future__ import annotations

import math
import re
from collections.abc import Iterable


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    text = clean_text(value).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def split_keywords(value: object) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    parts = re.split(r"[|｜,，;；\n]+", text)
    return list(dict.fromkeys(part.strip() for part in parts if part.strip()))


def first_nonempty(mapping: dict[str, object], names: Iterable[str]) -> object:
    for name in names:
        if name in mapping and mapping[name] not in (None, ""):
            return mapping[name]
    return ""


def normalize_yes(value: object) -> bool:
    return clean_text(value).casefold() in {"y", "yes", "true", "1", "是", "有效", "通过"}


def normalize_no(value: object) -> bool:
    return clean_text(value).casefold() in {"n", "no", "false", "0", "否", "无效", "驳回"}
