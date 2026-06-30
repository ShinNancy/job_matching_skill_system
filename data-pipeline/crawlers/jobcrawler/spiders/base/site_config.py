# spiders/base/site_config.py
# Cấu hình tập trung cho từng site — thêm site mới chỉ cần thêm 1 entry ở đây.

from dataclasses import dataclass


@dataclass(frozen=True)
class SiteConfig:
    name: str               # Key định danh site (dùng làm prefix trong MinIO path)
    start_url: str          # URL trang danh sách job đầu tiên
    page_param: str         # Tên query param phân trang (vd: "page", "start")
    max_pages: int          # Giới hạn số trang tối đa để tránh crawl vô tận
    requires_playwright: bool   # True nếu site render bằng JavaScript (SPA)
    wait_for_selector: str | None   # CSS selector chờ load xong (chỉ dùng khi requires_playwright=True)
    download_delay: float   # Giây chờ giữa các request (lịch sự với server)
    job_id_pattern: str     # Regex để extract job ID từ URL


SITE_CONFIGS: dict[str, SiteConfig] = {

    "itviec": SiteConfig(
        name="itviec",
        start_url="https://itviec.com/it-jobs",
        page_param="page",
        max_pages=50,
        requires_playwright=True,
        wait_for_selector=None,         # __NEXT_DATA__ không cần wait selector
        download_delay=2.0,
        job_id_pattern=r"-([A-Za-z0-9]+)$",   # Lấy segment cuối: "...-1643" → "1643"
    ),

    "topcv": SiteConfig(
        name="topcv",
        start_url="https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-cr257",
        page_param="page",
        max_pages=100,
        requires_playwright=True,       # Bật Playwright — plain HTTP dễ bị 403 hơn
        wait_for_selector=None,
        download_delay=1.5,
        job_id_pattern=r"/(\d+)\.html$",
    ),

    "vietnamworks": SiteConfig(
        name="vietnamworks",
        start_url="https://www.vietnamworks.com/viec-lam?q=it",  # IT category
        page_param="page",
        max_pages=100,
        requires_playwright=True,
        wait_for_selector=None,
        download_delay=2.0,
        job_id_pattern=r"-(\d+)-jv",    # không dùng $ vì URL có thể còn query params
    ),

    # LinkedIn yêu cầu đăng nhập — cần xử lý auth cookie riêng
    # TODO: Research ToS và cơ chế auth trước khi crawl thật
    "linkedin": SiteConfig(
        name="linkedin",
        start_url="https://www.linkedin.com/jobs/search/?keywords=software+engineer&location=Vietnam",
        page_param="start",             # LinkedIn dùng offset, không phải page number
        max_pages=40,                   # 25 jobs/page × 40 = 1000 jobs
        requires_playwright=True,
        wait_for_selector=None,
        download_delay=3.0,             # Anti-bot mạnh → delay cao hơn
        job_id_pattern=r"/(\d+)/",
    ),
}
