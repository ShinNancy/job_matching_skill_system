# data-pipeline/crawlers/jobcrawler/settings.py
# ──────────────────────────────────────────────────────────────────────────────
# Project-level settings cho Scrapy.
# Đây là cấu hình mặc định (môi trường dev/local).
# ──────────────────────────────────────────────────────────────────────────────

import os

# ── BOT IDENTITY ──────────────────────────────────────────────────────────────
# Mô tả  mục đích của bot.
# Giúp website operator liên hệ nếu cần, thể hiện good faith.
BOT_NAME = "jobcrawler"

SPIDER_MODULES = ["jobcrawler.spiders"]
NEWSPIDER_MODULE = "jobcrawler.spiders"

# Dùng Chrome UA thật — bot UA như "JobMatchResearchBot" bị chặn ngay lập tức
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# Headers bổ sung để giống browser thật hơn — giảm khả năng bị block 403
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7", 
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ── CRAWLING ETIQUETTE ────────────────────────────────────────────────────────
ROBOTSTXT_OBEY = True
COOKIES_ENABLED = True          # Bật cookies — một số site cần session cookie để không bị 403         
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# ── AUTO-THROTTLE ─────────────────────────────────────────────────────────────
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False       # True khi cần debug tốc độ crawl

# ── RETRY ─────────────────────────────────────────────────────────────────────
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [403, 429, 500, 502, 503, 504]

# ── PLAYWRIGHT ────────────────────────────────────────────────────────────────
DOWNLOAD_HANDLERS = {
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "http":  "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": ["--no-sandbox", "--disable-dev-shm-usage"],  # Cần trong Docker
}
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60_000
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 4    # Giới hạn memory

# ── ITEM PIPELINES ────────────────────────────────────────────────────────────
# Thứ tự pipeline: số nhỏ = chạy trước.
# Validation trước để không lưu data xấu vào storage.
ITEM_PIPELINES = {
    "jobcrawler.pipelines.ValidationPipeline": 100,
    "jobcrawler.pipelines.DedupPipeline":      200,
    "jobcrawler.pipelines.MinIOPipeline":      300,
    "jobcrawler.pipelines.PostgresPipeline":   400,
}

# ── LOGGING ───────────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# ── DEPTH ─────────────────────────────────────────────────────────────────────
# Giới hạn độ sâu crawl để tránh crawl vô tận trong trường hợp có bug pagination.
DEPTH_LIMIT = 5