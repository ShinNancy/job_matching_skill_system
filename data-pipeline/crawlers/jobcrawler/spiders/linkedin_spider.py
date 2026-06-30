# spiders/linkedin_spider.py
# LinkedIn yêu cầu cookie auth. Nếu chưa có LINKEDIN_LI_AT thì sẽ lưu debug HTML
# để biết trang trả về gì (thường là login page hoặc limited results).

import json
import os

import scrapy
from scrapy.http import Response

from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class LinkedInSpider(BaseJobSpider):
    name = "linkedin"
    allowed_domains = ["linkedin.com", "www.linkedin.com"]

    # LinkedIn chặn bot trong robots.txt → override riêng cho spider này
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["linkedin"]

    def start_requests(self):
        """Override để inject auth cookie nếu có."""
        li_at = os.getenv("LINKEDIN_LI_AT", "").strip()
        config = self.site_config
        meta = self._build_playwright_meta(config.wait_for_selector)

        if li_at:
            meta["playwright_context_kwargs"] = {
                "storage_state": {
                    "cookies": [{
                        "name": "li_at",
                        "value": li_at,
                        "domain": ".linkedin.com",
                        "path": "/",
                        "secure": True,
                        "httpOnly": True,
                    }]
                }
            }
        else:
            self.logger.warning("LINKEDIN_LI_AT chưa set — crawl không cần auth (kết quả giới hạn)")

        yield scrapy.Request(
            url=config.start_url,
            meta={**meta, "page_num": 1},
            callback=self.parse_listing,
            errback=self.handle_error,
        )

    def extract_job_links(self, response: Response) -> list[str]:
        # ── Thử JSON-LD ──────────────────────────────────────────────────────
        for raw in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(raw.strip())
            except (json.JSONDecodeError, ValueError):
                continue
            candidates = data if isinstance(data, list) else [data]
            for obj in candidates:
                if not isinstance(obj, dict):
                    continue
                if obj.get("@type") == "ItemList":
                    links = [item["url"] for item in obj.get("itemListElement", []) if item.get("url")]
                    if links:
                        self.logger.info("Tìm thấy %d links từ JSON-LD", len(links))
                        return links
                main = obj.get("mainEntity", {})
                if isinstance(main, dict) and main.get("@type") == "ItemList":
                    links = [
                        item["item"]["url"]
                        for item in main.get("itemListElement", [])
                        if isinstance(item.get("item"), dict) and item["item"].get("url")
                    ]
                    if links:
                        self.logger.info("Tìm thấy %d links từ JSON-LD mainEntity", len(links))
                        return links

        # ── CSS selectors LinkedIn đã biết ───────────────────────────────────
        selectors = [
            "a.base-card__full-link::attr(href)",
            "a[data-tracking-control-name*='search-card']::attr(href)",
            "a[href*='/jobs/view/']::attr(href)",
        ]
        for sel in selectors:
            links = response.css(sel).getall()
            if links:
                self.logger.info("Tìm thấy %d links từ CSS selector: %s", len(links), sel)
                return links

        # ── DEBUG ─────────────────────────────────────────────────────────────
        self.logger.warning("Không tìm thấy job links — lưu debug_linkedin.html")
        with open("debug_linkedin.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        return []
