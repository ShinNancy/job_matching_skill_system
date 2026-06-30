# spiders/topcv_spider.py
# TopCV dùng JSON-LD với cấu trúc lồng:
# CollectionPage → mainEntity (ItemList) → itemListElement[i].item.url

import json

from scrapy.http import Response

from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class TopCVSpider(BaseJobSpider):
    name = "topcv"
    allowed_domains = ["topcv.vn", "www.topcv.vn"]

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["topcv"]

    def extract_job_links(self, response: Response) -> list[str]:
        """
        TopCV dùng JSON-LD CollectionPage với mainEntity là ItemList.
        Path: data["mainEntity"]["itemListElement"][i]["item"]["url"]
        """
        for raw in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(raw.strip())
            except (json.JSONDecodeError, ValueError):
                continue

            # JSON-LD có thể là object hoặc array
            candidates = data if isinstance(data, list) else [data]
            for obj in candidates:
                if not isinstance(obj, dict):
                    continue

                # TopCV: CollectionPage chứa mainEntity là ItemList
                main_entity = obj.get("mainEntity", {})
                if isinstance(main_entity, dict) and main_entity.get("@type") == "ItemList":
                    items = main_entity.get("itemListElement", [])
                    links = [
                        item["item"]["url"]
                        for item in items
                        if isinstance(item.get("item"), dict) and item["item"].get("url")
                    ]
                    if links:
                        self.logger.info("Tìm thấy %d job links từ JSON-LD mainEntity", len(links))
                        return links

                # Fallback: ItemList trực tiếp (giống ITViec)
                if obj.get("@type") == "ItemList":
                    links = [item["url"] for item in obj.get("itemListElement", []) if item.get("url")]
                    if links:
                        self.logger.info("Tìm thấy %d job links từ JSON-LD ItemList", len(links))
                        return links

        self.logger.warning("Không tìm thấy job links trong JSON-LD")
        return []
