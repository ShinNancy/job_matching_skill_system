# spiders/topcv_spider.py
# TopCV dùng JSON-LD CollectionPage với mainEntity là ItemList (lồng nhau).
# Path: data["mainEntity"]["itemListElement"][i]["item"]["url"]
# title + company nằm trong ["item"]["name"] và ["item"]["hiringOrganization"]["name"].

import json

from scrapy.http import Response

from jobcrawler.crawl_strategy import ListingItem
from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class TopCVSpider(BaseJobSpider):
    name = "topcv"
    allowed_domains = ["topcv.vn", "www.topcv.vn"]

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["topcv"]

    def extract_listing_items(self, response: Response) -> list[ListingItem]:
        """
        TopCV: CollectionPage → mainEntity (ItemList) → itemListElement[i].item.url
        Fallback: ItemList trực tiếp (như ITViec).
        """
        for raw in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(raw.strip())
            except (json.JSONDecodeError, ValueError):
                continue

            candidates = data if isinstance(data, list) else [data]
            for obj in candidates:
                if not isinstance(obj, dict):
                    continue

                # Cấu trúc lồng: CollectionPage → mainEntity → ItemList
                main_entity = obj.get("mainEntity", {})
                if isinstance(main_entity, dict) and main_entity.get("@type") == "ItemList":
                    items = self._parse_item_list(main_entity)
                    if items:
                        self.logger.info("TopCV: %d jobs từ JSON-LD mainEntity", len(items))
                        return items

                # Fallback: ItemList trực tiếp
                if obj.get("@type") == "ItemList":
                    items = self._parse_item_list(obj)
                    if items:
                        self.logger.info("TopCV: %d jobs từ JSON-LD ItemList trực tiếp", len(items))
                        return items

        self.logger.warning("TopCV: không tìm thấy job links trong JSON-LD")
        return []

    def _parse_item_list(self, item_list: dict) -> list[ListingItem]:
        """Parse itemListElement — hỗ trợ cả flat ({url}) và nested ({item: {url}})."""
        result = []
        for el in item_list.get("itemListElement", []):
            if not isinstance(el, dict):
                continue

            # TopCV nested: el["item"]["url"]
            inner = el.get("item", {})
            if isinstance(inner, dict) and inner.get("url"):
                url     = inner["url"]
                title   = inner.get("name", "")
                org     = inner.get("hiringOrganization", {})
                company = org.get("name", "") if isinstance(org, dict) else ""
            # Flat: el["url"]
            elif el.get("url"):
                url     = el["url"]
                title   = el.get("name", "")
                org     = el.get("hiringOrganization", {})
                company = org.get("name", "") if isinstance(org, dict) else ""
            else:
                continue

            job_id = self._extract_job_id(url, self.site_config.job_id_pattern)
            result.append(ListingItem(
                job_id=job_id,
                url=url,
                list_checksum=self._make_checksum(title, company),
            ))
        return result
