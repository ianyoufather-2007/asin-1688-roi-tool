from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from asin_1688_roi.models import CandidateProduct
from asin_1688_roi.utils import clean_text, to_float


def is_allowed_1688_url(value: str) -> bool:
    parsed = urlparse(clean_text(value))
    host = (parsed.hostname or "").casefold()
    return parsed.scheme.casefold() == "https" and (
        host == "1688.com" or host.endswith(".1688.com")
    )


def safe_screenshot_name(asin: str, offer_id: str, index: int) -> str:
    safe_asin = re.sub(r"[^A-Za-z0-9_-]+", "_", clean_text(asin)).strip("_-") or "unknown"
    value = clean_text(offer_id) or str(index)
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).replace("..", "_")
    safe_offer = value.strip("._-") or str(index)
    return f"{safe_asin}_{safe_offer}.png"


def enrich_with_browser(
    candidates: list[CandidateProduct],
    *,
    output_dir: str | Path,
    chrome_user_data_dir: str | None = None,
    pause_seconds: float = 2.0,
    limit: int | None = None,
) -> list[CandidateProduct]:
    selected = candidates[:limit] if limit is not None else candidates
    for candidate in selected:
        if candidate.product_url and not is_allowed_1688_url(candidate.product_url):
            raise ValueError(f"拒绝打开非 1688 HTTPS 链接：{candidate.product_url}")
    if not selected:
        return candidates

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as exc:
        raise RuntimeError("请安装浏览器依赖：pip install -e '.[browser]'") from exc

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    options = Options()
    if chrome_user_data_dir:
        options.add_argument(f"--user-data-dir={chrome_user_data_dir}")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        for index, candidate in enumerate(selected, start=1):
            if not candidate.product_url:
                continue
            driver.get(candidate.product_url)
            time.sleep(pause_seconds)
            body = clean_text(driver.find_element("tag name", "body").text)
            candidate.detail_text = body[:30000]
            candidate.source_timestamp = datetime.now().isoformat(timespec="seconds")
            screenshot = directory / safe_screenshot_name(candidate.asin, candidate.offer_id, index)
            driver.save_screenshot(str(screenshot))
            candidate.screenshot_path = str(screenshot)
            prices = [to_float(value) for value in re.findall(r"¥\s*([0-9]+(?:\.[0-9]+)?)", body)]
            prices = [value for value in prices if value is not None]
            if prices:
                observed = "页面识别价格：" + "、".join(
                    f"¥{value:.2f}" for value in sorted(set(prices))
                )
                candidate.detail_text = (candidate.detail_text + "\n" + observed)[:32000]
            # 不自动写入 comparison_price_cny：详情页可能同时含引流价、单件价、阶梯价和配件价。
            moq = re.search(r"(?:起批|起订|最小起订量)[^0-9]{0,8}(\d+(?:\.\d+)?)", body)
            if moq and candidate.min_order_quantity is None:
                candidate.min_order_quantity = float(moq.group(1))
    finally:
        driver.quit()
    return candidates
