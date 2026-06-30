# spiders/vietnamworks_spider.py
# VietnamWorks spider — SPA, cần Playwright để render JavaScript.

from scrapy.http import Response

from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class VietnamWorksSpider(BaseJobSpider):
    name = "vietnamworks"
    allowed_domains = ["vietnamworks.com"]

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["vietnamworks"]

    def extract_job_links(self, response: Response) -> list[str]:
        """
        VietnamWorks là React SPA → Playwright render trước, sau đó parse HTML.
        Thử __NEXT_DATA__ / inline JSON trước, fallback CSS selector.
        """
        # VietnamWorks có thể nhúng data trong <script> tag khác — thử __NEXT_DATA__ trước
        next_data = self._extract_next_data(response)
        if next_data:
            try:
                jobs = next_data["props"]["pageProps"]["jobs"]
                links = [job.get("url") or job.get("jobUrl") for job in jobs]
                links = [l for l in links if l]
                if links:
                    return links
            except (KeyError, TypeError):
                pass

        # Fallback: CSS selector
        # TODO: Inspect DOM thực tế trên vietnamworks.com để verify selector
        self.logger.warning("Dùng CSS selector fallback cho VietnamWorks")
        return response.css("a.job-title::attr(href)").getall()
