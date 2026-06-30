# spiders/base/base_spider.py
# BaseJobSpider — Template Method Pattern.
# Các spider con chỉ cần implement 2 abstract method: site_config và extract_job_links.

import hashlib
import json
import re
from abc import ABC, abstractmethod
from collections.abc import Generator
from datetime import datetime, timezone

import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod

from jobcrawler.items import RawJob
from .site_config import SiteConfig


class BaseJobSpider(scrapy.Spider, ABC):

    # ── Abstract interface ────────────────────────────────────────────────────

    @property
    @abstractmethod
    def site_config(self) -> SiteConfig:
        """Trả về config của site — mỗi spider con định nghĩa một lần."""
        ...

    @abstractmethod
    def extract_job_links(self, response: Response) -> list[str]:
        """Trích xuất danh sách URL job từ trang listing."""
        ...

    # ── Shared crawl flow (Template Method) ──────────────────────────────────

    def start_requests(self) -> Generator:
        """Bắt đầu crawl từ trang 1."""
        config = self.site_config
        yield self._make_listing_request(config.start_url, page_num=1)

    def parse_listing(self, response: Response) -> Generator:
        """Xử lý trang danh sách: yield job requests + request trang tiếp theo."""
        config = self.site_config
        links = self.extract_job_links(response)

        for url in links:
            yield scrapy.Request(
                url=response.urljoin(url),
                meta=self._build_playwright_meta(config.wait_for_selector) if config.requires_playwright else {},
                callback=self.parse_job,
                errback=self.handle_error,
            )

        # Phân trang: tăng page_num đến max_pages
        current_page = response.meta.get("page_num", 1)
        if links and current_page < config.max_pages:
            next_url = f"{config.start_url}?{config.page_param}={current_page + 1}"
            yield self._make_listing_request(next_url, page_num=current_page + 1)

    def parse_job(self, response: Response) -> Generator:
        """Lưu raw HTML + metadata của từng trang job."""
        config = self.site_config
        html_bytes = response.text.encode("utf-8")

        yield RawJob(
            source_site=config.name,
            source_job_id=self._extract_job_id(response.url, config.job_id_pattern),
            source_url=response.url,
            raw_html=response.text,
            raw_json=self._extract_next_data(response),
            crawled_at=datetime.now(timezone.utc),
            http_status_code=response.status,
            content_length=len(html_bytes),
            content_checksum=hashlib.md5(html_bytes).hexdigest(),
            playwright_used=config.requires_playwright,
        )

    def handle_error(self, failure) -> None:
        """Log lỗi network — tránh request bị drop âm thầm."""
        self.logger.error("Request failed [%s]: %s", failure.type.__name__, failure.request.url)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_listing_request(self, url: str, page_num: int) -> scrapy.Request:
        """Tạo Request cho trang listing, kèm meta page_num để track phân trang."""
        config = self.site_config
        meta: dict = {"page_num": page_num}
        if config.requires_playwright:
            meta.update(self._build_playwright_meta(config.wait_for_selector))
        return scrapy.Request(
            url=url,
            meta=meta,
            callback=self.parse_listing,
            errback=self.handle_error,
        )

    @staticmethod
    def _build_playwright_meta(wait_selector: str | None) -> dict:
        """Tạo meta dict cho Playwright request."""
        meta: dict = {"playwright": True}
        if wait_selector:
            meta["playwright_page_methods"] = [PageMethod("wait_for_selector", wait_selector)]
        return meta

    @staticmethod
    def _extract_next_data(response: Response) -> dict | None:
        """
        Trích JSON từ thẻ <script id="__NEXT_DATA__"> của Next.js.
        Bền hơn CSS selector vì đây là data chính thức của app, không phải DOM layout.
        """
        raw = response.css("#__NEXT_DATA__::text").get()
        if raw:
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                pass
        return None

    @staticmethod
    def _extract_job_id(url: str, pattern: str) -> str:
        """
        Trích job ID từ URL bằng regex.
        Nếu không match → fallback MD5 của URL để không bao giờ trả về chuỗi rỗng.
        """
        match = re.search(pattern, url.rstrip("/"))
        if match:
            return match.group(1)
        return hashlib.md5(url.encode()).hexdigest()[:12]
