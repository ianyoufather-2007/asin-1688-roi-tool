import pytest

from asin_1688_roi.search import search_candidates


@pytest.mark.parametrize(
    ("pages", "page_size"),
    [(0, 30), (-1, 30), (1, 0), (1, -1)],
)
def test_search_rejects_non_positive_pagination(pages, page_size):
    with pytest.raises(ValueError, match="正整数"):
        search_candidates(
            object(),
            asin="B000000001",
            keyword="厨房收纳",
            pages=pages,
            page_size=page_size,
        )
