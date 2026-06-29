from dataclasses import dataclass
from datetime import datetime

# Dataclass dùng để lưu dữ liệu thô (raw data) của một tin tuyển dụng
# ngay sau khi crawl từ website, trước khi được xử lý hoặc chuẩn hóa.
@dataclass
class RawJob:
    # Tên website nguồn (ví dụ: vietnamworks, topcv, linkedin...)
    source_site: str

    # ID của tin tuyển dụng trên website nguồn
    source_job_id: str

    # Đường dẫn (URL) gốc của tin tuyển dụng
    source_url: str

    # Nội dung HTML gốc của trang tuyển dụng.
    # Có thể là None nếu không lưu HTML.
    raw_html: str | None

    # Dữ liệu JSON gốc lấy từ API hoặc website.
    # Có thể là None nếu nguồn không trả về JSON.
    raw_json: dict | None

    # Thời điểm hệ thống crawl và lưu dữ liệu
    crawled_at: datetime