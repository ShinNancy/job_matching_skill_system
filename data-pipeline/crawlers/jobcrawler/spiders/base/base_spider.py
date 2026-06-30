# spiders/base/base_spider.py
# BaseJobSpider — Template Method Pattern.
# Spider con implement 2 abstract method: site_config + extract_listing_items.
# CrawlStrategy quyết định có fetch detail hay không (incremental crawling).

import hashlib
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from collections.abc import Generator
from datetime import datetime, timezone

import scrapy
from scrapy.http import Response
from scrapy_playwright.page import PageMethod

from jobcrawler.crawl_strategy import CrawlDecision, CrawlStrategy, ListingItem
from jobcrawler.items import RawJob
from .site_config import SiteConfig

logger = logging.getLogger(__name__)


class BaseJobSpider(scrapy.Spider, ABC):

    # ── Abstract interface ────────────────────────────────────────────────────

    @property
    @abstractmethod
    def site_config(self) -> SiteConfig:
        """Trả về config của site — mỗi spider con định nghĩa một lần."""
        ...

    @abstractmethod
    def extract_listing_items(self, response: Response) -> list[ListingItem]:
        """
        Trích xuất ListingItem từ trang listing.
        Mỗi item chứa: job_id, url, list_checksum (MD5 của title+company+salary).
        """
        ...

    # ── Spider lifecycle ──────────────────────────────────────────────────────

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Kết nối Redis ngay khi spider được khởi tạo.
        # open_spider() là method của Pipeline, không phải Spider — không được gọi tự động.
        redis_client = None
        try:
            import redis as redis_lib
            redis_client = redis_lib.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                socket_connect_timeout=3,
            )
            redis_client.ping()
            logger.info("Redis kết nối OK — incremental crawling bật")
        except Exception as e:
            logger.warning("Redis không kết nối được (%s) — crawl toàn bộ", e)
            redis_client = None

        self.strategy = CrawlStrategy(redis_client, self.site_config.name)
        self._skip_count = 0
        self._fetch_count = 0

    def closed(self, reason: str) -> None:
        """Scrapy gọi method này khi spider kết thúc (khác với close_spider của pipeline)."""
        logger.info(
            "%s: fetch=%d, skip=%d (incremental dedup) — reason=%s",
            self.site_config.name, self._fetch_count, self._skip_count, reason
        )

    # ── Shared crawl flow (Template Method) ──────────────────────────────────

    def start_requests(self) -> Generator:
        config = self.site_config
        yield self._make_listing_request(config.start_url, page_num=1)

    def parse_listing(self, response: Response) -> Generator:
        config = self.site_config
        items = self.extract_listing_items(response)

        for listing_item in items:
            decision = self.strategy.decide(listing_item)

            if decision == CrawlDecision.SKIP:
                self._skip_count += 1
                logger.debug("SKIP %s (fresh, unchanged)", listing_item.job_id)
                continue

            self._fetch_count += 1
            detail_url = response.urljoin(listing_item.url)
            meta = {"listing_item": listing_item}
            if config.requires_playwright:
                meta.update(self._build_playwright_meta(config.wait_for_selector))

            yield scrapy.Request(
                url=detail_url,
                meta=meta,
                callback=self.parse_job,
                errback=self.handle_error,
            )

        # Phân trang: tiếp tục nếu còn items và chưa đạt max_pages
        current_page = response.meta.get("page_num", 1)
        if items and current_page < config.max_pages:
            next_url = f"{config.start_url}?{config.page_param}={current_page + 1}"
            yield self._make_listing_request(next_url, page_num=current_page + 1)

    def parse_job(self, response: Response) -> Generator:
        """Lưu raw HTML + metadata. Cập nhật Redis cache sau khi fetch thành công."""
        config = self.site_config
        listing_item: ListingItem | None = response.meta.get("listing_item")
        html_bytes = response.text.encode("utf-8")

        # Cập nhật Redis — ghi nhận đã crawl thành công
        if listing_item:
            self.strategy.mark_crawled(listing_item)

        yield RawJob(
            source_site=config.name,
            source_job_id=listing_item.job_id if listing_item else self._extract_job_id(response.url, config.job_id_pattern),
            source_url=response.url,
            raw_html=response.text,
            raw_json=self._extract_next_data(response),
            crawled_at=datetime.now(timezone.utc),
            http_status_code=response.status,
            content_length=len(html_bytes),
            content_checksum=hashlib.md5(html_bytes).hexdigest(),
            playwright_used=config.requires_playwright,
            list_checksum=listing_item.list_checksum if listing_item else "",
            source_updated_at=listing_item.source_updated_at if listing_item else None,
        )

    def handle_error(self, failure) -> None:
        """Log lỗi network — tránh request bị drop âm thầm."""
        self.logger.error("Request failed [%s]: %s", failure.type.__name__, failure.request.url)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_listing_request(self, url: str, page_num: int) -> scrapy.Request:
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
        meta: dict = {"playwright": True}
        if wait_selector:
            meta["playwright_page_methods"] = [PageMethod("wait_for_selector", wait_selector)]
        return meta

    @staticmethod
    def _extract_next_data(response: Response) -> dict | None:
        raw = response.css("#__NEXT_DATA__::text").get()
        if raw:
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                pass
        return None

    @staticmethod
    def _extract_job_id(url: str, pattern: str) -> str:
        match = re.search(pattern, url.rstrip("/"))
        if match:
            return match.group(1)
        return hashlib.md5(url.encode()).hexdigest()[:12]

    @staticmethod
    def _make_checksum(*parts: str) -> str:
        """Tạo MD5 checksum từ nhiều phần — dùng để tính list_checksum."""
        combined = "|".join(p.strip().lower() for p in parts)
        return hashlib.md5(combined.encode()).hexdigest()
