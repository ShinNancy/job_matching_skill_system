# spiders/topcv_spider.py
# TopCV spider — SSR nên không cần Playwright, dùng CSS selector trực tiếp.

from scrapy.http import Response

from jobcrawler.spiders.base.base_spider import BaseJobSpider
from jobcrawler.spiders.base.site_config import SITE_CONFIGS, SiteConfig


class TopCVSpider(BaseJobSpider):
    name = "topcv"
    allowed_domains = ["topcv.vn"]

    @property
    def site_config(self) -> SiteConfig:
        return SITE_CONFIGS["topcv"]

    def extract_job_links(self, response: Response) -> list[str]:
        """
        TopCV render phía server → HTML có sẵn, không cần Playwright.
        Thử __NEXT_DATA__ trước (TopCV cũng dùng Next.js), fallback CSS selector.
        """
        next_data = self._extract_next_data(response)
        if next_data:
            try:
                jobs = next_data["props"]["pageProps"]["jobs"]
                links = [job.get("url") or job.get("link") for job in jobs]
                links = [l for l in links if l]
                if links:
                    return links
            except (KeyError, TypeError):
                pass

        # Fallback: CSS selector
        # TODO: Verify selector bằng cách inspect DOM thực tế trên topcv.vn/viec-lam-it
        self.logger.warning("Dùng CSS selector fallback cho TopCV")
        return response.css("div.job-item a.title::attr(href)").getall()
