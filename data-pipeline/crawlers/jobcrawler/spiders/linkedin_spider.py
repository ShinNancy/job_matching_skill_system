# spiders/linkedin_spider.py
# LinkedIn spider — CẦN XỬ LÝ ĐẶC BIỆT vì yêu cầu đăng nhập.
#
# ⚠️  QUAN TRỌNG TRƯỚC KHI CHẠY:
#   1. LinkedIn chặn bot rất mạnh (Cloudflare + fingerprinting).
#   2. Crawl mà không đăng nhập chỉ thấy được ~5-10 job đầu tiên.
#   3. Cần inject cookie `li_at` từ browser đã đăng nhập thật.
#
# Cách lấy cookie li_at:
#   - Đăng nhập LinkedIn trên Chrome
#   - F12 → Application → Cookies → linkedin.com → copy giá trị `li_at`
#   - Đặt vào biến môi trường: LINKEDIN_LI_AT=<value>
#
# TODO: Cân nhắc ToS của LinkedIn trước khi crawl thật sự.

import os

import scrapy
from scrapy.http import Response

from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class LinkedInSpider(BaseJobSpider):
    name = "linkedin"
    allowed_domains = ["linkedin.com", "www.linkedin.com"]

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["linkedin"]

    def start_requests(self):
        """Override để inject auth cookie trước khi crawl."""
        li_at = os.getenv("LINKEDIN_LI_AT", "")
        if not li_at:
            self.logger.error(
                "LINKEDIN_LI_AT chưa được set. "
                "Lấy cookie từ browser đã đăng nhập và set biến môi trường này."
            )
            return  # Không crawl nếu chưa có auth

        config = self.site_config
        meta = self._build_playwright_meta(config.wait_for_selector)

        # Inject cookie auth vào Playwright context
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

        yield scrapy.Request(
            url=config.start_url,
            meta={**meta, "page_num": 1},
            callback=self.parse_listing,
            errback=self.handle_error,
        )

    def extract_job_links(self, response: Response) -> list[str]:
        """
        LinkedIn pagination dùng offset (start=0, start=25, start=50...).
        Job links nằm trong thẻ <a class="base-card__full-link">.
        """
        links = response.css("a.base-card__full-link::attr(href)").getall()

        if not links:
            # Thử selector dạng khác nếu LinkedIn thay đổi DOM
            links = response.css("a[data-tracking-control-name='public_jobs_jserp-result_search-card']::attr(href)").getall()

        if not links:
            self.logger.warning("Không tìm thấy job links — LinkedIn có thể đã chặn hoặc thay đổi DOM")

        return links
