import scrapy
from urllib.parse import urljoin


class ItviecSpider(scrapy.Spider):
    name = "itviec"
    allowed_domains = ["itviec.com"]
    start_urls = ["https://itviec.com/it-jobs?sort=latest"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 3,
        "AUTOTHROTTLE_ENABLED": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_TIMEOUT": 60,
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse_job_list,
                meta={"playwright": True, "playwright_include_page": False},
            )

    def parse_job_list(self, response):
        # Lấy link các tin tuyển dụng từ trang danh sách.
        # Nếu website đổi cấu trúc HTML, chỉ cần đổi các selector bên dưới.
        job_links = response.css("a[href*='/jobs/']::attr(href)").getall()
        for href in job_links:
            job_url = urljoin(response.url, href)
            if "/subscriptions/" in job_url:
                continue
            yield scrapy.Request(
                job_url,
                callback=self.parse_job_detail,
                meta={"playwright": True, "playwright_include_page": False},
            )

        # Crawl tiếp trang tiếp theo nếu có.
        next_page = response.css("a[rel='next']::attr(href), a.next::attr(href)").get()
        if next_page:
            next_url = urljoin(response.url, next_page)
            yield scrapy.Request(
                next_url,
                callback=self.parse_job_list,
                meta={"playwright": True, "playwright_include_page": False},
            )

    def parse_job_detail(self, response):
        title = self._clean_text(response.css("h1::text").get(default=""))
        company = self._clean_text(
            response.css("h2::text, .company-name::text, [class*='company']::text").get(default="")
        )
        location = self._clean_text(
            response.css(".location::text, [class*='location']::text").get(default="")
        )
        salary = self._clean_text(
            response.css(".salary::text, [class*='salary']::text").get(default="")
        )
        description = self._clean_text(
            " ".join(response.css(".job-description ::text, .description ::text, .content ::text").getall())
        )

        # Lấy job id từ URL nếu có thể.
        source_job_id = ""
        parts = [p for p in response.url.split("/") if p]
        if parts:
            source_job_id = parts[-1]

        yield {
            "source_site": "itviec",
            "source_job_id": source_job_id,
            "source_url": response.url,
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "description": description,
            "raw_html": response.text,
        }

    def _clean_text(self, text):
        if not text:
            return ""
        return " ".join(text.split())
