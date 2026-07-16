import math

import pytest

from asin_1688_roi.input_io import load_candidates, load_targets
from asin_1688_roi.utils import split_keywords, to_float


def test_split_keywords():
    assert split_keywords("收纳盒|抽屉收纳，厨房收纳") == ["收纳盒", "抽屉收纳", "厨房收纳"]


def test_to_float():
    assert to_float("¥ 12.50") == 12.5


def test_to_float_rejects_non_finite_numbers():
    assert to_float(math.inf) is None
    assert to_float(-math.inf) is None


def test_to_float_rejects_boolean_cells():
    assert to_float(True) is None
    assert to_float(False) is None


def test_load_targets_reads_tab_separated_file(tmp_path):
    source = tmp_path / "targets.tsv"
    source.write_text(
        "ASIN\t售价\tCPC\t1688搜索关键词\nB000000001\t29.99\t0.80\t厨房收纳|抽屉收纳\n",
        encoding="utf-8",
    )

    targets = load_targets(source)

    assert len(targets) == 1
    assert targets[0].asin == "B000000001"
    assert targets[0].search_keywords == ["厨房收纳", "抽屉收纳"]


def test_load_targets_rejects_invalid_asin(tmp_path):
    source = tmp_path / "targets.csv"
    source.write_text("ASIN,售价,CPC\nnot-an-asin,29.99,0.80\n", encoding="utf-8")

    with pytest.raises(ValueError, match="ASIN"):
        load_targets(source)


def test_load_targets_rejects_negative_business_values(tmp_path):
    source = tmp_path / "targets.csv"
    source.write_text("ASIN,售价,CPC\nB000000001,-1,0.80\n", encoding="utf-8")

    with pytest.raises(ValueError, match="售价"):
        load_targets(source)


def test_load_targets_rejects_empty_dataset(tmp_path):
    source = tmp_path / "targets.csv"
    source.write_text("ASIN,售价,CPC\n", encoding="utf-8")

    with pytest.raises(ValueError, match="未读取到"):
        load_targets(source)


def test_load_targets_rejects_duplicate_asin(tmp_path):
    source = tmp_path / "targets.csv"
    source.write_text(
        "ASIN,售价,CPC\nB000000001,29.99,0.80\nB000000001,39.99,0.90\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="重复 ASIN"):
        load_targets(source)


def test_load_candidates_rejects_non_positive_procurement_price(tmp_path):
    source = tmp_path / "candidates.csv"
    source.write_text(
        "ASIN,1688搜索关键词,完整销售单元采购价\nB000000001,厨房收纳,-10\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="采购价"):
        load_candidates(source)
