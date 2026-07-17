import pytest

import asin_1688_roi.detail_browser as detail_browser
from asin_1688_roi.models import CandidateProduct


def test_only_https_1688_urls_are_allowed_for_browser_capture():
    assert detail_browser.is_allowed_1688_url("https://detail.1688.com/offer/123.html")
    assert not detail_browser.is_allowed_1688_url("http://detail.1688.com/offer/123.html")
    assert not detail_browser.is_allowed_1688_url("https://1688.com.example.org/offer/123.html")
    assert not detail_browser.is_allowed_1688_url("file:///C:/Windows/win.ini")


def test_screenshot_name_drops_path_control_characters():
    name = detail_browser.safe_screenshot_name("B000000001", "../bad\\name:42", 1)

    assert name == "B000000001_bad_name_42.png"


def test_browser_rejects_unsafe_url_before_starting_selenium(tmp_path):
    candidate = CandidateProduct(
        asin="B000000001",
        search_keyword="测试",
        product_url="file:///C:/Windows/win.ini",
    )

    with pytest.raises(ValueError, match="非 1688 HTTPS"):
        detail_browser.enrich_with_browser([candidate], output_dir=tmp_path)


def test_browser_empty_input_does_not_require_optional_dependencies(tmp_path):
    assert detail_browser.enrich_with_browser([], output_dir=tmp_path) == []
