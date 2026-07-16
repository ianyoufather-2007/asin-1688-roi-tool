from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from asin_1688_roi.detail_browser import enrich_with_browser
from asin_1688_roi.exporter import write_workbook
from asin_1688_roi.input_io import load_candidates, load_targets
from asin_1688_roi.matcher import evaluate_all
from asin_1688_roi.roi import FX_API_URL, calculate_results, fetch_fx_usd_cny
from asin_1688_roi.workflow import collect, save_candidates_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Amazon ASIN → 1688候选 → 采购价 → 投产比")
    sub = parser.add_subparsers(dest="command", required=True)

    collect_cmd = sub.add_parser("collect", help="从1688按关键词采集候选")
    collect_cmd.add_argument("--input", required=True, type=Path)
    collect_cmd.add_argument("--cookie-file", type=Path)
    collect_cmd.add_argument("--pages", type=int, default=1)
    collect_cmd.add_argument("--page-size", type=int, default=30)
    collect_cmd.add_argument("--output", type=Path, default=Path("outputs/1688_candidates.json"))

    detail_cmd = sub.add_parser("capture-details", help="本地Chrome打开候选页面并保存截图/详情文本")
    detail_cmd.add_argument("--candidates", required=True, type=Path)
    detail_cmd.add_argument("--output-dir", type=Path, default=Path("outputs/screenshots"))
    detail_cmd.add_argument("--chrome-user-data-dir")
    detail_cmd.add_argument("--limit", type=int)
    detail_cmd.add_argument("--output", type=Path, default=Path("outputs/enriched_candidates.xlsx"))
    detail_cmd.add_argument("--input", required=True, type=Path, help="ASIN输入Excel")

    calc = sub.add_parser("calculate", help="读取候选表，匹配并计算投产比")
    calc.add_argument("--input", required=True, type=Path)
    calc.add_argument("--candidates", required=True, type=Path)
    calc.add_argument("--output", type=Path, default=Path("outputs/asin_roi_result.xlsx"))
    calc.add_argument("--fx", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "collect":
            targets, candidates = collect(args.input, args.cookie_file, args.pages, args.page_size)
            save_candidates_json(args.output, candidates)
            workbook = args.output.with_suffix(".xlsx")
            write_workbook(workbook, targets=targets, candidates=candidates, results=[])
            print(
                json.dumps(
                    {"json": str(args.output), "xlsx": str(workbook), "count": len(candidates)},
                    ensure_ascii=False,
                )
            )
            return 0
        if args.command == "capture-details":
            targets = load_targets(args.input)
            candidates = enrich_with_browser(
                load_candidates(args.candidates),
                output_dir=args.output_dir,
                chrome_user_data_dir=args.chrome_user_data_dir,
                limit=args.limit,
            )
            write_workbook(args.output, targets=targets, candidates=candidates, results=[])
            print(args.output)
            return 0
        targets = load_targets(args.input)
        candidates = evaluate_all(targets, load_candidates(args.candidates))
        fx = args.fx if args.fx is not None else fetch_fx_usd_cny()
        fx_source = "运行参数 --fx" if args.fx is not None else FX_API_URL
        results = calculate_results(targets, candidates, fx, fx_source=fx_source)
        write_workbook(args.output, targets=targets, candidates=candidates, results=results)
        print(args.output)
        return 0
    except Exception as exc:  # CLI must return a useful error without a traceback by default.
        print(
            json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
