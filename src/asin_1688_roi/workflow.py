from __future__ import annotations

import json
import os
from pathlib import Path

from asin_1688_roi.exporter import write_workbook
from asin_1688_roi.input_io import load_candidates, load_targets
from asin_1688_roi.matcher import evaluate_all
from asin_1688_roi.models import CandidateProduct
from asin_1688_roi.mtop import MTopClient
from asin_1688_roi.roi import FX_API_URL, calculate_results, fetch_fx_usd_cny
from asin_1688_roi.search import search_candidates


def read_cookie(cookie_file: str | Path | None) -> str:
    if cookie_file:
        value = Path(cookie_file).read_text(encoding="utf-8").strip()
    else:
        value = os.getenv("CRAWLER_1688_COOKIE", "").strip()
    if value.casefold().startswith("cookie:"):
        value = value.split(":", 1)[1].strip()
    if not value:
        raise ValueError("缺少 Cookie：使用 --cookie-file 或 CRAWLER_1688_COOKIE")
    return value


def collect(
    input_path: str | Path,
    cookie_file: str | Path | None,
    pages: int,
    page_size: int,
    *,
    checkpoint_path: str | Path | None = None,
) -> tuple[list, list[CandidateProduct]]:
    targets = load_targets(input_path)
    cookie = read_cookie(cookie_file)
    candidates: list[CandidateProduct] = []
    seen_candidates: set[tuple[str, str]] = set()
    with MTopClient(cookie_header=cookie) as mtop:
        for target in targets:
            if not target.search_keywords:
                continue
            for keyword in target.search_keywords:
                found = search_candidates(
                    mtop,
                    asin=target.asin,
                    keyword=keyword,
                    pages=pages,
                    page_size=page_size,
                )
                for candidate in found:
                    identifier = candidate.offer_id or candidate.product_url
                    if identifier:
                        key = (candidate.asin, identifier)
                        if key in seen_candidates:
                            continue
                        seen_candidates.add(key)
                    candidates.append(candidate)
                if checkpoint_path is not None:
                    save_candidates_json(checkpoint_path, candidates)
    return targets, candidates


def save_candidates_json(path: str | Path, candidates: list[CandidateProduct]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps([candidate.to_dict() for candidate in candidates], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(output)
    return output


def run_calculation(
    *,
    input_path: str | Path,
    candidate_path: str | Path,
    output_path: str | Path,
    fx: float | None,
):
    targets = load_targets(input_path)
    candidates = evaluate_all(targets, load_candidates(candidate_path))
    actual_fx = fx if fx is not None else fetch_fx_usd_cny()
    fx_source = "运行参数 --fx" if fx is not None else FX_API_URL
    results = calculate_results(targets, candidates, actual_fx, fx_source=fx_source)
    return write_workbook(output_path, targets=targets, candidates=candidates, results=results)
