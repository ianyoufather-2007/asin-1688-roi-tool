import json

import pytest

from asin_1688_roi import workflow
from asin_1688_roi.models import CandidateProduct


def test_collect_deduplicates_same_offer_across_keywords(tmp_path, monkeypatch):
    source = tmp_path / "targets.csv"
    source.write_text(
        "ASIN,售价,CPC,1688搜索关键词\nB000000001,29.99,0.80,厨房收纳|抽屉收纳\n",
        encoding="utf-8",
    )

    class FakeMTopClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    def fake_search(_mtop, *, asin, keyword, **_kwargs):
        return [
            CandidateProduct(
                asin=asin,
                search_keyword=keyword,
                offer_id="123",
                product_url="https://detail.1688.com/offer/123.html",
            )
        ]

    monkeypatch.setattr(workflow, "MTopClient", FakeMTopClient)
    monkeypatch.setattr(workflow, "search_candidates", fake_search)
    monkeypatch.setattr(workflow, "read_cookie", lambda _path: "test-cookie")

    _targets, candidates = workflow.collect(source, None, pages=1, page_size=30)

    assert len(candidates) == 1
    assert candidates[0].search_keyword == "厨房收纳"


def test_collect_keeps_checkpoint_when_a_later_keyword_fails(tmp_path, monkeypatch):
    source = tmp_path / "targets.csv"
    source.write_text(
        "ASIN,售价,CPC,1688搜索关键词\nB000000001,29.99,0.80,厨房收纳|抽屉收纳\n",
        encoding="utf-8",
    )
    checkpoint = tmp_path / "candidates.json"

    class FakeMTopClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    def fake_search(_mtop, *, asin, keyword, **_kwargs):
        if keyword == "抽屉收纳":
            raise RuntimeError("second keyword failed")
        return [
            CandidateProduct(
                asin=asin,
                search_keyword=keyword,
                offer_id="123",
                product_url="https://detail.1688.com/offer/123.html",
            )
        ]

    monkeypatch.setattr(workflow, "MTopClient", FakeMTopClient)
    monkeypatch.setattr(workflow, "search_candidates", fake_search)
    monkeypatch.setattr(workflow, "read_cookie", lambda _path: "private-cookie-value")

    with pytest.raises(RuntimeError, match="second keyword failed"):
        workflow.collect(
            source,
            None,
            pages=1,
            page_size=30,
            checkpoint_path=checkpoint,
        )

    saved = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [item["offer_id"] for item in saved] == ["123"]
    assert "private-cookie-value" not in checkpoint.read_text(encoding="utf-8")
