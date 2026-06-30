# spiders/vietnamworks_spider.py
# VietnamWorks render job list phía server — dùng CSS selector trực tiếp.
# Job cards nằm trong div[class*="new-job-card"], link là thẻ <a href*="-jv">.

import json

from scrapy.http import Response

from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class VietnamWorksSpider(BaseJobSpider):
    name = "vietnamworks"
    allowed_domains = ["vietnamworks.com", "www.vietnamworks.com"]

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["vietnamworks"]

    def extract_job_links(self, response: Response) -> list[str]:
        """
        VietnamWorks render job list trong SSR HTML.
        CSS: div.new-job-card > a[href*='-jv']
        URL có query params → strip trước khi dùng.
        """
        # CSS selector — lấy href từ thẻ a bên trong new-job-card
        raw_links = response.css('div[class*="new-job-card"] a[href*="-jv"]::attr(href)').getall()

        # Strip query params: /ten-job-12345-jv?source=... → /ten-job-12345-jv
        links = [url.split("?")[0] for url in raw_links]
        links = [l for l in links if l]  # bỏ empty

        if links:
            self.logger.info("Tìm thấy %d job links từ CSS selector", len(links))
            return links

        # Fallback: thử JSON-LD nếu CSS không ra
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
                    found = [item["url"] for item in obj.get("itemListElement", []) if item.get("url")]
                    if found:
                        return found
                main = obj.get("mainEntity", {})
                if isinstance(main, dict) and main.get("@type") == "ItemList":
                    found = [
                        item["item"]["url"]
                        for item in main.get("itemListElement", [])
                        if isinstance(item.get("item"), dict) and item["item"].get("url")
                    ]
                    if found:
                        return found

        self.logger.warning("Không tìm thấy job links trên VietnamWorks")
        return []
