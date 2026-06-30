# spiders/vietnamworks_spider.py
# VietnamWorks render job list phía server (SSR).
# Job cards: div[class*="new-job-card"] — link, title, company đều có trong HTML.
# list_checksum = MD5(title + company) — detect nếu job được đổi title hoặc công ty.

import json
import re

from scrapy.http import Response

from jobcrawler.crawl_strategy import ListingItem
from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class VietnamWorksSpider(BaseJobSpider):
    name = "vietnamworks"
    allowed_domains = ["vietnamworks.com", "www.vietnamworks.com"]

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["vietnamworks"]

    def extract_listing_items(self, response: Response) -> list[ListingItem]:
        """
        Lấy job cards từ HTML — mỗi card có div.new-job-card.
        Strip query params khỏi URL vì VietnamWorks thêm tracking params.
        """
        items = []
        cards = response.css('div[class*="new-job-card"]')

        for card in cards:
            # Lấy URL từ thẻ a đầu tiên có href chứa "-jv"
            href = card.css('a[href*="-jv"]::attr(href)').get()
            if not href:
                continue
            url = href.split("?")[0]  # bỏ query params

            # Title và company từ card (nếu có trong HTML)
            title   = card.css('h2::text, h3::text, [class*="title"]::text').get(default="").strip()
            company = card.css('[class*="company"]::text, [class*="employer"]::text').get(default="").strip()

            job_id = self._extract_job_id(url, self.site_config.job_id_pattern)
            items.append(ListingItem(
                job_id=job_id,
                url=url,
                list_checksum=self._make_checksum(title, company, url),
                # url vào checksum để phân biệt khi title/company chưa extract được
            ))

        if items:
            self.logger.info("VietnamWorks: %d jobs từ CSS selector", len(items))
            return items

        # Fallback: JSON-LD
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
                    fallback = []
                    for el in target.get("itemListElement", []):
                        url = (el.get("item", {}) or {}).get("url") or el.get("url")
                        if url:
                            job_id = self._extract_job_id(url, self.site_config.job_id_pattern)
                            fallback.append(ListingItem(
                                job_id=job_id,
                                url=url,
                                list_checksum=self._make_checksum(url),
                            ))
                    if fallback:
                        return fallback

        self.logger.warning("VietnamWorks: không tìm thấy job links")
        return []
