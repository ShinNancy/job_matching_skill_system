# jobcrawler/items.py
# RawJob — data class lưu dữ liệu thô ngay sau khi crawl, chưa qua xử lý.

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawJob:
    # ── Thông tin định danh ───────────────────────────────────────────────────
    source_site: str        # Tên site nguồn: "itviec", "topcv", ...
    source_job_id: str      # ID job trên site gốc
    source_url: str         # URL gốc của trang job

    # ── Nội dung thô ─────────────────────────────────────────────────────────
    raw_html: str | None    # HTML đầy đủ của trang (None nếu không lưu)
    raw_json: dict | None   # JSON từ __NEXT_DATA__ hoặc API (None nếu không có)

    # ── Metadata crawl ────────────────────────────────────────────────────────
    crawled_at: datetime    # Thời điểm crawl (UTC)

    # ── Fields có giá trị mặc định ────────────────────────────────────────────
    http_status_code: int = 200         # HTTP status code của response
    content_length: int = 0             # Kích thước HTML (bytes)
    content_checksum: str = ""          # MD5 của HTML — dùng để detect thay đổi
    playwright_used: bool = False       # True nếu dùng Playwright để render
    minio_path: str = ""                # Object path trong MinIO sau khi upload
