# crawl_strategy/decision.py
# Logic quyết định có fetch trang detail không, dựa vào Redis cache.
#
# Redis key schema:
#   KEY  : crawl:{site}:{job_id}          (HASH, TTL 90 ngày)
#   FIELDS:
#     list_checksum  — MD5 lần cuối thấy trên listing page
#     last_crawled   — ISO-8601 UTC lần cuối fetch detail
#     first_seen     — ISO-8601 UTC lần đầu phát hiện job
#
# Staleness intervals (dựa trên tuổi job tính từ first_seen):
#   0-7 ngày  → recrawl sau 1 ngày    (job mới, hay có update)
#   7-30 ngày → recrawl sau 7 ngày
#   30-90 ngày→ recrawl sau 30 ngày
#   90+ ngày  → recrawl sau 90 ngày   (job cũ, ít thay đổi)

import logging
from datetime import datetime, timezone
from enum import Enum

from .listing_item import ListingItem

logger = logging.getLogger(__name__)


class CrawlDecision(Enum):
    FETCH   = "fetch"    # Chưa từng thấy → fetch detail
    REFETCH = "refetch"  # Đã thấy nhưng có thay đổi hoặc stale → fetch lại
    SKIP    = "skip"     # Còn fresh, không có gì đổi → bỏ qua


class CrawlStrategy:
    """
    Dùng Redis để nhớ trạng thái qua nhiều lần crawl.
    Nếu Redis không kết nối được → luôn trả FETCH (crawl như cũ, không crash).
    """

    def __init__(self, redis_client, site_name: str):
        self.redis = redis_client   # redis.Redis instance hoặc None
        self.site = site_name

    # ── Public API ────────────────────────────────────────────────────────────

    def decide(self, item: ListingItem) -> CrawlDecision:
        """Trả quyết định cho 1 job. O(1) — 1 Redis HGETALL call."""
        if self.redis is None:
            return CrawlDecision.FETCH

        key = self._key(item.job_id)
        try:
            cached = self.redis.hgetall(key)
        except Exception as e:
            logger.warning("Redis HGETALL failed (%s) — fallback FETCH", e)
            return CrawlDecision.FETCH

        if not cached:
            return CrawlDecision.FETCH  # ① Chưa từng thấy

        now = datetime.now(timezone.utc)

        # ② source_updated_at mới hơn last_crawled
        if item.source_updated_at:
            last_crawled = self._parse_dt(cached.get(b"last_crawled"))
            if last_crawled and item.source_updated_at > last_crawled:
                logger.debug("REFETCH %s (source_updated_at mới hơn)", item.job_id)
                return CrawlDecision.REFETCH

        # ③ list_checksum thay đổi (title / company / salary đổi trên listing)
        cached_checksum = cached.get(b"list_checksum", b"").decode()
        if cached_checksum != item.list_checksum:
            logger.debug("REFETCH %s (list_checksum đổi)", item.job_id)
            return CrawlDecision.REFETCH

        # ④ Staleness interval đã hết
        first_seen   = self._parse_dt(cached.get(b"first_seen"))
        last_crawled = self._parse_dt(cached.get(b"last_crawled"))
        if first_seen and last_crawled:
            age_days     = (now - first_seen).days
            interval     = self._staleness_interval(age_days)
            elapsed_days = (now - last_crawled).days
            if elapsed_days >= interval:
                logger.debug(
                    "REFETCH %s (age=%dd, interval=%dd, elapsed=%dd)",
                    item.job_id, age_days, interval, elapsed_days
                )
                return CrawlDecision.REFETCH

        return CrawlDecision.SKIP

    def mark_crawled(self, item: ListingItem) -> None:
        """Ghi vào Redis sau khi đã fetch thành công. TTL reset về 90 ngày."""
        if self.redis is None:
            return
        key = self._key(item.job_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            # Giữ nguyên first_seen nếu đã tồn tại
            existing_first = self.redis.hget(key, "first_seen")
            first_seen = existing_first.decode() if existing_first else now_iso
            self.redis.hset(key, mapping={
                "list_checksum": item.list_checksum,
                "last_crawled":  now_iso,
                "first_seen":    first_seen,
            })
            self.redis.expire(key, 90 * 24 * 3600)  # 90 ngày
        except Exception as e:
            logger.warning("Redis HSET failed (%s) — bỏ qua cache update", e)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _key(self, job_id: str) -> str:
        return f"crawl:{self.site}:{job_id}"

    @staticmethod
    def _parse_dt(value: bytes | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.decode())
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _staleness_interval(age_days: int) -> int:
        """Trả số ngày tối thiểu giữa 2 lần crawl dựa vào tuổi job."""
        if age_days <= 7:  return 1
        if age_days <= 30: return 7
        if age_days <= 90: return 30
        return 90
