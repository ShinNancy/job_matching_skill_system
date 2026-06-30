# spiders/itviec_spider.py
# ITViec dùng JSON-LD Schema.org ItemList trong <script type="application/ld+json">.
# Mỗi phần tử itemListElement có: url, name (job title), hiringOrganization.name.
# list_checksum = MD5(title + company) — đủ để phát hiện job bị rename hoặc đổi công ty.

import json

from scrapy.http import Response

from jobcrawler.crawl_strategy import ListingItem
from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class ItViecSpider(BaseJobSpider):
    name = "itviec"
    allowed_domains = ["itviec.com"]

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["itviec"]

    def extract_listing_items(self, response: Response) -> list[ListingItem]:
        """Trích ListingItem từ JSON-LD ItemList — bền vì là SEO structured data."""
        for raw in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(raw.strip())
            except (json.JSONDecodeError, ValueError):
                continue

            candidates = data if isinstance(data, list) else [data]
            for obj in candidates:
                if not isinstance(obj, dict):
                    continue
                if obj.get("@type") != "ItemList":
                    continue

                items = []
                for el in obj.get("itemListElement", []):
                    url = el.get("url", "")
                    if not url:
                        continue
                    title   = el.get("name", "")
                    org     = el.get("hiringOrganization", {})
                    company = org.get("name", "") if isinstance(org, dict) else ""
                    job_id  = self._extract_job_id(url, self.site_config.job_id_pattern)
                    items.append(ListingItem(
                        job_id=job_id,
                        url=url,
                        list_checksum=self._make_checksum(title, company),
                    ))

                if items:
                    self.logger.info("ITViec: %d jobs từ JSON-LD ItemList", len(items))
                    return items

        # Fallback: CSS selector — khi JSON-LD thay đổi cấu trúc
        self.logger.warning("JSON-LD không có — dùng CSS selector fallback")
        links = response.css('div[class*="job"] a[href*="/it-jobs/"]::attr(href)').getall()
        return [
            ListingItem(
                job_id=self._extract_job_id(url, self.site_config.job_id_pattern),
                url=url,
                list_checksum=self._make_checksum(url),  # checksum tối thiểu
            )
            for url in links
        ]
