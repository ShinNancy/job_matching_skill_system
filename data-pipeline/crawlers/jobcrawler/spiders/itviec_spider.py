# spiders/itviec_spider.py
# ITViec spider — dùng JSON-LD Schema.org ItemList để lấy job URLs.
# ITViec không dùng Next.js __NEXT_DATA__, data nằm trong <script type="application/ld+json">

import json
import re

from scrapy.http import Response

from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class ItViecSpider(BaseJobSpider):
    name = "itviec"
    allowed_domains = ["itviec.com"]

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["itviec"]

    def extract_job_links(self, response: Response) -> list[str]:
        """
        Trích job URLs từ JSON-LD <script type="application/ld+json"> có @type=ItemList.
        Bền hơn CSS selector vì đây là structured data chính thức của site (SEO data).
        """
        # Tìm tất cả JSON-LD blocks — có thể là object hoặc array
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
                        self.logger.info("Tìm thấy %d job links từ JSON-LD ItemList", len(links))
                        return links

        # Fallback: CSS selector (chỉ dùng khi JSON-LD thay đổi)
        self.logger.warning("JSON-LD ItemList không có — dùng CSS selector fallback")
        return response.css('div[class*="job"] a[href*="/it-jobs/"]::attr(href)').getall()
