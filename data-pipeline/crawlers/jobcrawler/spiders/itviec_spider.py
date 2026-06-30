# spiders/itviec_spider.py
# ITViec spider — kế thừa BaseJobSpider

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
        Ưu tiên __NEXT_DATA__ JSON — bền hơn CSS selector vì không đổi khi UI thay đổi.
        Fallback về CSS selector nếu __NEXT_DATA__ không có.
        """
        next_data = self._extract_next_data(response)
        if next_data:
            try:
                jobs = next_data["props"]["pageProps"]["jobs"]
                links = [job["url"] for job in jobs if job.get("url")]
                if links:
                    return links
            except (KeyError, TypeError):
                pass

        # Fallback: CSS selector — cần verify lại bằng cách inspect DOM thực tế
        # TODO: Mở DevTools trên itviec.com/it-jobs và tìm selector đúng
        self.logger.warning("__NEXT_DATA__ không có job links, dùng CSS selector fallback")
        return response.css("h3.title a::attr(href)").getall()
