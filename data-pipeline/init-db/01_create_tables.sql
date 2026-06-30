-- Chạy tự động lần đầu khi PostgreSQL container khởi động.
-- Tạo bảng lưu metadata của mỗi job đã crawl.

CREATE TABLE IF NOT EXISTS raw_job_postings (
    id                BIGSERIAL PRIMARY KEY,
    source_site       VARCHAR(50)  NOT NULL,            -- "itviec", "topcv", ...
    source_job_id     VARCHAR(255) NOT NULL,            -- ID job trên site gốc
    source_url        TEXT         NOT NULL,            -- URL đầy đủ
    minio_path        TEXT         DEFAULT '',          -- Path HTML trong MinIO
    crawled_at        TIMESTAMPTZ  NOT NULL,            -- Thời điểm crawl (UTC)
    http_status_code  SMALLINT     DEFAULT 200,
    content_length    INTEGER      DEFAULT 0,
    content_checksum  VARCHAR(32)  DEFAULT '',          -- MD5 của HTML
    playwright_used   BOOLEAN      DEFAULT FALSE,
    etl_status        VARCHAR(20)  DEFAULT 'PENDING',   -- PENDING | PROCESSING | DONE | FAILED
    created_at        TIMESTAMPTZ  DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  DEFAULT NOW(),

    -- Tránh duplicate: mỗi job_id trên mỗi site chỉ lưu 1 lần
    CONSTRAINT uq_source UNIQUE (source_site, source_job_id)
);

-- Index để query nhanh theo site và trạng thái ETL
CREATE INDEX IF NOT EXISTS idx_raw_jobs_site        ON raw_job_postings (source_site);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_etl_status  ON raw_job_postings (etl_status);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_crawled_at  ON raw_job_postings (crawled_at DESC);
