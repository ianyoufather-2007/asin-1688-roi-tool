import json
from pathlib import Path

import asin_1688_roi.cli as cli
from asin_1688_roi.models import TargetProduct


def test_calculate_accepts_verbose_and_roi_config(tmp_path, monkeypatch):
    config = tmp_path / "roi.json"
    config.write_text('{"commission_rate": 0.12}', encoding="utf-8")
    output = tmp_path / "result.xlsx"
    captured = {}

    monkeypatch.setattr(
        cli,
        "load_targets",
        lambda _path: [TargetProduct(asin="B000000001", selling_price_usd=20, cpc_usd=1)],
    )
    monkeypatch.setattr(cli, "load_candidates", lambda _path: [])
    monkeypatch.setattr(cli, "evaluate_all", lambda _targets, candidates: candidates)

    def fake_calculate(_targets, _candidates, _fx, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(cli, "calculate_results", fake_calculate)
    monkeypatch.setattr(cli, "write_workbook", lambda path, **_kwargs: Path(path))

    code = cli.main(
        [
            "calculate",
            "--input",
            "input.xlsx",
            "--candidates",
            "candidates.xlsx",
            "--output",
            str(output),
            "--fx",
            "7",
            "--config",
            str(config),
            "--verbose",
        ]
    )

    assert code == 0
    assert captured["assumptions"].commission_rate == 0.12
    assert captured["assumptions_source"] == config.name


def test_collect_uses_output_as_progress_checkpoint(tmp_path, monkeypatch):
    output = tmp_path / "candidates.json"
    captured = {}

    def fake_collect(_input, _cookie, _pages, _page_size, **kwargs):
        captured.update(kwargs)
        return [], []

    monkeypatch.setattr(cli, "collect", fake_collect)
    monkeypatch.setattr(cli, "save_candidates_json", lambda path, _items: Path(path))
    monkeypatch.setattr(cli, "write_workbook", lambda path, **_kwargs: Path(path))

    code = cli.main(
        [
            "collect",
            "--input",
            "input.xlsx",
            "--cookie-file",
            "cookies.txt",
            "--output",
            str(output),
        ]
    )

    assert code == 0
    assert captured["checkpoint_path"] == output


def test_cli_error_json_contains_actionable_hint(tmp_path, capsys):
    missing = tmp_path / "missing.xlsx"

    code = cli.main(
        [
            "calculate",
            "--input",
            str(missing),
            "--candidates",
            str(missing),
            "--fx",
            "7",
        ]
    )

    payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert code == 1
    assert payload["error"] == "FileNotFoundError"
    assert "路径" in payload["hint"]
