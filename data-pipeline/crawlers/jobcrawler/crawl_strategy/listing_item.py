# crawl_strategy/listing_item.py
# Dữ liệu 1 job lấy từ trang LISTING (trước khi vào trang detail).
# Đủ để quyết định có cần crawl detail hay không — không cần fetch thêm gì.

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ListingItem:
    job_id: str                         # ID trích từ URL (dùng job_id_pattern)
    url: str                            # URL trang detail (tuyệt đối hoặc tương đối)
    list_checksum: str                  # MD5(title + company + salary) từ trang listing
    source_updated_at: datetime | None = field(default=None)
    # ↑ Thời điểm site báo "job vừa cập nhật" — nếu có → so sánh với last_crawled
    # Không phải site nào cũng cung cấp; để None nếu không có.
