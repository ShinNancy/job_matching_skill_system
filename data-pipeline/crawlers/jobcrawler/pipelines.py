# jobcrawler/pipelines.py
# Item Pipelines — xử lý RawJob theo thứ tự sau khi Spider yield ra.
# Thứ tự thực thi được khai báo trong settings.py (số nhỏ chạy trước).

import io
import logging
import os

import psycopg2
import psycopg2.extras
from minio import Minio
from minio.error import S3Error
from scrapy.exceptions import DropItem

from jobcrawler.items import RawJob

logger = logging.getLogger(__name__)


# ── Pipeline 1: Validation (priority 100) ────────────────────────────────────
# Kiểm tra dữ liệu hợp lệ trước khi lưu. Item lỗi bị drop ngay tại đây.

class ValidationPipeline:

    def open_spider(self, spider):
        self.dropped_count = 0  # Fix: không được dùng self.open_spider = 0

    def close_spider(self, spider):
        logger.info("ValidationPipeline: dropped %d invalid items", self.dropped_count)

    def process_item(self, item: RawJob, spider) -> RawJob:
        if not item.source_url:
            self.dropped_count += 1
            raise DropItem(f"Missing source_url: site={item.source_site}")

        if not item.source_job_id:
            self.dropped_count += 1
            raise DropItem(f"Missing source_job_id: url={item.source_url}")

        # Cả HTML lẫn JSON đều None → crawl thất bại hoàn toàn
        if item.raw_html is None and item.raw_json is None:
            self.dropped_count += 1
            raise DropItem(f"No content: {item.source_url}")

        # HTML quá ngắn → nhiều khả năng bị block hoặc CAPTCHA
        if item.raw_html and item.content_length < 500:
            self.dropped_count += 1
            raise DropItem(f"Suspiciously short ({item.content_length}B): {item.source_url}")

        return item


# ── Pipeline 2: Deduplication (priority 200) ─────────────────────────────────
# Bỏ qua job đã thấy trong cùng 1 run.
# TODO: Thay in-memory set bằng Redis để dedup across runs.

class DedupPipeline:

    def open_spider(self, spider):
        self.seen: set[str] = set()
        self.dedup_count = 0

    def close_spider(self, spider):
        logger.info("DedupPipeline: skipped %d duplicates", self.dedup_count)

    def process_item(self, item: RawJob, spider) -> RawJob:
        key = f"{item.source_site}:{item.source_job_id}"
        if key in self.seen:
            self.dedup_count += 1
            raise DropItem(f"Duplicate: {key}")
        self.seen.add(key)
        return item


# ── Pipeline 3: MinIO Storage (priority 300) ──────────────────────────────────
# Upload raw HTML lên MinIO.
# Path convention: {site}/{year}/{month}/{day}/{job_id}.html

class MinIOPipeline:

    def open_spider(self, spider):
        self.client = None
        self.bucket = os.getenv("MINIO_BUCKET", "raw-jobs")
        self.upload_count = 0
        self.error_count = 0
        try:
            self.client = Minio(
                endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
                secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
            )
            # Tạo bucket nếu chưa tồn tại (lần đầu chạy)
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info("Created MinIO bucket: %s", self.bucket)
        except Exception as e:
            # Không crash crawler khi MinIO chưa sẵn sàng — chỉ log warning
            logger.warning("MinIOPipeline: không kết nối được MinIO: %s", e)
            self.client = None

    def close_spider(self, spider):
        logger.info("MinIOPipeline: uploaded=%d, errors=%d", self.upload_count, self.error_count)

    def process_item(self, item: RawJob, spider) -> RawJob:
        if self.client is None or not item.raw_html:
            return item  # MinIO chưa kết nối hoặc không có HTML → bỏ qua

        ts = item.crawled_at
        object_name = (
            f"{item.source_site}/"
            f"{ts.year}/{ts.month:02d}/{ts.day:02d}/"
            f"{item.source_job_id}.html"
        )
        html_bytes = item.raw_html.encode("utf-8")

        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=io.BytesIO(html_bytes),
                length=len(html_bytes),
                content_type="text/html; charset=utf-8",
            )
            item.minio_path = object_name
            self.upload_count += 1
            logger.debug("Uploaded: %s", object_name)
        except S3Error as e:
            self.error_count += 1
            logger.error("MinIO upload failed [%s]: %s", item.source_url, e)

        return item


# ── Pipeline 4: PostgreSQL Storage (priority 400) ────────────────────────────
# Lưu metadata của job vào bảng raw_job_postings.
# Dùng ON CONFLICT để upsert — nếu URL đã tồn tại thì cập nhật và reset etl_status.

class PostgresPipeline:

    UPSERT_SQL = """
        INSERT INTO raw_job_postings (
            source_site, source_job_id, source_url,
            minio_path, crawled_at,
            http_status_code, content_length, content_checksum,
            playwright_used, etl_status
        ) VALUES (
            %(source_site)s, %(source_job_id)s, %(source_url)s,
            %(minio_path)s, %(crawled_at)s,
            %(http_status_code)s, %(content_length)s, %(content_checksum)s,
            %(playwright_used)s, 'PENDING'
        )
        ON CONFLICT (source_site, source_job_id) DO UPDATE SET
            crawled_at      = EXCLUDED.crawled_at,
            minio_path      = EXCLUDED.minio_path,
            content_checksum = EXCLUDED.content_checksum,
            etl_status      = 'PENDING';
    """

    def open_spider(self, spider):
        self.conn = psycopg2.connect(
            dsn=os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/jobmatching"
            )
        )
        self.conn.autocommit = False
        self.cursor = self.conn.cursor()
        self.insert_count = 0
        self.error_count = 0

    def close_spider(self, spider):
        # Guard: open_spider có thể đã fail → conn/cursor chưa được set
        if self.conn is None:
            logger.info("PostgresPipeline: không có kết nối DB để đóng")
            return
        try:
            self.conn.commit()
        finally:
            if self.cursor:
                self.cursor.close()
            self.conn.close()
        logger.info("PostgresPipeline: inserted/updated=%d, errors=%d", self.insert_count, self.error_count)

    def process_item(self, item: RawJob, spider) -> RawJob:
        try:
            self.cursor.execute(self.UPSERT_SQL, {
                "source_site":      item.source_site,
                "source_job_id":    item.source_job_id,
                "source_url":       item.source_url,
                "minio_path":       item.minio_path,
                "crawled_at":       item.crawled_at,
                "http_status_code": item.http_status_code,
                "content_length":   item.content_length,
                "content_checksum": item.content_checksum,
                "playwright_used":  item.playwright_used,
            })
            # Commit mỗi 100 items để tránh transaction quá lớn
            self.insert_count += 1
            if self.insert_count % 100 == 0:
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.error_count += 1
            logger.error("DB insert failed [%s]: %s", item.source_url, e)

        return item
