# jobcrawler/middlewares.py
# Custom middlewares — đăng ký trong settings.py nếu muốn bật.

import logging
import time

from scrapy import signals

logger = logging.getLogger(__name__)


# ── Spider Middleware: Crawl Stats ────────────────────────────────────────────
# Log số trang / item / lỗi khi spider kết thúc.
# Đăng ký trong settings.py:
#   SPIDER_MIDDLEWARES = {"jobcrawler.middlewares.CrawlStatsMiddleware": 543}

class CrawlStatsMiddleware:

    @classmethod                        # Fix: phải là classmethod, không phải method thường
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        # Gắn stats dict vào spider để process_spider_output có thể cập nhật
        spider.crawl_stats = {
            "pages_crawled": 0,
            "items_yielded": 0,
            "errors": 0,
            "start_time": time.time(),
        }
        logger.info("Spider '%s' started.", spider.name)

    def spider_closed(self, spider, reason):
        stats = getattr(spider, "crawl_stats", {})
        duration = time.time() - stats.get("start_time", time.time())
        logger.info(
            "Spider '%s' closed | reason=%s | duration=%.1fs | pages=%d | items=%d | errors=%d",
            spider.name, reason, duration,
            stats.get("pages_crawled", 0),
            stats.get("items_yielded", 0),
            stats.get("errors", 0),
        )

    def process_spider_output(self, response, result, spider):
        """Đếm số trang và items đã xử lý."""
        stats = getattr(spider, "crawl_stats", {})
        stats["pages_crawled"] = stats.get("pages_crawled", 0) + 1
        for obj in result:
            if hasattr(obj, "source_url"):  # Là RawJob item
                stats["items_yielded"] = stats.get("items_yielded", 0) + 1
            yield obj

    def process_spider_exception(self, response, exception, spider):
        """Đếm lỗi xảy ra trong spider callback."""
        stats = getattr(spider, "crawl_stats", {})
        stats["errors"] = stats.get("errors", 0) + 1
        logger.error("Spider error on %s: %s", response.url, exception)
        return None  # None = tiếp tục xử lý các middleware khác


# ── Downloader Middleware: Playwright Error Handler ───────────────────────────
# Bắt lỗi Playwright và log rõ ràng thay vì để Scrapy xử lý mặc định.
# Đăng ký trong settings.py:
#   DOWNLOADER_MIDDLEWARES = {"jobcrawler.middlewares.PlaywrightErrorMiddleware": 585}

class PlaywrightErrorMiddleware:

    def process_exception(self, request, exception, spider):
        name = type(exception).__name__

        if "TimeoutError" in name or "PlaywrightTimeout" in name:
            logger.warning("Playwright timeout on %s — sẽ được retry tự động", request.url)
        else:
            logger.error("Playwright error [%s] on %s: %s", name, request.url, exception)

        return None  # None = để Scrapy retry theo RETRY_HTTP_CODES
