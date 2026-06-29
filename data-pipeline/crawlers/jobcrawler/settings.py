# data-pipeline\crawlers\jobcrawler\settings.py

# Đọc robot.txt
ROBOTSTXT_OBEY = True
# Nghỉ 2s giữa các request tới cùng domain
DOWNLOAD_DELAY = 2
# 0.5x–1.5x delay 
RANDOMIZE_DOWNLOAD_DELAY = True
# Tối đa 2 request song song
CONCURRENT_REQUESTS_PER_DOMAIN = 2 

# Tự giảm tốc khi server phản hồi chậm
AUTOTHROTTLE_ENABLED = True         
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

RETRY_ENABLED = True              
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]

USER_AGENT = (
    "JobMatchResearchBot/1.0 "
    "(Academic Research; "
    "https://github.com/ShinNancy/job_matching_skill_system)"
)

# Sử dụng Playwright thay cho downloader mặc định của Scrapy
# để render các trang có JavaScript (SPA, React, Vue, Angular...)
DOWNLOAD_HANDLERS = {
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "http":  "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Playwright hoạt động trên asyncio, vì vậy Scrapy cần sử dụng
# AsyncioSelectorReactor để tương thích.
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Chọn trình duyệt Chromium để Playwright điều khiển.
# Ngoài ra có thể dùng "firefox" hoặc "webkit".
PLAYWRIGHT_BROWSER_TYPE = "chromium"

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True
}

# Thời gian tối đa (60 giây) chờ trang tải xong trước khi timeout.
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000

# Số lượng request tối đa chạy đồng thời trên toàn bộ spider.
# Vì Playwright tiêu tốn nhiều CPU/RAM nên không nên đặt quá cao.
CONCURRENT_REQUESTS = 4

# Giới hạn số request đồng thời tới cùng một domain,
# giúp giảm tải cho server và tránh bị chặn.
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Chờ 2 giây giữa các request liên tiếp.
# Giúp crawl lịch sự hơn và giảm nguy cơ bị anti-bot phát hiện.
DOWNLOAD_DELAY = 2