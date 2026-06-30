# spiders/linkedin_spider.py
# LinkedIn yêu cầu cookie auth. Nếu chưa có LINKEDIN_LI_AT thì lưu debug HTML.
# list_checksum = MD5(title + company) từ JSON-LD hoặc CSS.

import json
import os

import scrapy
from scrapy.http import Response

from jobcrawler.crawl_strategy import ListingItem
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

    def extract_listing_items(self, response: Response) -> list[ListingItem]:
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
                target = None
                if obj.get("@type") == "ItemList":
                    target = obj
                main = obj.get("mainEntity", {})
                if isinstance(main, dict) and main.get("@type") == "ItemList":
                    target = main
                if target:
                    items = self._parse_jsonld_items(target)
                    if items:
                        self.logger.info("LinkedIn: %d jobs từ JSON-LD", len(items))
                        return items

        # ── CSS selectors LinkedIn đã biết ───────────────────────────────────
        cards = response.css("div.base-card, li.jobs-search__results-list > div")
        if cards:
            items = []
            for card in cards:
                href = (
                    card.css("a.base-card__full-link::attr(href)").get()
                    or card.css("a[data-tracking-control-name*='search-card']::attr(href)").get()
                    or card.css("a[href*='/jobs/view/']::attr(href)").get()
                )
                if not href:
                    continue
                url     = href.split("?")[0]
                title   = card.css("h3.base-search-card__title::text").get(default="").strip()
                company = card.css("h4.base-search-card__subtitle::text").get(default="").strip()
                job_id  = self._extract_job_id(url, self.site_config.job_id_pattern)
                items.append(ListingItem(
                    job_id=job_id,
                    url=url,
                    list_checksum=self._make_checksum(title, company),
                ))
            if items:
                self.logger.info("LinkedIn: %d jobs từ CSS selector", len(items))
                return items

        # ── Fallback: href only (no card structure) ───────────────────────────
        hrefs = response.css("a[href*='/jobs/view/']::attr(href)").getall()
        if hrefs:
            items = []
            for href in hrefs:
                url    = href.split("?")[0]
                job_id = self._extract_job_id(url, self.site_config.job_id_pattern)
                items.append(ListingItem(
                    job_id=job_id,
                    url=url,
                    list_checksum=self._make_checksum(url),
                ))
            self.logger.info("LinkedIn: %d jobs từ href fallback", len(items))
            return items

        # ── DEBUG ─────────────────────────────────────────────────────────────
        self.logger.warning("LinkedIn: không tìm thấy job links — lưu debug_linkedin.html")
        with open("debug_linkedin.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        return []

    def _parse_jsonld_items(self, item_list: dict) -> list[ListingItem]:
        result = []
        for el in item_list.get("itemListElement", []):
            inner = el.get("item", {}) if isinstance(el.get("item"), dict) else el
            url   = inner.get("url", "")
            if not url:
                continue
            title   = inner.get("name", "")
            org     = inner.get("hiringOrganization", {})
            company = org.get("name", "") if isinstance(org, dict) else ""
            job_id  = self._extract_job_id(url, self.site_config.job_id_pattern)
            result.append(ListingItem(
                job_id=job_id,
                url=url,
                list_checksum=self._make_checksum(title, company),
            ))
        return result
